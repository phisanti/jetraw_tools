import numpy as np
import ctypes
import ctypes.util
import functools
from .libs import (
    _load_libraries,
    _adapt_path_to_os,
    _dptiff_ptr,
)


def dp_status_as_exception(func):
    """Decorator to raise exception on non-zero dp status"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        dp_status = func(*args, **kwargs)
        if dp_status != 0:
            message = _jetraw_lib.dp_status_description(dp_status).decode("utf-8")
            raise RuntimeError(message)

    return wrapper


class JetrawTiff:
    """Wrapper for Jetraw TIFF functions"""

    def __init__(self):
        self._handle = _dptiff_ptr()
        self._href = ctypes.byref(self._handle)

    @property
    def width(self):
        return _jetraw_tiff_lib.jetraw_tiff_get_width(self._handle)

    @property
    def height(self):
        return _jetraw_tiff_lib.jetraw_tiff_get_height(self._handle)

    @property
    def pages(self):
        return _jetraw_tiff_lib.jetraw_tiff_get_pages(self._handle)

    @dp_status_as_exception
    def open(self, path, mode, width=0, height=0, description=""):
        """Open a Jetraw TIFF file"""

        cpath = _adapt_path_to_os(path)
        cdescr = bytes(description, "UTF-8")
        cmode = bytes(mode, "UTF-8")
        return _jetraw_tiff_lib.jetraw_tiff_open(
            cpath, width, height, cdescr, self._href, cmode
        )

    @dp_status_as_exception
    def append_page(self, image):
        """Append a page to the TIFF"""

        bufptr = image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort))
        return _jetraw_tiff_lib.jetraw_tiff_append(self._handle, bufptr)

    @dp_status_as_exception
    def _read_page_buffer(self, bufptr, pageidx):
        return _jetraw_tiff_lib.jetraw_tiff_read_page(self._handle, bufptr, pageidx)

    def read_page(self, pageidx):
        """Read a page from the TIFF"""
        image = np.empty((self.height, self.width), dtype=np.uint16)
        bufptr = image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort))
        self._read_page_buffer(bufptr, pageidx)
        return image

    @dp_status_as_exception
    def close(self):
        """Close the TIFF file"""
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
