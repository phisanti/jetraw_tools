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

# Local package imports - lazy import jetraw_tiff only when needed
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


# Helper functions for multi-calibration support


def _get_first_calibration_file(config: configparser.ConfigParser) -> tuple:
    """Get first available calibration file from config.

    Handles both legacy (calibration_file) and new (calibration_file1) formats.

    :param config: ConfigParser instance with loaded configuration
    :type config: configparser.ConfigParser
    :return: Tuple of (calibration_key, calibration_path)
    :rtype: tuple
    :raises typer.Exit: If no calibration file is configured
    """
    cal_section = (
        dict(config["calibration_file"]) if "calibration_file" in config else {}
    )

    # Try legacy format first
    if "calibration_file" in cal_section:
        return ("calibration_file", cal_section["calibration_file"])

    # Try numbered format
    if "calibration_file1" in cal_section:
        return ("calibration_file1", cal_section["calibration_file1"])

    logger.error("No calibration file configured. Run 'jetraw_tools settings' first.")
    raise typer.Exit(1)


def _get_first_identifier_for_calibration(
    config: configparser.ConfigParser, cal_file_key: str
) -> tuple:
    """Find first identifier mapped to a given calibration file.

    :param config: ConfigParser instance with loaded configuration
    :type config: configparser.ConfigParser
    :param cal_file_key: Calibration file key (e.g., 'calibration_file1')
    :type cal_file_key: str
    :return: Tuple of (identifier_key, identifier_value)
    :rtype: tuple
    :raises typer.Exit: If no identifiers are configured
    """
    identifiers = dict(config["identifiers"]) if "identifiers" in config else {}

    if not identifiers:
        logger.error("No identifiers configured. Run 'jetraw_tools settings' first.")
        raise typer.Exit(1)

    # Check if calibration_mapping exists
    if "calibration_mapping" in config:
        mapping = dict(config["calibration_mapping"])

        # Sort keys numerically (id1 before id10)
        sorted_ids = sorted(
            mapping.keys(),
            key=lambda x: int(x[2:]) if x.startswith("id") and x[2:].isdigit() else 999,
        )

        for id_key in sorted_ids:
            if mapping[id_key] == cal_file_key and id_key in identifiers:
                return (id_key, identifiers[id_key])

    # Fallback: return first identifier (legacy behavior)
    sorted_ids = sorted(
        identifiers.keys(),
        key=lambda x: int(x[2:]) if x.startswith("id") and x[2:].isdigit() else 999,
    )
    first_id = sorted_ids[0] if sorted_ids else "id1"
    return (first_id, identifiers.get(first_id, ""))


def _lookup_calibration_for_identifier(
    config: configparser.ConfigParser, identifier_key: str
) -> str:
    """Look up calibration file path for a given identifier key.

    :param config: ConfigParser instance with loaded configuration
    :type config: configparser.ConfigParser
    :param identifier_key: Identifier key (e.g., 'id1', 'id2')
    :type identifier_key: str
    :return: Path to calibration file
    :rtype: str
    :raises typer.Exit: If mapping or calibration file not found
    """
    # Check calibration_mapping section
    if "calibration_mapping" in config:
        mapping = dict(config["calibration_mapping"])
        if identifier_key in mapping:
            cal_key = mapping[identifier_key]
            cal_section = dict(config["calibration_file"])
            if cal_key in cal_section:
                return cal_section[cal_key]

    # Fallback: use first calibration file (legacy behavior)
    _, cal_path = _get_first_calibration_file(config)
    return cal_path


def _paths_match(path1: str, path2: str) -> bool:
    """Compare two file paths for equality.

    Resolves both paths to absolute paths and compares.

    :param path1: First path to compare
    :type path1: str
    :param path2: Second path to compare
    :type path2: str
    :return: True if paths point to the same file
    :rtype: bool
    """
    return os.path.abspath(path1) == os.path.abspath(path2)


