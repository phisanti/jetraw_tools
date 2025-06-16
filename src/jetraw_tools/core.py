from .jetraw_tiff import (  # noqa: F401
    _jetraw_lib,
    dp_status_as_exception,
)
import ctypes
import numpy as np


def encode_raw(image: np.ndarray) -> np.ndarray:
    """Encode input 2D numpy array image (uint16 pixel type) using JetRaw compression.

    :param image: Input image with pixel type uint16. Already dpcore prepared.
    :type image: np.ndarray
    :returns: Encoded 1D buffer (int8 type)
    :rtype: np.ndarray
    :raises ValueError: If image is not of dtype 'uint16' or not a 2D array
    """
    if image.dtype != np.uint16:
        raise ValueError("Image must be of dtype 'uint16'")
    if image.ndim != 2:
        raise ValueError("Image must be a 2D array.")

    output = np.empty(image.size, dtype="b")
    output_size = ctypes.c_int32(output.size)
    dp_status_as_exception(_jetraw_lib.jetraw_encode)(
        image.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
        image.shape[1],
        image.shape[0],
        output.ctypes.data_as(ctypes.c_char_p),
        ctypes.byref(output_size),
    )

    return output[: output_size.value]


def encode(image: np.ndarray) -> np.ndarray:
    """Encode input 2D numpy array image using JetRaw compression.

    The encoded output 1D buffer stores the original shape of the input image in
    the first 8 bytes of the buffer (4 bytes width - 4 bytes height).

    :param image: Input image with pixel type uint16. Already dpcore prepared.
    :type image: np.ndarray
    :returns: Encoded 1D buffer with type int8. Original image shape is stored at the beginning of buffer.
    :rtype: np.ndarray
    """
    encoded = encode_raw(image)
    shape = np.array(image.shape, dtype=np.uint32)
    return np.r_[shape.view(dtype="b"), encoded]


def decode_raw(raw_encoded_image: np.ndarray, output: np.ndarray) -> None:
    """Decode input raw_encoded_image and result is stored in output parameter.

    :param raw_encoded_image: Jetraw encoded input buffer with int8 type.
    :type raw_encoded_image: np.ndarray
    :param output: Container for decoded image with original image shape and pixel type uint16.
    :type output: np.ndarray
    :raises ValueError: If encoded image is not of dtype 'b'/'int8' or not a 1D array
    """
    if raw_encoded_image.dtype != np.dtype("b"):
        raise ValueError("Encoded image must be of dtype 'b' / 'int8'")
    if raw_encoded_image.ndim != 1:
        raise ValueError("Encoded image data must be 1d.")

    dp_status_as_exception(_jetraw_lib.jetraw_decode)(
        raw_encoded_image.ctypes.data_as(ctypes.c_char_p),
        raw_encoded_image.size,
        output.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
        output.size,
    )


def decode(encoded_image: np.ndarray) -> np.ndarray:
    """Decode input encoded_image and decoded 2D image is returned.

    :param encoded_image: Jetraw encoded input buffer with int8 type.
    :type encoded_image: np.ndarray
    :returns: 2D numpy array containing decoded image with pixel type uint16.
    :rtype: np.ndarray
    """
    shape = encoded_image[:8].view(dtype=np.uint32)
    output = np.empty(shape, dtype=np.uint16)
    decode_raw(encoded_image[8:], output)
    return output
