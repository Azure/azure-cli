# Debian Packaging
================

Building the Debian package
---------------------------

On a machine with Docker, execute the following command from the root directory of this repository:

``` bash
docker build --target build-env -f ./scripts/release/debian/Dockerfile -t azure/azure-cli:ubuntu-builder .
```

After several minutes, this will have created a Docker image named `azure/azure-cli:ubuntu-builder` containing an
unsigned `.deb` built from the current contents of your azure-cli directory. To extract the build product from the image
you can run the following command:

``` bash
docker run azure/azure-cli:ubuntu-builder cat /azure-cli/debian/
```

The script only runs in container environment.

Verification
------------

``` bash
sudo dpkg -i azure-cli_${CLI_VERSION}-1_$(dpkg --print-architecture).deb
az
az --version
```
