Automated PyPI and GitHub releases of all CLI modules
=====================================================

Description
-----------
This is a Docker image that automates releases of all CLI modules to PyPI and then creates GitHub releases for each.
The scripts have been tested on Python 3 so it's recommended to run the Docker image.

How to Build
------------
```
sudo docker build --no-cache -t azuresdk/azure-cli-release-automation:<VERSION> .
```

How to Run
----------
```
sudo docker run -it -e "REPO_NAME=azure/azure-cli" -e "GITHUB_USER=user1" -e "GITHUB_USER_TOKEN=<guid>" \
-e "PYPI_REPO=https://test.pypi.org/legacy/" -e "TWINE_USERNAME=<user>" -e "TWINE_PASSWORD=<pass>" \
-e "CLI_VERSION=0.0.0a1" -e "AZURE_STORAGE_CONNECTION_STRING=<connectionstring>" \
 azuresdk/azure-cli-release-automation:<VERSION>
```

Once the container has started, there are several scripts available.  
They each require they're own set of environment variables.  
These can be set in the initial `docker run` command above or by using `export ENV=VALUE` directly in the running container.  

```
python release.py
python release-docker.py
python release-debian.py
```

Environment Variables
---------------------
`REPO_NAME` - The name of the GitHub repo (e.g. azure/azure-cli)
`GITHUB_USER` - User id of the bot that will post comments and create releases.  
`GITHUB_USER_TOKEN` - Access token for this user.  
`PYPI_REPO` - URL to PyPI (e.g. https://test.pypi.org/legacy/ or https://upload.pypi.org/legacy/).  
`TWINE_USERNAME` - Username to authenticate with PyPI.  
`TWINE_PASSWORD` - Password to authenticate with PyPI.
`CLI_VERSION` - The new version of the CLI (used for packaged releases)
`AZURE_STORAGE_CONNECTION_STRING` - The Azure storage connection string to upload release assets

The `GITHUB_USER` should have the following GitHub OAuth scopes:  
- repo_deployment (to create GitHub releases and commit to master)

`CLI_DOWNLOAD_SHA256` - The SHA256 sum of the packaged release (produced by `release.py`).

`DOCKER_REPO` - The Docker repo to push the image to (e.g. azuresdk/azure-cli-python).
`DOCKER_USERNAME` - The Docker username that has push permissions to the above Docker repo.
`DOCKER_PASSWORD` - The Docker password for the user.

`DEBIAN_REPO_ID` - The repository ID to publish the .deb package.
`DEBIAN_REPO_URL` - The repository URL to publish the .deb package.
`DEBIAN_REPO_USERNAME` - The repository username to publish the .deb package.
`DEBIAN_REPO_PASSWORD` - The user password to publish the .deb package.
