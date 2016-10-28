#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import json
import os
import time
from subprocess import check_output, CalledProcessError

import requests
import yaml

import azure.cli.core._logging as _logging
from azure.cli.core._profile import Profile
# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,too-many-locals,line-too-long
from azure.cli.core._util import CLIError

logger = _logging.get_az_logger(__name__)
BASE_URL = "https://management.azure.com"
RESOURCE_BASE_URL = "/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
CONTAINER_SERVICE_BASE_URL = RESOURCE_BASE_URL + "/providers/Microsoft.ContainerService"
CONTAINER_SERVICE_RESOURCE_URL = (CONTAINER_SERVICE_BASE_URL +
                                  "/containerServices/{container_service_name}")
VISUAL_STUDIO_BASE_URL = RESOURCE_BASE_URL + "/providers/microsoft.visualstudio"
VISUAL_STUDIO_ACCOUNT_URL = VISUAL_STUDIO_BASE_URL + "/account/{vsts_account_name}"
VISUAL_STUDIO_PROJECT_URL = VISUAL_STUDIO_ACCOUNT_URL + "/project/{vsts_project_name}"
RP_URL = BASE_URL + CONTAINER_SERVICE_RESOURCE_URL + "/providers/Microsoft.Mindaro"
API_VERSION = "2016-11-01-preview"

DOCKERFILE_FILE = 'Dockerfile'
DOCKER_COMPOSE_FILE = 'docker-compose.yml'
DOCKER_COMPOSE_TEST_FILE = 'docker-compose.test.yml'
DOCKER_COMPOSE_EXPECTED_VERSION = '2'

def add_release(
        name,
        resource_group_name,
        remote_url=None,
        remote_access_token=None,
        vsts_account_name=None,
        vsts_project_name=None,
        registry_resource_group=None,
        registry_name=None):
    """
    Creates a build definition that automates building and pushing Docker images to an Azure container registry, and creates a release definition that automates deploying container images from a container registry to an Azure container service. Source repository must define a docker-compose.yml file.

    :param name: Name of the target Azure container service instance to deploy containers to.
    :type name: String
    :param resource_group_name: Name of Azure container service's resource group.
    :type resource_group_name: String
    :param remote_url: Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.
    :type remote_url: String
    :param remote_access_token: GitHub personal access token (minimum permission is 'repo'). Required if the source repository is in GitHub.
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.
    :type vsts_project_name: String
    :param registry_resource_group: Azure container registry resource group name.
    :type registry_resource_group: String
    :param registry_name: Azure container registry name. A new Azure container registry is created if omitted or does not exist.
    :type registry_name: String
    """
    # Ensure docker-compose file is correct.
    _ensure_docker_compose()

    # Call the RP
    return _call_rp_configure_cicd(
        name,
        resource_group_name,
        vsts_account_name,
        vsts_project_name,
        registry_name,
        registry_resource_group,
        _get_valid_remote_url(remote_url, remote_access_token),
        remote_access_token)

def _get_valid_remote_url(remote_url=None, remote_access_token=None):
    """
    Calls the git repo parser to check for non VSTS repository and
    returns remote url for repository.
    """
    remote_url = remote_url or _get_remote_url()
    repo_type = _get_repo_type(remote_url)

    if not repo_type:
        raise CLIError("Invalid repository. Only Github and VSTS repositories supported.")

    if repo_type != 'vsts' and not remote_access_token:
        raise CLIError("--remote-access-token is required for non VSTS repositories")

    return remote_url

def _get_repo_type(remote_url):
    """
    Returns repo type by parsing the remote_url for github.com and visualstudio.com
    """
    lower_case_url = remote_url.lower()
    if 'github.com' in lower_case_url:
        return 'github'
    elif 'visualstudio.com' in lower_case_url:
        return 'vsts'

    return None

def _call_rp_configure_cicd(
        name,
        resource_group_name,
        vsts_account_name,
        vsts_project_name,
        registry_name,
        registry_resource_group,
        remote_url,
        remote_access_token,
        create_release=True):
    """
    Calls the RP to build and deploy the service(s) in the cluster.

    :param name: Name of the target Azure container service instance to deploy containers to.
    :type name: String
    :param resource_group_name: Name of Azure container service's resource group.
    :type resource_group_name: String
    :param remote_url: Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.
    :type remote_url: String
    :param remote_access_token: GitHub personal access token (minimum permission is 'repo'). Required if the source repository is in GitHub.
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.
    :type vsts_project_name: String
    :param registry_resource_group: Azure container registry resource group name.
    :type registry_resource_group: String
    :param registry_name: Azure container registry name. A new Azure container registry is created if omitted or does not exist.
    :type registry_name: String
    :param create_release: Whether to create a release definition and deploy the application.
    :type create_release: bool
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
    if req.status_code != 200:
        raise CLIError(
            'Server returned status code: ' + str(req.status_code) + '. Could not configure CI/CD: ' + req.text)
    json_request = req.json()
    return json_request

def list_releases(name, resource_group_name):
    """
    Lists all the release definitions that are deployed to a given Azure container service.

    :param name: Name of the target Azure container service instance.
    :type name: String
    :param resource_group_name: Name of Azure container service's resource group.
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
    if req.status_code != 200:
        raise CLIError(
            'Server returned status code: ' + str(req.status_code) + '. Could not list releases: ' + req.text)
    json_request = req.json()
    return json_request

