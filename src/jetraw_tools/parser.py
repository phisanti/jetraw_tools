import importlib.metadata

try:
    __version__ = importlib.metadata.version("jetraw_tools")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

import os
import re
import logging
import configparser
from typing import Optional

import typer
from rich.console import Console

# Local package imports
from jetraw_tools import jetraw_tiff
from jetraw_tools.compression_tool import CompressionTool
from jetraw_tools.config import ConfigManager, init as config_init
from jetraw_tools.logger import logger, setup_logger
from jetraw_tools.utils import cores_validation

app = typer.Typer(
    name="jetraw_tools",
    help="JetRaw compression tools for image processing",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Display version information and exit.

    :param value: Whether to show version (True triggers version display)
    :type value: bool
    :raises typer.Exit: Always exits after displaying version
    """
    if value:
        typer.echo(f"jetraw_tools version: {__version__}")
        raise typer.Exit()


@app.command()
def compress(
    path: str = typer.Argument(..., help="Path to folder/file to compress"),
    calibration_file: str = typer.Option(
        "",
        "--calibration_file",
        help="Path to calibration file (defaults to config file if not provided)",
    ),
    identifier: str = typer.Option(
        "",
        "-i",
        "--identifier",
        help="Camera identifier (defaults to first identifier from config file if not provided)",
    ),
    key: str = typer.Option(
        "", "--key", help="License key (defaults to config file if not provided)"
    ),
    extension: str = typer.Option(
        ".nd2", "--extension", help="File extension to process"
    ),
    ncores: int = typer.Option(0, "--ncores", help="Number of cores to use"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output directory"
    ),
    metadata: bool = typer.Option(
        True, "--metadata/--no-metadata", help="Process metadata"
    ),
    json: bool = typer.Option(False, "--json", help="Save metadata as JSON"),
    remove: bool = typer.Option(
        False, "--remove", help="Remove source files after processing"
    ),
    op: bool = typer.Option(True, "--op/--no-op", help="Omit processed files"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
    """Compress images using JetRaw compression."""
    _process_files(
        path,
        "compress",
        calibration_file,
        identifier,
        key,
        extension,
        ncores,
        output,
        metadata,
        json,
        remove,
        op,
        verbose,
    )


@app.command()
def decompress(
    path: str = typer.Argument(..., help="Path to folder/file to decompress"),
    calibration_file: str = typer.Option(
        "",
        "--calibration_file",
        help="Path to calibration file (defaults to config file if not provided)",
    ),
    identifier: str = typer.Option(
        "",
        "-i",
        "--identifier",
        help="Camera identifier (defaults to first identifier from config file if not provided)",
    ),
    key: str = typer.Option(
        "", "--key", help="License key (defaults to config file if not provided)"
    ),
    extension: str = typer.Option(
        ".ome.p.tiff", "--extension", help="File extension to process"
    ),
    ncores: int = typer.Option(0, "--ncores", help="Number of cores to use"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output directory"
    ),
    metadata: bool = typer.Option(
        True, "--metadata/--no-metadata", help="Process metadata"
    ),
    remove: bool = typer.Option(
        False, "--remove", help="Remove source files after processing"
    ),
    op: bool = typer.Option(True, "--op/--no-op", help="Omit processed files"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
    """Decompress JetRaw compressed images."""
    _process_files(
        path,
        "decompress",
        calibration_file,
        identifier,
        key,
        extension,
        ncores,
        output,
        metadata,
        False,
        remove,
        op,
        verbose,
    )


@app.command()
def settings() -> None:
    """Run configuration setup wizard."""
    setup_logger(level=logging.INFO)
    logger.info("Starting configuration setup...")
    try:
        config_init(force=False)
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        raise typer.Exit(1)


def _process_files(
    path: str,
    mode: str,
    calibration_file: str,
    identifier: str,
    key: str,
    extension: str,
    ncores: int,
    output: Optional[str],
    metadata: bool,
    json: bool,
    remove: bool,
    op: bool,
    verbose: bool,
) -> None:
    """Process files for compression or decompression operations.

    Internal function that handles the core logic for file processing including
    configuration loading, parameter validation, and delegating to CompressionTool.

    :param path: Path to folder or file to process
    :type path: str
    :param mode: Processing mode ('compress' or 'decompress')
    :type mode: str
    :param calibration_file: Path to calibration file
    :type calibration_file: str
    :param identifier: Camera identifier
    :type identifier: str
    :param key: License key
    :type key: str
    :param extension: File extension to process
    :type extension: str
    :param ncores: Number of cores to use
    :type ncores: int
    :param output: Output directory path
    :type output: Optional[str]
    :param metadata: Whether to process metadata
    :type metadata: bool
    :param json: Whether to save metadata as JSON
    :type json: bool
    :param remove: Whether to remove source files after processing
    :type remove: bool
    :param op: Whether to omit processed files
    :type op: bool
    :param verbose: Whether to enable verbose output
    :type verbose: bool
    :raises typer.Exit: If configuration is invalid or processing fails
    """

    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logger(level=log_level)

    # Load existing configuration
    config_manager = ConfigManager()
    config_file = os.path.expanduser("~/.config/jetraw_tools/jetraw_tools.cfg")

    if not os.path.exists(config_file):
        logger.error(
            f"Config file not found at {config_file}. Run 'jetraw_tools settings' first."
        )
        raise typer.Exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)

    # Set calibration file
    if calibration_file == "":
        try:
            cal_file = config["calibration_file"]["calibration_file"]
        except KeyError:
            logger.error(
                "No calibration file configured. Run 'jetraw_tools settings' first."
            )
            raise typer.Exit(1)
    else:
        cal_file = calibration_file

    # Set identifier
    if identifier == "":
        try:
            identifier = config["identifiers"]["id1"]
        except KeyError:
            logger.error(
                "No identifiers configured. Run 'jetraw_tools settings' first."
            )
            raise typer.Exit(1)
    elif re.match(r"^id\d+$", identifier):
        try:
            identifier = config["identifiers"][identifier]
        except KeyError:
            logger.error(f"Identifier {identifier} not found in config.")
            raise typer.Exit(1)

    # Set license key
    if key == "":
        try:
            licence_key = config["licence_key"]["key"]
        except KeyError:
            logger.error(
                "No license key configured. Run 'jetraw_tools settings' first."
            )
            raise typer.Exit(1)
    else:
        licence_key = key

    # Set license in jetraw library
    try:
        jetraw_tiff._jetraw_tiff_lib.jetraw_tiff_set_license(
            licence_key.encode("utf-8")
        )
    except AttributeError:
        pass

    if identifier == "" or cal_file == "":
        logger.error("Identifier and calibration file must be set.")
        raise typer.Exit(1)

    status, validated_ncores, message = cores_validation(ncores)
    if status == "ERROR":
        logger.error(message)
        raise typer.Exit(1)
    elif status == "WARN":
        logger.warning(message)
    else:  # status == 'OK'
        logger.info(message)

    ncores = validated_ncores

    full_path = os.path.join(os.getcwd(), path)

    logger.info(f"Jetraw_tools package version: {__version__}")
    logger.info(
        f"Using calibration file: {os.path.basename(cal_file)} and identifier: {identifier}"
    )

    compressor = CompressionTool(cal_file, identifier, ncores, op, verbose)
    compressor.process_folder(
        full_path,
        mode,
        extension,
        metadata,
        ome_bool=True,
        metadata_json=json,
        remove_source=remove,
        target_folder=output,
    )


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """JetRaw compression tools for image processing."""
    pass
