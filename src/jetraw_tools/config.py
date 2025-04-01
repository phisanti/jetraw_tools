import os
import shutil
import glob
import platform
import subprocess
import configparser


def configjrt():
    """
    Initialize the configuration file
    """

    # Create config folder
    config_folder = os.path.expanduser("~/.config/jetraw_tools")
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)

    # Config calibration.dat file
    cal_files = glob.glob(os.path.join(config_folder, "*.dat"))
    if cal_files:
        print("There is a calibration.dat file in the config folder:")
        dat_name = os.path.basename(cal_files[0])
        print(dat_name)
        overwrite = input(
            "\nDo you want to overwrite the existing calibration.dat file? (yes/no): "
        )
        if overwrite.lower() == "yes":
            copy_calibration_file(config_folder)

            for dat_file in cal_files:
                os.remove(dat_file)
        elif overwrite.lower() == "no":
            print("The existing calibration.dat file will be used.")
            config_identifiers(config_folder)
        elif overwrite.lower() == "":
            pass
    else:
        print("There are no *.dat files in the config folder.")

        copy_calibration_file(config_folder)
        # Config image identifiers
        config_identifiers(config_folder)

    # Add jetraw path
    add_jetraw_paths(config_folder)

    # Add licence key
    add_licence_key(config_folder)


def add_licence_key(config_folder):
    """Adds the licence key to the configuration file.
    :param config_folder: The path to the folder containing the configuration file.
    :type config_folder: str
    """

    config_file = os.path.join(config_folder, "jetraw_tools.cfg")
    config = configparser.ConfigParser()
    config.read(config_file)

    if not config.has_section("licence_key"):
        config.add_section("licence_key")

    current_key = config.get("licence_key", "key", fallback=None)

    if current_key:
        print(f"Current licence key: {current_key}")
        overwrite = input("Do you want to overwrite the current key? (y/n): ")
        if overwrite.lower() != "y":
            print("Licence key not updated.")
            return
    else:
        print("No licence key found.")

    new_key = input("Enter the new licence key: ")
    config["licence_key"]["key"] = new_key

    with open(config_file, "w") as f:
        config.write(f)

    print("Licence key updated successfully.")


def config_identifiers(config_folder: str) -> None:
    """
    Configure identifiers in the configuration file.

    This function reads the existing identifiers from the configuration file,
    provides an option to remove all identifiers, and allows the user to add new identifiers.
    The updated identifiers are then written back to the configuration file.

    :param config_folder: The path to the folder containing the configuration file.
    :type config_folder: str
    """

    config_file = os.path.join(config_folder, "jetraw_tools.cfg")
    config = configparser.ConfigParser()
    config.read(config_file)

    # Show identifiers
    if "identifiers" in config and config["identifiers"]:
        # Read existing config
        print("Existing identifiers:")
        for id in config["identifiers"]:
            print(id, ":", config["identifiers"][id])

        remove_all = input("Do you want to remove all identifiers? (yes/no): ")
        if remove_all.lower() == "yes":
            config.remove_section("identifiers")
            config["identifiers"] = {}
            with open(config_file, "w") as f:
                config.write(f)
            print("All identifiers have been removed.")

        elif remove_all.lower() == "no" or remove_all == "":
            print("No identifiers will be removed.")
            return

    # Config identifiers
    id_counter = 1
    while True:
        identifier = input(
            f"Enter identifier {id_counter} (or press Enter to finish): "
        )
        if identifier == "":
            break

        if identifier.lower() == "no":
            print("No identifiers will be added.")
            return

        if "identifiers" not in config:
            config.add_section("identifiers")
        config["identifiers"][f"id{id_counter}"] = identifier
        id_counter += 1

    with open(config_file, "w") as f:
        config.write(f)


def copy_calibration_file(config_folder: str) -> None:
    """Copy calibration file
    Interactively copies a '.dat' calibration file to a configuration
    folder and updates the configuration file.

    :param config_folder: Path to the configuration folder.
    :type config_folder: str
    """

    while True:
        calibration_file = input(
            "Enter the path to the calibration file (or 'enter' to quit): "
        )

        if calibration_file.lower() == "exit" or calibration_file == "":
            print("No identifier entered, exiting...")
            return

        elif not calibration_file.endswith(".dat"):
            print("File must be a .dat file")

        else:
            try:
                new_calibration = os.path.basename(calibration_file)
                new_calibration = os.path.join(config_folder, new_calibration)
                shutil.copy(calibration_file, new_calibration)

                # Write calibration file name to config file
                config_file = os.path.join(config_folder, "jetraw_tools.cfg")
                config = configparser.ConfigParser()
                if os.path.exists(config_file):
                    config.read(config_file)
                config["calibration_file"] = {"calibration_file": new_calibration}
                with open(config_file, "w") as f:
                    config.write(f)

                break
            except FileNotFoundError:
                print("The specified file does not exist. Please try again.")
            except Exception as e:
                print(f"An error occurred: {e}. Please try again.")


