RPM Packaging
================

Building the RPM package
------------------------

On a build machine (e.g. new CentOS 7 VM) run the following.

Install dependencies required to build:
```
# Required for rpm build tools.
sudo yum install -y gcc rpm-build rpm-devel rpmlint make python bash coreutils diffutils patch rpmdevtools

# Required to build the CLI.
sudo yum install -y gcc python libffi-devel python-devel openssl-devel
```

Set up directory structure for build:
```
mkdir -p ~/rpmbuild/
cd ~/rpmbuild/
mkdir -p BUILD RPMS SOURCES SPECS SRPMS
> SPECS/azure-cli.spec; vi SPECS/azure-cli.spec
```

Set the CLI version and SHA256 for the archive:
```
export CLI_VERSION=2.0.16
export CLI_DOWNLOAD_SHA256=22c048d2911c13738c6b901a741ea655f277e0d9eb756c4fb9aee6bb6c2b0109
```

RPM Build:
```
rpmbuild -v -bb --clean SPECS/azure-cli.spec
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
