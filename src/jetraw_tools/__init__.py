# Import non-jetraw dependent modules first
from .utils import setup_locale

setup_locale()
__version__ = "0.7.0"


# Define lazy loading functions
def get_jetraw_tiff():
    """Get JetrawTiff class, loading libraries if necessary."""
    try:
        from .jetraw_tiff import JetrawTiff, get_libraries

        # This doesn't load the libraries yet, just imports the class
        return JetrawTiff
    except ImportError as e:
        raise ImportError("JetrawTiff class could not be imported") from e


# Only expose what's needed without triggering imports
__all__ = [
    "CompressionTool",
    "get_config_manager",
    "get_jetraw_tiff",
    "TiffReader",
    "imread",
    "TiffWriter_5D",
    "imwrite",
]

# These don't depend on jetraw libraries
from .tiff_reader import TiffReader, imread
from .tiff_writer import TiffWriter_5D, imwrite
