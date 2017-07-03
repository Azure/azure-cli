Docker Packaging
================

The Docker image is available at https://hub.docker.com/r/azuresdk/azure-cli-python/tags/.

Updating the Docker image
-------------------------
1. Run `docker build` with this Dockerfile.
    When tagging this Docker image, choose an appropriate version number.
      e.g.: ``sudo docker build --no-cache --build-arg BUILD_DATE="`date -u +"%Y-%m-%dT%H:%M:%SZ"`" --build-arg CLI_VERSION=${CLI_VERSION} --build-arg CLI_DOWNLOAD_SHA256=${CLI_DOWNLOAD_SHA256} -f Dockerfile -t azuresdk/azure-cli-python:${CLI_VERSION} .``
2. Push the image to the registry,
      e.g.: `sudo docker push azuresdk/azure-cli-python:${CLI_VERSION}`
3. Create a PR to commit the Dockerfile changes back to the repository.


Verification
------------

Run the image.

```
$ sudo docker run -it azuresdk/azure-cli-python:${CLI_VERSION}
$ az
$ az --version
```
