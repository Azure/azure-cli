# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import enum
from subprocess import getoutput
from knack.util import CLIError
from .custom import get_docker_command
from .helm import _get_helm_command
from ._utils import get_registry_by_name

DOCKER_DAEMON_NOT_RUNNING = "This error may also indicate that the docker daemon is not running."
DOCKER_PULL_SUCCEEDED = "Downloaded newer image for {}:{}"
DOCKER_IMAGE_UP_TO_DATE = "Image is up to date for {}:{}"

class Errors(enum.Enum):
    DOCKER_DAEMON_ERROR = 1
    DOCKER_VERSION_ERROR = 2
    ACR_CLI_VERSION_ERROR = 4
    HELM_CLIENT_VERSION_ERROR = 8
    HELM_SERVER_VERSION_ERROR = 16
    LOGIN_SERVER_ERROR = 32
    CONNECTIVITY_REGISTRY_STATUS_ERROR = 64
    CONNECTIVITY_ENDPOINT_FORBIDDEN_ERROR = 128
    CONNECTIVITY_ENDPOINT_CHALLENGE_ERROR = 256
    CONNECTIVITY_AAD_LOGIN_ERROR = 512
    CONNECTIVITY_REFRESH_TOKEN_ERROR = 1024
    CONNECTIVITY_ACCESS_TOKEN_ERROR = 2048
    DOCKER_PULL_ERROR = 4096
    DOCKER_COMMAND_ERROR = 8192
    HELM_COMMAND_ERROR = 16384

recommendations_map = {
    "DOCKER_DAEMON_ERROR": "restart Docker daemon",
    "DOCKER_VERSION_ERROR": "update Docker version",
    "ACR_CLI_VERSION_ERROR": "update Azure CLI version",
    "HELM_CLIENT_VERSION_ERROR": "update helm version",
    "HELM_SERVER_VERSION_ERROR": "update helm version; restart kubernetes manager",
    "LOGIN_SERVER_ERROR": "check spelling and permissions on the registry; run az login to refresh token",
    "CONNECTIVITY_REGISTRY_STATUS_ERROR": "check if registry exists, if name is correct and check permissions on it",
    "CONNECTIVITY_ENDPOINT_FORBIDDEN_ERROR": "add current IP to network rules",
    "CONNECTIVITY_ENDPOINT_CHALLENGE_ERROR": "contact ACR team",
    "CONNECTIVITY_AAD_LOGIN_ERROR": "enable AAD login (contact ACR team)",
    "CONNECTIVITY_REFRESH_TOKEN_ERROR": "run az login to refresh token",
    "CONNECTIVITY_ACCESS_TOKEN_ERROR": "check permissions to the registry; run az login to refresh token",
    "DOCKER_PULL_ERROR": "restart docker services",
    "DOCKER_COMMAND_ERROR": "install, start or restart docker client and services",
    "HELM_COMMAND_ERROR": "install or start helm client; restart kubernetes manager"
}

## Utilities functions ##

def print_pass(message):
    from colorama import Fore, Style, init
    init()
    print(str(message) + " : " + Fore.GREEN + "OK" + Style.RESET_ALL)

def print_warning(message):
    from colorama import Fore, Style, init
    init()
    print(Fore.YELLOW + str(message) + Style.RESET_ALL)

def print_error(message):
    from colorama import Fore, Style, init
    init()
    print(Fore.RED + str(message) + Style.RESET_ALL)

def _error_handler(error, operation, ignore_errors, additional_message=None):
    error_message = \
        "{} : FAILED\n" \
        "Error : {}\n" \
        "Recommendations : {}" \
        .format(operation, error.name, recommendations_map[error.name])

    if additional_message is not None:
        error_message += "\n" + additional_message

    if ignore_errors:
        print_error(error_message)
        return error.value
    else:
        _raise_exception(error.value, error_message)

def _raise_exception(accumulated_errors, error_message=None):
    if accumulated_errors == 0:
        print("All checks passed. Please refer to https://aka.ms/acr/faq for more informations.")
        return

    if error_message is None:
        error_message = ""
    else:
        error_message += "\n"

    error_message += "An error occured. Please refer to https://aka.ms/acr/faq for more informations."

    raise CLIError(error_message)

## Checks for the environment ##

