import nd2
import tifffile
import numpy as np
import ome_types
import os
from .tiff_reader import imread
from .utils import flatten_dict, dict2ome
from typing import Tuple, Union, Dict, Any


class ImageReader:
    """Class for reading microscopy images in various formats.

    :param input_filename: Path to the image file
    :param image_extension: File extension (.nd2, .tif, .tiff, etc)
    :param read_ome: Whether to read OME metadata, defaults to True
    :raises FileNotFoundError: If input file does not exist
    :raises ValueError: If extension is not supported
    """

    def __init__(
        self, input_filename: str, image_extension: str, read_ome: bool = True
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

        self.input_filename = input_filename
        self.image_extension = image_extension
        self.read_ome = read_ome

        pass

    def read_nd2_image(self) -> Tuple[np.ndarray, ome_types.OME]:
        """Read ND2 image file and metadata.

        :return: Tuple of (image array, OME metadata)
        :rtype: Tuple[np.ndarray, ome_types.OME]
        """
        with nd2.ND2File(self.input_filename) as img_nd2:
            img_map = img_nd2.asarray().astype(np.uint16)

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
        """Read TIFF image with optional OME metadata.

        :return: Tuple of (image array, metadata)
        :rtype: Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME, None]]
        """
        with tifffile.TiffFile(self.input_filename) as tif:
            img_map = tif.asarray()
            if self.read_ome:
                try:
                    metadata = ome_types.from_tiff(tif)
                except:
                    try:
                        metadata = ome_types.from_xml(tif.ome_metadata)
                    except:
                        metadata = None
            else:
                metadata = tif.imagej_metadata

        return img_map, metadata

    def read_p_tiff(self) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME]]:
        """Read pyramidal TIFF using specialized reader.

        :return: Tuple of (image array, metadata)
        :rtype: Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME]]
        """
        img_map = imread(self.input_filename)
        with tifffile.TiffFile(self.input_filename) as tif:
            if self.read_ome:
                metadata = ome_types.from_xml(tif.ome_metadata)
            else:
                metadata = tif.imagej_metadata

        return img_map, metadata

    def read_image(self) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME]]:
        """Read image based on file extension.

        :return: Tuple of (image array, metadata)
        :rtype: Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME]]
        """
        if self.image_extension == ".nd2":
            return self.read_nd2_image()
        elif self.image_extension in [".p.tif", ".p.tiff", ".ome.p.tif", ".ome.p.tiff"]:
            return self.read_p_tiff()
        else:
            return self.read_tiff()
