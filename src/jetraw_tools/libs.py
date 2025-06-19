import configparser
import ctypes
import os
from pathlib import Path
from sys import platform as _platform
from typing import Tuple, Union


class _DPTiffStruct(ctypes.Structure):
    """C structure for DPTiff objects.

    This is an incomplete type used for opaque pointers to DPTiff structures.
    """

    pass


_dptiff_ptr = ctypes.POINTER(_DPTiffStruct)


def _check_path_pointer_type(system: str) -> ctypes.c_char_p:
    """Determine the appropriate path pointer type for the given operating system.

    :param system: Operating system identifier ('windows', 'macOS', or 'linux')
    :type system: str
    :returns: The appropriate ctypes pointer type for file paths
    :rtype: ctypes.c_char_p or ctypes.c_wchar_p
    :raises ValueError: If the operating system is not supported
    """
    if system == "windows":
        return ctypes.c_wchar_p
    elif system == "macOS" or system == "linux":
        return ctypes.c_char_p
    else:
        raise ValueError(
            f"Unknown system '{system}'. Expected one of 'windows', 'macOS' or 'linux'"
        )


def _check_os() -> str:
    """Determine the current operating system.

    :returns: Operating system identifier ('windows', 'macOS', or 'linux')
    :rtype: str
    :raises ValueError: If the platform is not supported
    """
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


def _adapt_path_to_os(path: str) -> Union[str, bytes]:
    """Convert a path string to the appropriate format for the current OS.

    :param path: Path to be converted
    :type path: str
    :returns: Path in the appropriate format for the current OS
    :rtype: str or bytes
    """
    system = _check_os()
    if system == "windows":
        return str(path)
    elif system == "macOS" or system == "linux":
        return bytes(path, "UTF-8")
    else:
        return path


def _add_lib_paths(lib: str) -> bool:
    """Add library installation paths to the environment variables.

    Reads paths from configuration file and adds bin/lib directories
    to the appropriate environment variables.

    :param lib: Library identifier ('dpcore' or 'jetraw')
    :type lib: str
    :returns: True if paths were successfully added, False otherwise
    :rtype: bool
    """
    # Read configuration file
    config_file = os.path.expanduser("~/.config/jetraw_tools/jetraw_tools.cfg")
    config = configparser.ConfigParser()
    _os_platform = _check_os()
    try:
        config.read(config_file)

        # Get installation paths from config
        if "jetraw_paths" in config:
            install_path = None

            # Use the specific library path or fallback to the other one
            if lib == "dpcore" and "dpcore" in config["jetraw_paths"]:
                install_path = config["jetraw_paths"]["dpcore"]
            elif lib == "jetraw" and "jetraw" in config["jetraw_paths"]:
                install_path = config["jetraw_paths"]["jetraw"]

            if install_path:
                # Add bin directory to PATH
                bin_path = os.path.join(install_path, "bin")
                if os.path.exists(bin_path):
                    env_path = os.environ["PATH"].split(os.pathsep)
                    if bin_path not in env_path:
                        os.environ["PATH"] = os.pathsep.join([bin_path] + env_path)

                # Add lib directory to appropriate environment variable
                lib_path = os.path.join(install_path, "lib")
                if os.path.exists(lib_path):
                    # For macOS
                    if _os_platform == "macOS":
                        dyld_path = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
                        if lib_path not in dyld_path:
                            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = os.pathsep.join(
                                [lib_path]
                                + (dyld_path.split(os.pathsep) if dyld_path else [])
                            )
                    # For Linux
                    elif _os_platform == "linux":
                        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
                        if lib_path not in ld_path:
                            os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(
                                [lib_path]
                                + (ld_path.split(os.pathsep) if ld_path else [])
                            )
                    # For Windows, add to PATH
                    elif _os_platform == "windows":
                        if lib_path not in env_path:
                            os.environ["PATH"] = os.pathsep.join([lib_path] + env_path)

                return True
    except (FileNotFoundError, KeyError, configparser.Error) as e:
        import warnings

        warnings.warn(f"Error reading configuration: {e}")

    return False


def _load_libraries(lib: str) -> Tuple[ctypes.CDLL, ctypes.CDLL]:
    """Load the specified C libraries and configure function signatures.

    :param lib: Library identifier ('dpcore' or 'jetraw')
    :type lib: str
    :returns: Tuple of loaded libraries (jetraw_lib, dpcore_lib) or (jetraw_lib, jetraw_tiff_lib)
    :rtype: Tuple[ctypes.CDLL, ctypes.CDLL]
    :raises ValueError: If an invalid library is specified
    :raises ImportError: If libraries could not be loaded
    """
    system = _check_os()

    if lib not in ["dpcore", "jetraw"]:
        raise ValueError("Invalid library specified. Expected 'dpcore' or 'jetraw'.")

    # add current path to PATH in case jetraw libraries are placed in here
    _add_lib_paths(lib)

    if lib == "dpcore":
        try:
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

    elif lib == "jetraw":
        try:
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