def _get_docker_version(ignore_errors):
    accumulated_errors = 0

    # If there's no docker command there's no reason to proceed the operations
    try:
        docker_command = get_docker_command()
    except CLIError:
        accumulated_errors |= _error_handler(Errors.DOCKER_COMMAND_ERROR,
                                             "Obtain docker command",
                                             ignore_errors,
                                             "DOCKER OPERATIONS FAILED")
        return accumulated_errors

    output = getoutput(docker_command + ' system info')

    # Docker daemon check
    if output.find(DOCKER_DAEMON_NOT_RUNNING) != -1:
        accumulated_errors |= _error_handler(Errors.DOCKER_DAEMON_ERROR, "Docker daemon status", ignore_errors)
    else:
        daemon_status = 'available'
        print('Docker daemon status: {}'.format(daemon_status))

    # Docker version check
    lines = output.splitlines()
    regex = re.compile(r'([0-9.b]+)')
    docker_version = ""

    for line in lines:
        if line.startswith("Server Version"):
            try:
                docker_version = regex.search(line).group(1)
            except AttributeError:
                pass

    if docker_version in ("", None):
        accumulated_errors |= _error_handler(Errors.DOCKER_VERSION_ERROR, "Docker server version", ignore_errors)
    else:
        print('Docker server version: {}'.format(docker_version))

    return accumulated_errors

def _get_cli_version(ignore_errors):
    accumulated_errors = 0

    #ACR CLI check
    output = getoutput('az --version')

    lines = output.splitlines()
    acr_cli_version = ""
    regex = re.compile(r'([0-9.b]+)')

    for line in lines:
        if line.startswith('acr'):
            try:
                acr_cli_version = regex.search(line).group(1)
            except AttributeError:
                pass

    if acr_cli_version in ("", None):
        accumulated_errors |= _error_handler(Errors.ACR_CLI_VERSION_ERROR, "ACR CLI version", ignore_errors)
    else:
        print('ACR cli version: {}'.format(acr_cli_version))

    return accumulated_errors

def _get_helm_version(ignore_errors):
    accumulated_errors = 0

    # If there's not helm command there's no reason to proceed with the operations
    try:
        helm_command = _get_helm_command()
    except CLIError:
        accumulated_errors |= _error_handler(Errors.HELM_COMMAND_ERROR,
                                             "Obtain helm command",
                                             ignore_errors,
                                             "HELM OPERATIONS FAILED")
        return accumulated_errors

    # Helm check
    output = getoutput(helm_command + ' version')

    lines = output.splitlines()
    regex = re.compile(r'SemVer:"([0-9.vb]+)"')
    client_version = ""
    server_version = ""

    for line in lines:
        if line.startswith('Client'):
            try:
                client_version = regex.search(line).group(1)
            except AttributeError:
                pass
        elif line.startswith('Server'):
            try:
                server_version = regex.search(line).group(1)
            except AttributeError:
                pass

    if client_version in ("", None):
        accumulated_errors |= _error_handler(Errors.HELM_CLIENT_VERSION_ERROR, "Helm client version", ignore_errors)
    else:
        print('Helm client version: {}'.format(client_version))

    if server_version in ("", None):
        accumulated_errors |= _error_handler(Errors.HELM_SERVER_VERSION_ERROR, "Helm server version", ignore_errors)
    else:
        print('Helm server version: {}'.format(server_version))

    return accumulated_errors


def _check_health_environment(ignore_errors):
    accumulated_errors = _get_docker_version(ignore_errors)
    accumulated_errors |= _get_cli_version(ignore_errors)
    accumulated_errors |= _get_helm_version(ignore_errors)

    return accumulated_errors

## Checks for the connectivity ##

def _get_registry_status(login_server, ignore_errors):
    accumulated_errors = 0

    # Check DNS lookup
    import socket

    registry_ip = ""

    try:
        registry_ip = socket.gethostbyname(login_server)
    except socket.gaierror:
        pass

    if registry_ip == "":
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_REGISTRY_STATUS_ERROR,
                                             "DNS lookup to {}".format(login_server),
                                             ignore_errors,
                                             "CONNECTIVITY OPERATIONS FAILED")
    else:
        print_pass("DNS lookup to {} at IP {}".format(login_server, registry_ip))

    return accumulated_errors