def _gitroot():
    """
    Gets the absolute path of the repository root
    """
    try:
        base = check_output(['git', 'rev-parse', '--show-toplevel'])
    except OSError:
        raise CLIError('Git is not currently installed.')
    except CalledProcessError:
        raise CLIError('Current working directory is not a git repository')
    return base.decode('utf-8').strip()

def _get_filepath_in_current_git_repo(file_to_search):
    """
    retrieves the full path of the first file in the git repo that matches filename
    """
    for dirpath, _, filenames in os.walk(_gitroot()):
        for file_name in filenames:
            if file_name.lower() == file_to_search.lower():
                return os.path.join(dirpath, file_name)
    return None

def _ensure_docker_compose():
    """
    1. Raises an error if there is no docker_compose_file present.
    2. Raises an error if the version specified in the docker_compose_file is not
    docker_compose_version.
    3. Raises an error if docker_compose_test_file has a version other than docker_compose_version.
    """
    docker_compose_file = _get_filepath_in_current_git_repo(DOCKER_COMPOSE_FILE)
    docker_compose_test_file = _get_filepath_in_current_git_repo(DOCKER_COMPOSE_TEST_FILE)

    if not docker_compose_file:
        raise CLIError('Docker compose file "{}" was not found.'.format(DOCKER_COMPOSE_FILE))
    _ensure_version(docker_compose_file, DOCKER_COMPOSE_EXPECTED_VERSION)

    if docker_compose_test_file:
        _ensure_version(docker_compose_test_file, DOCKER_COMPOSE_EXPECTED_VERSION)

def _ensure_version(filepath, expected_version):
    with open(filepath, 'r') as f:
        compose_data = yaml.load(f)
        if 'version' not in compose_data.keys():
            raise CLIError('File : "{}"\nis missing version information.'.format(
                filepath))
        if not expected_version in compose_data['version']:
            raise CLIError(
                'File : "{}"\nhas incorrect version. \
                \n Only version "{}" is supported.'.format(
                    filepath,
                    expected_version))


def _ensure_dockerfile():
    """
    1. Raises an error if there is no dockerfile present.
    """
    dockerfile_file = _get_filepath_in_current_git_repo(DOCKERFILE_FILE)

    if not dockerfile_file:
        raise CLIError('Docker file "{}" was not found.'.format(dockerfile_file))

def _get_remote_url():
    """
    Tries to find a remote for the repo in the current folder.
    If only one remote is present return that remote,
    if more than one remote is present it looks for origin.
    """
    try:
        remotes = check_output(['git', 'remote']).strip().splitlines()
        remote_url = ''
        if len(remotes) == 1:
            remote_url = check_output(['git', 'remote', 'get-url', remotes[0].decode()]).strip()
        else:
            remote_url = check_output(['git', 'remote', 'get-url', 'origin']).strip()
    except ValueError as e:
        logger.debug(e)
        raise CLIError(
            "A default remote was not found for the current folder. \
            Please run this command in a git repository folder with \
            an 'origin' remote or specify a remote using '--remote-url'")
    return remote_url.decode()

def add_ci(
        name,
        resource_group_name,
        remote_url=None,
        remote_access_token=None,
        vsts_account_name=None,
        vsts_project_name=None,
        registry_resource_group=None,
        registry_name=None):
    """
    Creates a build definition that automates building and pushing Docker images to an Azure container registry. Source repository must define a Dockerfile.

    :param name: Name of the target Azure container service instance to deploy containers to.
    :type name: String
    :param resource_group_name: Name of Azure container service's resource group.
    :type resource_group_name: String
    :param remote_url: Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.
    :type remote_url: String
    :param remote_access_token: GitHub personal access token (minimum permission is 'repo'). Required if the source repository is in GitHub.
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.
    :type vsts_project_name: String
    :param registry_resource_group: Azure container registry resource group name.
    :type registry_resource_group: String
    :param registry_name: Azure container registry name. A new Azure container registry is created if omitted or does not exist.
    :type registry_name: String
    """
    _ensure_dockerfile()
    # Call the RP
    return _call_rp_configure_cicd(
        name,
        resource_group_name,
        vsts_account_name,
        vsts_project_name,
        registry_name,
        registry_resource_group,
        _get_valid_remote_url(remote_url, remote_access_token),
        remote_access_token,
        False)
