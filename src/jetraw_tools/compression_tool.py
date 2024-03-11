import os
import numpy as np
import tifffile
import dpcore
import locale
from .utils import prepare_images, add_extension, create_compress_folder
from .tiff_writer import imwrite, metadata_writer
from .image_reader import ImageReader

class CompressionTool:
    
    def __init__(self, calibration_file=None, identifier="", verbose=False):
        self.calibration_file = calibration_file
        self.identifier = identifier
        self.verbose = verbose
    
    def list_files(self, folder_path, image_extension):
        
        if os.path.isfile(folder_path) and folder_path.endswith(image_extension):
            image_files = [folder_path]
        else:
            image_files = [f for f in os.listdir(folder_path) if f.endswith(image_extension)]
        if len(image_files) == 0:
            print(f"No file found in the folder with extension {image_extension}")
        
        return image_files


    def compress_image(self, img_map, target_file, metadata, ome_bool=True, metadata_json=True):

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


    def decompress_image(self, img_map, target_file, metadata, ome_bool=True, metadata_json=False):

        #tifffile.imwrite(target_file, img_map, description="")

        with tifffile.TiffWriter(target_file) as tif:
            tif.write(img_map)     
        if metadata:
            if not ome_bool:
                imageJ_metadata = True            
            else:
                imageJ_metadata = False

            metadata_writer(target_file, metadata=metadata, ome_bool=ome_bool, imagej=imageJ_metadata, as_json=metadata_json)
        
        return True


    def remove_files(self, output_tiff_filename, input_filename):
        # Verify that the new file exist with size > 5%original before removal
        if os.path.exists(output_tiff_filename):
            original_size = os.path.getsize(input_filename)
            compressed_size = os.path.getsize(output_tiff_filename)
            if compressed_size > 0.05 * original_size:
                os.remove(input_filename)


    def process_folder(self, folder_path, mode="compress", image_extension=".tif", process_metadata=True, ome_bool=True, metadata_json=True, remove_source=False):

        # Check image_extension
        if mode == "decompress":
            suffix = "_decompressed"
        else:
            suffix = "_compressed"
        # Create output folder
            
        output_folder=create_compress_folder(folder_path, suffix=suffix)
        image_files = self.list_files(folder_path, image_extension)

        for image_file in image_files:

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