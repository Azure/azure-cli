Docker Packaging
================

The Docker image is available at https://hub.docker.com/r/microsoft/azure-cli/tags/.

Updating the Docker image
-------------------------
1. Run `docker build` with the Dockerfile.
    When tagging this Docker image, choose an appropriate version number.
      e.g.: ``sudo docker build --no-cache --build-arg BUILD_DATE="`date -u +"%Y-%m-%dT%H:%M:%SZ"`" --build-arg CLI_VERSION=${CLI_VERSION} -f Dockerfile -t microsoft/azure-cli:${CLI_VERSION} .``
2. Push the image to the registry,
      e.g.: `sudo docker push microsoft/azure-cli:${CLI_VERSION}`
3. Create a PR to commit the Dockerfile changes back to the repository.


Verification
------------

Run the image.

```
$ docker run -it microsoft/azure-cli:${CLI_VERSION}
$ az
$ az --version
```

Save the image
```
docker save -o docker-microsoft-azure-cli-VERSION.tar microsoft/azure-cli:${CLI_VERSION}
```

Load the saved image
```
docker load -i docker-microsoft-azure-cli-VERSION.tar
```
