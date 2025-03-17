import numpy as np
import tifffile
import ome_types
from .jetraw_tiff import JetrawTiff
import json
from .utils import convert_to_ascii, flatten_dict, serialise
import json
from typing import Union


class TiffWriter_5D:
    """TiffWriter writes numpy array to a JetRaw compressed TIFF file.

    The goal of TiffWriter is to save the input numpy array/s to a JetRaw
    compressed TIFF file in disk.

    Any TiffWriter instance must be closed when finished, in order to
    do that the user needs to use the method close(). If using the
    feature "with" this close() method is called automatically at the end.

    Remember that TiffWriter instances are not thread-safe.

    """

    def __init__(self, filepath: str, description: str = "") -> None:
        """Open TIFF file for writing.
        Open TIFF file for writing. An empty TIFF file is created if there is no input data passed.

        :param str filepath: File name for output TIFF file
        :param str description: The subject of the image. Must be 7-bit ASCII. Cannot be used with the ImageJ or OME formats. Saved with the first page of a series only.
        """

        self.description = description
        self.fpath = filepath
        self.image_shape = None
        self._jrtif = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self._jrtif is not None:
            try:
                self._jrtif.close()
            # Handle error when the upper with block is closed
            except RuntimeError as e:
                pass
        self._jrtif = None

    def write(self, image_buffer: np.ndarray) -> None:
        """
        Write image buffer to .p.tiff file.

        :param numpy.ndarray image_buffer: Image data to write. Must have dtype uint16.
        :raises ValueError: If image dimensions are inconsistent.
        :raises TypeError: If image dtype is not uint16.
        """

        # Raise warnings
        if not image_buffer.flags["CONTIGUOUS"]:
            raise ValueError(
                "Input image array data must be contiguous. Please run np.ascontiguousarray(image_buffer) before prepare_images."
            )
        if image_buffer.dtype != "uint16":
            raise TypeError(
                f"Input data {image_buffer.dtype} is not supported.Should be uint16."
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

    def _check_and_adapt_input_image_5D(self, image):
        """Ensures consistent dimensions for iteration, adding dummy dimensions if needed."""

        expected_dimensions = 5  # Assuming you need at least t, c, s, x, y
        while np.ndim(image) != expected_dimensions:
            image = np.expand_dims(image, axis=0)

        num_dimensions = np.ndim(image)
        if num_dimensions == expected_dimensions:
            if image.dtype != "uint16":
                raise TypeError(
                    f"Input data {image.dtype} is not supported.Should be uint16."
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


def imwrite(output_tiff_filename, input_image, description=""):
    """Write numpy array to a JetRaw compressed TIFF file.
    Refer to the TiffWriter class and its write function for more information.

    :param output_tiff_filename: File name of output TIFF file to be written into disk.
    :param input_image: Input image buffer.
    :param description: The subject of the image. Saved with the first page only.
    :return: True
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
    """
    Write metadata to the final image file.

    :param output_tiff_filename: The output TIFF filename.
    :param metadata: The metadata to write, defaults to None.
    :param ome_bool: Whether to use OME metadata, defaults to True.
    :param imagej: Whether to use ImageJ metadata, defaults to False.
    :param as_json: Whether to write metadata as JSON, defaults to True.
    :return: Whether the operation was successful.
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
