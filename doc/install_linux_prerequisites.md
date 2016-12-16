Linux Install Prerequisites
===========================

Some native Linux packages are required when installing the CLI with:
- Interactive install script
- ``pip``

The commands to run to install the dependencies for some common distributions are listed below.

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

### Ubuntu 12.04 LTS
Python 2.7.3 should be already on the machine.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev
```

### Ubuntu 14.04 LTS and BASH on Windows (Build 14362+)
Python 2.7.6 should be already on the machine.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev
```

### Ubuntu 15.10
Python 2.7.10 should be already on the machine.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### Ubuntu 16.04 LTS
Python 2.7.11 should be already on the machine.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### Debian 7
Python 2.7.3 should be already on the machine.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev
```

### Debian 8
Python 2.7.9 should be already on the machine.
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### CentOS 6.5 / 6.6 / 6.7

Not supported with the default version of Python (2.6.6) on the machine.

### CentOS 7.1 / 7.2
Python 2.7.5 should be already on the machine.
```
sudo yum check-update; sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

### RedHat RHEL 6.7

Not supported with the default version of Python (2.6.6) on the machine.

### RedHat RHEL 7.2
Python 2.7.5 should be already on the machine.
```
sudo yum check-update; sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

### SUSE OpenSUSE 13.2
Python 2.7.8 should be already on the machine.
```
sudo zypper refresh && sudo zypper --non-interactive install gcc libffi-devel python-devel openssl-devel
```

### CoreOS Stable-899.15.0 / Beta-1010.1.0 / Alpha-1010.1.0

Python is not installed by default.
