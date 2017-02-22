Docker Packaging
================

The Docker image is available at https://hub.docker.com/r/azuresdk/azure-cli-python/tags/.

Updating the Docker image
-------------------------
1. Create a temp directory that only contains the Dockerfile.
2. In the Dockerfile, modify `CLI_VERSION` and the `CLI_DOWNLOAD_SHA256` hash as appropriate.
3. Run `docker build` with this Dockerfile.
    When tagging this Docker image, choose an appropriate version number.
      e.g.: ``sudo docker build --no-cache --build-arg BUILD_DATE="`date -u +"%Y-%m-%dT%H:%M:%SZ"`" -f Dockerfile -t azuresdk/azure-cli-python:${CLI_VERSION} .``
4. Push the image to the registry,
      e.g.: `sudo docker push azuresdk/azure-cli-python:${CLI_VERSION}`
5. Create a PR to commit the Dockerfile changes back to the repository.


Verification
------------

Run the image.

```
$ sudo docker run -it azuresdk/azure-cli-python:${CLI_VERSION}
$ az
$ az --version
```