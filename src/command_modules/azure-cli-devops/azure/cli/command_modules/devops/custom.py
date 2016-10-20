#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import json
import os
import re
import subprocess
import time
from subprocess import check_output

import requests
import yaml

import azure.cli.core._logging as _logging
from azure.cli.command_modules.devops import git_repo_parser
from azure.cli.core._profile import Profile
# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use
from azure.cli.core._util import CLIError

logger = _logging.get_az_logger(__name__)
# LOCALRUN change this to "http://localhost:44454"
BASE_URL = "https://management.azure.com"
RESOURCE_BASE_URL = "/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
CONTAINER_SERVICE_BASE_URL = RESOURCE_BASE_URL + "/providers/Microsoft.ContainerService"
CONTAINER_SERVICE_RESOURCE_URL = CONTAINER_SERVICE_BASE_URL + "/containerServices/{container_service_name}"
VISUAL_STUDIO_BASE_URL = RESOURCE_BASE_URL + "/providers/microsoft.visualstudio"
VISUAL_STUDIO_ACCOUNT_URL = VISUAL_STUDIO_BASE_URL + "/account/{vsts_account_name}"
VISUAL_STUDIO_PROJECT_URL = VISUAL_STUDIO_ACCOUNT_URL + "/project/{vsts_project_name}"
RP_URL = BASE_URL + CONTAINER_SERVICE_RESOURCE_URL + "/providers/Microsoft.Mindaro"
API_VERSION = "2016-11-01-preview"

def add_release(name, resource_group_name, remote_url, remote_access_token, vsts_account_name, vsts_project_name, registry_resource_group, registry_name):
    """
    Adds a deployment to an existing ACS cluster

    :param name: repo name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    :param remote_url: Repository url
    :type remote_url: String
    :param remote_access_token: Access token
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name
    :type vsts_project_name: String
    :param registry_resource_group: Registry esource group name
    :type registry_resource_group: String
    :param registry_name: Registry name
    :type registry_name: String
    """
    # Ensure docker-compose file is correct.
    ensure_docker_compose()

    #Call the RP
    call_rp_configure_cicd(name, resource_group_name, vsts_account_name, vsts_project_name, registry_name, registry_resource_group, get_valid_remote_url(remote_url, remote_access_token), remote_access_token)
    return

def get_valid_remote_url(remote_url = None, remote_access_token = None):
    """
    Calls the git repo parser to check for non VSTS repository and returns remote url for repository.
    """
    remote_url = remote_url or get_remote_url()
    repo_info = git_repo_parser.get_repo_info(remote_url)

    if repo_info['repo_type'] != 'vsts' and not remote_access_token:
        raise CLIError("--remote-access-token is required for non VSTS repositories")

    return remote_url

def call_rp_configure_cicd(name, resource_group_name, vsts_account_name, vsts_project_name, registry_name, registry_resource_group, remote_url, remote_access_token, create_release = True):
    """
    Calls the RP to build and deploy the service(s) in the cluster.

    :param name: ACS resource name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    :param vsts_account_name: VSTS account name to use/create
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create
    :type vsts_project_name: String
    """
    profile = Profile()
    cred, subscription_id, _ = profile.get_login_credentials()
    
    o_auth_token = cred.signed_session().headers['Authorization']
       
    data = {
        'vstsAccountName': vsts_account_name,
        'vstsProjectName': vsts_project_name,
        'token': o_auth_token,
        'registryName': registry_name,
        'registryResourceGroup': registry_resource_group,
        'remoteToken': remote_access_token,
        'remoteUrl': remote_url,
        'createRelease' : create_release
    }

    configure_ci_cd_url = RP_URL.format(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        container_service_name=name) + '/configureCI?api-version=' + API_VERSION

    headers = {'Content-type': 'application/json', 'Authorization': o_auth_token}
    req = requests.post(configure_ci_cd_url, data=json.dumps(data), headers=headers, timeout=600)
    while req.status_code == 202:  # Long-running operation
        time.sleep(10)
        req = requests.get(BASE_URL + req.headers['Location'], headers=headers, timeout=600)
    json_request = req.json()
    if req.status_code != 200:
        raise CLIError('Error: ' + str(req.status_code) + '. Could not configure CI/CD: ' + req.text)
    print (json.dumps(json_request, indent=4, sort_keys=True))
    return json_request

