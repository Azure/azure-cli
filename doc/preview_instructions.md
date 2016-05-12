Microsoft Azure Command-Line Tools
==================================

This is the Microsoft Azure CLI.

This package has [not] been tested [much] with Python 2.7, 3.4 and 3.5.


Installation
============

Installation via CURL (recommended)
-----------------

To install via cURL on Linux, Unix and OS X, type:

.. code:: shell

    curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | bash

If you chose to enable tab completion, type `exec -l $SHELL` to restart your shell.

Note: This will install the latest nightly builds.


Installation via PIP (not recommended)
----------------

To install via the Python Package Index (PyPI), type:

.. code:: shell

    pip install azure-cli


Providing Feedback and Reporting Issues
=======================================

If you encounter any bugs with the tool please file an issue in the
`Issues <https://github.com/Azure/azure-cli/issues>`__
section of the project.


Troubleshooting
==============

**Errors on install with cffi or cryptography:**

If you get errors on install on **OS X**, upgrade pip by typing:

.. code:: shell

    pip install --upgrade --force-reinstall pip


If you get errors on install on **Debian or Ubuntu** such as the examples below,
install libssl-dev and libffi-dev by typing:

.. code:: shell

    sudo apt-get update
    sudo apt-get install -y libssl-dev libffi-dev

Also install Python Dev for your version of Python.

Python 2:

.. code:: shell

    sudo apt-get install -y python-dev

Python 3:

.. code:: shell

    sudo apt-get install -y python3-dev

Ubuntu 15 may require `build-essential` also:

.. code:: shell

    sudo apt-get install -y build-essential


**Example Errors**

.. code:: shell

    Downloading cffi-1.5.2.tar.gz (388kB)
      100% |################################| 389kB 3.9MB/s
      Complete output from command python setup.py egg_info:

          No working compiler found, or bogus compiler options
          passed to the compiler from Python's distutils module.
          See the error messages above.
          (If they are about -mno-fused-madd and you are on OS/X 10.8,
          see http://stackoverflow.com/questions/22313407/ .)

      ----------------------------------------
    Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-77i2fido/cffi/

.. code:: shell

    #include <openssl/e_os2.h>
                             ^
    compilation terminated.
    error: command 'x86_64-linux-gnu-gcc' failed with exit status 1

    Failed building wheel for cryptography

`See Stack Overflow question - Failed to install Python Cryptography package with PIP and setup.py <http://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py>`__
