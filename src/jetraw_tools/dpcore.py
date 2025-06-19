import ctypes
import ctypes.util
import functools
from typing import Callable, Any
import numpy as np
from .libs import (
    _load_libraries,
    _adapt_path_to_os,
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


def set_loglevel(level: str) -> None:
    """Set the logging level for DPCore operations.

    :param level: Log level ('NONE', 'INFO', or 'DEBUG')
    :type level: str
    :raises ValueError: If level is not one of the valid options
    """
    levels = ["NONE", "INFO", "DEBUG"]
    if level.upper() not in levels:
        raise ValueError("Log level has to be one of " + str(levels))

    idx = levels.index(level.upper())
    _dpcore_lib.dpcore_set_loglevel(idx)


@dp_status_as_exception
def set_logfile(path: str) -> int:
    """Set the log file path for DPCore operations.

    :param path: Path to the log file
    :type path: str
    :returns: DPCore status code
    :rtype: int
    """
    cpath = _adapt_path_to_os(path)
    return _dpcore_lib.dpcore_set_logfile(cpath)


@dp_status_as_exception
def load_parameters(path: str) -> int:
    """Load DPCore parameters from a file.

    :param path: Path to the parameters file
    :type path: str
    :returns: DPCore status code
    :rtype: int
    """
    cpath = _adapt_path_to_os(path)
    return _dpcore_lib.dpcore_load_parameters(cpath)


@dp_status_as_exception
def prepare_image(image: np.ndarray, identifier: str, error_bound: int = 1) -> int:
    """Prepare an image for DPCore processing.

    :param image: Input image array
    :type image: np.ndarray
    :param identifier: Image identifier string
    :type identifier: str
    :param error_bound: Error bound for processing (default: 1)
    :type error_bound: int
    :returns: DPCore status code
    :rtype: int
    """
    return _dpcore_lib.dpcore_prepare_image(
        image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)),
        image.size,
        bytes(identifier, "UTF-8"),
        error_bound,
    )


@dp_status_as_exception
def embed_meta(image: np.ndarray, identifier: str, error_bound: int = 1) -> int:
    """Embed metadata into an image using DPCore.

    :param image: Input image array
    :type image: np.ndarray
    :param identifier: Image identifier string
    :type identifier: str
    :param error_bound: Error bound for processing (default: 1)
    :type error_bound: int
    :returns: DPCore status code
    :rtype: int
    """
    return _dpcore_lib.dpcore_embed_meta(
        image.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)),
        image.size,
        bytes(identifier, "UTF-8"),
        error_bound,
    )
