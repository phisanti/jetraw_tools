import ctypes
import ctypes.util
import functools
from .libs import (
    _load_libraries,
    _adapt_path_to_os,
)

def dp_status_as_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        dp_status = func(*args, **kwargs)
        if dp_status != 0:
            message = _jetraw_lib.dp_status_description(dp_status).decode("utf-8")
            raise RuntimeError(message)

    return wrapper


# Initialize module
try:
    _jetraw_lib, _dpcore_lib = _load_libraries(lib="dpcore")
except (ImportError, AttributeError, OSError) as e:
    _jetraw_lib = None
    _dpcore_lib = None

try:
    _dpcore_lib.dpcore_init()
except (RuntimeError, AttributeError) as e:
    import warnings

    warnings.warn(f"DPCore C libraries could not be loaded: {e}")


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
