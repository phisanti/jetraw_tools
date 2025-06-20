# 🚀 JetRaw_tools

Welcome to `jetraw_tools`! This repository contains a collection of supplementary tools to work with the [JetRaw](https://github.com/Jetraw/Jetraw) compression tool. JetRaw is an innovative image compression format that allows a file reduction ~70-80% while keeping absolute original image resolution. The reasoning for developing these complementary tools was that our team mainly worked with nd2 images of high order (TZCXY) and we needed to preserve the metadata of the images.

## 🛠️ Installation

To install `jetraw_tools`, follow these simple steps:

1. Make sure you have [Python](https://www.python.org/) installed on your system (version 3.8 or higher). 
2. Install the Jetraw app and add it to the PATH environment as described in the [JetRaw](https://jetraw-releases.s3.eu-central-2.amazonaws.com/Jetraw-user-manual/latest/html/jetraw_core/index.html).
3. Install this repository to your local machine using the following command:

```shell
pip install jetraw_tools
```

Or directly from the repository:

```shell
pip install git+https://github.com/phisanti/jetraw_tools.git
```

### Dependencies

The package requires the following main dependencies:
- nd2
- ome-types
- tifffile
- numpy
- typer

These will be automatically installed when you install the package.

## 📖 Usage

Once installed, you can use the `jetraw-tools` from the command line or from a python script.

### Initial Configuration

Before using jetraw-tools for the first time, you need to configure it with your calibration file, identifiers, and license key:

```bash
jetraw-tools settings
```

The configuration tool will guide you through each step with interactive prompts, making setup straightforward even for first-time users. This command will:
- Create the ~/.config/jetraw_tools folder if it doesn't exist
- Copy a calibration .dat file to the configuration folder
- Store a list of camera identifiers for easy reference
- Detect and configure Jetraw and DPCore installation paths
  - Automatically finds installed binaries when possible
  - Allows manual entry of installation directories if needed
- Add your license key for JetRaw functionality

### Compression and Decompression

You can directly compress an image via:

```bash
jetraw-tools compress /path/to/image_or_folder --calibration_file "calibration_file.dat" -i "identifier" --extension ".ome.tiff"
```

The calibration file and identifier are required for compression. You can provide these parameters with each command or configure them once using the settings command.

By default, compressed files are saved in a new folder with your original folder's name plus the `_compressed` suffix. For custom output locations, use the `--output` parameter.

After configuration, the default calibration .dat file, identifier, and paths don't need to be specified each time you run the tool. Therefore, you can run simpler commands like:

```bash
jetraw-tools compress "sample_images/" --extension ".ome.tiff"
jetraw-tools decompress "sample_images/" --extension ".ome.p.tiff"
```

### 📋 Options 

#### Compression/Decompression Command
```bash
jetraw-tools compress [TARGETPATH] [OPTIONS]
jetraw-tools decompress [TARGETPATH] [OPTIONS]
```

**Available Options:**
- `--calibration_file`: Path to calibration .dat file (if not provided, it will use the default one from the configuration)
- `-i, --identifier`: Image capture mode identifier (if not provided, it will use the first one from the configuration)
- `--extension`: Input image file extension (default: .nd2 for compress, .ome.p.tiff for decompress)
- `--ncores`: Number of cores to use (default: 0 for auto-detection)
- `-o, --output`: Specify a custom output folder for processed images
- `--metadata/--no-metadata`: Process metadata (default: True)
- `--json`: Save metadata as JSON (default: False for compress)
- `--key`: Pass license key to JetRaw (if not provided, it will use the stored one from the configuration)
- `--remove`: Delete original images after compression (default: False)
- `--op/--no-op`: Omit processed files (default: True)
- `-v, --verbose`: Enable detailed logging output (default: False)
- `--version`: Show version and exit

#### Settings Command
```bash
jetraw-tools settings
```

# 📜 Disclaimer
This library is not affiliated with Dotphoton or Jetraw in any way, but we are grateful for their support.
