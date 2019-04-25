# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from subprocess import getoutput
from knack.util import CLIError
from .custom import get_docker_command
from ._utils import get_registry_by_name, get_resource_group_name_by_registry_name

## Checks for the environment ##

def _get_docker_version():
    docker_command = get_docker_command()
    output = getoutput(docker_command + ' system info')

    lines = output.splitlines()
    regex = re.compile(r'([0-9.b]+)')
    docker_version = ""

    for line in lines:
        if line.startswith("Server Version"):
            docker_version = regex.search(line).group(1)

    if docker_version == "":
        raise CLIError("Could not find which Docker Server version is running.")
    else:
        print("Docker running with server version {}.".format(docker_version))

def _get_cli_version():
    output = getoutput('az --version')

    lines = output.splitlines()
    acr_cli_version = ""

    regex = re.compile(r'([0-9.b]+)')

    for line in lines:
        if line.startswith('acr'):
            acr_cli_version = regex.search(line).group(1)

    if acr_cli_version == "":
        raise CLIError("Could not find which ACR CLI version is running.")
    else:
        print('Azure Container Registry CLI is running with version {}.'.format(acr_cli_version))

def _health_check_environment():
    aggregated_exceptions = ""

    try:
        _get_docker_version()
    except CLIError as e:
        error = "Error while finding docker server version: " + str(e) + "\n"
        aggregated_exceptions = aggregated_exceptions + error

    try:
        _get_cli_version()
    except CLIError as e:
        error = "Error while finding ACR CLI version: " + str(e) + "\n"
        aggregated_exceptions = aggregated_exceptions + error

    return aggregated_exceptions

## Checks for the connection ##

def _get_registry_status(cmd, registry_name):
    registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name)
    login_server = registry.login_server

    import socket

    registry_ip = ""

    try:
        registry_ip = socket.gethostbyname(login_server)
    except socket.gaierror:
        pass

    if registry_ip == "":
        raise CLIError("Could not connect to {}. ".format(login_server)
                       + "Please make sure that the registry is reachable from this environment.")
    else:
        print("DNS lookup to {} at IP {}: OK.".format(login_server, registry_ip))

def _get_token_status(cmd, registry_name):
    registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name)
    login_server = registry.login_server

    import requests
    try:
        from urllib.parse import urlencode, urlparse, urlunparse
    except ImportError:
        from urllib import urlencode
        from urlparse import urlparse, urlunparse

    # Validate the login server is accessible from environment
    url = 'https://' + login_server + '/v2/'
    challenge = requests.get(url)

    if challenge.status_code == 403:
        raise CLIError("Looks like you don't have access to registry '{}'. "
                       "Are firewalls and virtual networks enabled?".format(login_server))
    elif challenge.status_code != 401 or 'WWW-Authenticate' not in challenge.headers:
        raise CLIError("Registry '{}' did not issue a challenge.".format(login_server))

    # Validate support for AAD login
    authenticate = challenge.headers['WWW-Authenticate']
    tokens = authenticate.split(' ', 2)
    if len(tokens) < 2 or tokens[0].lower() != 'bearer':
        raise CLIError("Registry '{}' does not support AAD login.".format(login_server))

    params = {y[0]: y[1].strip('"') for y in
              (x.strip().split('=', 2) for x in tokens[1].split(','))}
    if 'realm' not in params or 'service' not in params:
        raise CLIError("Registry '{}' does not support AAD login.".format(login_server))

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
        raise CLIError("Access to registry '{}' was denied. Response code: {}.".format(
            login_server, response.status_code))

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
        raise CLIError("Access to registry '{}' was denied. Response code: {}.".format(
            login_server, response.status_code))

    print("Obtain access token for registry {} : OK".format(login_server))

def _get_admin_credentials_status(cmd, registry_name):
    registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name)
    login_server = registry.login_server
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name)

    from ._client_factory import cf_acr_registries

    if registry.admin_user_enabled:
        print("Admin user enabled for registry {}.".format(login_server))
        try:
            cf_acr_registries(cmd.cli_ctx).list_credentials(resource_group_name, registry_name)
        except CLIError as e:
            raise CLIError("Unable to get admin user credentials with message: " + str(e))
        print("Obtain admin credentials for registry {} : OK".format(login_server))
    else:
        print("Admin user not enabled for registry {}.".format(login_server))



def _health_check_connectivity(cmd, registry_name):
    if not registry_name:
        return "Registry name must be provided to check connectivity."

    aggregated_exceptions = ""

    try:
        _get_registry_status(cmd, registry_name)
    except CLIError as e:
        error = "Error while retrieving registry status: " + str(e) + "\n"
        return error

    try:
        _get_token_status(cmd, registry_name)
    except CLIError as e:
        error = "Error while acquiring tokens: " + str(e) + "\n"
        aggregated_exceptions = aggregated_exceptions + error

    try:
        _get_admin_credentials_status(cmd, registry_name)
    except CLIError as e:
        error = "Error while listing credentials: " + str(e) + "\n"
        aggregated_exceptions = aggregated_exceptions + error

    return aggregated_exceptions

def acr_health_check(cmd,
                     connectivity,
                     environment,
                     all_checks,
                     registry_name=None):

    connectivity_exceptions, environment_exceptions = "", ""

    if connectivity or all_checks:
        connectivity_exceptions = _health_check_connectivity(cmd, registry_name)

    if environment or all_checks:
        environment_exceptions = _health_check_environment()

    all_exceptions = ""
    if connectivity_exceptions != "":
        all_exceptions = "The following error(s) occurred while checking connectivity:\n" + connectivity_exceptions
    if environment_exceptions != "":
        all_exceptions = "The following error(s) occurred while checking environment:\n" + environment_exceptions

    if all_exceptions != "":
        raise CLIError(all_exceptions)
    else:
        print("Passed all health checks successfully. If error persists, please open a ticket to ACR Team.")
