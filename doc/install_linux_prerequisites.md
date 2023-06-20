Linux Install Prerequisites
===========================

Some native Linux packages are required when installing the CLI with:

- Interactive install script
- `pip`

Current supported Python versions are Python 3.7 ~ 3.10.

The commands to run to install the dependencies for some common distributions are listed below.

### Ubuntu 18.04 LTS, Ubuntu 20.04 LTS, Ubuntu 22.04 LTS, Debian 9, Debian 10
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### RHEL 8, CentOS Stream 8
Install the latest Python 3.9 available in the software repo.
```
sudo dnf install -y gcc libffi-devel python39-devel openssl-devel
```

### SUSE OpenSUSE 13.2
Install Python 3.7+ if needed.
```
sudo zypper refresh && sudo zypper --non-interactive install gcc libffi-devel python-devel openssl-devel
```

### Flatcar

Python is installed in the Azure-specific distribution of Flatcar, but is installed into the non-standard location `/usr/share/oem/python/bin/python`.
