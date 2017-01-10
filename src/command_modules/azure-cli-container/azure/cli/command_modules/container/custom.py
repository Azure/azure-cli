# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
import uuid
from subprocess import CalledProcessError, check_output

import requests
import yaml

import azure.cli.core._logging as _logging
from azure.cli.core._config import az_config
from azure.cli.core._profile import Profile, CredsCache, _SERVICE_PRINCIPAL
# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,too-many-locals,line-too-long
from azure.cli.core._util import CLIError

logger = _logging.get_az_logger(__name__)

BASE_URL = az_config.get('container', 'service_url', fallback='https://westus.mindaro.microsoft.io')
SUBSCRIPTION_URL = "/subscriptions/{subscription_id}"
RESOURCE_BASE_URL = SUBSCRIPTION_URL + "/resourceGroups/{resource_group_name}"
CONTAINER_SERVICE_PROVIDER = "/providers/Microsoft.ContainerService"
CONTAINER_SERVICE_RESOURCE_URL = (RESOURCE_BASE_URL + CONTAINER_SERVICE_PROVIDER + "/containerServices/{container_service_name}")

SERVICE_URL = BASE_URL + SUBSCRIPTION_URL
API_VERSION = "2016-11-01-preview"
SERVICE_RESOURCE_ID = "https://mindaro.microsoft.io/"

DOCKERFILE_FILE = 'Dockerfile'
DOCKER_COMPOSE_FILE = 'docker-compose.yml'
DOCKER_COMPOSE_EXPECTED_VERSION = '2'

def add_release(
        target_name,
        target_resource_group,
        remote_url=None,
        remote_branch=None,
        remote_access_token=None,
        vsts_account_name=None,
        vsts_project_name=None,
        registry_resource_id=None,
        registry_name=None):
    """
    Creates a build definition that automates building and pushing Docker images to an Azure container registry, and creates a release definition that automates deploying container images from a container registry to an Azure container service. Source repository must define a docker-compose.yml file.

    :param target_name: Name of the target Azure container service instance to deploy containers to.
    :type target_name: String
    :param target_resource_group: Name of Azure container service's resource group.
    :type target_resource_group: String
    :param remote_url: Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.
    :type remote_url: String
    :param remote_branch: Remote branch of the GitHub or VSTS source repository that will be built and deployed. If omitted refs/heads/master will be selected.
    :type remote_branch: String
    :param remote_access_token: GitHub personal access token (minimum permission is 'repo'). Required if the source repository is in GitHub.
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.
    :type vsts_project_name: String
    :param registry_resource_id: Azure container registry resource id.
    :type registry_resource_id: String
    :param registry_name: Azure container registry name. A new Azure container registry is created if omitted or does not exist.
    :type registry_name: String
    """
    # Ensure docker-compose file is correct if no remote url provided.
    if not remote_url:
        _ensure_docker_compose()

    _check_registry_information(registry_name, registry_resource_id)

    # Call the RP
    return _call_rp_configure_cicd(
        target_name,
        target_resource_group,
        vsts_account_name,
        vsts_project_name,
        registry_name,
        registry_resource_id,
        _get_valid_remote_url(remote_url, remote_access_token),
        remote_branch,
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
        target_name,
        target_resource_group,
        vsts_account_name,
        vsts_project_name,
        registry_name,
        registry_resource_id,
        remote_url,
        remote_branch,
        remote_access_token,
        create_release=True):
    """
    Calls the RP to build and deploy the service(s) in the cluster.

    :param target_name: Name of the target Azure container service instance to deploy containers to.
    :type target_name: String
    :param target_resource_group: Name of Azure container service's resource group.
    :type target_resource_group: String
    :param remote_url: Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.
    :type remote_url: String
    :param remote_branch: Remote branch of the GitHub or VSTS source repository that will be built and deployed. If omitted refs/heads/master will be selected.
    :type remote_branch: String
    :param remote_access_token: GitHub personal access token (minimum permission is 'repo'). Required if the source repository is in GitHub.
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.
    :type vsts_project_name: String
    :param registry_resource_id: Azure container registry resource id.
    :type registry_resource_id: String
    :param registry_name: Azure container registry name. A new Azure container registry is created if omitted or does not exist.
    :type registry_name: String
    :param create_release: Whether to create a release definition and deploy the application.
    :type create_release: bool
    """
    profile = Profile()
    _, subscription_id, _ = profile.get_login_credentials()

    o_auth_token = _get_service_token()
    container_service_resource_id = CONTAINER_SERVICE_RESOURCE_URL.format(subscription_id=subscription_id, resource_group_name=target_resource_group, container_service_name=target_name)
    data = {
        'acsResourceId': container_service_resource_id,
        'vstsAccountName': vsts_account_name,
        'vstsProjectName': vsts_project_name,
        'registryName': registry_name,
        'registryResourceId': registry_resource_id,
        'remoteToken': remote_access_token,
        'remoteUrl': remote_url,
        'remoteBranch': remote_branch,
        'createRelease' : create_release
    }

    configure_ci_cd_url = SERVICE_URL.format(
        subscription_id=subscription_id) + '/configureCI?api-version=' + API_VERSION

    headers = {}
    headers['Authorization'] = o_auth_token
    headers['Content-Type'] = 'application/json; charset=utf-8'
    headers['x-ms-client-request-id'] = str(uuid.uuid1())
    req = requests.post(configure_ci_cd_url, data=json.dumps(data), headers=headers, timeout=600)
    while req.status_code == 202:  # Long-running operation
        time.sleep(10)
        req = requests.get(BASE_URL + req.headers['Location'], headers=headers, timeout=600)
    if req.status_code != 200:
        raise CLIError(
            'Server returned status code: ' + str(req.status_code) + '. Could not configure CI/CD: ' + req.text)
    json_request = req.json()
    return json_request

