import nd2
import tifffile
import numpy as np
import ome_types
import os
from .tiff_reader import imread
from .utils import flatten_dict, dict2ome
from .logger import logger
from typing import Tuple, Union, Dict, Any, Optional


VALID_METADATA_FORMATS = ("ome", "imagej")

# Module-level dedup so each unique fallback warning fires once per process.
# Note: under multiprocessing.Pool, each worker subprocess maintains its own
# copy of this set, so a batch run will emit each unique warning at most once
# per worker (not once per file, but not globally deduped either).
_warned_messages: set = set()


def _warn_once(message: str) -> None:
    """Emit a warning at most once per process for a given message."""
    if message not in _warned_messages:
        _warned_messages.add(message)
        logger.warning(message)


def _try_parse_ome(xml: Optional[str]) -> Optional[ome_types.OME]:
    """Attempt to parse an OME-XML string. Return None on failure or empty input."""
    if xml is None:
        return None
    try:
        return ome_types.from_xml(xml)
    except Exception:
        return None


class ImageReader:
    """Class for reading microscopy images in various formats.

    :param input_filename: Path to the image file
    :param image_extension: File extension (.nd2, .tif, .tiff, etc)
    :param metadata_format: Preferred metadata format ('ome' or 'imagej').
        If the requested format is not available in the file, the reader
        falls back to the other format and emits a warning suggesting how
        to silence it. Defaults to 'ome'.
    :param read_metadata: If False, skip metadata parsing entirely and
        return None for metadata. Defaults to True.
    :raises FileNotFoundError: If input file does not exist
    :raises ValueError: If extension or metadata_format is not supported
    """

    def __init__(
        self,
        input_filename: str,
        image_extension: str,
        metadata_format: str = "ome",
        read_metadata: bool = True,
    ):
        if not os.path.isfile(input_filename):
            raise FileNotFoundError(f"No file found at {input_filename}")

        valid_extensions = [
            ".nd2",
            ".tif",
            ".tiff",
            ".ome.tif",
            ".ome.tiff",
            ".p.tif",
            ".p.tiff",
            ".ome.p.tif",
            ".ome.p.tiff",
        ]
        if image_extension not in valid_extensions:
            raise ValueError(f"The image_extension must be either {valid_extensions}.")

        if metadata_format not in VALID_METADATA_FORMATS:
            raise ValueError(
                f"metadata_format must be one of {VALID_METADATA_FORMATS}, "
                f"got {metadata_format!r}."
            )

        self.input_filename = input_filename
        self.image_extension = image_extension
        self.metadata_format = metadata_format
        self.read_metadata = read_metadata

    def _resolve_metadata(
        self, tif: tifffile.TiffFile
    ) -> Union[Dict[str, Any], ome_types.OME, None]:
        """Resolve metadata from a TIFF file according to the requested format.

        Tries the preferred format first; falls back to the other format with
        a deduplicated warning that suggests the flag to silence it.
        """
        fname = os.path.basename(self.input_filename)

        if self.metadata_format == "ome":
            ome = _try_parse_ome(tif.ome_metadata)
            if ome is not None:
                return ome
            if tif.imagej_metadata is not None:
                _warn_once(
                    f"No OME-XML metadata found in '{fname}'; falling back to "
                    f"ImageJ metadata. This file was likely compressed with "
                    f"JetRaw 26+. To silence this warning, re-run with: "
                    f"--metadata-format imagej"
                )
                return tif.imagej_metadata
            _warn_once(f"No OME-XML or ImageJ metadata found in '{fname}'.")
            return None

        # metadata_format == "imagej"
        if tif.imagej_metadata is not None:
            return tif.imagej_metadata
        ome = _try_parse_ome(tif.ome_metadata)
        if ome is not None:
            _warn_once(
                f"No ImageJ metadata found in '{fname}'; falling back to "
                f"OME-XML. To silence this warning, re-run with: "
                f"--metadata-format ome"
            )
            return ome
        _warn_once(f"No OME-XML or ImageJ metadata found in '{fname}'.")
        return None

    def read_nd2_image(
        self,
    ) -> Tuple[np.ndarray, Union[ome_types.OME, None]]:
        """Read ND2 image file and metadata.

        Note: ND2 files only expose OME metadata via the `nd2` library, so the
        `metadata_format` preference is ignored here. A debug message is
        emitted if the user requested 'imagej' to make this explicit.

        :return: Tuple of (image array, OME metadata or None if read_metadata=False)
        :rtype: Tuple[np.ndarray, Union[ome_types.OME, None]]
        """
        with nd2.ND2File(self.input_filename) as img_nd2:
            img_map = img_nd2.asarray().astype(np.uint16)

            if not self.read_metadata:
                return img_map, None

            if self.metadata_format == "imagej":
                logger.debug(
                    f"ND2 source '{os.path.basename(self.input_filename)}' only "
                    f"exposes OME metadata; '--metadata-format imagej' is ignored "
                    f"for the read step."
                )

            # Extract and combine metadata
            ome_metadata = img_nd2.ome_metadata()
            metadata_dict = img_nd2.unstructured_metadata()
            flatten_metadata = flatten_dict(metadata_dict)
            metadata_dict.update(ome_metadata.dict())
            ome_extra = dict2ome(flatten_metadata)
            ome_metadata.structured_annotations.extend([ome_extra])
            metadata = ome_metadata

        return img_map, metadata

    def read_tiff(
        self,
    ) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]:
        """Read TIFF image with metadata according to the requested format.

        :return: Tuple of (image array, metadata)
        :rtype: Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]
        """
        with tifffile.TiffFile(self.input_filename) as tif:
            img_map = tif.asarray()
            metadata = self._resolve_metadata(tif) if self.read_metadata else None

        return img_map, metadata

    def read_p_tiff(
        self,
    ) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]:
        """Read pyramidal TIFF using specialized reader.

        :return: Tuple of (image array, metadata)
        :rtype: Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]
        """
        img_map = imread(self.input_filename)
        if not self.read_metadata:
            return img_map, None
        with tifffile.TiffFile(self.input_filename) as tif:
            metadata = self._resolve_metadata(tif)

        return img_map, metadata

    def read_image(
        self,
    ) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]:
        """Read image based on file extension.

        :return: Tuple of (image array, metadata)
        :rtype: Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]
        """
        if self.image_extension == ".nd2":
            return self.read_nd2_image()
        elif self.image_extension in [".p.tif", ".p.tiff", ".ome.p.tif", ".ome.p.tiff"]:
            return self.read_p_tiff()
        else:
            return self.read_tiff()
