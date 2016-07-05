Smoke testing CLI Installation
==============================

# 1. Overview
The document outlines the steps to take when smoke testing the installation of the CLI. We focus on installation with cURL and pip (for Windows).
We test on multiple system configurations.  
For example:
- OS type
- OS version
- Python version
- Local/global install
- Clean install vs. back-to-back updates
- Tab Completion set up

## <a name="heading1_1"></a>1.1 Installing
Example of installing the CLI and pointing to a specific nightly build:
```
curl http://azure-cli-nightly.westus.cloudapp.azure.com/install-dev-latest | bash
```
`sudo` may be required.

## <a name="heading1_2"></a>1.2 Basic verification
Run `az` and you should see the CLI.  
Type `az <tab><tab>` and you should see tab completion working.  
`az --version` should show the expected versions.  
If you enabled tab completion, you should see a line added to your rc file.  

**Before each test, remove the previous install:**  
1. Delete the install directory (e.g. `sudo rm -rf /usr/local/az` or `rm -rf ~/az-cli`)  
2. Delete the az executable (e.g. `sudo rm -f /usr/local/bin/az` or `rm -f ~/az`)  
3. Remove the az completion line from your rc file (e.g. ~/.bash_profile)  

#2. OS X
Python 2.7 is installed by default on OS X.

## 2.1. clean, global
### Steps

