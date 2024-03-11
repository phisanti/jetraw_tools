import os
import re
import argparse
import locale
import configparser
from jetraw_tools.compression_tool import CompressionTool
from jetraw_tools.config import configjrt

def main():

    valid_extensions = [".nd2", ".tif", ".tiff", ".ome.tif", ".ome.tiff", ".p.tif", ".p.tiff", ".ome.p.tif", ".ome.p.tiff"]
    parser = argparse.ArgumentParser(prog="jetraw_tools", description='Compress images to JetRaw format')
    parser.add_argument('-d', '--decompress', type=str, help='Path to file or folder to compress')
    parser.add_argument('-c', '--compress', type=str, help='Path to file or folder to compress')
    parser.add_argument("-s", "--settings", action="store_true", help="Initialize the configuration")
    parser.add_argument('--calibration_file', type=str, default='', help='Path to calibration file')
    parser.add_argument('--identifier', type=str, default='', help='Identifier for capture mode')
    parser.add_argument('--extension', type=str, default='.tif', choices=valid_extensions, help='Image file extension')
    parser.add_argument('--metadata', action='store_true', default=True, help='Process metadata')
    parser.add_argument('--json', action='store_true', default=True, help='Save metadata as JSON')
    parser.add_argument('--remove', action='store_true', default=False, help='Delete original images')
    parser.add_argument('--verbose', action='store_true', default=True, help='Prints verbose output')

    # Pase and set locale
    args = parser.parse_args()
    locale.setlocale(locale.LC_ALL, locale.getlocale())
    
    # Set default calibration file path
    if args.settings:
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

    
    if args.verbose:
        print(f"Using calibration file: {os.path.basename(cal_file)} and identifier: {identifier}")

    if identifier == "" or cal_file == "":
        raise ValueError("Identifier and calibration file must be set. Use --config to set them or provide them as arguments.")
    
    # Execure compress/decompress
    if args.compress:
        full_path = os.path.join(os.getcwd(), args.compress)
        mode = "compress"
        process_json=args.json

    if args.decompress:
        full_path = os.path.join(os.getcwd(), args.decompress)
        mode = "decompress"
        process_json=False
    compressor = CompressionTool(cal_file, identifier, args.verbose)
    compressor.process_folder(full_path, mode, args.extension, args.metadata, ome_bool=True, metadata_json=process_json, remove_source=args.remove)

if __name__ == '__main__':
    main()
