import numpy as np
import tifffile
import ome_types
import ctypes
from typing import Optional, Union, List, Tuple, Any, Dict
from .jetraw_tiff import JetrawTiff


class TiffReader:
    """TiffReader reads a JetRaw compressed TIFF file from disk.

    The goal of TiffReader is to load the TIFF file into a numpy array.

    Any TiffWriter instance must be closed when finished, in order to
    do that the user needs to use the method close(). If using the
    feature "with" this close() method is called automatically at the end.

    Remember that TiffReader instances are not thread-safe.
    """

    def __init__(self, filepath: str) -> None:
        """Open TIFF file for reading.

        :param filepath: File name for TIFF file to be opened
        :type filepath: str
        """
        self._jrtif = JetrawTiff()
        self._jrtif.open(filepath, "r")

    def __del__(self) -> None:
        """Destructor that ensures the file is closed.

        Automatically called when the object is garbage collected.
        """
        self.close()

    def __enter__(self) -> "TiffReader":
        """Context manager entry.

        :returns: The TiffReader instance
        :rtype: TiffReader
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Optional[Any],
    ) -> None:
        """Context manager exit.

        :param exc_type: Exception type if an exception occurred
        :type exc_type: Optional[type]
        :param exc_value: Exception value if an exception occurred
        :type exc_value: Optional[Exception]
        :param traceback: Traceback if an exception occurred
        :type traceback: Optional[Any]
        """
        self.close()

    def close(self) -> None:
        """Close the TIFF file and release resources.

        Should be called when finished with the TiffReader instance.
        """
        if self._jrtif is not None:
            self._jrtif.close()
        self._jrtif = None

    @property
    def width(self) -> int:
        """Get the width of the TIFF image.

        :returns: Image width in pixels
        :rtype: int
        :raises RuntimeError: If file was already closed
        """
        if self._jrtif is None:
            raise RuntimeError("File was already closed.")
        return self._jrtif.width

    @property
    def height(self) -> int:
        """Get the height of the TIFF image.

        :returns: Image height in pixels
        :rtype: int
        :raises RuntimeError: If file was already closed
        """
        if self._jrtif is None:
            raise RuntimeError("File was already closed.")
        return self._jrtif.height

    @property
    def pages(self) -> int:
        """Get the number of pages in the TIFF file.

        :returns: Number of pages
        :rtype: int
        :raises RuntimeError: If file was already closed
        """
        if self._jrtif is None:
            raise RuntimeError("File was already closed.")
        return self._jrtif.pages

    def read(self, pages: Optional[Union[int, range, List[int]]] = None) -> np.ndarray:
        """Read pages from the TIFF file.

        :param pages: Indices of TIFF pages to be read. By default all pages are read
        :type pages: Optional[Union[int, range, List[int]]]
        :returns: Image data as numpy array
        :rtype: np.ndarray
        :raises IOError: If file was already closed
        """
        if self._jrtif is None:
            raise IOError("File was already closed.")

        # compute list to be read
        pages_list, num_pages = self._compute_list_to_read(pages)
        # create buffer for range of pages
        out = np.empty((num_pages, self.height, self.width), dtype=np.uint16)

        c_uint16_p = ctypes.POINTER(ctypes.c_uint16)
        for i, page_idx in enumerate(pages_list):
            buf = out[i].ctypes.data_as(c_uint16_p)
            self._jrtif._read_page_buffer(buf, page_idx)

        return np.squeeze(out)

    def _compute_list_to_read(
        self, pages: Optional[Union[int, range, List[int]]]
    ) -> Tuple[List[int], int]:
        """Compute the list of page indices to read.

        :param pages: Page specification (int, range, list, or None for all pages)
        :type pages: Optional[Union[int, range, List[int]]]
        :returns: Tuple of (page indices list, number of pages)
        :rtype: Tuple[List[int], int]
        :raises TypeError: If pages parameter has invalid type
        """
        if pages is None:
            pages_list = list(range(self.pages))
            num_pages = len(pages_list)
        elif isinstance(pages, int):
            pages_list = [pages]
            num_pages = 1
        else:
            try:
                pages_list = list(pages)
            except TypeError as e:
                raise TypeError(
                    f"Invalid type for pages: {e}. Use e.g. array, list, int."
                )
            num_pages = len(pages_list)

        return pages_list, num_pages


def imread(
    input_tiff_filename: str, pages: Optional[Union[int, range, List[int]]] = None
) -> np.ndarray:
    """Read JetRaw compressed TIFF file from disk and store in numpy array.

    Refer to the TiffReader class and its read function for more information.

    :param input_tiff_filename: File name of input TIFF file to be read from disk
    :type input_tiff_filename: str
    :param pages: Indices of TIFF pages to be read. By default all pages are read
    :type pages: Optional[Union[int, range, List[int]]]
    :returns: Image data as numpy array
    :rtype: np.ndarray
    """
    # read TIFF image pages and return numpy array
    with TiffReader(input_tiff_filename) as jetraw_reader:
        image = jetraw_reader.read(pages)
        return image


def read_metadata(
    input_tiff_filename: str, ome: bool = False
) -> Union[Dict[str, Any], Any]:
    """Read metadata from a TIFF file.

    :param input_tiff_filename: The path to the input TIFF file
    :type input_tiff_filename: str
    :param ome: Whether to read OME metadata. Defaults to False
    :type ome: bool
    :returns: The metadata read from the TIFF file
    :rtype: Union[Dict[str, Any], Any]
    """

    # Read the TIFF file
    with tifffile.TiffFile(input_tiff_filename) as tif:
        if ome:
            metadata_read = tif.ome_metadata
            metadata_read = ome_types.from_xml(metadata_read)
        else:
            metadata_read = tif.imagej_metadata

        return metadata_read