Install the CLI. See [Installing](#heading1_1).  

Since we are doing a global install, when prompted, use the defaults.  
When prompted, choose to enable tab completion,

Run `exec -l $SHELL` to restart your shell to enable tab completion.

### Verification
See [Basic verification](#heading1_2).


## 2.2. upgrade, global
### Steps
Follow the steps from the previous test to install the CLI but instead install a previous version
by setting the `AZURE_CLI_PACKAGE_VERSION` environment variable before performing the install.  
e.g. `export AZURE_CLI_PACKAGE_VERSION=2016.05.30.nightly`.

Now, we can perform an upgrade.  
Set `AZURE_CLI_PACKAGE_VERSION` to the new version.  
e.g. `export AZURE_CLI_PACKAGE_VERSION=2016.05.31.nightly`.  

Install the CLI again.

Since we are doing a global install, when prompted, use the defaults.  
When prompted, choose to enable tab completion,

Run `exec -l $SHELL` to restart your shell to enable tab completion.

### Verification
See [Basic verification](#heading1_2).

Unset the environment variable so it doesn't affect other tests.  
```
unset AZURE_CLI_PACKAGE_VERSION
```

## 2.3. clean, global (no .bashrc or .bash_profile)
### Steps
Create a backup of your .bashrc and .bash_profile files and delete the original files.  
For example:
```
mv ~/.bashrc ~/bashrc.backup
mv ~/.bash_profile ~/bash_profile.backup
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).  
Even though you chose to enable tab completion, it will not be set up as you didn't have a
.bashrc or .bash_profile file.

Restore your backups.  
For example:
```
mv ~/bashrc.backup ~/.bashrc
mv ~/bash_profile.backup ~/.bash_profile
```

## 2.4. clean, local
### Steps
Install the CLI. See [Installing](#heading1_1).  
When prompted specify a local location for the install use `~/az-cli`.  
When prompted for a location for the executable, use '~'.  
When prompted, choose to enable tab completion.

Run `exec -l $SHELL` to restart your shell to enable tab completion.

### Verification
Instead of running `az`, `cd ~` and run `./az` and follow the steps in [Basic verification](#heading1_2).  

## 2.5. upgrade, local
### Steps
Follow the steps from the previous test to install the CLI but instead install a previous version
by setting the `AZURE_CLI_PACKAGE_VERSION` environment variable before performing the install.  
e.g. `export AZURE_CLI_PACKAGE_VERSION=2016.05.30.nightly`.

Now, we can perform an upgrade.  
Set `AZURE_CLI_PACKAGE_VERSION` to the new version.  
e.g. `export AZURE_CLI_PACKAGE_VERSION=2016.05.31.nightly`.  

Install the CLI locally again (use the same directories as before when prompted).


### Verification
Instead of running `az`, `cd ~` and run `./az` and follow the steps in [Basic verification](#heading1_2). 

Unset the environment variable so it doesn't affect other tests.  
```
unset AZURE_CLI_PACKAGE_VERSION
```

## 2.6 Other tests

### Install dir same as exec path
An error should occur if you try to specify an install directory and directory for the `az`
executable that clash.  

#### Steps

Install the CLI (see [installing](#heading1_1)) but when prompted for install directory, type `~/az`.  
When prompted for the directory to place the executable, type `~`.  

#### Verification
You should see an error message stating that you must 'Choose either a different install directory
or directory to place the executable.'


#3. Linux
We complete these tests by creating VMs on Azure.

```
export AZURE_CLI_SMOKE_TEST_RG=cli-smoke-test-$(date +%Y%m%d-%H%M%S)
az resource group create -n $AZURE_CLI_SMOKE_TEST_RG -l westus
```

At the end of the tests, delete the resource group.
```
az resource group delete -n $AZURE_CLI_SMOKE_TEST_RG
```

## 3.1. ubuntu 14.04 LTS
### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm1-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-username ubuntu
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh ubuntu@<ip_address>
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.2. ubuntu 12.04 LTS

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm2-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image Canonical:UbuntuServer:12.04.5-LTS:12.04.201605160 --admin-username ubuntu
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh ubuntu@<ip_address>
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.3. ubuntu 15.10

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm3-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image Canonical:UbuntuServer:15.10:15.10.201605160 --admin-username ubuntu
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh ubuntu@<ip_address>
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
sudo apt-get install -y build-essential
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.4. ubuntu 16.04 LTS

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm4-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image Canonical:UbuntuServer:16.04.0-LTS:16.04.201605161 --admin-username ubuntu
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh ubuntu@<ip_address>
sudo apt-get update
sudo apt-get install -y libssl-dev libffi-dev
sudo apt-get install -y python-dev
sudo apt-get install -y build-essential
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.5. centos 7.1

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm5-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image OpenLogic:CentOS:7.1:7.1.20160308 --admin-username centos
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh centos@<ip_address>
sudo yum check-update
sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.6. centos 7.2

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm6-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image OpenLogic:CentOS:7.2:7.2.20160308 --admin-username centos
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh centos@<ip_address>
sudo yum check-update
sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.7. debian 8

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm7-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image credativ:Debian:8:8.0.201604200 --admin-username debian
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh debian@<ip_address>
sudo apt-get update
sudo apt-get install -y curl
sudo apt-get install -y libssl-dev libffi-dev python-dev
sudo apt-get install -y build-essential
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.8. debian 7

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm8-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image credativ:Debian:7:7.0.201604200 --admin-username debian
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh debian@<ip_address>
sudo apt-get update
sudo apt-get install -y curl
sudo apt-get install -y libssl-dev libffi-dev python-dev
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.9. RedHat RHEL 7.2

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm9-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image RedHat:RHEL:7.2:7.2.20160302 --admin-username redhat
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh redhat@<ip_address>
sudo yum check-update
sudo yum install -y gcc libffi-devel python-devel openssl-devel
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

## 3.10. SUSE OpenSUSE 13.2

### Steps
```
export AZURE_CLI_SMOKE_TEST_VM=vm10-$AZURE_CLI_SMOKE_TEST_RG
az vm create -g $AZURE_CLI_SMOKE_TEST_RG -n $AZURE_CLI_SMOKE_TEST_VM --authentication-type ssh --image SUSE:openSUSE:13.2:2016.03.02 --admin-username suse
az vm list-ip-addresses -g $AZURE_CLI_SMOKE_TEST_RG --vm-name $AZURE_CLI_SMOKE_TEST_VM
ssh suse@<ip_address>
sudo zypper refresh
sudo zypper --non-interactive install gcc libffi-devel python-devel openssl-devel
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).


## 3.11. Other tests
### Python 3 (with Docker container)
```
sudo docker run -it python:3.5 bash
```

Install the CLI. See [Installing](#heading1_1).

### Verification
See [Basic verification](#heading1_2).

#4. Windows
## 4.1 Manual pip install
### Steps
Set the environment variable to point to the version you wish to install.

e.g. `set AZURE_CLI_NIGHTLY_VERSION=2016.06.21.nightly`.

```
set AZURE_CLI_DISABLE_POST_INSTALL=1
set AZURE_CLI_PRIVATE_PYPI_URL=http://40.112.211.51:8080
set AZURE_CLI_PRIVATE_PYPI_HOST=40.112.211.51
```

Install the CLI.
```
pip install azure-cli==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
```

Install all the components.  
At the time of writing, here are the available ones.
```
pip install azure-cli-component==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-profile==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-storage==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-vm==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-network==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-resource==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-role==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
pip install azure-cli-feedback==%AZURE_CLI_NIGHTLY_VERSION% --extra-index-url %AZURE_CLI_PRIVATE_PYPI_URL% --trusted-host %AZURE_CLI_PRIVATE_PYPI_HOST%
```

### Verification
See [Basic verification](#heading1_2).  
Note: Tab completion is not supported on Windows.

You can now uninstall the packages you installed.
```
pip uninstall azure-cli azure-cli-component azure-cli-network azure-cli-profile azure-cli-resource azure-cli-storage azure-cli-vm
```
