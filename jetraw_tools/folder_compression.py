import os
import nd2
import numpy as np
import ome_types
import utils
import tifffile
from .jetraw_tools import imwrite


def compress_folder(folder_path, identifier, image_extension=".tif", process_metadata=True, metadata_json=True, verbose=False):
    """
    Compress a folder containing TIFF images to JetRaw compressed TIFF format.

    :param folder_path: The path to the folder containing the TIFF images.
    :type folder_path: str
    :param identifier: The identifier to be used for compression.
    :type identifier: str
    :param image_extension: The file extension of the images to be compressed. Default is ".tif".
    :type image_extension: str
    :param metadata: Flag indicating whether to include metadata in the compressed images. Default is True.
    :type metadata: bool
    :param metadata_json: Flag indicating whether to save metadata as JSON. Default is True.
    :type metadata_json: bool
    :param verbose: Flag indicating whether to print verbose output during compression. Default is False.
    :type verbose: bool
    """

    # Check image_extension
    if image_extension not in [".tif", ".nd2", ".ome.tif"]:
        raise ValueError("The image_extension must be either '.tif', '.nd2', or '.ome.tif'.")

    # Create output folder
    output_folder = folder_path + "_compressed"
    if not os.path.exists(output_folder):
        root_folder = os.path.dirname(folder_path)
        os.makedirs(os.path.join(root_folder, output_folder))

    # Get images
    image_files = [f for f in os.listdir(folder_path) if f.endswith(image_extension)]

    for image_file in image_files:
        # If .nd2
        if image_extension == ".nd2":
        # Convert each ND2 image to TIFF
            input_nd2_filename = os.path.join(folder_path, image_file)
            with nd2.ND2File(input_nd2_filename) as img_nd2:
                img_map = img_nd2.asarray().astype(np.uint16)
                ome = img_nd2.ome_metadata()
                metadata_dict = img_nd2.unstructured_metadata()

            flatten_metadata = utils.flatten_dict(metadata_dict)
            metadata_dict.update(ome.dict())
            ome_extra = utils.dict2ome(flatten_metadata)
            ome.structured_annotations.extend([ome_extra])
                    
            if process_metadata:
                metadata=ome
                ome_bool=True
            else:
                metadata=None
                ome_bool=False

        # If .OME.TIFF
        if image_extension == "ome.tif":
            input_tiff_filename = os.path.join(folder_path, image_file)
            # Access OME-XML metadata (if present)
            with tifffile.TiffFile(input_tiff_filename) as tif:
                metadata = tif.ome_metadata
                metadata = ome_types.from_xml(metadata_read)
                img_map = tif.asarray()
    
        # If .TIFF 
        if image_extension == ".tif":
            input_tiff_filename = os.path.join(folder_path, image_file)#
            with tifffile.TiffFile(input_tiff_filename) as tif:
                if tif.imagej_metadata:
                    metadata = tif.imagej_metadata
                    img_map = tif.asarray()

        
            output_tiff_filename = os.path.join(output_folder, image_file.replace(".nd2", "p.tif"))
            process_image(img_map, output_tiff_filename, identifier, metadata, ome_bool, metadata_json)


def process_image(input_image, image_file, identifier, metadata, ome_bool, metadata_json):
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
    input_image = np.ascontiguousarray(input_image, dtype=np.uint16)
    utils.prepare_images(input_image, identifier=identifier)

    # Compress input image to JetRaw compressed TIFF format
    output_tiff_filename = image_file + ".p.tiff"
    imwrite(output_tiff_filename, input_image, description="", metadata=metadata, ome=ome_bool, as_json=metadata_json)