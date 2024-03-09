import nd2
import tifffile
import numpy as np
import ome_types
import os
from .tiff_reader import imread
from .utils import flatten_dict, dict2ome


class ImageReader:
    """
    The ImageReader class provides methods to read different types of image files.
    Each method returns a tuple containing the image data and metadata.

    Methods:
        read_nd2_image(): Reads .nd2 image files.
        read_ome_tiff(): Reads .ome.tif image files.
        read_p_tiff(): Reads .p.tif image files.
        read_tif_image(): Reads .tif image files.
        read_image(): Reads the image file specified in the constructor.
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
    

    def read_nd2_image(self):
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


    def read_ome_tiff(self):
        metadata = {}
        with tifffile.TiffFile(self.input_filename) as tif:
            img_map = tif.asarray()
            metadata = ome_types.from_tiff(metadata)
        
        return img_map, metadata


    def read_p_tiff(self):
        img_map = imread(self.input_filename)
        metadata = {}
        with tifffile.TiffFile(self.input_filename) as tif:
            metadata["imagej_metadata"] = tif.imagej_metadata
            metadata["ome_metadata"] = tif.ome_metadata
        return img_map, metadata


    def read_tif_image(self): 
        with tifffile.TiffFile(self.input_filename) as tif:
            img_map = tif.asarray()
            metadata = tif.imagej_metadata
        return img_map, metadata
    
    
    def read_image(self):
        if self.image_extension == ".nd2":
            return self.read_nd2_image()

        if self.image_extension in [".ome.tif", ".ome.tiff"]:
            return self.read_ome_tiff()

        if self.image_extension in [".p.tif", ".p.tiff", ".ome.p.tif", ".ome.p.tiff"]:
            return self.read_p_tiff()
        
        if self.image_extension in [".tif", ".tiff"]:
            return self.read_tif_image()
        
        pass