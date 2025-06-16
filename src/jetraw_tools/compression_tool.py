import os
import logging
import numpy as np
import tifffile
import locale
import multiprocessing

# Local package imports
from functools import partial
from .dpcore import load_parameters
from .utils import prepare_images, add_extension, create_compress_folder
from .tiff_writer import imwrite, metadata_writer
from .image_reader import ImageReader
from .logger import logger


class CompressionTool:
    """
    A tool for compressing and decompressing images using the JetRaw algorithm.

    :param calibration_file: The calibration file to use.
    :type calibration_file: str, optional
    :param identifier: The identifier for the images.
    :type identifier: str, optional
    :param verbose: Whether to print verbose output.
    :type verbose: bool, optional
    :param extension: Image file extension.
    :type extension: str, optional
    :param metadata: Whether to process metadata.
    :type metadata: bool, optional
    :param json: Whether to save metadata as JSON.
    :type json: bool, optional
    :param remove: Whether to delete original images.
    :type remove: bool, optional
    :param key: Licence key.
    :type key: str, optional
    :param ncores: Number of cores to use.
    :type ncores: int, optional
    """

    def __init__(
        self,
        calibration_file: str = None,
        identifier: str = "",
        ncores=0,
        omit_processed: bool = True,
        verbose: bool = False,
    ):
        # Check if calibration file exists
        if calibration_file is not None and not os.path.exists(calibration_file):
            logger.error(f"\033[91m\033[1mCalibration file not found:\033[0m\033[91m {calibration_file}\033[0m")
            raise FileNotFoundError(f"Calibration file does not exist: {calibration_file}")
        self.calibration_file = calibration_file
        self.identifier = identifier
        self.ncores = ncores
        self.omit_processed = omit_processed
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)

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
            image_files = [
                f for f in os.listdir(folder_path) if f.endswith(image_extension)
            ]
        if len(image_files) == 0:
            logger.info(f"No file found in the folder with extension {image_extension}")

        return image_files

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

    def compress_image(
        self,
        img_map: np.ndarray,
        target_file: str,
        metadata: dict,
        ome_bool: bool = True,
        metadata_json: bool = True,
    ) -> bool:
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
        img_map = np.ascontiguousarray(img_map, dtype=img_map.dtype)
        load_parameters(self.calibration_file)
        prepare_images(img_map, identifier=self.identifier)

        # Compress input image to JetRaw compressed TIFF format
        imwrite(target_file, img_map, description="")
        if metadata:
            if not ome_bool:
                imageJ_metadata = True
            else:
                imageJ_metadata = False
            metadata_writer(
                target_file,
                metadata=metadata,
                ome_bool=ome_bool,
                imagej=imageJ_metadata,
                as_json=metadata_json,
            )

        logger.debug(f"Successfully compressed image to: {target_file}")
        return True

    def decompress_image(
        self,
        img_map: np.ndarray,
        target_file: str,
        metadata: dict,
        ome_bool: bool = True,
        metadata_json: bool = False,
    ) -> bool:
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

            metadata_writer(
                target_file,
                metadata=metadata,
                ome_bool=ome_bool,
                imagej=imageJ_metadata,
                as_json=metadata_json,
            )

        return True

    def process_image(
        self,
        folder_path: str,
        output_folder: str,
        image_file: str,
        mode: str,
        image_extension: str,
        process_metadata: bool,
        ome_bool: bool,
        metadata_json: bool,
        remove_source: bool,
        progress_info: tuple,
    ) -> int:
        """
        Process an image file.

        :param folder_path: The path to the folder containing the image.
        :param output_folder: The path to the folder where the processed image will be saved.
        :param image_file: The name of the image file to process.
        :param mode: The mode, either "compress" or "decompress".
        :param image_extension: The image file extension.
        :param process_metadata: Whether to process metadata.
        :param ome_bool: Whether to use OME metadata.
        :param metadata_json: Whether to write metadata as JSON.
        :param remove_source: Whether to remove the source files after processing.
        :param progress_info: The total number of files to process.
        :return: None
        """

        if self.verbose:
            logger.info(
                f"Processing {image_file}... (File {progress_info[0]} of {progress_info[1]})"
            )

        # Input/output files
        input_filename = os.path.join(folder_path, image_file)
        output_filename = os.path.join(output_folder, image_file)
        if not ome_bool and process_metadata:
            logger.warning(
                "Metadata not allowed for *.p.tif files yet, omitting metadata..."
            )
            process_metadata = False

        output_filename = add_extension(
            output_filename, image_extension, mode=mode, ome=ome_bool
        )

        failed_files = 0
        try:
            # Read image and metadata
            image_reader = ImageReader(input_filename, image_extension)
            img_map, metadata = image_reader.read_image()

            if process_metadata is False:
                metadata = {}

            if mode == "compress":
                self.compress_image(
                    img_map,
                    output_filename,
                    metadata,
                    ome_bool=ome_bool,
                    metadata_json=metadata_json,
                )
            elif mode == "decompress":
                self.decompress_image(
                    img_map,
                    output_filename,
                    metadata,
                    ome_bool=ome_bool,
                    metadata_json=False,
                )
            else:
                error_msg = f"Mode {mode} is not supported. Please use 'compress' or 'decompress'."
                logger.error(error_msg)
                raise ValueError(error_msg)

            if remove_source:
                self.remove_files(output_filename, input_filename)
        except Exception as e:
            failed_files += 1
            logger.error(f"Error processing {image_file}: {e}")

        return failed_files

    def process_folder(
        self,
        folder_path: str,
        mode: str = "compress",
        image_extension: str = ".tiff",
        process_metadata: bool = True,
        ome_bool: bool = True,
        metadata_json: bool = True,
        remove_source: bool = False,
        target_folder: str = None,  # New parameter for target folder
    ) -> bool:
        """
        Process a folder of images.

        :param folder_path: The path to the folder.
        :param mode: The mode, either "compress" or "decompress".
        :param image_extension: The image file extension.
        :param process_metadata: Whether to process metadata.
        :param ome_bool: Whether to use OME metadata.
        :param metadata_json: Whether to write metadata as JSON.
        :param remove_source: Whether to remove the source files.
        :param target_folder: Optional target folder for processed images.
        """

        # Create or use the output folder (with check if it exists)
        if target_folder:
            output_folder = os.path.abspath(target_folder)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
        else:
            if mode == "decompress":
                suffix = "_decompressed"
            else:
                suffix = "_compressed"

            if os.path.isdir(folder_path):
                output_folder = create_compress_folder(folder_path, suffix=suffix)
            else:
                output_folder = folder_path

        logger.debug(f"Using output directory: {output_folder}")
        image_files = self.list_files(folder_path, image_extension)

        removed_count = 0
        if self.omit_processed:
            processed_files = set()
            for file in os.listdir(output_folder):
                base_name, _ = os.path.splitext(file)
                processed_files.add(base_name)

            original_count = len(image_files)
            image_files = [
                file
                for file in image_files
                if os.path.splitext(file)[0] not in processed_files
            ]
            removed_count = original_count - len(image_files)

        total_files = len(image_files)

        if self.verbose:
            logger.info(f"Total files to process: {total_files}")
            logger.info(f"Files already processed: {removed_count}")
        # Create a pool of worker processes
        if self.ncores > 0:
            pool = multiprocessing.Pool(processes=self.ncores)
        else:
            num_processes = multiprocessing.cpu_count()
            pool = multiprocessing.Pool(processes=num_processes)

        # Prepare arguments for the worker function
        worker_args = [
            (
                folder_path,
                output_folder,
                image_file,
                mode,
                image_extension,
                process_metadata,
                ome_bool,
                metadata_json,
                remove_source,
                (index + 1, total_files),
            )
            for index, image_file in enumerate(image_files)
        ]

        # Run the worker function in parallel
        results = pool.starmap(self.process_image, worker_args)

        # Close the pool and wait for all tasks to complete
        pool.close()
        pool.join()

        if self.verbose:
            logger.info(f"Processed {len(image_files)} images")
            failed = sum(results)
            success_files = len(image_files) - failed
            logger.info(
                f"{success_files} files processed correctly and {failed} images failed to process"
            )

        return True
