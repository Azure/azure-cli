RPM Packaging
================

Building the RPM package
------------------------

On a build machine (e.g. new CentOS 7 VM) run the following.

Install dependencies required to build:
Required for rpm build tools & required to build the CLI.
```
sudo yum install -y gcc git rpm-build rpm-devel rpmlint make bash coreutils diffutils patch rpmdevtools python libffi-devel python-devel openssl-devel
```

Build example:
Note: use the full path to the repo path, not a relative path.
```
git clone https://github.com/azure/azure-cli
cd azure-cli
export CLI_VERSION=2.0.16
export REPO_PATH=$(pwd)
rpmbuild -v -bb --clean build_scripts/rpm/azure-cli.spec
```

Verification
------------

```
sudo rpm -i RPMS/*/azure-cli-2.0.16-1.noarch.rpm
az --version
```

Check the file permissions of the package:  
```
rpmlint RPMS/*/azure-cli-2.0.16-1.x86_64.rpm
```

Check the file permissions of the package:  
```
rpm -qlvp RPMS/*/azure-cli-2.0.16-1.x86_64.rpm
```

To remove:  
```
sudo rpm -e azure-cli
```

Links
-----

https://fedoraproject.org/wiki/How_to_create_an_RPM_package

https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros
