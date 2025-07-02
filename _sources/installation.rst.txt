Installation
============

Requirements
------------

jetraw_tools requires Python 3.8 or later and depends on several scientific computing libraries:

- numpy
- nd2
- ome-types
- tifffile
- typer
- JetRaw libraries (for compression/decompression)
- dpcore python libraries

Installing from PyPI
---------------------

To install jetraw_tools from PyPI, use pip:

.. code-block:: bash

   pip install jetraw_tools


Installing from Source
----------------------

To install jetraw_tools latest version directly from the repository:

.. code-block:: bash

   pip install git+https://github.com/phisanti/jetraw_tools.git

This will install the package in development mode, allowing you to make changes to the source code.

To install jetraw_tools from source:

.. code-block:: bash

   git clone https://github.com/phisanti/jetraw_tools.git
   cd jetraw_tools
   pip install -e .

This will install the package in development mode, allowing you to make changes to the source code.

Dependencies
------------

The main dependencies are automatically installed:

- **numpy**: For numerical operations and array handling
- **nd2**: For reading ND2 microscopy files
- **ome-types**: For OME metadata handling
- **tifffile**: For TIFF file I/O operations
- **typer**: For command-line interface functionality
- **JetRaw C-libraries**: For compression and decompression functionality (installed separately)

Environment Setup
------------------

It's recommended to use a conda environment:

.. code-block:: bash

   conda create -n jetraw_tools python=3.8
   conda activate jetraw_tools
   pip install git+https://github.com/phisanti/jetraw_tools.git

Verification
------------

To verify the installation:

.. code-block:: bash

   jetraw-tools --version

This should print the current version of jetraw_tools.

You can also verify in Python:

.. code-block:: python

   import jetraw_tools
   print(jetraw_tools.__version__)

Initial Configuration
---------------------

After installation, run the configuration wizard to set up your environment:

.. code-block:: bash

   jetraw-tools settings

This will guide you through configuring:

- Calibration file path
- Camera identifiers  
- License key
- JetRaw and DPCore installation paths
