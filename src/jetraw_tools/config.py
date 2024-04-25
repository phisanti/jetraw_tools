import os
import shutil
import glob
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
        if overwrite.lower() != 'y':
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
