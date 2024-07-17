from .jetraw_tiff import (  # noqa: F401
    JetrawTiff,
    _jetraw_lib,
    dp_status_as_exception,
)
from .tiff_reader import TiffReader, imread  # noqa: F401
from .tiff_writer import TiffWriter_5D, imwrite  # noqa: F401
import ctypes
import numpy as np
import locale

# TODO: these lines of code had a reason to be here but still not very clear when
# are really needed. More investigation needed. In windows environment these lines
# are commented out.

# The next two lines seem necessary. Otherwise, the C++ runtime raises an
# exception:
#   libc++abi.dylib: terminating with uncaught exception of type
#   std::runtime_error: collate_byname<char>::collate_byname failed
#   to construct for C/en_US.UTF-8/C/C/C/C

# import locale

try:
    locale.setlocale(locale.LC_ALL, locale.getlocale())
except locale.Error:
    print(
        "Warning: The system's default locale is unsupported. Falling back to the default 'C' locale."
    )
    locale.setlocale(locale.LC_ALL, "C")  # Fallback to the default 'C' locale


def encode_raw(image):
    """Encode input 2D numpy array image (uint16 pixel type) using JetRaw compression.

    Parameters
    ----------
    image : 2D numpy array
        Input image with pixel type uint16. Already dpcore prepared.

    Returns
    -------
    Encoded 1D buffer (int8 type).

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


def encode(image):
    """Encode input 2D numpy array image using JetRaw compression.
    The encoded output 1D buffer stores the original shape of the input image in
    the first 8 bytes of the buffer (4 bytes width - 4 bytes height)

    Parameters
    ----------
    image : 2D numpy array
        Input image with pixel type uint16. Already dpcore prepared.

    Returns
    -------
    Encoded 1D buffer with type int8. Original image shape is stored at the beginning of buffer.

    """
    encoded = encode_raw(image)
    shape = np.array(image.shape, dtype=np.uint32)
    return np.r_[shape.view(dtype="b"), encoded]


def decode_raw(raw_encoded_image, output):
    """Decode input raw_encoded_image and result is stored in output parameter.

    Parameters
    ----------
    raw_encoded_image : 1D numpy array
        Jetraw encoded input buffer with int8 type.
    output : 2D numpy array
        Container for decoded image with original image shape and pixel type uint16.

    Returns
    -------
    None

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


def decode(encoded_image):
    """Decode input encoded_image and decoded 2D image is returned.

    Parameters
    ----------
    encoded_image : 1D numpy array
        Jetraw encoded input buffer with int8 type.

    Returns
    -------
    2D numpy array containing decoded image with pixel type uint16.

    """
    shape = encoded_image[:8].view(dtype=np.uint32)
    output = np.empty(shape, dtype=np.uint16)
    decode_raw(encoded_image[8:], output)
    return output
