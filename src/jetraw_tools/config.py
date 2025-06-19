"""
JetRaw Tools Configuration Manager

Configuration tool for setting up JetRaw Tools.
"""

import shutil
import platform
import subprocess
import configparser
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# Initialize console and Typer app
console: Console = Console()
app: typer.Typer = typer.Typer(
    name="jetraw-config",
    help="JetRaw Tools Configuration Manager",
    rich_markup_mode="rich",
)

# Constants
CONFIG_DIR: Path = Path.home() / ".config" / "jetraw_tools"
CONFIG_FILE: Path = CONFIG_DIR / "jetraw_tools.cfg"
VALID_DAT_EXTENSIONS: List[str] = [".dat"]
REQUIRED_SECTIONS: List[str] = [
    "calibration_file",
    "identifiers",
    "licence_key",
    "jetraw_paths",
]


class ConfigError(Exception):
    """
    Custom exception for configuration errors.

    :param message: Error message describing the configuration issue.
    :type message: str
    """

    pass


class ConfigManager:
    """
    Handles configuration file operations with validation and backup.

    This class manages the JetRaw Tools configuration file, providing methods
    for loading, saving, backing up, and modifying configuration settings.
    """

    def __init__(self) -> None:
        """
        Initialize the ConfigManager.

        Creates the configuration directory if it doesn't exist and loads
        any existing configuration file.
        """
        self.config: configparser.ConfigParser = configparser.ConfigParser()
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self) -> None:
        """
        Create configuration directory if it doesn't exist.

        :raises ConfigError: If permission is denied when creating the directory.
        :rtype: None
        """
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise ConfigError(
                f"Permission denied creating config directory: {CONFIG_DIR}"
            )

    def _load_config(self) -> None:
        """
        Load existing configuration or create new one.

        :raises ConfigError: If the configuration file is invalid or corrupted.
        :rtype: None
        """
        if CONFIG_FILE.exists():
            try:
                self.config.read(CONFIG_FILE)
            except configparser.Error as e:
                raise ConfigError(f"Invalid configuration file: {e}")

    def backup_config(self) -> Optional[Path]:
        """
        Create backup of current configuration.

        Creates a timestamped backup of the current configuration file
        before making changes.

        :return: Path to the backup file if successful, None otherwise.
        :rtype: Optional[Path]
        """
        if not CONFIG_FILE.exists():
            return None

        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path: Path = CONFIG_DIR / f"jetraw_tools.cfg.backup_{timestamp}"

        try:
            shutil.copy2(CONFIG_FILE, backup_path)
            return backup_path
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")
            return None

    def save_config(self) -> None:
        """
        Save configuration to file with backup.

        Creates a backup of the existing configuration and saves the current
        configuration to the config file.

        :raises ConfigError: If the configuration cannot be saved.
        :rtype: None
        """
        backup_path: Optional[Path] = self.backup_config()

        try:
            with open(CONFIG_FILE, "w") as f:
                self.config.write(f)

            if backup_path:
                console.print(
                    f"[green]✓[/green] Configuration saved (backup: {backup_path.name})"
                )
            else:
                console.print("[green]✓[/green] Configuration saved")

        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")

    def get_section_dict(self, section: str) -> Dict[str, str]:
        """
        Get section as dictionary.

        :param section: Name of the configuration section to retrieve.
        :type section: str
        :return: Dictionary containing all key-value pairs from the section.
        :rtype: Dict[str, str]
        """
        if section in self.config:
            return dict(self.config[section])
        return {}

    def set_section_value(self, section: str, key: str, value: str) -> None:
        """
        Set value in configuration section.

        :param section: Name of the configuration section.
        :type section: str
        :param key: Configuration key within the section.
        :type key: str
        :param value: Value to set for the specified key.
        :type value: str
        :rtype: None
        """
        if section not in self.config:
            self.config.add_section(section)
        self.config[section][key] = value


