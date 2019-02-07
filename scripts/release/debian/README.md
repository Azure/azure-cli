# Debian Packaging
================

Building the Debian package
---------------------------

On a machine with Docker, execute the following command from the root directory of this repository:

``` bash
docker build --target build-env -f ./scripts/release/debian/Dockerfile -t microsoft/azure-cli:ubuntu-builder .
```

After several minutes, this will have created a Docker image named `microsoft/azure-cli:ubuntu-builder` containing an
unsigned `.deb` built from the current contents of your azure-cli directory. To extract the build product from the image
you can run the following command:

``` bash
docker run microsoft/azure-cli:ubuntu-builder cat /azure-cli/debian/
```

The script only runs in container environment.

Verification
------------

``` bash
sudo dpkg -i azure-cli_${CLI_VERSION}-1_all.deb
az
az --version
```
