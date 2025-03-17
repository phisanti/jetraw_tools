import os
from sys import platform as _platform
import ctypes
import ctypes.util
import functools


def _check_path_pointer_type(system):
    if system == "windows":
        return ctypes.c_wchar_p
    elif system == "macOS" or system == "linux":
        return ctypes.c_char_p
    else:
        raise ValueError(
            f"Unknown system '{system}'. Expected one of 'windows', 'macOS' or 'linux'"
        )


def _adapt_path_to_os(path):
    system = _check_os()
    if system == "windows":
        return str(path)
    elif system == "macOS" or system == "linux":
        return bytes(path, "UTF-8")
    else:
        return path


def _check_os():
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
    system = _check_os()
    # search for jetraw dir

    try:
        # add current path to PATH in case jetraw libraries are placed in here
        pydpcore_path = os.path.dirname(os.path.abspath(__file__))
        env_path = os.environ["PATH"].split(os.pathsep)
        if pydpcore_path not in env_path:
            os.environ["PATH"] = os.pathsep.join([pydpcore_path] + env_path)

        path_to_jetraw = ctypes.util.find_library("jetraw")
        path_to_dpcore = ctypes.util.find_library("dpcore")

        _jetraw_lib = ctypes.cdll.LoadLibrary(path_to_jetraw)
        _dpcore_lib = ctypes.cdll.LoadLibrary(path_to_dpcore)

    except OSError:
        raise ImportError(f"JetRaw/DPCore C libraries could not be loaded.")

    # Register function signature
    _jetraw_lib.dp_status_description.argtypes = [ctypes.c_uint32]
    _jetraw_lib.dp_status_description.restype = ctypes.c_char_p

    _dpcore_lib.dpcore_set_logfile.argtypes = [_check_path_pointer_type(system)]

    _dpcore_lib.dpcore_load_parameters.argtypes = [_check_path_pointer_type(system)]

    _dpcore_lib.dpcore_prepare_image.argtypes = [
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.c_int32,
        ctypes.c_char_p,
        ctypes.c_float,
    ]

    _dpcore_lib.dpcore_embed_meta.argtypes = [
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.c_int32,
        ctypes.c_char_p,
        ctypes.c_float,
    ]
    return _jetraw_lib, _dpcore_lib


def dp_status_as_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        dp_status = func(*args, **kwargs)
        if dp_status != 0:
            message = _jetraw_lib.dp_status_description(dp_status).decode("utf-8")
            raise RuntimeError(message)

    return wrapper


# Initialize module
_jetraw_lib, _dpcore_lib = _load_libraries()

_dpcore_lib.dpcore_init()


def set_loglevel(level):
    levels = ["NONE", "INFO", "DEBUG"]
    if level.upper() not in levels:
        raise ValueError("Log level has to be one of " + str(levels))

    idx = levels.index(level.upper())
    _dpcore_lib.dpcore_set_loglevel(idx)


@dp_status_as_exception
def set_logfile(path):
    cpath = _adapt_path_to_os(path)
    return _dpcore_lib.dpcore_set_logfile(cpath)


@dp_status_as_exception
def load_parameters(path):
    cpath = _adapt_path_to_os(path)
    return _dpcore_lib.dpcore_load_parameters(cpath)


@dp_status_as_exception
def prepare_image(image, identifier, error_bound=1):
    return _dpcore_lib.dpcore_prepare_image(
        image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)),
        image.size,
        bytes(identifier, "UTF-8"),
        error_bound,
    )


@dp_status_as_exception
def embed_meta(image, identifier, error_bound=1):
    return _dpcore_lib.dpcore_embed_meta(
        image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)),
        image.size,
        bytes(identifier, "UTF-8"),
        error_bound,
    )
