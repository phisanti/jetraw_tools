.. jetraw_tools documentation master file, created by
   sphinx-quickstart on Thu Jun 19 21:30:05 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

jetraw_tools Documentation
==========================

jetraw_tools is a Python API interface to the C-bindings of the JetRaw Compression Algorithm. 
This package provides Python wrappers around the native JetRaw C libraries, enabling high-performance 
image compression and decompression through an intuitive Python interface.

The package consists of two main components:

* **CLI command line interface** for direct terminal-based image processing
* **CompressionTool Class** for programmatic integration into Python workflows

Key Features
------------

* **C-bindings interface**: Direct Python API to native JetRaw C libraries for optimal performance
* **TIFF file support**: Read and write TIFF files with full metadata preservation
* **Command-line interface**: Process images directly from the terminal using the CLI
* **Compression tool**: Programmatic API for batch processing of multiple images in a folder and workflow integration

Basic Examples
------------------

After configuring jetraw-tools with ``jetraw-tools settings``, here are some common usage examples:

Basic compression and decompression:

.. code-block:: bash

   # Compress all .nd2 files in a directory
   jetraw-tools compress /path/to/images/

   # Decompress all compressed files
   jetraw-tools decompress /path/to/compressed_images/

Using extension flag to specify file types:

.. code-block:: bash

   # Compress specific file types
   jetraw-tools compress /path/to/images/ --extension ".tiff"

   # Decompress specific compressed file types
   jetraw-tools decompress /path/to/compressed/ --extension ".ome.p.tiff"

Using remove flag to delete original files after processing:

.. code-block:: bash

   # Remove original files after successful compression
   jetraw-tools compress /path/to/images/ --remove

   # Remove compressed files after successful decompression
   jetraw-tools decompress /path/to/compressed/ --remove

Using output flag to specify custom output directory:

.. code-block:: bash

   # Custom output directory for compression
   jetraw-tools compress /path/to/images/ --output /custom/output/directory/

   # Custom output directory for decompression
   jetraw-tools decompress /path/to/compressed/ --output /restored/images/

Using metadata flags to control metadata processing:

.. code-block:: bash

   # Process files without preserving metadata
   jetraw-tools compress /path/to/images/ --no-metadata

   # Process files with metadata (default behavior)
   jetraw-tools compress /path/to/images/ --metadata

   # Save metadata as JSON during compression
   jetraw-tools compress /path/to/images/ --json

.. toctree::

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
