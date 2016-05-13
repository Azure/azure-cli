Microsoft Project AZ Preview
==================================

The Project AZ team is excited to offer a preview build for members of the GitHub Azure organization.  While we are still early in this experiment, it is never too early to get feedback and we are eagerly interested in getting yours!

Installation via CURL
-----------------

To install via cURL on Linux, Unix and OS X, type:

    curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | bash

If you chose to enable tab completion, type `exec -l $SHELL` to restart your shell.

Note: This will install the latest nightly builds.  You may re-run this script later to safely update to the latest version.

Example Demo Script
-------------------

This preview covers a number of popular scenarios:

1. Find common VM images
2. Search all VM images
3. Create a Linux VM using SSH
4. List all IP Addresses in a resource group
5. Export a resource group to an ARM template
6. Using Query to control outputs
7. Learning to Query with JPTerm
8. Simplified help experience

For sample scripts and commands, please visit the [Demo Scripts](https://github.com/Azure/azure-cli/blob/master/doc/preview_demo_scripts.md) page.  

Reporting issues and feedback
=======================================

If you encounter any bugs with the tool please file an issue in the [Issues](https://github.com/Azure/azure-cli/issues) section of our GitHub repo.


Troubleshooting
---------------

**Errors on install with cffi or cryptography:**

If you get errors on install on **OS X**, upgrade pip by typing:

    pip install --upgrade --force-reinstall pip

If you get errors on install on **Debian or Ubuntu** such as the examples below,
install libssl-dev and libffi-dev by typing:

    sudo apt-get update
    sudo apt-get install -y libssl-dev libffi-dev

Also install Python Dev for your version of Python.

Python 2:

    sudo apt-get install -y python-dev

Python 3:

    sudo apt-get install -y python3-dev

Ubuntu 15 may require `build-essential` also:

    sudo apt-get install -y build-essential


**Example Errors**

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


    #include <openssl/e_os2.h>
                             ^
    compilation terminated.
    error: command 'x86_64-linux-gnu-gcc' failed with exit status 1

    Failed building wheel for cryptography

See Stack Overflow question - [Failed to install Python Cryptography package with PIP and setup.py](http://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py>)
