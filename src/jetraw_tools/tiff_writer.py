import numpy as np
import tifffile
import ome_types
from .jetraw_tiff import JetrawTiff
import json
from .utils import convert_to_ascii, flatten_dict, serialise
import json
from typing import Union, Optional, Any, Tuple


class TiffWriter_5D:
    """Writer for N-dimensional numpy arrays to JetRaw compressed TIFF files.

    TiffWriter_5D provides a high-level interface for writing multi-dimensional
    image data to disk using JetRaw compression. The class automatically handles
    dimension adaptation, ensuring input arrays are properly formatted for the
    underlying compression algorithm.

    The writer supports arrays with up to 5 dimensions (T, C, Z, Y, X) and
    automatically expands lower-dimensional inputs by adding singleton dimensions
    as needed. All input data must be C-contiguous for optimal
    compression performance.

    Examples:
        Basic usage with context manager:
        >>> with TiffWriter_5D('output.p.tiff') as writer:
        ...     writer.write(image_array)

        Writing multi-dimensional data:
        >>> with TiffWriter_5D('stack.p.tiff', 'Time-lapse data') as writer:
        ...     writer.write(timestack)  # Shape: (t, c, z, y, x)
    """

    def __init__(self, filepath: str, description: str = "") -> None:
        """Open TIFF file for writing.

        Open TIFF file for writing. An empty TIFF file is created if there is no input data passed.

        :param filepath: File name for output TIFF file
        :type filepath: str
        :param description: The subject of the image. Must be 7-bit ASCII. Cannot be used with the ImageJ or OME formats. Saved with the first page of a series only
        :type description: str
        """

        self.description = description
        self.fpath = filepath
        self.image_shape = None
        self._jrtif = None

    def __del__(self) -> None:
        """Destructor that ensures the file is closed.

        Automatically called when the object is garbage collected.
        """
        self.close()

    def __enter__(self) -> "TiffWriter_5D":
        """Context manager entry.

        :returns: The TiffWriter_5D instance
        :rtype: TiffWriter_5D
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the TIFF file and release resources.

        Should be called when finished with the TiffWriter_5D instance.
        """
        if self._jrtif is not None:
            try:
                self._jrtif.close()
            # Handle error when the upper with block is closed
            except RuntimeError as e:
                pass
        self._jrtif = None

    def write(self, image_buffer: np.ndarray) -> None:
        """Write image buffer to .p.tiff file.

        :param image_buffer: Image data to write. Must have dtype uint16
        :type image_buffer: np.ndarray
        :raises ValueError: If image dimensions are inconsistent or array is not contiguous
        :raises TypeError: If image dtype is not uint16
        """

        # Raise warnings
        if not image_buffer.flags["CONTIGUOUS"]:
            raise ValueError(
                "Input image array data must be contiguous. Please run np.ascontiguousarray(image_buffer) before prepare_images."
            )
        if not np.issubdtype(image_buffer.dtype, np.unsignedinteger):
            raise TypeError(
                f"Input data {image_buffer.dtype} is not supported. Should be an unsigned integer type (uint8, uint16, uint32, etc.)."
            )

        image_stack = self._check_and_adapt_input_image_5D(image_buffer)

        # Open file, if not already the case
        if self._jrtif is None:
            self._jrtif = JetrawTiff()
            self._jrtif.open(
                self.fpath,
                "w",
                self.image_shape[1],
                self.image_shape[0],
                self.description,
            )

        frames = image_stack.shape[0]
        slices = image_stack.shape[1]
        channels = image_stack.shape[2]
        # Iterate over pages based on dimensions
        for frame in range(frames):
            for slice in range(slices):  # Add frame iteration for 4D/5D
                for channel in range(channels):  # Add channel iteration for 5D
                    self._jrtif.append_page(
                        image_stack[frame, slice, channel]
                    )  # Adjust indexing

    def _check_and_adapt_input_image_5D(self, image: np.ndarray) -> np.ndarray:
        """Ensures consistent dimensions for iteration, adding dummy dimensions if needed.

        :param image: Input image array
        :type image: np.ndarray
        :returns: Image array with exactly 5 dimensions
        :rtype: np.ndarray
        :raises TypeError: If image dtype is not uint16
        :raises ValueError: If image dimensions are inconsistent or invalid
        """

        expected_dimensions = 5  # Assuming you need at least t, c, s, x, y
        while np.ndim(image) != expected_dimensions:
            image = np.expand_dims(image, axis=0)

        num_dimensions = np.ndim(image)
        if num_dimensions == expected_dimensions:
            if not np.issubdtype(image.dtype, np.unsignedinteger):
                raise TypeError(
                    f"Input data {image.dtype} is not supported. Should be an unsigned integer type (uint8, uint16, uint32, etc.)."
                )
            if self.image_shape is None:
                self.image_shape = image.shape[3:]
            elif self.image_shape != image.shape[3:]:
                raise ValueError(
                    "All images in the stack must have the same dimensions."
                )
        else:
            raise ValueError(
                "Input image data must be 2d (single image) or"
                " 3d (image stack), or 4d/5d (image hyperstack)."
            )

        return image


