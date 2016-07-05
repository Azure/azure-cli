Microsoft Azure Command-Line Tools
==================================

This is the Microsoft Azure CLI.

This package has [not] been tested [much] with Python 2.7, 3.4 and 3.5.


Installation
============

cURL Installation (nightly build)
---------------------------------

To install via cURL on Linux, Unix and OS X, type:

.. code:: shell

    curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | bash

``sudo bash`` may be required if you get a 'Permission error'.

If you chose to enable tab completion, type ``exec -l $SHELL`` to restart your shell.

Note: This will install the latest nightly builds.

Installation with pip (nightly build)
-------------------------------------

**1 Prerequisites that should be installed**

    - Python
    - pip
    - virtualenv / venv

On Windows, you can install Python 3.5.1 from the `Python download site <https://www.python.org/downloads/release/python-351/>`__.
When installing, enable the 'add Python to PATH' option. Also, choose to include 'pip' in the installation.
After Python has been installed, to install virtualenv, run ``pip install virtualenv``.

Also, it is recommended to upgrade pip to the latest version ``pip install --upgrade pip``.

**2 Create and activate your virtual environment**

For example, ``virtualenv env`` to create the environment.

Activate the environment.

(Unix)
``source env/bin/activate``

(Windows)
``env\Scripts\activate``

**3 Install the CLI**

**(Unix)**

Set the environment variable to point to the version you wish to install.

e.g. ``export AZURE_CLI_NIGHTLY_VERSION=2016.05.19.nightly``

.. code:: shell

    export AZURE_CLI_DISABLE_POST_INSTALL=1
    export AZURE_CLI_PRIVATE_PYPI_URL=http://40.112.211.51:8080
    export AZURE_CLI_PRIVATE_PYPI_HOST=40.112.211.51
    # Install the CLI and all default components
    pip install azure-cli==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-component==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-profile==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-storage==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-vm==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-network==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-resource==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST
    pip install azure-cli-feedback==$AZURE_CLI_NIGHTLY_VERSION --extra-index-url $AZURE_CLI_PRIVATE_PYPI_URL --trusted-host $AZURE_CLI_PRIVATE_PYPI_HOST

    # Enable tab completion if you wish.
    eval "$(register-python-argcomplete az)"


**(Windows)**

Set the environment variable to point to the version you wish to install.

e.g. ``set AZURE_CLI_NIGHTLY_VERSION=2016.05.19.nightly``

.. code:: shell

    set AZURE_CLI_DISABLE_POST_INSTALL=1
    set AZURE_CLI_PRIVATE_PYPI_URL=http://40.112.211.51:8080
    set AZURE_CLI_PRIVATE_PYPI_HOST=40.112.211.51
    pip install azure-cli==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-component==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-profile==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-storage==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-vm==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-network==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-resource==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
    pip install azure-cli-feedback==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%

**4 Run the CLI**

.. code:: shell

   az

Installation Troubleshooting
----------------------------

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

This project has adopted the `Microsoft Open Source Code of Conduct <https://opensource.microsoft.com/codeofconduct/>`__. For more information see the `Code of Conduct FAQ <https://opensource.microsoft.com/codeofconduct/faq/>`__ or contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`__ with any additional questions or comments.

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