def _resolve_calibration_and_identifier(
    config: configparser.ConfigParser,
    calibration_file_arg: str,
    identifier_arg: str,
) -> tuple:
    """Resolve calibration file and identifier based on CLI arguments and config.

    Handles four cases:
    - Case 1: Neither provided → use first cal file + first mapped identifier
    - Case 2: Only calibration provided → use it + first identifier for that file (warn)
    - Case 3: Only identifier provided → lookup calibration from mapping
    - Case 4: Both provided → validate they match

    :param config: ConfigParser instance with loaded configuration
    :type config: configparser.ConfigParser
    :param calibration_file_arg: Calibration file path from CLI (empty string if not provided)
    :type calibration_file_arg: str
    :param identifier_arg: Identifier from CLI (empty string if not provided)
    :type identifier_arg: str
    :return: Tuple of (calibration_file_path, identifier_value)
    :rtype: tuple
    :raises typer.Exit: If configuration is invalid or mismatch detected
    """
    cal_provided = calibration_file_arg != ""
    id_provided = identifier_arg != ""

    # Step 1: Resolve identifier key and value
    identifier_key = None
    identifier_value = None

    if id_provided:
        if re.match(r"^id\d+$", identifier_arg):
            # User provided a key like "id1", "id2"
            identifier_key = identifier_arg
            try:
                identifier_value = config["identifiers"][identifier_key]
            except KeyError:
                available_ids = (
                    list(config["identifiers"].keys())
                    if "identifiers" in config
                    else []
                )
                logger.error(
                    f"Identifier '{identifier_key}' not found in config. "
                    f"Available identifiers: {', '.join(available_ids)}"
                )
                raise typer.Exit(1)
        else:
            # User provided a value like "A0001_WidefieldGreen"
            identifier_value = identifier_arg
            # Reverse lookup to find the key
            identifiers = dict(config["identifiers"]) if "identifiers" in config else {}
            for key, value in identifiers.items():
                if value == identifier_value:
                    identifier_key = key
                    break
            # If not found in config, use the value directly (allows ad-hoc identifiers)
            if identifier_key is None:
                logger.debug(
                    f"Identifier '{identifier_value}' not in config, using as-is"
                )

    # Step 2: Resolve calibration file
    if cal_provided:
        cal_file = calibration_file_arg
        needs_validation = id_provided and identifier_key is not None
    else:
        if identifier_key is not None:
            # Case 3: Only identifier provided → lookup calibration
            cal_file = _lookup_calibration_for_identifier(config, identifier_key)
            needs_validation = False
        else:
            # Case 1: Neither provided → use first cal file + first identifier
            cal_key, cal_file = _get_first_calibration_file(config)
            identifier_key, identifier_value = _get_first_identifier_for_calibration(
                config, cal_key
            )
            needs_validation = False

    # Step 3: Handle Case 2 - calibration provided but no identifier
    if cal_provided and not id_provided:
        # Find which cal_key matches the provided path
        cal_section = (
            dict(config["calibration_file"]) if "calibration_file" in config else {}
        )
        matched_cal_key = None
        for key, path in cal_section.items():
            if _paths_match(path, cal_file):
                matched_cal_key = key
                break

        if matched_cal_key:
            identifier_key, identifier_value = _get_first_identifier_for_calibration(
                config, matched_cal_key
            )
        else:
            # Calibration file not in config, use first identifier
            _, first_cal = _get_first_calibration_file(config)
            cal_key = (
                "calibration_file"
                if "calibration_file" in cal_section
                else "calibration_file1"
            )
            identifier_key, identifier_value = _get_first_identifier_for_calibration(
                config, cal_key
            )

        logger.warning(
            f"No identifier specified. Using first identifier for this calibration file: "
            f"{identifier_value} ({identifier_key}). "
            "It is recommended to always specify an identifier with --identifier flag."
        )
        needs_validation = False

    # Step 4: Validate Case 4 - both provided
    if needs_validation and identifier_key is not None:
        if "calibration_mapping" in config:
            mapping = dict(config["calibration_mapping"])
            if identifier_key in mapping:
                expected_cal_key = mapping[identifier_key]
                cal_section = dict(config["calibration_file"])
                if expected_cal_key in cal_section:
                    expected_cal_path = cal_section[expected_cal_key]
                    if not _paths_match(cal_file, expected_cal_path):
                        logger.error(
                            f"Calibration file mismatch!\n"
                            f"  Identifier:   {identifier_value} ({identifier_key})\n"
                            f"  Expected cal: {expected_cal_path}\n"
                            f"  Provided cal: {cal_file}\n\n"
                            f"Suggestion: Remove --calibration_file flag to auto-select the correct file:\n"
                            f"  jetraw-tools compress <path> --identifier {identifier_key}"
                        )
                        raise typer.Exit(1)

    # Final validation
    if identifier_value is None or identifier_value == "":
        logger.error("Could not resolve identifier. Run 'jetraw_tools settings' first.")
        raise typer.Exit(1)

    if cal_file == "":
        logger.error(
            "Could not resolve calibration file. Run 'jetraw_tools settings' first."
        )
        raise typer.Exit(1)

    return (cal_file, identifier_value)


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

    # Resolve calibration file and identifier using multi-calibration logic
    cal_file, identifier = _resolve_calibration_and_identifier(
        config, calibration_file, identifier
    )

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

    # Set license in jetraw library (lazy import)
    try:
        from jetraw_tools.libs import get_jetraw_libs

        _, _jetraw_tiff_lib = get_jetraw_libs()
        _jetraw_tiff_lib.jetraw_tiff_set_license(licence_key.encode("utf-8"))
    except (ImportError, AttributeError):
        # Libraries not available or license setting not supported
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
