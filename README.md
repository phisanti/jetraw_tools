# 🚀 JetRaw_tools

Welcome to `jetraw_tools`! This repository contains a collection of supplementary tools to work with the [JetRaw](https://github.com/Jetraw/Jetraw) compression tool. JetRaw is an innovative image compression format that allows a file reduction ~70-80% while keeping absolute original image resolution. The reasoning for developing these complementary tools was that our team mainly worked with nd2 images of high order (TZCXY) and we needed to preserve the metadata of the images.

## 🛠️ Installation

To install `jetraw_tools`, follow these simple steps:

1. Make sure you have [Python](https://www.python.org/) installed on your system (version 3.8 or higher). 
2. Install the Jetraw app and add it to the PATH environment as described in the [JetRaw](https://github.com/Jetraw/Jetraw) repository and install the `dpcore` python libraries. These are unfortunately not available to install via `pip` but you can find the wheel in the [JetRaw](https://github.com/Jetraw/Jetraw).
3. Install this repository to your local machine using the following command:

```shell
pip install git+https://github.com/phisanti/jetraw_tools.git
```
### Dependencies

The package requires the following main dependencies:
- nd2
- ome-types
- tifffile
- numpy

These will be automatically installed when you install the package.

## 📖 Usage
Once installed, you can use the jetraw_tools from the command line or from a python script. 

You can directly compress an image via:

```
jetraw_tools -c /path/to/image_or_folder --calibration_file "calibration_file.dat" -i "identifier"  --extension ".ome.tiff"
```

The calibration file and identifier are required for compression. You can provide these parameters with each command or configure them once using the settings command.

By default, compressed files are saved in a new folder with your original folder's name plus the `_compressed` suffix. For custom output locations, use the `--output` parameter.

```
jetraw_tools --settings
```

The configuration tool will guide you through each step with interactive prompts, making setup straightforward even for first-time users. This command will:
- Create the ~/.config/jetraw_tools folder if it doesn't exist
- Copy a calibration .dat file to the configuration folder
- Store a list of camera identifiers for easy reference
- Detect and configure Jetraw and DPCore installation paths
  - Automatically finds installed binaries when possible
  - Allows manual entry of installation directories if needed
- Add your license key for JetRaw functionality

After configuration, the default calibration .dat file, identifier, and paths don't need to be specified each time you run the tool. Therefore, you can run simpler commands like:

```
jetraw_tools -c "sample_images/" --extension ".ome.tiff"
jetraw_tools -d "sample_images/" --extension ".ome.p.tiff"

```


### 📋 Options 
- `-c, --compress`: path to image(s) to compress
- `-d, --decompress`: path to image(s) to decompress
- `-s, --settings`: Re-initialize configuration
- `--calibration_file`: Path to calibration .dat file
- `--identifier`: Image capture mode identifier
- `--extension`: Input image file extension (default: .tif)
- `--metadata`: Process metadata (default: True)
- `--json`: Save metadata as JSON (default: True)
- `--key`: Pass licence key to JetRaw (default: None)
- `--remove`: Delete original images after compression (default: False)
- `--output`: Specify a custom output folder for processed images (default: None)
- `--verbose`: Enable detailed logging output (default: False)

The compressed JetRaw files will be saved in a jetraw_compressed folder alongside the original images.

# 📜 Disclaimer
This library is not affiliated with Dotphoton or Jetraw in any way, but we are grateful for their support.




