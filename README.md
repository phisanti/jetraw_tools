# 🚀 JetRaw_tools

Welcome to `jetraw_tools`! This repository contains a collection of supplementary tools to work with the [JetRaw](https://github.com/Jetraw/Jetraw) compression tool. JetRaw is an innovative image compression format that allows a file reduction ~70-80% while keeping absolute original image resolution. The reasoning for developing these complementary tools was that our team mainly worked with nd2 images of high order (TZCXY) and we needed to preserve the metadata of the images.

## 🛠️ Installation

To install `jetraw_tools`, follow these simple steps:

1. Make sure you have [Python](https://www.python.org/) installed on your system (version 3.6 or higher). 
2. Install the Jetraw app and add it to the PATH environment as described in the [JetRaw](https://github.com/Jetraw/Jetraw) repository and install the `dpcore` python libraries. These are unfortunately not available to install via `pip` but you can find the wheel in the [JetRaw](https://github.com/Jetraw/Jetraw).
4. Clone this repository to your local machine using the following command:

```shell
pip install git+https://github.com/phisanti/jetraw_tools.git
```

## 📖 Usage
Once installed, you can use the jetraw_tools from the command line of from a python script. 

You can directly compress an image via:

```
jetraw_tools -c /path/to/image_or_folder -c "calibration_file.dat" -i "identifier"  --extension ".ome.tiff"
```
The calibrartion file and identifier are required for the compression. They can be provided each time or you can set a configuration file via.

```
jetraw_tools --settings
```

This command will:
- Create the ~/.config/jetraw_tools folder if it doesn't exist
- Copy a calibration .dat
- Store a list of identifiers
- Add licence key

Then, default calibration .dat file and identifier don't need to be specified each time. Therefore, you can run:

```
jetraw_tools -c "sample_images/" --extension ".ome.tiff"
jetraw_tools -d "sample_images/" --extension ".ome.p.tiff"

```


### 📋 Options 
- -c, --compress: path to image(s) to compress
- -d, --decompress: path to image(s) to decompress
- -s, --settings: Re-initialize configuration
- --calibration_file: Path to calibration .dat file
- --identifier: Image capture mode identifier
- --extension: Input image file extension (default .tif)
- --metadata: Process metadata (default True)
- --json: Save metadata as JSON (default True)
- --key: Pass licecne key to JetRaw (default None)
- --remove: Delete original images after compression (default False)

The compressed JetRaw files will be saved in a jetraw_compressed folder alongside the original images.




