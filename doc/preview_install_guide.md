Preview Install Guide
========================================

Looking to get started with Project Az?

We've provided some step-by-step instructions on installing for different platforms and versions.
This assumes a clean install with nothing else previously installed on the box.

Click on your OS for steps:

* [OS X](#os-x)
* Ubuntu
  * [12.04 LTS](#ubuntu-1204-lts)
  * [14.04 LTS](#ubuntu-1404-lts-and-bash-on-windows-build-14362)
  * [15.10](#ubuntu-1510)
  * [16.04 LTS](#ubuntu-1604-lts)
* Debian
  * [7](#debian-7)
  * [8](#debian-8)
* CentOS
  * [6.5 - 6.7](#centos-65--66--67)
  * [7.1 - 7.2](#centos-71--72)
* RHEL
  * [6.7](#redhat-rhel-67)
  * [7.2](#redhat-rhel-72)
* [SUSE](#suse-opensuse-132)
* [CoreOS](#coreos-stable-899150--beta-101010--alpha-101010)
* Windows
  * [Command Prompt / cmd](#windows-cmd)
  * [Bash on Windows](#ubuntu-1404-lts-and-bash-on-windows-build-14362)
* Python/PIP
  * [Developer Setup](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md)
* [Installation troubleshooting](#installation-troubleshooting)

# Instructions per Platform and Version

## OS X
```
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```
`sudo bash` instead of just `bash` may be required if you get a 'Permission error'.

## Ubuntu 12.04 LTS
On a fresh Ubuntu 12.04 VM, install the CLI by executing the following.
Python 2.7.3 should be already on the machine.

```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

**Known warnings**
Warning 1:
You may see the following warning message during install and execution of `az`.
```
/usr/local/az/envs/default/local/lib/python2.7/site-packages/pip/pep425tags.py:30: RuntimeWarning: invalid Python installation: unable to open /usr/az/envs/default/lib/python2.7/config/Makefile (No such file or directory)
  warnings.warn("{0}".format(e), RuntimeWarning)
```
See also https://github.com/pypa/pip/issues/1074.


Warning 2:
InsecurePlatformWarning
```
/usr/local/az/envs/default/local/lib/python2.7/site-packages/requests/packages/urllib3/util/ssl_.py:122: InsecurePlatformWarning: A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail. You can upgrade to a newer version of Python to solve this. For more information, see https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.
  InsecurePlatformWarning
```

Use the defaults for the install location and location of the executable.

This will install the CLI globally on the system.

## Ubuntu 14.04 LTS and BASH on Windows (Build 14362+)
Python 2.7.6 should be already on the machine.

```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

Use the defaults for the install location and location of the executable.

This will install the CLI globally on the system.

**Known warnings**
InsecurePlatformWarning
```
/usr/local/az/envs/default/local/lib/python2.7/site-packages/requests/packages/urllib3/util/ssl_.py:122: InsecurePlatformWarning: A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail. You can upgrade to a newer version of Python to solve this. For more information, see https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.
  InsecurePlatformWarning
```

## Ubuntu 15.10
Python 2.7.10 should be already on the machine.
```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
sudo apt-get install -y build-essential
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

Use the defaults for the install location and location of the executable.

This will install the CLI globally on the system.

## Ubuntu 16.04 LTS
Python 2.7.11 should be already on the machine.
```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
sudo apt-get install -y build-essential
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

## Debian 7
Python 2.7.3 should be already on the machine.
```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.

## Debian 8
Python 2.7.9 should be already on the machine.
```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
sudo apt-get install -y build-essential
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.


## CentOS 6.5 / 6.6 / 6.7

Not supported with the default version of Python (2.6.6) on the machine.

## CentOS 7.1 / 7.2
Python 2.7.5 should be already on the machine.
```
sudo yum check-update
sudo yum install -y gcc libffi-devel python-devel openssl-devel
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.

/usr/local/bin is not in root's path so if you become root, you have to run /usr/local/bin/az to get it to work.
https://bugs.centos.org/view.php?id=5707

## RedHat RHEL 6.7

Not supported with the default version of Python (2.6.6) on the machine.

## RedHat RHEL 7.2
Python 2.7.5 should be already on the machine.
```
sudo yum check-update
sudo yum install -y gcc libffi-devel python-devel openssl-devel
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.

/usr/local/bin is not in root's path so if you become root, you have to run /usr/local/bin/az to get it to work.
https://bugs.centos.org/view.php?id=5707

## SUSE OpenSUSE 13.2
Python 2.7.8 should be already on the machine.
```
sudo zypper refresh
sudo zypper --non-interactive install gcc libffi-devel python-devel openssl-devel
curl -L https://aka.ms/ProjectAzInstall | sudo bash
```

## CoreOS Stable-899.15.0 / Beta-1010.1.0 / Alpha-1010.1.0

Doesn't have python installed by default and is not currently supported.


## Windows (cmd)

Set the environment variable to point to the version you wish to install.

```shell
    set AZURE_CLI_NIGHTLY_VERSION=2016.06.30.nightly
```

Run the following from a command prompt

```shell
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
```

Run the CLI

```shell
   az
```

Installation Troubleshooting
----------------------------

**Errors with curl redirection**

If you get an error with the curl command regarding the `-L` parameter or an error saying `Object Moved`, try using the full url instead of the aka.ms url:
```shell
# If you see this:
$ curl -L https://aka.ms/ProjectAzInstall | sudo bash
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   175  100   175    0     0    562      0 --:--:-- --:--:-- --:--:--   560
bash: line 1: syntax error near unexpected token `<'
'ash: line 1: `<html><head><title>Object moved</title></head><body>

# Try this instead:
$ curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
```


**Errors on install with cffi or cryptography:**

If you get errors on install on **OS X**, upgrade pip by typing:

```shell
    pip install --upgrade --force-reinstall pip
```

If you get errors on install on **Debian or Ubuntu** such as the examples below,
install libssl-dev and libffi-dev by typing:

```shell
    sudo apt-get update
    sudo apt-get install -y libssl-dev libffi-dev
```

Also install Python Dev for your version of Python.

Python 2:

```shell
    sudo apt-get install -y python-dev
```

Python 3:

```shell
    sudo apt-get install -y python3-dev
```

Ubuntu 15 may require `build-essential` also:

```shell
    sudo apt-get install -y build-essential
```

**Example Errors**

```shell

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
```

```shell
    #include <openssl/e_os2.h>
                             ^
    compilation terminated.
    error: command 'x86_64-linux-gnu-gcc' failed with exit status 1

    Failed building wheel for cryptography
```

See Stack Overflow question - [Failed to install Python Cryptography package with PIP and setup.py](http://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py)
