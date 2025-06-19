import numpy as np
import ctypes
import ctypes.util
import functools
from typing import Callable, Optional
from .libs import (
    _load_libraries,
    _adapt_path_to_os,
    _dptiff_ptr,
)


def dp_status_as_exception(func: Callable[..., int]) -> Callable[..., None]:
    """Decorator that converts DPCore status codes to exceptions.

    Wraps functions that return DPCore status codes and raises RuntimeError
    if the status code indicates an error (non-zero).

    :param func: Function that returns a DPCore status code
    :type func: Callable[..., int]
    :returns: Wrapped function that raises exceptions on error
    :rtype: Callable[..., None]
    :raises RuntimeError: If the wrapped function returns a non-zero status code
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        dp_status = func(*args, **kwargs)
        if dp_status != 0:
            message = _jetraw_lib.dp_status_description(dp_status).decode("utf-8")
            raise RuntimeError(message)

    return wrapper


class JetrawTiff:
    """Wrapper for Jetraw TIFF functions"""

    def __init__(self) -> None:
        """Initialize a new JetrawTiff instance.

        Creates a new TIFF handle for Jetraw operations.
        """
        self._handle = _dptiff_ptr()
        self._href = ctypes.byref(self._handle)

    @property
    def width(self) -> int:
        """Get the width of the TIFF image.

        :returns: Image width in pixels
        :rtype: int
        """
        return _jetraw_tiff_lib.jetraw_tiff_get_width(self._handle)

    @property
    def height(self) -> int:
        """Get the height of the TIFF image.

        :returns: Image height in pixels
        :rtype: int
        """
        return _jetraw_tiff_lib.jetraw_tiff_get_height(self._handle)

    @property
    def pages(self) -> int:
        """Get the number of pages in the TIFF file.

        :returns: Number of pages
        :rtype: int
        """
        return _jetraw_tiff_lib.jetraw_tiff_get_pages(self._handle)

    @dp_status_as_exception
    def open(
        self,
        path: str,
        mode: str,
        width: int = 0,
        height: int = 0,
        description: str = "",
    ) -> int:
        """Open a Jetraw TIFF file.

        :param path: Path to the TIFF file
        :type path: str
        :param mode: File opening mode
        :type mode: str
        :param width: Image width (default: 0)
        :type width: int
        :param height: Image height (default: 0)
        :type height: int
        :param description: Image description (default: "")
        :type description: str
        :returns: DPCore status code
        :rtype: int
        """

        cpath = _adapt_path_to_os(path)
        cdescr = bytes(description, "UTF-8")
        cmode = bytes(mode, "UTF-8")
        return _jetraw_tiff_lib.jetraw_tiff_open(
            cpath, width, height, cdescr, self._href, cmode
        )

    @dp_status_as_exception
    def append_page(self, image: np.ndarray) -> int:
        """Append a page to the TIFF file.

        :param image: Image array to append
        :type image: np.ndarray
        :returns: DPCore status code
        :rtype: int
        """

        bufptr = image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort))
        return _jetraw_tiff_lib.jetraw_tiff_append(self._handle, bufptr)

    @dp_status_as_exception
    def _read_page_buffer(
        self, bufptr: ctypes.POINTER(ctypes.c_ushort), pageidx: int
    ) -> int:
        """Read a page from the TIFF into a buffer.

        :param bufptr: Pointer to the buffer to read into
        :type bufptr: ctypes.POINTER(ctypes.c_ushort)
        :param pageidx: Page index to read
        :type pageidx: int
        :returns: DPCore status code
        :rtype: int
        """
        return _jetraw_tiff_lib.jetraw_tiff_read_page(self._handle, bufptr, pageidx)

    def read_page(self, pageidx: int) -> np.ndarray:
        """Read a page from the TIFF file.

        :param pageidx: Page index to read
        :type pageidx: int
        :returns: Image array containing the page data
        :rtype: np.ndarray
        """
        image = np.empty((self.height, self.width), dtype=np.uint16)
        bufptr = image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort))
        self._read_page_buffer(bufptr, pageidx)
        return image

    @dp_status_as_exception
    def close(self) -> int:
        """Close the TIFF file.

        :returns: DPCore status code
        :rtype: int
        """
        return _jetraw_tiff_lib.jetraw_tiff_close(self._href)


# Initialize module
try:
    _jetraw_lib, _jetraw_tiff_lib = _load_libraries(lib="jetraw")
except (ImportError, AttributeError, OSError) as e:
    _jetraw_lib = None
    _jetraw_tiff_lib = None

try:
    dp_status_as_exception(_jetraw_tiff_lib.jetraw_tiff_init)()
except (RuntimeError, AttributeError) as e:
    import warnings

    # Change error for warning
    warnings.warn(f"Jetraw C libraries could not be loaded: {e}")
