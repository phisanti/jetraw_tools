import os
import numpy as np
import tifffile
import dpcore
import locale
from .utils import prepare_images, add_extension, create_compress_folder
from .tiff_writer import imwrite, metadata_writer
from .image_reader import ImageReader

class CompressionTool:
    """
    A tool for compressing and decompressing images using the JetRaw algorithm.

    :param calibration_file: The calibration file to use.
    :type calibration_file: str, optional
    :param identifier: The identifier for the images.
    :type identifier: str, optional
    :param verbose: Whether to print verbose output.
    :type verbose: bool, optional
    """


    def __init__(self, calibration_file: str = None, identifier: str = "", verbose: bool = False):
        self.calibration_file = calibration_file
        self.identifier = identifier
        self.verbose = verbose
    

    def list_files(self, folder_path: str, image_extension: str) -> list:
        """
        List all files in a folder with a specific extension.

        :param folder_path: The path to the folder.
        :param image_extension: The image file extension.
        :return: A list of image files.
        """
        
        if os.path.isfile(folder_path) and folder_path.endswith(image_extension):
            image_files = [folder_path]
        else:
            image_files = [f for f in os.listdir(folder_path) if f.endswith(image_extension)]
        if len(image_files) == 0:
            print(f"No file found in the folder with extension {image_extension}")
        
        return image_files


    def compress_image(self, img_map: np.ndarray, target_file: str, metadata: dict, ome_bool: bool = True, metadata_json: bool = True) -> bool:
        """
        Compress an image.

        :param img_map: The image map.
        :param target_file: The target file.
        :param metadata: The metadata.
        :param ome_bool: Whether to use OME metadata.
        :param metadata_json: Whether to write metadata as JSON.
        :return: Whether the operation was successful.
        """

        # Prepare input image
        locale.setlocale(locale.LC_ALL, locale.getlocale())
        img_map = np.ascontiguousarray(img_map, dtype=np.uint16)
        dpcore.load_parameters(self.calibration_file)
        prepare_images(img_map, identifier=self.identifier)

        # Compress input image to JetRaw compressed TIFF format
        imwrite(target_file, img_map, description="")
        if metadata:
            if not ome_bool:
                imageJ_metadata = True
            else:
                imageJ_metadata = False
            metadata_writer(target_file, metadata=metadata, ome_bool=ome_bool, imagej=imageJ_metadata, as_json=metadata_json)

        return True


    def decompress_image(self, img_map: np.ndarray, target_file: str, metadata: dict, ome_bool: bool = True, metadata_json: bool = False) -> bool:
        """
        Decompress an image.

        :param img_map: The image map.
        :param target_file: The target file.
        :param metadata: The metadata.
        :param ome_bool: Whether to use OME metadata.
        :param metadata_json: Whether to write metadata as JSON.
        :return: Whether the operation was successful.
        """

        with tifffile.TiffWriter(target_file) as tif:
            tif.write(img_map)     
        if metadata:
            if not ome_bool:
                imageJ_metadata = True            
            else:
                imageJ_metadata = False

            metadata_writer(target_file, metadata=metadata, ome_bool=ome_bool, imagej=imageJ_metadata, as_json=metadata_json)
        
        return True


    def remove_files(self, output_tiff_filename: str, input_filename: str) -> None:
        """
        Remove files if the new file exists and its size is > 5% of the original.

        :param output_tiff_filename: The output TIFF filename.
        :param input_filename: The input filename.
        """

        # Verify that the new file exist with size > 5%original before removal
        if os.path.exists(output_tiff_filename):
            original_size = os.path.getsize(input_filename)
            compressed_size = os.path.getsize(output_tiff_filename)
            if compressed_size > 0.05 * original_size:
                os.remove(input_filename)


    def process_folder(self, 
                       folder_path: str, 
                       mode: str = "compress", 
                       image_extension: str = ".tiff", 
                       process_metadata: bool = True, 
                       ome_bool: bool = True, 
                       metadata_json: bool = True, 
                       remove_source: bool = False) -> None:
        """
        Process a folder of images.

        :param folder_path: The path to the folder.
        :param mode: The mode, either "compress" or "decompress".
        :param image_extension: The image file extension.
        :param process_metadata: Whether to process metadata.
        :param ome_bool: Whether to use OME metadata.
        :param metadata_json: Whether to write metadata as JSON.
        :param remove_source: Whether to remove the source files.
        """

        # Create output folder
        if mode == "decompress":
            suffix = "_decompressed"
        else:
            suffix = "_compressed"    
        output_folder=create_compress_folder(folder_path, suffix=suffix)
        image_files = self.list_files(folder_path, image_extension)

        # Iterate over images
        for image_file in image_files:

            if self.verbose:
                print(f"Processing {image_file}...")
                
            # Input/output files
            input_filename = os.path.join(folder_path, image_file)
            output_filename = os.path.join(output_folder, image_file)
            if not ome_bool and process_metadata:
                print("Metadata not allowed for *.p.tif files yet, omiting metadata...")
                process_metadata=False

            output_filename=add_extension(output_filename, image_extension, mode=mode, ome=ome_bool)

            # Read image and metadata
            image_reader = ImageReader(input_filename, image_extension)
            img_map, metadata = image_reader.read_image()

            if process_metadata is False:
                metadata={}
            
            if mode == "compress":
                self.compress_image(img_map, output_filename, metadata, ome_bool=ome_bool, metadata_json=metadata_json)
            elif mode == "decompress":
                self.decompress_image(img_map, output_filename, metadata, ome_bool=ome_bool, metadata_json=False)
            else:
                raise ValueError(f"Mode {mode} is not supported. Please use 'compress' or 'decompress'.")

            if remove_source:
                self.remove_files(output_filename, input_filename)

        return True