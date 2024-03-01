import os
import re
import argparse
from jetraw_tools.folder_compression import compress_folder, process_image
from jetraw_tools.utils import create_compress_folder
from jetraw_tools.config import configjrt
import configparser

def main():


    parser = argparse.ArgumentParser(prog="jetraw_tools", description='Compress images to JetRaw format')
    parser.add_argument("-c", "--config", action="store_true", help="Initialize the configuration")
    parser.add_argument('compress', type=str, help='Path to file or folder to compress')
    parser.add_argument('--calibration_file', type=str, default='', help='Path to calibration file')
    parser.add_argument('--identifier', type=str, default='', help='Identifier for capture mode')
    parser.add_argument('--extension', type=str, default='.tif', choices=['.tif', '.nd2', '.ome.tif'], help='Image file extension')
    parser.add_argument('--metadata', action='store_true', default=True, help='Process metadata')
    parser.add_argument('--json', action='store_true', default=True, help='Save metadata as JSON')
    parser.add_argument('--remove', action='store_true', default=False, help='Delete original images')

    args = parser.parse_args()
    
    # Set default calibration file path
    if args.config:
        configjrt()

    config_file=os.path.expanduser("~/.config/jetraw_tools/jetraw_tools.cfg")    
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

    if args.calibration_file == "":
        cal_file = config['calibration_file']["calibration_file"]
    else:
        cal_file = args.calibration_file
    
    if args.identifier == "":
        identifier = config['identifiers']["id1"]
    elif re.match(r'^id\d+$', args.identifier):
        identifier = config['identifiers'][args.identifier]
    else:
        identifier = args.identifier

    
    print(f"Using calibration file: {os.path.basename(cal_file)} and identifier: {identifier}")

    if identifier == "" or cal_file == "":
        raise ValueError("Identifier and calibration file must be set. Use --config to set them or provide them as arguments.")
    
    full_path = os.path.join(os.getcwd(), args.compress)
    compress_folder(full_path, cal_file, identifier, args.extension, args.metadata, args.json, args.remove)

if __name__ == '__main__':
    main()
