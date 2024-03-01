import os
import dpcore
import numpy as np
import tifffile
from ome_types.model import MapAnnotation, Map
from ome_types.model.map import M


def add_extension(input_filename, ome=False):

    """Add an extension to a filename.
    
    :param filename: The filename to add the extension to
    :type filename: str
    :param ext: The extension to add, including the dot
    :type ext: str
    :returns: The filename with the extension added
    :rtype: str
    """

    base, ext = os.path.splitext(input_filename)
    if ome:
        output_filename = f"{base}.ome.p.tiff" 
    else:
        output_filename = f"{base}.p.tiff"

    return output_filename


def create_compress_folder(folder_path, suffix="_compressed"):
    """Create a folder for compressed images.
    :param folder_path: The path to the with the source images.
    :type folder_path: str
    :param suffix: The suffix to append to the compressed folder name. 
                  Default is "_compressed".
    :type suffix: str
    :returns: The path to the newly created compressed folder.
    :rtype: str
    """
        
    path = os.path.normpath(folder_path)
    folder_path_split = path.split(os.sep)
    compressed_folder_name = folder_path_split[-1] + suffix
    compressed_folder_path = os.path.join(os.sep.join(folder_path_split[:-1]), compressed_folder_name)
    
    if not os.path.exists(compressed_folder_path):
        os.makedirs(compressed_folder_path)
    
    return compressed_folder_path


def convert_to_ascii(data):
    """
    Converts the given data to ASCII encoding.

    :param data: The data to be converted.
    :type data: bytes or bytearray
    :return: The converted data in ASCII encoding.
    :rtype: str
    """
    if isinstance(data, dict):
        return {k: convert_to_ascii(v) for k, v in data.items()}
    elif isinstance(data, str):
        return data.encode('ascii', 'ignore').decode()
    else:
        return data
    

def flatten_dict(d):
    """
    Recursively flattens a nested dictionary.

    :param d: The dictionary to be flattened.
    :type d: dict
    :return: The flattened dictionary.
    :rtype: dict
    """
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result.update(flatten_dict(value))
        else:
            result[key] = value
    return result


def serialise(data):
    if isinstance(data, dict):
        return {key: serialise(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialise(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(serialise(item) for item in data)
    elif isinstance(data, set):
        return {serialise(item) for item in data}
    elif isinstance(data, frozenset):
        return frozenset(serialise(item) for item in data)
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    else:
        return str(data)


def dict2ome(metadata):
    """Converts metadata dictionary to OME MapAnnotation"""
    
    map_annotation = MapAnnotation(value=Map(m=[
                    M(k=_key, value=str(_value))
                    for _key, _value in metadata.items()
                ]))
    
    return map_annotation


def inspect_metadata(image_path, verbose=False):
    """
    Inspects the metadata of a TIFF image file.

    :param image_path: The path to the TIFF image file.
    :param verbose: Whether to print verbose output. Default is False.
    :return: A dictionary containing the metadata information.
    """

    metadata = {}

    with tifffile.TiffFile(image_path) as tif:
        # Access metadata for each page (image) in the file
        metadata['pages'] = []
        for page in tif.pages:
            page_metadata = {
                'dimensions': page.shape,
                'data_type': page.dtype,
                'compression': page.compression,
                'tags': {tag_id: str(tag_value) for tag_id, tag_value in page.tags.items()},
            }
            metadata['pages'].append(page_metadata)

            if verbose:
                print(f"Page {page.index} metadata: {page_metadata}")

        # Access OME-XML metadata (if present)
        if tif.ome_metadata:
            metadata['ome_metadata'] = tif.ome_metadata

        if tif.imagej_metadata:
            metadata['imagej_metadata'] = tif.imagej_metadata

        if verbose:
            print(f"OME-XML metadata: {metadata.get('ome_metadata')}")
            print(f"ImageJ metadata: {metadata.get('imagej_metadata')}")

    return metadata


def prepare_images(image_stack, depth=0, identifier=False, First_call=True, verbose=False):
    """
    Prepare images in the image stack for processing.

    :param image_stack: The image stack to be prepared. Must be a NumPy array.
    :type image_stack: np.ndarray
    :param depth: The depth level of the image stack. Defaults to 0.
    :type depth: int
    :param identifier: The identifier for the prepared images. Defaults to False.
    :type identifier: bool

    :raises TypeError: If the 'image_stack' parameter is not a NumPy array.
    :raises ValueError: If the 'identifier' parameter is not provided.

    :returns: None
    """

    # Check image and identifier
    if not image_stack.flags['C_CONTIGUOUS']:
        raise ValueError("The input image must be contiguous for proper compression.")

    if not isinstance(image_stack, np.ndarray):
        raise TypeError("The 'image_stack' parameter must be a NumPy array.")
    elif First_call:
        print(f'Image stack shape: {image_stack.shape}')
    
    if not identifier:
        raise ValueError("The 'identifier' parameter is not provided. Please provide an identifier.")

    # Prepare images in the stack
    if len(image_stack.shape) > 2:

        for i in range(image_stack.shape[depth]):
            prepare_images(image_stack[i], depth, identifier, First_call=False)

    elif len(image_stack.shape) == 2:
        if verbose:
            print("compress image")
        
        dpcore.prepare_image(image_stack, identifier)

    depth += 1

    return True


def reshape_tiff(image_stack, new_frames, new_slices = 1, new_channels = 1):
    
    # Get dimensions 
    z, y, x = image_stack.shape
    total_elements_5d = new_frames * new_slices * new_channels

    # Check if dimensions are compatible
    if z != total_elements_5d:
        raise ValueError("The total number of elements in the 3D stack must be equal to the total number of elements in the 5D stack.")

    # Reshape the 3D stack into a 5D stack
    image_stack_5d = np.reshape(image_stack, (new_frames, new_slices, new_channels, y, x))

    return image_stack_5d