Linux Install Prerequisites
===========================

Some native Linux packages are required when installing the CLI with:

- Interactive installation script
- `pip`

Current supported Python versions are Python 3.10 ~ 3.13.

The commands to run to install the dependencies for some common distributions are listed below.

### Ubuntu 22.04 LTS, Ubuntu 24.04 LTS, Debian 11, Debian 12
```
sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev python-dev build-essential
```

### RHEL 8, CentOS Stream 8, RHEL 9, CentOS Stream 9
Install the latest Python 3.12 available in the software repo.
```
sudo dnf install -y gcc libffi-devel python312-devel openssl-devel
```
