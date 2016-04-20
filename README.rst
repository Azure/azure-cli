Microsoft Azure Command-Line Tools
==================================

This is the Microsoft Azure CLI.

This package has [not] been tested [much] with Python 2.7, 3.4 and 3.5.


Installation
============

cURL Installation
-----------------

To install via cURL on Linux, Unix and OS X, type:

.. code:: shell

    curl http://azure-cli-nightly.cloudapp.net/install | bash

Note: This will install the latest nightly builds.

**Errors on install with cffi or cryptography:**

If you get errors on install on **OS X**, upgrade pip by typing:

.. code:: shell

    pip install --upgrade --force-reinstall pip


If you get errors on install on **Debian or Ubuntu** such as the examples below,
install libssl-dev, libffi-dev and python3-dev by typing:

.. code:: shell

    sudo apt-get update
    sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev


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


Download Package
----------------

To install via the Python Package Index (PyPI), type:

.. code:: shell

    pip install azure-cli


Download Source Code
--------------------

To get the source code of the SDK via **git** type:

.. code:: shell

    git clone https://github.com/Azure/azure-cli.git


Usage
=====



Need Help?
==========

Be sure to check out the Microsoft Azure `Developer Forums on Stack
Overflow <http://go.microsoft.com/fwlink/?LinkId=234489>`__ if you have
trouble with the provided code.


Contribute Code or Provide Feedback
===================================

If you would like to become an active contributor to this project please
follow the instructions provided in `Microsoft Azure Projects
Contribution
Guidelines <http://azure.github.io/guidelines.html>`__.

If you encounter any bugs with the tool please file an issue in the
`Issues <https://github.com/Azure/azure-cli/issues>`__
section of the project.


Learn More
==========

`Microsoft Azure Python Developer
Center <http://azure.microsoft.com/en-us/develop/python/>`__
