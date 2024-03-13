import numpy as np
import os
from sys import platform as _platform
import ctypes
import ctypes.util
import functools


# DPTiff Structure is an incomplete type
class _DPTiffStruct(ctypes.Structure):
    pass


_dptiff_ptr = ctypes.POINTER(_DPTiffStruct)


def _check_path_pointer_type(system):
    """Check the pointer type for the given OS"""

    if system == "windows":
        return ctypes.c_wchar_p
    elif system == "macOS" or system == "linux":
        return ctypes.c_char_p
    else:
        raise ValueError(
            f"Unknown system '{system}'. "
            "Expected one of 'windows', 'macOS' or 'linux'"
        )


def _adapt_path_to_os(path):
    """Adapt the path to the OS specific type"""

    system = _check_os()
    if system == "windows":
        return str(path)
    elif system == "macOS" or system == "linux":
        return bytes(path, "UTF-8")
    else:
        return path


def _check_os():
    """Check the current OS"""

    system = ""
    if _platform == "linux" or _platform == "linux2":
        system = "linux"
    elif _platform == "darwin":
        system = "macOS"
    elif _platform == "win32" or _platform == "win64":
        system = "windows"
    else:
        raise ValueError(f"Platform {_platform} is not supported.")

    return system


def _load_libraries():
    """Load the Jetraw dynamic libraries"""

    system = _check_os()
    # search for jetraw dir

    try:
        # add current path to PATH in case jetraw libraries are placed in here
        pyjetraw_path = os.path.dirname(os.path.abspath(__file__))
        env_path = os.environ["PATH"].split(os.pathsep)
        if pyjetraw_path not in env_path:
            os.environ["PATH"] = os.pathsep.join([pyjetraw_path] + env_path)

        path_to_jetraw = ctypes.util.find_library("jetraw")
        path_to_jetraw_tiff = ctypes.util.find_library("jetraw_tiff")

        _jetraw_lib = ctypes.cdll.LoadLibrary(path_to_jetraw)
        _jetraw_tiff_lib = ctypes.cdll.LoadLibrary(path_to_jetraw_tiff)

    except OSError:
        raise ImportError(f"JetRaw C libraries could not be loaded.")

    # Register function signature
    _jetraw_lib.dp_status_description.argtypes = [ctypes.c_uint32]
    _jetraw_lib.dp_status_description.restype = ctypes.c_char_p

    # Register jetraw_encode function signature
    _jetraw_lib.jetraw_encode.argtypes = [
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_int32),
    ]

    # Register jetraw_decode function signature
    _jetraw_lib.jetraw_decode.argtypes = [
        ctypes.c_char_p,
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.c_int32,
    ]

    # Register jetraw_tiff_open function signature
    _jetraw_tiff_lib.jetraw_tiff_open.argtypes = [
        _check_path_pointer_type(system),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.POINTER(_dptiff_ptr),
        ctypes.c_char_p,
    ]

    # Register jetraw_tiff_append function signature
    _jetraw_tiff_lib.jetraw_tiff_append.argtypes = [
        _dptiff_ptr,
        ctypes.POINTER(ctypes.c_ushort),
    ]

    # Register jetraw_tiff_read_page function signature
    _jetraw_tiff_lib.jetraw_tiff_read_page.argtypes = [
        _dptiff_ptr,
        ctypes.POINTER(ctypes.c_ushort),
        ctypes.c_int,
    ]

    # Register jetraw_tiff_close function signature
    _jetraw_tiff_lib.jetraw_tiff_close.argtypes = [ctypes.POINTER(_dptiff_ptr)]

    # getters for dp_tiff struct
    _jetraw_tiff_lib.jetraw_tiff_get_width.argtypes = [_dptiff_ptr]
    _jetraw_tiff_lib.jetraw_tiff_get_width.restype = ctypes.c_int
    _jetraw_tiff_lib.jetraw_tiff_get_height.argtypes = [_dptiff_ptr]
    _jetraw_tiff_lib.jetraw_tiff_get_height.restype = ctypes.c_int
    _jetraw_tiff_lib.jetraw_tiff_get_pages.argtypes = [_dptiff_ptr]
    _jetraw_tiff_lib.jetraw_tiff_get_pages.restype = ctypes.c_int

    return _jetraw_lib, _jetraw_tiff_lib


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
_jetraw_lib, _jetraw_tiff_lib = _load_libraries()

try:
    dp_status_as_exception(_jetraw_tiff_lib.jetraw_tiff_init)()
except RuntimeError as e:
    raise ImportError(e)
