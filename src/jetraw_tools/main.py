import importlib.metadata

try:
    __version__ = importlib.metadata.version("jetraw_tools")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

import os
import re
import locale
import logging
import configparser

# Local package imports
from jetraw_tools.parser import parser
from jetraw_tools import jetraw_tiff
from jetraw_tools.compression_tool import CompressionTool
from jetraw_tools.config import configjrt
from jetraw_tools.logger import setup_logger


def main():
    # Parse and set locale
    args = parser.parse_args()
    # locale.setlocale(locale.LC_ALL, locale.getlocale())
    # locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(level=log_level)

    # Set default calibration file path
    if args.settings:
        configjrt()

    config_file = os.path.expanduser("~/.config/jetraw_tools/jetraw_tools.cfg")
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
    else:
        logger.warning(f"Config file not found at {config_file}")

    if args.calibration_file == "":
        cal_file = config["calibration_file"]["calibration_file"]
    else:
        cal_file = args.calibration_file

    if args.identifier == "":
        identifier = config["identifiers"]["id1"]
    elif re.match(r"^id\d+$", args.identifier):
        identifier = config["identifiers"][args.identifier]
    else:
        identifier = args.identifier

    if args.key == "":
        licence_key = config["licence_key"]["key"]
    try:
        jetraw_tiff._jetraw_tiff_lib.jetraw_tiff_set_license(
            licence_key.encode("utf-8")
        )
    except AttributeError:
        pass

    if identifier == "" or cal_file == "":
        logger.error(
            "Identifier and calibration file must be set. Use --settings to set them or provide them as arguments."
        )
        raise ValueError(
            "Identifier and calibration file must be set. Use --settings to set them or provide them as arguments."
        )

    # Execute compress/decompress
    if args.compress:
        full_path = os.path.join(os.getcwd(), args.compress)
        mode = "compress"
        process_json = args.json

    if args.decompress:
        full_path = os.path.join(os.getcwd(), args.decompress)
        mode = "decompress"
        process_json = False

    if args.compress or args.decompress:
        logger.info(f"Jetraw_tools package version: {__version__}")
        logger.info(
            f"Using calibration file: {os.path.basename(cal_file)} and identifier: {identifier}"
        )

        compressor = CompressionTool(
            cal_file, identifier, args.ncores, args.op, args.verbose
        )
        compressor.process_folder(
            full_path,
            mode,
            args.extension,
            args.metadata,
            ome_bool=True,
            metadata_json=process_json,
            remove_source=args.remove,
            target_folder=args.output,
        )


if __name__ == "__main__":
    main()
