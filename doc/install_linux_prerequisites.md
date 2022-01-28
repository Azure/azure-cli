Linux Install Prerequisites
===========================

Some native Linux packages are required when installing the CLI with:
- Interactive install script
- ``pip``

Current supported Python versions are Python 3.6, 3.7, 3.8. Azure CLI packages prior to version 2.1.0 support both Python 2.7 and Python 3.

The commands to run to install the dependencies for some common distributions are listed below.

* Ubuntu
  * [12.04 LTS](#ubuntu-1204-lts)
  * [14.04 LTS](#ubuntu-1404-lts-and-bash-on-windows-build-14362)
  * [15.10](#ubuntu-1510)
  * [16.04 LTS](#ubuntu-1604-lts)
  * [18.04 LTS](#ubuntu-1804-lts)
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
* [Flatcar](#flatcar)

### Ubuntu 12.04 LTS
Python 2.7.3 should be already on the machine. Install Python 3.6+ if needed.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev
```

### Ubuntu 14.04 LTS and BASH on Windows (Build 14362+)
Python 2.7.6 should be already on the machine. Install Python 3.6+ if needed.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev
```

### Ubuntu 15.10
Python 2.7.10 should be already on the machine. Install Python 3.6+ if needed.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### Ubuntu 16.04 LTS
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### Ubuntu 18.04 LTS
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### Debian 7
Python 2.7.3 should be already on the machine. Install Python 3.6+ if needed.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev
```

### Debian 8
Python 2.7.9 should be already on the machine. Install Python 3.6+ if needed.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### CentOS 6.5 / 6.6 / 6.7

Not supported with the default version of Python (2.6.6) on the machine. Install Python 3.6+ if needed.

### CentOS 7.1 / 7.2
Python 2.7.5 should be already on the machine. Install Python 3.6+ if needed.
```
sudo yum check-update; sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

### RedHat RHEL 6.7

Not supported with the default version of Python (2.6.6) on the machine. Install Python 3.6+ if needed.

### RedHat RHEL 7.2
Python 2.7.5 should be already on the machine. Install Python 3.6+ if needed.
```
sudo yum check-update; sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

### SUSE OpenSUSE 13.2
Python 2.7.8 should be already on the machine. Install Python 3.6+ if needed.
```
sudo zypper refresh && sudo zypper --non-interactive install gcc libffi-devel python-devel openssl-devel
```

### Flatcar

Python is installed in the Azure-specific distribution of Flatcar, but is installed into the non-standard location `/usr/share/oem/python/bin/python`.
