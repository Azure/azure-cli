# RPM Packaging

## Building the RPM package

On a machine with Docker, execute the following command from the root directory of this repository:

``` bash
docker build --target build-env -f ./scripts/release/rpm/Dockerfile -t microsoft/azure-cli:centos7-builder .
```

After several minutes, this will have created a Docker image named `microsoft/azure-cli:centos7-builder` containing an
unsigned `.rpm` built from the current contents of your azure-cli directory. To extract the build product from the image
you can run the following command:

``` bash
docker run microsoft/azure-cli:centos7-builder cat /root/rpmbuild/RPMS/x86_64/azure-cli-dev-1.el7.x86_64.rpm > ./bin/azure-cli-dev-1.el7.x86_64.rpm
```

This launches a container running from the image built and tagged by the previous command, prints the contents of the
built package to standard out, and pipes it to a file on your host machine.

### Additional Build Flags

`--build-arg cli_version={your version string}`

This will allow you to name your build. If not specified, the value "dev" is assumed.

`--build-arg base_image={docker image name}`

RPMs must be built using a Red Hat distro or derivative. By default, this build uses CentOS7, but one could easily tweak
it to include slightly different packages for distribution.

### Verification

Run the RPM package
-------------------

On a machine with Docker, execute the following command from the root directory of this repository:

``` bash
docker build -f ./scripts/release/rpm/Dockerfile -t microsoft/azure-cli:centos7 .
``` 

If you had previously followed this instructions above for building an RPM package, this should finish very quickly.
Otherwise, it'll take a few minutes to create an image with a copy of the azure-cli installed.
> Note: The image that is created by this command does not contain the source code of the azure-cli.

Verification
------------

Install the RPM:
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

- [Fedora Project: How to Create an RPM Package](https://fedoraproject.org/wiki/How_to_create_an_RPM_package)
- [Fedora Project: Packaging RPM Macros](https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros)