def list_releases(name, resource_group_name):
    """
    Calls the RP to list all the releases present for the cluster.

    :param name: ACS resource name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    """
    profile = Profile()
    cred, subscription_id, _ = profile.get_login_credentials()
    o_auth_token = cred.signed_session().headers['Authorization']
    o_auth_token.replace(" ", "%20")
    get_releases_action = '/configureCI/1/releases?api-version={version}&token={o_auth_token}'
    get_releases_url = RP_URL.format(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        container_service_name=name) + get_releases_action.format(
            version=API_VERSION,            
            o_auth_token=o_auth_token)
    
    headers = {'Content-type': 'application/json', 'Authorization': o_auth_token}
    req = requests.get(get_releases_url, headers=headers, timeout=600)
    json_request = req.json()
    if req.status_code != 200:
        print ('Error: ' + str(req.status_code) + '. Could not list releases: ' + json_request["error"]["code"])
        raise CLIError(req.text)
    print (json.dumps(req.json(), indent=4, sort_keys=True))
    return json_request

def ensure_docker_compose():
    """
    1. Raises an error if there is no docker_compose_file present.
    2. Raises an error if the version specified in the docker_compose_file is not docker_compose_version.
    3. Raises an error if docker_compose_test_file has a version other than docker_compose_version.
    """
    docker_compose_file = 'docker-compose.yml'
    docker_compose_test_file = 'docker-compose.test.yml'
    docker_compose_expected_version = '2'
    if (not os.path.isfile(docker_compose_file)):
        raise CLIError('Docker compose file "{}" was not found.'.format(docker_compose_file))
    with open(docker_compose_file, 'r') as f:
        compose_data = yaml.load(f)
        if 'version' not in compose_data.keys():
            raise CLIError('Docker compose file "{}" is missing version information.'.format(docker_compose_file))
        if not docker_compose_expected_version in compose_data['version']:
            raise CLIError('Docker compose file "{}" has incorrect version. Only version "{}" is supported.'.format(docker_compose_file, docker_compose_expected_version))
    if (os.path.isfile(docker_compose_test_file)):
        with open(docker_compose_test_file, 'r') as f:
            compose_data = yaml.load(f)
            if 'version' not in compose_data.keys():
                raise CLIError('Docker compose file "{}" is missing version information.'.format(docker_compose_test_file))
            if not docker_compose_expected_version in compose_data['version']:
                raise CLIError('Docker compose file "{}" has incorrect version. Only version "{}" is supported.'.format(docker_compose_test_file, docker_compose_expected_version))


def get_remote_url():
    """
    Tries to find a remote for the repo in the current folder. If only one remote is present return that remote, 
    if more than one remote is present looks for origin.
    """
    try:
        remotes = check_output(['git','remote']).strip().splitlines()
        remote_url = ""
        if len(remotes) == 1:
            remote_url = check_output(['git', 'remote', 'get-url', remotes[0].decode()]).strip()
        else:
            remote_url = check_output(['git', 'remote', 'get-url', 'origin']).strip()
    except ValueError as e:
        logger.debug(e);
        raise CLIError("A default remote was not found for the current folder. Please run this command in a git repository folder with an 'origin' remote or specify a remote using '--remote-url'")
    return remote_url.decode()

def add_ci(name, resource_group_name, remote_url, remote_access_token, vsts_account_name, vsts_project_name, registry_resource_group, registry_name):
    """
    Creates a build definition for a DockerFile-based repository
    
    :param name: repo name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    :param remote_url: Repository url
    :type remote_url: String
    :param remote_access_token: Access token
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name
    :type vsts_project_name: String
    :param registry_resource_group: Registry esource group name
    :type registry_resource_group: String
    :param registry_name: Registry name
    :type registry_name: String
    """
    
    #Call the RP
    call_rp_configure_cicd(name, resource_group_name, vsts_account_name, vsts_project_name, registry_name, registry_resource_group, get_valid_remote_url(remote_url, remote_access_token), remote_access_token, False)