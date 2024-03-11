import nd2
import tifffile
import numpy as np
import ome_types
import os
from .tiff_reader import imread
from .utils import flatten_dict, dict2ome
from typing import Tuple, Union, Dict, Any

class ImageReader:
    """
    A class for reading images in various formats.

    :param input_filename: The input filename.
    :type input_filename: str
    :param image_extension: The image file extension.
    :type image_extension: str
    """

    def __init__(self, input_filename : str, image_extension : str):
        
        if not os.path.isfile(input_filename):
            raise FileNotFoundError(f"No file found at {input_filename}")
        
        valid_extensions = [".nd2", ".tif", ".tiff", ".ome.tif", ".ome.tiff", ".p.tif", ".p.tiff", ".ome.p.tif", ".ome.p.tiff"]
        if image_extension not in valid_extensions:
            raise ValueError(f"The image_extension must be either {valid_extensions}.")

        self.input_filename = input_filename
        self.image_extension = image_extension

        pass
    

    def read_nd2_image(self) -> Tuple[np.ndarray, ome_types.OME]:
        with nd2.ND2File(self.input_filename) as img_nd2:
            img_map = img_nd2.asarray().astype(np.uint16)

            ome_metadata = img_nd2.ome_metadata()
            metadata_dict = img_nd2.unstructured_metadata()
            flatten_metadata = flatten_dict(metadata_dict)
            metadata_dict.update(ome_metadata.dict())
            ome_extra = dict2ome(flatten_metadata)
            ome_metadata.structured_annotations.extend([ome_extra])
            metadata=ome_metadata

        return img_map, metadata


    def read_ome_tiff(self) -> Tuple[np.ndarray, ome_types.OME]:
        metadata = {}
        with tifffile.TiffFile(self.input_filename) as tif:
            img_map = tif.asarray()
            metadata = ome_types.from_tiff(metadata)
        
        return img_map, metadata


    def read_p_tiff(self, ome_bool: bool = False) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME]]:
        img_map = imread(self.input_filename)
        with tifffile.TiffFile(self.input_filename) as tif:
            if ome_bool:
                metadata = ome_types.from_xml(tif.ome_metadata)
            else:
                metadata = tif.imagej_metadata

        return img_map, metadata


    def ead_tif_image(self) -> Tuple[np.ndarray, Dict[str, Any]]: 
        with tifffile.TiffFile(self.input_filename) as tif:
            img_map = tif.asarray()
            metadata = tif.imagej_metadata
        return img_map, metadata
    
    
    def read_image(self) -> Tuple[np.ndarray, Union[Dict[str, Any], ome_types.OME]]:
        """
        Read any image.

        :return: The image map and metadata.
        """
        if self.image_extension == ".nd2":
            return self.read_nd2_image()

        if self.image_extension in [".p.tif", ".p.tiff", ".ome.p.tif", ".ome.p.tiff"]:
            if self.image_extension in [".ome.p.tif", ".ome.p.tiff"]:
                ome_bool = True
            else:
                ome_bool = False
            return self.read_p_tiff(ome_bool)

        if self.image_extension in [".ome.tif", ".ome.tiff"]:
            return self.read_ome_tiff()

        if self.image_extension in [".tif", ".tiff"]:
            return self.read_tif_image()
        
        pass