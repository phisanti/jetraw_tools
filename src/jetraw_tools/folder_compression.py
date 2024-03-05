import os
import nd2
import numpy as np
import ome_types
import tifffile
import dpcore
import locale
from .utils import flatten_dict, dict2ome, prepare_images, add_extension, create_compress_folder, convert_to_ascii
from .tiff_writer import imwrite
from .tiff_reader import imread

def compression_tool(folder_path, 
                     mode = "compress",
                    calibration_file=None, 
                    identifier="", 
                    image_extension=".tif", 
                    process_metadata=True, 
                    metadata_json=True, 
                    remove_source=False, 
                    verbose=False):
    """
    Compress a folder containing TIFF images to JetRaw compressed TIFF format.

    :param folder_path: The path to the folder containing the TIFF images.
    :type folder_path: str
    :param identifier: The identifier to be used for compression.
    :type identifier: str
    :param image_extension: The file extension of the images to be compressed. Default is ".tif".
    :type image_extension: str
    :param process_metadata: Flag indicating whether to include metadata in the compressed images. Default is True.
    :type process_metadata: bool
    :param metadata_json: Flag indicating whether to save metadata as JSON. Default is True.
    :type metadata_json: bool
    :param verbose: Flag indicating whether to print verbose output during compression. Default is False.
    :type verbose: bool
    """

    # Check image_extension
    if mode == "decompress":
        suffix = "_decompressed"
    else:
        suffix = "_compressed"
    
    valid_extensions = [".tif", ".nd2", ".ome.tif", ".p.tif", ".p.tiff"]
    if image_extension not in valid_extensions:
        raise ValueError(f"The image_extension must be either {valid_extensions}.")
    
    if calibration_file is None:
        raise ValueError("The calibration_file must be provided.")
    
    if identifier is None or identifier == "":
        raise ValueError("The identifier must be provided.")

    # Create output folder
    output_folder=create_compress_folder(folder_path, suffix=suffix)

    # Get images
    if os.path.isfile(folder_path) and folder_path.endswith(image_extension):
        image_files = [folder_path]
    else:
        image_files = [f for f in os.listdir(folder_path) if f.endswith(image_extension)]

    print(f"From folder: {folder_path}")
    for image_file in image_files:


        if verbose:
            print(f"Compressing {image_file}...")
        
        input_filename = os.path.join(folder_path, image_file)
        # If .nd2
        if image_extension == ".nd2":
            # Convert each ND2 image to TIFF
            with nd2.ND2File(input_filename) as img_nd2:
                img_map = img_nd2.asarray().astype(np.uint16)

                if process_metadata:
                    ome_metadata = img_nd2.ome_metadata()
                    metadata_dict = img_nd2.unstructured_metadata()
                    flatten_metadata = flatten_dict(metadata_dict)
                    metadata_dict.update(ome_metadata.dict())
                    ome_extra = dict2ome(flatten_metadata)
                    ome_metadata.structured_annotations.extend([ome_extra])
                    metadata=ome_metadata
                    
        # If .OME.TIFF
        if image_extension == ".ome.tif":
            with tifffile.TiffFile(input_filename) as tif:
                img_map = tif.asarray()
                if process_metadata:
                    metadata = tif.ome_metadata
                    metadata = ome_types.from_tiff(metadata)

        # If p.TIFF
        if image_extension == ".p.tif" or image_extension == ".p.tiff" :
            img_map = imread(input_filename)
            metadata = {}
            with tifffile.TiffFile(input_filename) as tif:
                if tif.imagej_metadata:
                    if process_metadata:
                        metadata["imagej_metadata"] = tif.imagej_metadata
                        metadata["ome_metadata"] = tif.ome_metadata

        # If .TIFF 
        if image_extension == ".tif":
            with tifffile.TiffFile(input_filename) as tif:
                if tif.imagej_metadata:
                    img_map = tif.asarray()
                    if process_metadata:
                        metadata = tif.imagej_metadata


        if mode == "compress":
            # Set OME Flag
            if process_metadata and image_extension in [".nd2", ".ome.tif"]:
                ome_bool=True
            elif process_metadata and image_extension==".tif":
                ome_bool=False
            else:
                metadata=None
                ome_bool=False
            
            # Validate output_tiff_filename
            output_tiff_filename = os.path.join(output_folder, image_file)
            print(f"Compressing image {image_file}...")
            output_tiff_filename=add_extension(output_tiff_filename, ome=ome_bool)
            process_image(img_map, output_tiff_filename, calibration_file, identifier, metadata, ome_bool, metadata_json)
        else:
            # Decompress
            base, ext = os.path.splitext(image_file)
            output_tiff_filename = os.path.join(output_folder, base + "_decompressed" + ".tif")
            print(f"Decompressing image {image_file}...")
            tifffile.imwrite(output_tiff_filename, img_map, description="")
            metadata=flatten_dict(metadata)
            metadata=convert_to_ascii(metadata)
            
            if process_metadata and metadata:
                try:
                    tifffile.tiffcomment(output_tiff_filename, metadata)
                except:
                    print("Metadata could not be added to the decompressed image.")

        # Check if output file exists and has size > 5% of the original image
        if remove_source:
            if os.path.exists(output_tiff_filename):
                original_size = os.path.getsize(input_filename)
                compressed_size = os.path.getsize(output_tiff_filename)
                if compressed_size > 0.05 * original_size:
                    # Delete original image
                    os.remove(input_filename)
    
    return True


def process_image(input_image, image_file, calibration_file, identifier, metadata, ome_bool, metadata_json):
    """
    Process an input image and compress it to JetRaw compressed TIFF format.

    :param input_image: The input image to be compressed.
    :type input_image: numpy.ndarray
    :param identifier: The identifier to be used for compression.
    :type identifier: str
    :param metadata: Flag indicating whether to include metadata in the compressed image.
    :type metadata: bool
    :param metadata_json: Flag indicating whether to save metadata as JSON.
    :type metadata_json: bool
    """

    # Prepare input image
    locale.setlocale(locale.LC_ALL, locale.getlocale())
    input_image = np.ascontiguousarray(input_image, dtype=np.uint16)
    dpcore.load_parameters(calibration_file)
    prepare_images(input_image, identifier=identifier)

    # Compress input image to JetRaw compressed TIFF format
    imwrite(image_file, input_image, description="", metadata=metadata, ome=ome_bool, as_json=metadata_json)