def add_jetraw_paths(config_folder):
    """Add Jetraw and DPCore installation paths to configuration

    :param config_folder: Path to the configuration folder
    :type config_folder: str
    """

    config_file = os.path.join(config_folder, "jetraw_tools.cfg")
    config = configparser.ConfigParser()
    config.read(config_file)

    # Create section if it doesn't exist
    if "jetraw_paths" not in config:
        config.add_section("jetraw_paths")

    # Check if paths already exist
    current_jetraw = config.get("jetraw_paths", "jetraw", fallback=None)
    current_dpcore = config.get("jetraw_paths", "dpcore", fallback=None)

    if current_jetraw or current_dpcore:
        if current_jetraw:
            print(f"Current Jetraw installation: {current_jetraw}")
        if current_dpcore:
            print(f"Current DPCore installation: {current_dpcore}")
        overwrite = input("Do you want to update these paths? (y/n): ")
        if overwrite.lower() != "y":
            print("Paths not updated.")
            return

    # Try to find binaries using which/where
    binaries = {"jetraw": None, "dpcore": None}
    cmd = "where" if platform.system() == "Windows" else "which"

    for binary in binaries.keys():
        try:
            result = subprocess.run(
                [cmd, binary], capture_output=True, text=True, check=False
            )

            if result.returncode == 0 and result.stdout.strip():
                binary_full_path = result.stdout.strip().split("\n")[0]
                # Get the bin directory
                bin_dir = os.path.dirname(binary_full_path)
                # Get the installation directory (parent of bin)
                install_dir = os.path.dirname(bin_dir)
                binaries[binary] = install_dir
                print(f"Found {binary} at: {binary_full_path}")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Show detection status
    if not binaries["jetraw"]:
        print("Jetraw binary not detected automatically.")
    if not binaries["dpcore"]:
        print("DPCore binary not detected automatically.")

    # Check if both were found
    if binaries["jetraw"] and binaries["dpcore"]:
        use_detected = input("Add the detected installations to the config? (y/n): ")
        if use_detected.lower() == "y":
            config["jetraw_paths"]["jetraw"] = binaries["jetraw"]
            config["jetraw_paths"]["dpcore"] = binaries["dpcore"]
            with open(config_file, "w") as f:
                config.write(f)
            print("Paths updated successfully.")
            return

    # Manual input if needed
    print("\nManual configuration:")

    # Manual input for binaries that weren't found
    for binary_ in ["jetraw", "dpcore"]:
        if not binaries[binary]:
            while True:
                if binary == "jetraw":
                    prompt = (
                        "Enter the Jetraw installation directory (or 'exit' to quit): "
                    )
                else:  # dpcore
                    prompt = "Enter the DPCore installation directory (or 'same' if same as Jetraw): "

                path = input(prompt)

                # Handle exit option (jetraw only)
                if binary == "jetraw" and path.lower() == "exit":
                    print("Configuration cancelled.")
                    return

                # Handle same option (dpcore only)
                if binary == "dpcore" and path.lower() == "same" and binaries["jetraw"]:
                    binaries["dpcore"] = binaries["jetraw"]
                    break

                if not os.path.exists(path):
                    print("The specified directory does not exist.")
                    continue

                # Check if it looks like a valid path
                if os.path.exists(os.path.join(path, "bin")):
                    binaries[binary] = path
                    break
                else:
                    print(
                        f"Warning: This doesn't look like a {binary} installation (no bin directory)."
                    )
                    use_anyway = input("Use anyway? (y/n): ")
                    if use_anyway.lower() == "y":
                        binaries[binary] = path
                        break

    # Save to config
    config["jetraw_paths"]["jetraw"] = binaries["jetraw"]
    config["jetraw_paths"]["dpcore"] = binaries["dpcore"]
    with open(config_file, "w") as f:
        config.write(f)
    print("Paths updated successfully.")