def _get_endpoint_and_token_status(cmd, login_server, ignore_errors):
    accumulated_errors = 0

    import requests
    try:
        from urllib.parse import urlencode, urlparse, urlunparse
    except ImportError:
        from urllib import urlencode
        from urlparse import urlparse, urlunparse

    # Check access to login endpoint
    url = 'https://' + login_server + '/v2/'
    challenge = requests.get(url)

    if challenge.status_code == 403:
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_ENDPOINT_FORBIDDEN_ERROR,
                                             "Challenge endpoint",
                                             ignore_errors)
        return accumulated_errors
    elif challenge.status_code != 401 or 'WWW-Authenticate' not in challenge.headers:
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_ENDPOINT_CHALLENGE_ERROR,
                                             "Challenge endpoint",
                                             ignore_errors)
        return accumulated_errors

    print_pass("Challenge endpoint {}".format(url))

    # Check support for refresh access token
    authenticate = challenge.headers['WWW-Authenticate']
    tokens = authenticate.split(' ', 2)
    if len(tokens) < 2 or tokens[0].lower() != 'bearer':
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_AAD_LOGIN_ERROR, "AAD access", ignore_errors)
        return accumulated_errors # Can't continue if registry is not AAD-reachable

    params = {y[0]: y[1].strip('"') for y in
              (x.strip().split('=', 2) for x in tokens[1].split(','))}
    if 'realm' not in params or 'service' not in params:
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_AAD_LOGIN_ERROR, "AAD access", ignore_errors)
        return accumulated_errors # Can't continue if registry is not AAD-reachable

    # Ensure tokens can be obtained
    authurl = urlparse(params['realm'])
    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/exchange', '', '', ''))

    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cmd.cli_ctx)
    creds, _, tenant = profile.get_raw_token()

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    content = {
        'grant_type': 'access_token',
        'service': params['service'],
        'tenant': tenant,
        'access_token': creds[1]
    }

    response = requests.post(authhost, urlencode(content), headers=headers)

    if response.status_code not in [200]:
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_REFRESH_TOKEN_ERROR,
                                             "Obtain refresh token for registry {}".format(login_server),
                                             ignore_errors)
        return accumulated_errors # We can't continue if the refresh token is not received

    print_pass("Obtain refresh token for registry {}".format(login_server))

    from json import loads

    refresh_token = loads(response.content.decode("utf-8"))["refresh_token"]
    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/token', '', '', ''))
    content = {
        'grant_type': 'refresh_token',
        'service': login_server,
        'scope': 'registry:catalog:*',
        'refresh_token': refresh_token
    }

    response = requests.post(authhost, urlencode(content), headers=headers)

    if response.status_code not in [200]:
        accumulated_errors |= _error_handler(Errors.CONNECTIVITY_ACCESS_TOKEN_ERROR,
                                             "Obtain access token for registry {}".format(login_server),
                                             ignore_errors)
    else:
        print_pass("Obtain access token for registry {}".format(login_server))

    return accumulated_errors

def _check_health_connectivity(cmd, registry_name, ignore_errors):
    accumulated_errors = 0

    if registry_name is None:
        print_warning("Registry name must be provided to check connectivity.")
        return accumulated_errors

    try:
        registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name)
        login_server = registry.login_server
    except CLIError:
        from ._docker_utils import get_login_server_suffix
        suffix = get_login_server_suffix(cmd.cli_ctx)
        if suffix is None:
            suffix = '.azurecr.io'
        login_server = registry_name + suffix
        print_warning('Could not load login server for {0}, using default {1}.'.format(registry_name, login_server))

    accumulated_errors |= _get_registry_status(login_server, ignore_errors)
    if accumulated_errors == 0: # Can't continue if DNS lookup failed
        accumulated_errors |= _get_endpoint_and_token_status(cmd, login_server, ignore_errors)

    return accumulated_errors

## Checks for docker pull ##

def _pull_docker_image(skip_confirmation, ignore_errors):
    accumulated_errors = 0
    image = "mcr.microsoft.com/mcr/hello-world"
    tag = "latest"

    if skip_confirmation:
        confirmation = 'Y'
    else:
        confirmation = ''

    while confirmation not in ['Y', 'y', 'N', 'n']:
        confirmation = str(input("This will pull the image {}:{}. Proceed? (Y/n): ".format(image, tag)))
    if confirmation in ['N', 'n']:
        print_warning("Skipping pull check.")
        return accumulated_errors

    # If there's no docker command there's no reason to proceed with operation
    try:
        docker_command = get_docker_command()
    except CLIError:
        accumulated_errors |= _error_handler(Errors.DOCKER_COMMAND_ERROR,
                                             "Obtain docker command",
                                             ignore_errors,
                                             "DOCKER PULL FAILED")
        return accumulated_errors

    output = getoutput(docker_command + ' pull {}:{}'.format(image, tag))
    if output.find(DOCKER_PULL_SUCCEEDED.format(image, tag)) != -1 \
        or output.find(DOCKER_IMAGE_UP_TO_DATE.format(image, tag)) != -1:
        print_pass("Docker pull")
    else:
        accumulated_errors |= _error_handler(Errors.DOCKER_PULL_ERROR, "Docker pull", ignore_errors)

    return accumulated_errors

def _check_health_pull(skip_confirmation, ignore_errors):
    accumulated_errors = _pull_docker_image(skip_confirmation, ignore_errors)
    return accumulated_errors

## General command ##

def acr_check_health(cmd,
                     connectivity,
                     environment,
                     pull,
                     all_checks,
                     ignore_errors=False,
                     skip_confirmation=False,
                     registry_name=None):

    accumulated_errors = 0

    if environment or all_checks:
        accumulated_errors |= _check_health_environment(ignore_errors)

    if connectivity or all_checks:
        accumulated_errors |= _check_health_connectivity(cmd, registry_name, ignore_errors)

    if pull or all_checks:
        accumulated_errors |= _check_health_pull(skip_confirmation, ignore_errors)

    return _raise_exception(accumulated_errors)