class PathDetector:
    """
    Detects and validates installation paths.

    This class provides static methods for finding and validating
    JetRaw and DPCore installation paths on the system.
    """

    @staticmethod
    def find_binary_path(binary_name: str) -> Optional[Path]:
        """
        Find binary installation path using system commands.

        Uses system 'which' or 'where' commands to locate the binary
        and returns the installation directory.

        :param binary_name: Name of the binary to search for.
        :type binary_name: str
        :return: Path to the installation directory if found, None otherwise.
        :rtype: Optional[Path]
        """
        cmd: str = "where" if platform.system() == "Windows" else "which"

        try:
            result: subprocess.CompletedProcess = subprocess.run(
                [cmd, binary_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                binary_path: Path = Path(result.stdout.strip().split("\n")[0])
                # Return installation directory (parent of bin directory)
                return (
                    binary_path.parent.parent
                    if binary_path.parent.name == "bin"
                    else binary_path.parent
                )

        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        return None

    @staticmethod
    def validate_installation_path(path: Path, binary_name: str) -> bool:
        """
        Validate if path contains a valid installation.

        Checks if the provided path contains a valid installation by
        looking for the binary in the expected location.

        :param path: Path to validate as an installation directory.
        :type path: Path
        :param binary_name: Name of the binary to look for.
        :type binary_name: str
        :return: True if path contains a valid installation, False otherwise.
        :rtype: bool
        """
        if not path.exists():
            return False

        # Check for bin directory
        bin_dir: Path = path / "bin"
        if bin_dir.exists():
            # Check for binary in bin directory
            binary_extensions: List[str] = (
                [".exe"] if platform.system() == "Windows" else [""]
            )
            for ext in binary_extensions:
                if (bin_dir / f"{binary_name}{ext}").exists():
                    return True

        return False


def display_current_config(config_manager: ConfigManager) -> None:
    """
    Display current configuration in a formatted table.

    Shows all configuration sections and their values in a Rich table format.

    :param config_manager: ConfigManager instance containing the configuration.
    :type config_manager: ConfigManager
    :rtype: None
    """
    table: Table = Table(title="Current Configuration", show_header=True)
    table.add_column("Section", style="cyan", width=20)
    table.add_column("Key", style="magenta", width=25)
    table.add_column("Value", style="green")

    for section_name in REQUIRED_SECTIONS:
        section_data: Dict[str, str] = config_manager.get_section_dict(section_name)

        if section_data:
            for key, value in section_data.items():
                # Truncate long paths for display
                display_value: str = str(value)
                if len(display_value) > 50:
                    display_value = "..." + display_value[-47:]

                table.add_row(section_name, key, display_value)
        else:
            table.add_row(
                section_name, "[italic]empty[/italic]", "[dim]not configured[/dim]"
            )

    console.print(table)


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration without prompting",
    ),
) -> None:
    """
    Initialize complete JetRaw Tools configuration.

    Guides the user through setting up all configuration sections including
    calibration file, identifiers, license key, and installation paths.

    :param force: Whether to overwrite existing configuration without prompting.
    :type force: bool, optional
    :rtype: None
    """

    console.print(
        Panel.fit(
            "[bold blue]JetRaw Tools Configuration Setup[/bold blue]\n"
            "This will guide you through setting up your JetRaw Tools configuration.",
            title="🚀 Setup Wizard",
        )
    )

    config_manager: ConfigManager = ConfigManager()

    # Check if config exists and handle accordingly
    if CONFIG_FILE.exists() and not force:
        console.print("\n[yellow]⚠️  Configuration already exists[/yellow]")
        display_current_config(config_manager)

        if not Confirm.ask("\nDo you want to reconfigure?"):
            console.print("[blue]ℹ️  Configuration unchanged[/blue]")
            return

    try:
        # Run configuration steps
        _configure_calibration(config_manager)
        _configure_identifiers(config_manager)
        _configure_license_key(config_manager)
        _configure_paths(config_manager)

        config_manager.save_config()

        console.print(
            Panel.fit(
                "[bold green]✅ Configuration completed successfully![/bold green]\n"
                f"Configuration saved to: {CONFIG_FILE}",
                title="🎉 Success",
            )
        )

    except (ConfigError, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            console.print("\n[yellow]⚠️  Configuration cancelled by user[/yellow]")
        else:
            console.print(f"[red]❌ Configuration failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def calibration(
    file_path: Optional[str] = typer.Option(
        None, "--file", "-f", help="Path to calibration .dat file"
    ),
) -> None:
    """
    Configure calibration file.

    Sets up the calibration file path in the configuration. If no file path
    is provided, enters interactive mode.

    :param file_path: Path to calibration .dat file.
    :type file_path: str, optional
    :rtype: None
    """
    config_manager: ConfigManager = ConfigManager()

    try:
        if file_path:
            _set_calibration_file(config_manager, Path(file_path))
        else:
            _configure_calibration(config_manager)

        config_manager.save_config()
        console.print("[green]✅ Calibration configuration updated[/green]")

    except ConfigError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


@app.command()
def identifiers(
    clear: bool = typer.Option(False, "--clear", help="Clear all existing identifiers"),
) -> None:
    """
    Configure image identifiers.

    Sets up image identifiers for different image types/conditions.
    Can optionally clear all existing identifiers first.

    :param clear: Whether to clear all existing identifiers.
    :type clear: bool, optional
    :rtype: None
    """
    config_manager: ConfigManager = ConfigManager()

    try:
        if clear:
            if "identifiers" in config_manager.config:
                config_manager.config.remove_section("identifiers")
            console.print("[green]✅ All identifiers cleared[/green]")

        _configure_identifiers(config_manager)
        config_manager.save_config()
        console.print("[green]✅ Identifiers configuration updated[/green]")

    except ConfigError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


@app.command()
def license(
    key: Optional[str] = typer.Option(None, "--key", "-k", help="License key"),
) -> None:
    """
    Configure license key.

    Sets up the JetRaw license key in the configuration.

    :param key: License key for JetRaw.
    :type key: str, optional
    :rtype: None
    """
    config_manager: ConfigManager = ConfigManager()

    try:
        if key:
            config_manager.set_section_value("licence_key", "key", key)
        else:
            _configure_license_key(config_manager)

        config_manager.save_config()
        console.print("[green]✅ License key updated[/green]")

    except ConfigError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


@app.command()
def paths(
    jetraw_path: Optional[str] = typer.Option(
        None, "--jetraw", help="JetRaw installation path"
    ),
    dpcore_path: Optional[str] = typer.Option(
        None, "--dpcore", help="DPCore installation path"
    ),
    auto_detect: bool = typer.Option(
        False, "--auto", "-a", help="Auto-detect installation paths"
    ),
) -> None:
    """
    Configure JetRaw and DPCore installation paths.

    Sets up paths to JetRaw and DPCore installations. Can auto-detect
    paths or configure them manually.

    :param jetraw_path: Path to JetRaw installation directory.
    :type jetraw_path: str, optional
    :param dpcore_path: Path to DPCore installation directory.
    :type dpcore_path: str, optional
    :param auto_detect: Whether to auto-detect installation paths.
    :type auto_detect: bool, optional
    :rtype: None
    """
    config_manager: ConfigManager = ConfigManager()

    try:
        if auto_detect:
            _auto_detect_paths(config_manager)
        elif jetraw_path or dpcore_path:
            if jetraw_path:
                _validate_and_set_path(config_manager, "jetraw", Path(jetraw_path))
            if dpcore_path:
                _validate_and_set_path(config_manager, "dpcore", Path(dpcore_path))
        else:
            _configure_paths(config_manager)

        config_manager.save_config()
        console.print("[green]✅ Installation paths updated[/green]")

    except ConfigError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


@app.command()
def show() -> None:
    """
    Display current configuration.

    Shows all current configuration values in a formatted table.

    :rtype: None
    """
    config_manager: ConfigManager = ConfigManager()

    if not CONFIG_FILE.exists():
        console.print(
            "[yellow]⚠️  No configuration file found. Run 'jetraw-config init' first.[/yellow]"
        )
        return

    display_current_config(config_manager)


@app.command()
def validate() -> None:
    """
    Validate current configuration.

    Checks if all required configuration sections are present and valid,
    including file existence and path validation.

    :rtype: None
    """
    config_manager: ConfigManager = ConfigManager()

    if not CONFIG_FILE.exists():
        console.print("[red]❌ No configuration file found[/red]")
        raise typer.Exit(1)

    issues: List[str] = []

    # Check calibration file
    cal_section: Dict[str, str] = config_manager.get_section_dict("calibration_file")
    if not cal_section.get("calibration_file"):
        issues.append("Missing calibration file")
    elif not Path(cal_section["calibration_file"]).exists():
        issues.append("Calibration file does not exist")

    # Check license key
    license_section: Dict[str, str] = config_manager.get_section_dict("licence_key")
    if not license_section.get("key"):
        issues.append("Missing license key")

    # Check paths
    paths_section: Dict[str, str] = config_manager.get_section_dict("jetraw_paths")
    for binary in ["jetraw", "dpcore"]:
        path_str: Optional[str] = paths_section.get(binary)
        if not path_str:
            issues.append(f"Missing {binary} path")
        elif not PathDetector.validate_installation_path(Path(path_str), binary):
            issues.append(f"Invalid {binary} installation path")

    if issues:
        console.print("[red]❌ Configuration validation failed:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
        raise typer.Exit(1)
    else:
        console.print("[green]✅ Configuration is valid[/green]")


# Helper functions for configuration steps


def _configure_calibration(config_manager: ConfigManager) -> None:
    """
    Configure calibration file interactively.

    Guides the user through setting up the calibration file, including
    checking for existing files and copying the file to the config directory.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :rtype: None
    """
    console.print("\n[bold cyan]📁 Calibration File Setup[/bold cyan]")
    console.print(
        "Please provide the path to your calibration file with .dat extension."
    )

    # Check for existing .dat files
    existing_dat_files: List[Path] = list(CONFIG_DIR.glob("*.dat"))

    if existing_dat_files:
        console.print(
            f"[green]Found existing calibration file:[/green] {existing_dat_files[0].name}"
        )
        if not Confirm.ask("Use existing calibration file?"):
            for dat_file in existing_dat_files:
                dat_file.unlink()
        else:
            config_manager.set_section_value(
                "calibration_file", "calibration_file", str(existing_dat_files[0])
            )
            return

    while True:
        file_path: str = Prompt.ask(
            "Enter path to calibration .dat file (or 'skip' to skip)"
        )

        if file_path.lower() == "skip":
            console.print("[yellow]⚠️  Skipping calibration file configuration[/yellow]")
            return

        # Trim whitespace from the path
        file_path = file_path.strip()

        try:
            _set_calibration_file(config_manager, Path(file_path))
            break
        except ConfigError as e:
            console.print(f"[red]❌ {e}[/red]")
            continue


def _set_calibration_file(config_manager: ConfigManager, file_path: Path) -> None:
    """
    Validate and set calibration file.

    Validates the calibration file and copies it to the configuration directory.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :param file_path: Path to the calibration file.
    :type file_path: Path
    :raises ConfigError: If the file doesn't exist, has wrong extension, or cannot be copied.
    :rtype: None
    """
    if not file_path.exists():
        raise ConfigError(f"Calibration file does not exist: {file_path}")

    if file_path.suffix not in VALID_DAT_EXTENSIONS:
        raise ConfigError(
            f"Calibration file must have extension: {VALID_DAT_EXTENSIONS}"
        )

    # Copy file to config directory
    dest_path: Path = CONFIG_DIR / file_path.name
    try:
        shutil.copy2(file_path, dest_path)
        config_manager.set_section_value(
            "calibration_file", "calibration_file", str(dest_path)
        )
        console.print(f"[green]✓[/green] Calibration file copied to: {dest_path}")
    except Exception as e:
        raise ConfigError(f"Failed to copy calibration file: {e}")


def _configure_identifiers(config_manager: ConfigManager) -> None:
    """
    Configure image identifiers interactively.

    Guides the user through setting up image identifiers for different
    image types/conditions. Shows existing identifiers and allows adding new ones.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :rtype: None
    """
    console.print("\n[bold cyan]🏷️  Image Identifiers Setup[/bold cyan]")
    console.print("Configure identifiers for different image types/conditions.")
    console.print(
        "These should be single keywords such as AXXXXX_AcType "
        "where AXX is the camera model and AcType is the acquisition type."
    )

    # Show existing identifiers
    identifiers_section: Dict[str, str] = config_manager.get_section_dict("identifiers")

    if identifiers_section:
        console.print("\n[green]Existing identifiers:[/green]")
        table: Table = Table(show_header=True)
        table.add_column("Key", style="cyan")
        table.add_column("Identifier", style="green")

        for key, value in identifiers_section.items():
            table.add_row(key, value)

        console.print(table)

        if Confirm.ask("\nDo you want to remove all existing identifiers?"):
            if "identifiers" in config_manager.config:
                config_manager.config.remove_section("identifiers")
            console.print("[green]✓[/green] All identifiers removed")
        else:
            if not Confirm.ask("Do you want to add more identifiers?"):
                return

    # Add new identifiers
    console.print("\n[blue]Adding new identifiers...[/blue]")
    console.print("Press Enter without typing anything to finish.")

    id_counter: int = 1
    # Start from next available number if identifiers exist
    if identifiers_section:
        existing_nums: List[int] = [
            int(k[2:])
            for k in identifiers_section.keys()
            if k.startswith("id") and k[2:].isdigit()
        ]
        if existing_nums:
            id_counter = max(existing_nums) + 1

    while True:
        identifier: str = Prompt.ask(
            f"Enter identifier {id_counter} (or press Enter to finish)", default=""
        )

        if identifier == "":
            break

        if identifier.lower() == "no":
            console.print("[blue]ℹ️  No identifiers will be added[/blue]")
            return

        config_manager.set_section_value("identifiers", f"id{id_counter}", identifier)
        console.print(f"[green]✓[/green] Added: id{id_counter} = {identifier}")
        id_counter += 1

    if id_counter > 1:
        console.print(f"[green]✓[/green] Added {id_counter - 1} identifier(s)")


def _configure_license_key(config_manager: ConfigManager) -> None:
    """
    Configure license key interactively.

    Guides the user through setting up the JetRaw license key.
    Shows existing key (partially masked) and allows updating.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :rtype: None
    """
    console.print("\n[bold cyan]🔑 License Key Setup[/bold cyan]")
    console.print(
        "This should be a 32-characters long valid licence key"
        "xxxx-xxxx-xxxx-xxxx-xxxx-xxxx-xxxx-xxxx"
    )

    # Check for existing license key
    license_section: Dict[str, str] = config_manager.get_section_dict("licence_key")
    current_key: Optional[str] = license_section.get("key")

    if current_key:
        console.print(
            f"[green]Current license key:[/green] {current_key[:8]}...{current_key[-8:]}"
        )
        if not Confirm.ask("Do you want to update the license key?"):
            return

    while True:
        new_key: str = Prompt.ask(
            "Enter license key (or 'skip' to skip)", password=False
        )

        if new_key.lower() == "skip":
            console.print("[yellow]⚠️  Skipping license key configuration[/yellow]")
            return

        if len(new_key.strip()) == 0:
            console.print("[red]❌ License key cannot be empty[/red]")
            continue

        config_manager.set_section_value("licence_key", "key", new_key.strip())
        console.print("[green]✓[/green] License key updated")
        break


def _configure_paths(config_manager: ConfigManager) -> None:
    """
    Configure JetRaw and DPCore installation paths interactively.

    Guides the user through setting up installation paths, including
    auto-detection and manual configuration options.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :rtype: None
    """
    console.print("\n[bold cyan]📍 Installation Paths Setup[/bold cyan]")
    console.print("Configure paths to JetRaw and DPCore installations.")
    console.print(
        "This should be the path to the folder that contain the JetRaw bianres."
        "For example, /Applications/Jetraw UI.app/Contents/jetraw or C:\\Program Files\\Jetraw\\bin64"
    )

    # Check existing paths
    paths_section: Dict[str, str] = config_manager.get_section_dict("jetraw_paths")
    current_jetraw: Optional[str] = paths_section.get("jetraw")
    current_dpcore: Optional[str] = paths_section.get("dpcore")

    if current_jetraw or current_dpcore:
        console.print("\n[green]Current paths:[/green]")
        if current_jetraw:
            console.print(f"  JetRaw:  {current_jetraw}")
        if current_dpcore:
            console.print(f"  DPCore:  {current_dpcore}")

        if not Confirm.ask("Do you want to update these paths?"):
            return

    # Try auto-detection first
    console.print("\n[blue]🔍 Attempting auto-detection...[/blue]")

    detected_paths: Dict[str, Path] = {}
    for binary in ["jetraw", "dpcore"]:
        detected_path: Optional[Path] = PathDetector.find_binary_path(binary)
        if detected_path:
            console.print(f"[green]✓[/green] Found {binary} at: {detected_path}")
            detected_paths[binary] = detected_path
        else:
            console.print(f"[yellow]⚠️[/yellow] Could not auto-detect {binary}")

    # Ask if user wants to use detected paths
    if detected_paths:
        if Confirm.ask("\nUse auto-detected paths?"):
            for binary, path in detected_paths.items():
                config_manager.set_section_value("jetraw_paths", binary, str(path))
            console.print("[green]✓[/green] Auto-detected paths configured")
            return

    # Manual configuration
    console.print("\n[blue]Manual path configuration:[/blue]")

    for binary in ["jetraw", "dpcore"]:
        if binary in detected_paths:
            continue  # Skip if already detected and accepted

        while True:
            if binary == "jetraw":
                prompt: str = "Enter JetRaw installation directory (or 'skip' to skip)"
            else:
                prompt = "Enter DPCore installation directory (or 'same' if same as JetRaw, 'skip' to skip)"

            path_input: str = Prompt.ask(prompt)

            if path_input.lower() == "skip":
                console.print(
                    f"[yellow]⚠️  Skipping {binary} path configuration[/yellow]"
                )
                break

            if binary == "dpcore" and path_input.lower() == "same":
                jetraw_path: Optional[str] = config_manager.get_section_dict(
                    "jetraw_paths"
                ).get("jetraw")
                if jetraw_path:
                    config_manager.set_section_value(
                        "jetraw_paths", "dpcore", jetraw_path
                    )
                    console.print(
                        f"[green]✓[/green] DPCore path set to same as JetRaw: {jetraw_path}"
                    )
                    break
                else:
                    console.print("[red]❌ JetRaw path not configured yet[/red]")
                    continue

            try:
                _validate_and_set_path(config_manager, binary, Path(path_input.strip()))
                break
            except ConfigError as e:
                console.print(f"[red]❌ {e}[/red]")
                if Confirm.ask("Use this path anyway?"):
                    config_manager.set_section_value(
                        "jetraw_paths", binary, path_input.strip()
                    )
                    console.print(
                        f"[yellow]⚠️[/yellow] {binary} path set (validation bypassed)"
                    )
                    break


def _validate_and_set_path(
    config_manager: ConfigManager, binary: str, path: Path
) -> None:
    """
    Validate and set installation path.

    Validates that the path exists and contains a valid installation,
    then sets it in the configuration.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :param binary: Name of the binary (jetraw or dpcore).
    :type binary: str
    :param path: Path to validate and set.
    :type path: Path
    :raises ConfigError: If the directory doesn't exist.
    :rtype: None
    """
    if not path.exists():
        raise ConfigError(f"Directory does not exist: {path}")

    if not PathDetector.validate_installation_path(path, binary):
        console.print(
            f"[yellow]⚠️  Warning: This doesn't look like a {binary} installation (no bin/{binary} found)[/yellow]"
        )

    config_manager.set_section_value("jetraw_paths", binary, str(path))
    console.print(f"[green]✓[/green] {binary} path configured: {path}")


def _auto_detect_paths(config_manager: ConfigManager) -> None:
    """
    Auto-detect and configure installation paths.

    Attempts to automatically detect JetRaw and DPCore installation
    paths using system commands and sets them in the configuration.

    :param config_manager: ConfigManager instance to update.
    :type config_manager: ConfigManager
    :raises ConfigError: If no installations are auto-detected.
    :rtype: None
    """
    console.print("[blue]🔍 Auto-detecting installation paths...[/blue]")

    detected: bool = False
    for binary in ["jetraw", "dpcore"]:
        path: Optional[Path] = PathDetector.find_binary_path(binary)
        if path:
            config_manager.set_section_value("jetraw_paths", binary, str(path))
            console.print(f"[green]✓[/green] Auto-detected {binary}: {path}")
            detected = True
        else:
            console.print(f"[yellow]⚠️[/yellow] Could not auto-detect {binary}")

    if not detected:
        console.print(
            "[red]❌ No installations auto-detected. Please configure manually.[/red]"
        )
        raise ConfigError("Auto-detection failed")