def list_releases(target_name, target_resource_group):
    """
    Lists all the release definitions that are deployed to a given Azure container service.

    :param target_name: Name of the target Azure container service instance.
    :type target_name: String
    :param target_resource_group: Name of Azure container service's resource group.
    :type target_resource_group: String
    """
    profile = Profile()
    _, subscription_id, _ = profile.get_login_credentials()

    o_auth_token = _get_service_token()
    container_service_resource_id = CONTAINER_SERVICE_RESOURCE_URL.format(subscription_id=subscription_id, resource_group_name=target_resource_group, container_service_name=target_name)
    data = {
        'acsResourceId': container_service_resource_id
    }

    list_releases_url = SERVICE_URL.format(
        subscription_id=subscription_id) + '/listReleases?api-version=' + API_VERSION

    headers = {}
    headers['Authorization'] = o_auth_token
    headers['Content-Type'] = 'application/json; charset=utf-8'
    headers['x-ms-client-request-id'] = str(uuid.uuid1())
    req = requests.post(list_releases_url, data=json.dumps(data), headers=headers, timeout=600)
    while req.status_code == 202:  # Long-running operation
        time.sleep(10)
        req = requests.get(BASE_URL + req.headers['Location'], headers=headers, timeout=600)
    if req.status_code != 200:
        raise CLIError(
            'Server returned status code: ' + str(req.status_code) + '. Could not list releases: ' + req.text)
    json_request = req.json()
    return json_request

def _is_inside_git_directory():
    """
    Determines if the user is inside the .git folder of a git repo
    """
    try:
        is_inside_git_dir = check_output(['git', 'rev-parse', '--is-inside-git-dir'])
    except OSError:
        raise CLIError('Git is not currently installed.')

    git_result = is_inside_git_dir.decode('utf-8').strip()

    if git_result == 'false':
        return False
    elif git_result == 'true':
        return True
    else:
        raise CLIError('Unexpected value from git operation.')

def _gitroot():
    """
    Gets the absolute path of the repository root
    """
    if _is_inside_git_directory(): # special case need to navigate to parent
        os.chdir('..')
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
    """
    docker_compose_file = _get_filepath_in_current_git_repo(DOCKER_COMPOSE_FILE)

    if not docker_compose_file:
        raise CLIError('Docker compose file "{}" was not found.'.format(DOCKER_COMPOSE_FILE))
    _ensure_version(docker_compose_file, DOCKER_COMPOSE_EXPECTED_VERSION)

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
    except CalledProcessError as e:
        raise CLIError('Please ensure git version 2.7.0 or greater is installed.\n' + e)
    return remote_url.decode()

def _check_registry_information(registry_name, registry_resource_id):
    """
    Check that only one of registry_name and registry_resource_id is provided
    :param registry_name: The registry name.
    :type name: String
    :param registry_resource_id: The registry resource id.
    :type name: String
    Sample registry_resource_id: /subscriptions/{subscriptionId}/resourcegroups/{resourceGroup}/providers/Microsoft.ContainerRegistry/registries/{registryName}
    """
    if registry_name and registry_resource_id:
        raise CLIError("Please provide only one of registry-name and registry-resource-id, not both.")

def add_ci(
        target_name,
        target_resource_group,
        remote_url=None,
        remote_branch=None,
        remote_access_token=None,
        vsts_account_name=None,
        vsts_project_name=None,
        registry_resource_id=None,
        registry_name=None):
    """
    Creates a build definition that automates building and pushing Docker images to an Azure container registry. Source repository must define a Dockerfile.

    :param name: Name of the target Azure container service instance to deploy containers to.
    :type name: String
    :param resource_group_name: Name of Azure container service's resource group.
    :type resource_group_name: String
    :param remote_url: Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.
    :type remote_url: String
    :param remote_branch: Remote branch of the GitHub or VSTS source repository that will be built and deployed. If omitted refs/heads/master will be selected.
    :type remote_branch: String
    :param remote_access_token: GitHub personal access token (minimum permission is 'repo'). Required if the source repository is in GitHub.
    :type remote_access_token: String
    :param vsts_account_name: VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.
    :type vsts_account_name: String
    :param vsts_project_name: VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.
    :type vsts_project_name: String
    :param registry_resource_id: Azure container registry resource id.
    :type registry_resource_id: String
    :param registry_name: Azure container registry name. A new Azure container registry is created if omitted or does not exist.
    :type registry_name: String
    """
    _ensure_dockerfile()

    _check_registry_information(registry_name, registry_resource_id)

    # Call the RP
    return _call_rp_configure_cicd(
        target_name,
        target_resource_group,
        vsts_account_name,
        vsts_project_name,
        registry_name,
        registry_resource_id,
        _get_valid_remote_url(remote_url, remote_access_token),
        remote_branch,
        remote_access_token,
        False)

def _get_service_token():
    profile = Profile()
    credsCache = CredsCache()
    account = profile.get_subscription()

    user_name = account['user']['name']
    tenant = account['tenantId']

    if account['user']['type'] == _SERVICE_PRINCIPAL:
        scheme, token = credsCache.retrieve_token_for_service_principal(user_name, SERVICE_RESOURCE_ID)
    else:
        scheme, token = credsCache.retrieve_token_for_user(user_name, tenant, SERVICE_RESOURCE_ID)

    service_token = "{} {}".format(scheme, token)
    return service_token
    