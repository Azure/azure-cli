# RPM Packaging

## Building RPM packages

On a machine with Docker, execute the following command from the root directory of this repository:

_Enterprise Linux:_
```bash
docker build --target build-env -f ./scripts/release/rpm/centos7.dockerfile -t azure/azure-cli:centos7-builder .
```
_Fedora:_

```bash
docker build --target build-env -f ./scripts/release/rpm/fedora.dockerfile -t azure/azure-cli:fedora29-builder .
```

_Mariner:_

```bash
docker build --target build-env -f ./scripts/release/rpm/mariner.dockerfile -t azure/azure-cli:mariner-builder .
```

After several minutes, this will have created a Docker image named `azure/azure-cli:centos7-builder` containing an
unsigned `.rpm` built from the current contents of your azure-cli directory. To extract the build product from the image
you can run the following command:

_Enterprise Linux:_
```bash
docker run azure/azure-cli:centos7-builder cat /root/rpmbuild/RPMS/x86_64/azure-cli-dev-1.el7.x86_64.rpm > ./bin/azure-cli-dev-1.el7.x86_64.rpm
```

_Fedora:_
```bash
docker run azure/azure-cli:fedora29-builder cat /root/rpmbuild/RPMS/x86_64/azure-cli-dev-1.fc29.x86_64.rpm > ./bin/azure-cli-dev-1.fc29.x86_64.rpm
```

_Mariner:_
```bash
docker run azure/azure-cli:mariner-builder cat /usr/src/mariner/RPMS/x86_64/azure-cli-dev-1.cm1.x86_64.rpm > ./bin/azure-cli-dev-1.cm1.x86_64.rpm
```

This launches a container running from the image built and tagged by the previous command, prints the contents of the
built package to standard out, and pipes it to a file on your host machine.

### Additional Build Flags

`--build-arg cli_version={your version string}`

This will allow you to name your build. If not specified, the value "dev" is assumed.

`--build-arg tag={centos/fedora version}`

RPMs must be built using a Red Hat distro or derivative. By default, this build uses CentOS7, but one could easily tweak
it to include slightly different packages for distribution.

### Verification

Run the RPM package
-------------------

On a machine with Docker, execute the following command from the root directory of this repository:

```bash
docker build -f ./scripts/release/rpm/centos7.dockerfile -t azure/azure-cli:centos7 .
``` 

If you had previously followed this instructions above for building an RPM package, this should finish very quickly.
Otherwise, it'll take a few minutes to create an image with a copy of the azure-cli installed.
> Note: The image that is created by this command does not contain the source code of the azure-cli.

Verification
------------

Install the RPM:
```bash
sudo rpm -i RPMS/*/azure-cli-2.0.16-1.noarch.rpm
az --version
```

Check the file permissions of the package:  
```bash
rpmlint RPMS/*/azure-cli-2.0.16-1.x86_64.rpm
```

Check the file permissions of the package:  
```bash
rpm -qlvp RPMS/*/azure-cli-2.0.16-1.x86_64.rpm
```

To remove:  
```bash
sudo rpm -e azure-cli
```

Links
-----

- [Fedora Project: How to Create an RPM Package](https://fedoraproject.org/wiki/How_to_create_an_RPM_package)
- [Fedora Project: Packaging RPM Macros](https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros)