def imwrite(
    output_tiff_filename: str, input_image: np.ndarray, description: str = ""
) -> bool:
    """Write numpy array to a JetRaw compressed TIFF file.

    Refer to the TiffWriter class and its write function for more information.

    :param output_tiff_filename: File name of output TIFF file to be written into disk
    :type output_tiff_filename: str
    :param input_image: Input image buffer
    :type input_image: np.ndarray
    :param description: The subject of the image. Saved with the first page only
    :type description: str
    :returns: True if successful
    :rtype: bool
    :raises ValueError: If the input image is not contiguous
    """

    # Check if input image is contiguous
    if not input_image.flags["C_CONTIGUOUS"]:
        raise ValueError("The input image must be contiguous for proper compression.")

    # Call TiffWriter to write the compressed image
    with TiffWriter_5D(output_tiff_filename, description) as jetraw_writer:
        jetraw_writer.write(input_image)

    return True


def metadata_writer(
    output_tiff_filename: str,
    metadata: Union[ome_types.OME, dict] = None,
    ome_bool: bool = True,
    imagej: bool = False,
    as_json: bool = True,
) -> bool:
    """Write metadata to a TIFF file using various formats and export options.

    This function provides flexible metadata writing capabilities for TIFF files,
    supporting multiple metadata standards and export formats. It can embed metadata
    directly into the TIFF file following OME-XML or ImageJ conventions, and
    optionally export the metadata as a separate JSON file for external use.

    The function handles three main metadata workflows:
    - OME-XML format: Embeds structured metadata following OME-TIFF specification
    - ImageJ format: Flattens metadata for ImageJ compatibility
    - JSON export: Creates a human-readable JSON file alongside the TIFF

    :param output_tiff_filename: The output TIFF filename where metadata will be embedded
    :type output_tiff_filename: str
    :param metadata: The metadata to write, either as OME object or dictionary, defaults to None
    :type metadata: Union[ome_types.OME, dict]
    :param ome_bool: Whether to embed metadata using OME-XML format in TIFF comments, defaults to True
    :type ome_bool: bool
    :param imagej: Whether to embed flattened metadata for ImageJ compatibility, defaults to False
    :type imagej: bool
    :param as_json: Whether to export metadata as a separate JSON file, defaults to True
    :type as_json: bool
    :returns: True if the metadata writing operation was successful
    :rtype: bool
    """

    if as_json:
        json_filename = output_tiff_filename.replace(
            ".ome.p.tiff" if isinstance(metadata, ome_types.OME) else ".p.tiff", ".json"
        )

        try:
            metadata_dump = (
                json.loads(metadata.json())
                if isinstance(metadata, ome_types.OME)
                else metadata
            )
        except Exception:
            metadata_dump = convert_to_ascii(
                metadata.dict() if isinstance(metadata, ome_types.OME) else metadata
            )

        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(metadata_dump, f, indent=3, ensure_ascii=False, default=serialise)

    if ome_bool:
        if isinstance(metadata, ome_types.OME):
            tifffile.tiffcomment(
                output_tiff_filename, metadata.to_xml().encode("ascii", "ignore")
            )
        else:
            metadata = convert_to_ascii(metadata)
            metadata_str = json.dumps(serialise(metadata))

            tifffile.tiffcomment(output_tiff_filename, metadata_str)

    if imagej:
        if isinstance(metadata, ome_types.OME):
            metadata = convert_to_ascii(metadata.dict())
        else:
            metadata = convert_to_ascii(metadata)

        metadata = flatten_dict(metadata)
        metadata_str = json.dumps(serialise(metadata))
        tifffile.tiffcomment(output_tiff_filename, metadata_str)

    return True
