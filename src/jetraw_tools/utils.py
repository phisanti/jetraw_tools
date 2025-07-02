import os
import numpy as np
import tifffile
import locale
import multiprocessing
from ome_types.model import MapAnnotation, Map
from ome_types.model.map import M
from .dpcore import prepare_image


def cores_validation(ncores: int) -> tuple[str, int, str]:
    """
    Validates the number of cores requested.

    :param ncores: The number of cores requested by the user.
    :type ncores: int
    :return: A tuple containing a status ('OK', 'WARN', 'ERROR'),
             the number of cores to use, and a message.
    :rtype: tuple[str, int, str]
    """
    logical_cores = multiprocessing.cpu_count()
    # Set a threshold for a fatal error (e.g., more than double the logical cores)
    error_threshold = logical_cores * 2

    if ncores > error_threshold:
        message = (
            f"Requested {ncores} cores, which is more than double the available {logical_cores} "
            f"logical cores. This is highly likely to cause system instability. Aborting."
        )
        return "ERROR", ncores, message

    if ncores > logical_cores:
        message = (
            f"Warning: Requested {ncores} cores, but the system only has {logical_cores} logical cores. "
            "This may lead to performance degradation due to context switching."
        )
        return "WARN", ncores, message

    if ncores == 0:
        validated_ncores = max(1, logical_cores - 1)
        message = f"Automatically selected {validated_ncores} cores for processing."
        return "OK", validated_ncores, message

    # This case covers ncores > 0 and <= logical_cores
    message = f"Using {ncores} cores for processing."
    return "OK", ncores, message


def setup_locale():
    """Set up locale correctly, with fallback to C locale if needed."""
    try:
        locale.setlocale(locale.LC_ALL, locale.getlocale())
    except locale.Error:
        print(
            "Warning: The system's default locale is unsupported. Falling back to the default 'C' locale."
        )
        locale.setlocale(locale.LC_ALL, "C")


def add_extension(
    input_filename: str, image_extension: str, mode: str, ome: bool = False
) -> str:
    """Add an extension to a filename.

    :param filename: The filename to add the extension to
    :param ext: The extension to add, including the dot
    :returns: The filename with the extension added
    """

    base = input_filename.replace(image_extension, "")

    if mode == "compress":
        if ome:
            output_filename = f"{base}.ome.p.tiff"
        else:
            output_filename = f"{base}.p.tiff"
    elif mode == "decompress":
        if ome:
            output_filename = f"{base}.ome.tiff"
        else:
            output_filename = f"{base}.tiff"
    else:
        raise ValueError(
            f"The mode set to {mode}, it must be either 'compress' or 'decompress'."
        )

    return output_filename


def create_compress_folder(folder_path: str, suffix: str = "_compressed") -> str:
    """Create a folder for compressed images.

    :param folder_path: The path to the folder with the source images.
    :param suffix: The suffix to append to the compressed folder name.
        Default is "_compressed".
    :returns: The path to the newly created compressed folder.
    """

    path = os.path.normpath(folder_path)
    folder_path_split = path.split(os.sep)
    compressed_folder_name = folder_path_split[-1] + suffix
    compressed_folder_path = os.path.join(
        os.sep.join(folder_path_split[:-1]), compressed_folder_name
    )

    if not os.path.exists(compressed_folder_path):
        os.makedirs(compressed_folder_path)

    return compressed_folder_path


def convert_to_ascii(data: dict) -> dict:
    """
    Converts the given data to ASCII encoding.

    :param data: The data to be converted.
    :return: The converted data in ASCII encoding.
    """
    if isinstance(data, dict):
        return {k: convert_to_ascii(v) for k, v in data.items()}
    elif isinstance(data, str):
        return data.encode("ascii", "ignore").decode()
    else:
        return data


def flatten_dict(d: dict) -> dict:
    """
    Recursively flattens a nested dictionary.

    :param d: The dictionary to be flattened.
    :return: The flattened dictionary.
    """
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result.update(flatten_dict(value))
        else:
            result[key] = value
    return result


def serialise(data: dict) -> str:
    """Serialise dictionary to write as json or similar"""

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


def dict2ome(metadata: dict) -> MapAnnotation:
    """Converts metadata dictionary to OME MapAnnotation"""

    map_annotation = MapAnnotation(
        value=Map(
            ms=[M(k=_key, value=str(_value)) for _key, _value in metadata.items()]
        )
    )

    return map_annotation


def inspect_metadata(image_path: str, verbose: bool = False) -> dict:
    """
    Inspects the metadata of a TIFF image file.

    :param image_path: The path to the TIFF image file.
    :param verbose: Whether to print verbose output. Default is False.
    :return: A dictionary containing the metadata information.
    """

    metadata = {}

    with tifffile.TiffFile(image_path) as tif:
        # Access metadata for each page (image) in the file
        metadata["pages"] = []
        for page in tif.pages:
            page_metadata = {
                "dimensions": page.shape,
                "data_type": page.dtype,
                "compression": page.compression,
                "tags": {
                    tag_id: str(tag_value) for tag_id, tag_value in page.tags.items()
                },
            }
            metadata["pages"].append(page_metadata)

            if verbose:
                print(f"Page {page.index} metadata: {page_metadata}")

        # Access OME-XML metadata (if present)
        if tif.ome_metadata:
            metadata["ome_metadata"] = tif.ome_metadata

        if tif.imagej_metadata:
            metadata["imagej_metadata"] = tif.imagej_metadata

        if verbose:
            print(f"OME-XML metadata: {metadata.get('ome_metadata')}")
            print(f"ImageJ metadata: {metadata.get('imagej_metadata')}")

    return metadata


def prepare_images(
    image_stack, depth=0, identifier=False, First_call=True, verbose=False
):
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
    if not image_stack.flags["C_CONTIGUOUS"]:
        raise ValueError("The input image must be contiguous for proper compression.")

    if not isinstance(image_stack, np.ndarray):
        raise TypeError("The 'image_stack' parameter must be a NumPy array.")
    elif First_call and verbose:
        print(f"Compressing image to: {image_stack.shape}")

    if not identifier:
        raise ValueError(
            "The 'identifier' parameter is not provided. Please provide an identifier."
        )

    # Prepare images in the stack
    if len(image_stack.shape) > 2:
        for i in range(image_stack.shape[depth]):
            prepare_images(image_stack[i], depth, identifier, First_call=False)

    elif len(image_stack.shape) == 2:
        if verbose:
            print("compress image")

        prepare_image(image_stack, identifier)

    depth += 1

    return True


def reshape_tiff(image_stack, new_frames, new_slices=1, new_channels=1):
    # Get dimensions
    z, y, x = image_stack.shape
    total_elements_5d = new_frames * new_slices * new_channels

    # Check if dimensions are compatible
    if z != total_elements_5d:
        raise ValueError(
            "The total number of elements in the 3D stack must be equal to the total number of elements in the 5D stack."
        )

    # Reshape the 3D stack into a 5D stack
    image_stack_5d = np.reshape(
        image_stack, (new_frames, new_slices, new_channels, y, x)
    )

    return image_stack_5d
