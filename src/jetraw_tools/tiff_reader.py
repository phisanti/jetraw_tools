import numpy as np
import tifffile
import ome_types
import ctypes
from .jetraw_tiff import JetrawTiff


class TiffReader:
    """TiffReader reads a JetRaw compressed TIFF file from disk.

    The goal of TiffReader is to load the TIFF file into a numpy array.

    Any TiffWriter instance must be closed when finished, in order to
    do that the user needs to use the method close(). If using the
    feature "with" this close() method is called automatically at the end.

    Remember that TiffReader instances are not thread-safe.

    """

    def __init__(self, filepath):
        """Open TIFF file for reading.

        Parameters
        ----------
        filepath : str, path-like
            File name for TIFF file to be opened.
        """
        self._jrtif = JetrawTiff()
        self._jrtif.open(filepath, "r")

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self._jrtif is not None:
            self._jrtif.close()
        self._jrtif = None

    @property
    def width(self):
        if self._jrtif is None:
            raise RuntimeError("File was already closed.")
        return self._jrtif.width

    @property
    def height(self):
        if self._jrtif is None:
            raise RuntimeError("File was already closed.")
        return self._jrtif.height

    @property
    def pages(self):
        if self._jrtif is None:
            raise RuntimeError("File was already closed.")
        return self._jrtif.pages

    def read(self, pages=None):
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

    def _compute_list_to_read(self, pages):
        if pages is None:
            pages_list = range(self.pages)
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


def imread(input_tiff_filename, pages=None):
    """Read JetRaw compressed TIFF file from disk and store in numpy array.
    Refer to the TiffReader class and its read function for more information.

    Parameters
    ----------
    input_tiff_filename : str, path-like
        File name of input TIFF file to be read from disk.
    pages : int, range-like, list-like
        Indices of TIFF pages to be read. By default all pages are read.

    Returns
    -------
    None

    """
    # read TIFF image pages and return numpy array
    with TiffReader(input_tiff_filename) as jetraw_reader:
        image = jetraw_reader.read(pages)
        return image


def read_metadata(input_tiff_filename, ome=False):
    """
    Read metadata from a TIFF file.

    Args:
        input_tiff_filename (str): The path to the input TIFF file.
        ome (bool, optional): Whether to read OME metadata. Defaults to False.

    Returns:
        dict: The metadata read from the TIFF file.
    """

    # Read the TIFF file
    with tifffile.TiffFile(input_tiff_filename) as tif:
        if ome:
            metadata_read = tif.ome_metadata
            metadata_read = ome_types.from_xml(metadata_read)
        else:
            metadata_read = tif.imagej_metadata

        return metadata_read
