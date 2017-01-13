GitHub bot for Azure CLI
========================

Description
-----------
This is a GitHub bot/webhook for automated component/package releases.

The server can be extended to handle more GitHub webhook events in the future as needed.


Run locally with `export FLASK_APP=app.py; flask run -h '0.0.0.0'`

How to Build
------------
```
$ sudo docker build --no-cache -t azuresdk/azure-cli-bot:0.1.0 .
```

How to Run with Docker
----------------------
The following environment variables are required for the server to run:

`REPO_NAME` - The name of the GitHub repo (e.g. azure/azure-cli)
`GITHUB_SECRET_TOKEN` - The Secret that is configured in GitHub Webhook settings.  
`GITHUB_USER` - User id of the bot that will post comments and create releases.  
`GITHUB_USER_TOKEN` - Access token for this user.  
`ALLOWED_USERS` - Space separated list of GitHub usernames that can create releases.  
`PYPI_REPO` - URL to PyPI (e.g. https://testpypi.python.org/pypi or https://pypi.python.org/pypi).  
`TWINE_USERNAME` - Username to authenticate with PyPI.  
`TWINE_PASSWORD` - Password to authenticate with PyPI.

The `GITHUB_USER` should have the following GitHub OAuth scopes:  
- repo_deployment (to create GitHub releases)
- public_repo (to post comments on the repo)

For example:

```
$ sudo docker run -d -e "REPO_NAME=azure/azure-cli" -e "GITHUB_SECRET_TOKEN=<secret>" -e "GITHUB_USER=user1" \
-e "GITHUB_USER_TOKEN=<guid>" -e "ALLOWED_USERS=user1 user2 user3" \
-e "PYPI_REPO=https://testpypi.python.org/pypi" -e "TWINE_USERNAME=<user>" -e "TWINE_PASSWORD=<pass>" \
-p 80:80 azuresdk/azure-cli-bot:0.1.0
```


Verify server running
---------------------
```
$ curl -X GET -i 'http://<HOSTNAME>:<PORT>/'
HTTP/1.1 200 OK
Server: gunicorn/19.6.0
Connection: close
Content-Type: application/json
Content-Length: 58

{
  "message": "API is running!", 
  "version": "0.1.0"
}
```


Deploy on Azure Linux Web App (with Docker container)
-----------------------------------------------------
The docker image should be available on a Docker registry.

```
$ sudo docker push azuresdk/azure-cli-bot:0.1.0
```


For example:

```
$ az appservice plan create -g <RG> -n <PLAN-NAME> --sku s1 --is-linux
$ az appservice web create -g <RG> --plan <PLAN-NAME> -n <WEBAPP-NAME>
$ az appservice web config container update -g <RG> -n <WEBAPP-NAME> \
--docker-custom-image-name <DOCKER-IMAGE-NAME>
$ az appservice web config appsettings update -g <RG> -n <WEBAPP-NAME> \
--settings 'REPO_NAME=azure/azure-cli' 'GITHUB_SECRET_TOKEN=<secret>' 'GITHUB_USER=user1' 'GITHUB_USER_TOKEN=<guid>' \
'ALLOWED_USERS=user1 user2 user3' 'PYPI_REPO=https://testpypi.python.org/pypi' \
'TWINE_USERNAME=<user>' 'TWINE_PASSWORD=<pass>'
$ az appservice web browse -g <RG> -n <WEBAPP-NAME>
```


Registering the Webhook in GitHub
---------------------------------

- Enter the appropriate payload URL (i.e. https://<HOSTNAME>:<PORT>/github-webhook).
- The payload URL *should* be over SSL (i.e. https://).
- Set the Secret to be a value defined in the running service.
- Set the webhook to trigger for 'Pull request' events.
