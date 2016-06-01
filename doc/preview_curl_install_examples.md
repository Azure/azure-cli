cURL Install Examples
========================================

You can use cURL to install the CLI.

This document provides step-by-step instructions on installing on different systems.  
This assumes a clean install with nothing else previously installed on the box.

## OS X
```
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | bash
```

## Ubuntu 12.04 LTS
On a fresh Ubuntu 12.04 VM, install the CLI by executing the following.  
Python 2.7.3 should be already on the machine.

```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
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

## Ubuntu 14.04 LTS
Python 2.7.6 should be already on the machine.

```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
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
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
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
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
```

## Debian 7
Python 2.7.3 should be already on the machine.
```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.

## Debian 8
Python 2.7.9 should be already on the machine.
```
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
sudo apt-get install -y build-essential
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.


## CentOS 6.5 / 6.6 / 6.7

Not supported with the default version of Python (2.6.6) on the machine.

## CentOS 7.1 / 7.2
Python 2.7.5 should be already on the machine.
```
sudo yum check-update
sudo yum install -y gcc libffi-devel python-devel openssl-devel
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
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
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
```

Tab completion gets set up for the root user, not all users if installed globally.

/usr/local/bin is not in root's path so if you become root, you have to run /usr/local/bin/az to get it to work.
https://bugs.centos.org/view.php?id=5707

## SUSE OpenSUSE 13.2
Python 2.7.8 should be already on the machine.
```
sudo zypper refresh
sudo zypper --non-interactive install gcc libffi-devel python-devel openssl-devel
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install | sudo bash
```

## CoreOS Stable-899.15.0 / Beta-1010.1.0 / Alpha-1010.1.0

Doesn't have python installed by default.