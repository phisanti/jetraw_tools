import argparse


valid_extensions = [
    ".nd2",
    ".tif",
    ".tiff",
    ".ome.tif",
    ".ome.tiff",
    ".p.tif",
    ".p.tiff",
    ".ome.p.tif",
    ".ome.p.tiff",
]
parser = argparse.ArgumentParser(
    prog="jetraw_tools", description="Compress images to JetRaw format"
)
parser.add_argument(
    "-d", "--decompress", type=str, help="Path to file or folder to compress"
)
parser.add_argument(
    "-c", "--compress", type=str, help="Path to file or folder to compress"
)

parser.add_argument(
    "-o",
    "--output",
    type=str,
    default=None,
    help="Optional output folder for processed images",
)
parser.add_argument(
    "-s", "--settings", action="store_true", help="Initialize the configuration"
)
parser.add_argument(
    "--calibration_file", type=str, default="", help="Path to calibration file"
)
parser.add_argument(
    "-i", "--identifier", type=str, default="", help="Identifier for capture mode"
)
parser.add_argument(
    "--op",
    "--omit-processed",
    action="store_true",
    default=False,
    help="omit files that have been processed",
)

parser.add_argument(
    "--extension",
    type=str,
    default=".tif",
    choices=valid_extensions,
    help="Image file extension",
)

parser.add_argument(
    "--ncores",
    type=int,
    default=0,
    help="Number of cores to use, by default 0 (all available cores)",
)
parser.add_argument(
    "--metadata", action="store_true", default=True, help="Process metadata"
)
parser.add_argument(
    "--json", action="store_true", default=True, help="Save metadata as JSON"
)
parser.add_argument(
    "--remove", action="store_true", default=False, help="Delete original images"
)
parser.add_argument("-k", "--key", type=str, default="", help="Licence key")
parser.add_argument(
    "--verbose", action="store_true", default=True, help="Prints verbose output"
)
