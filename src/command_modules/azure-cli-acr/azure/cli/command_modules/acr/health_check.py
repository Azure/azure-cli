# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from knack.util import CLIError
from .custom import get_docker_command
from ._utils import get_registry_by_name
from ._docker_utils import get_access_credentials
from subprocess import PIPE, Popen, getoutput

def _get_docker_version():
    docker_command = get_docker_command()
    output = getoutput(docker_command + ' --version')

    version_search = re.search('Docker version ([0-9.b]+),*', output, re.IGNORECASE)

    if version_search:
        print("Docker is running with version {}.".format(version_search.group(1)))
    else:
        print("Could not find what docker version is running. Is docker running?")

def _get_cli_version():
    output = getoutput('az --version')

    lines = output.split('\n')
    az_cli_version, acr_cli_version = "", ""

    regex = re.compile(r'([0-9.b]+)')

    for line in lines:
        if line.startswith('azure-cli'):
            az_cli_version = regex.search(line).group(1)
        elif line.startswith('acr'):
            acr_cli_version = regex.search(line).group(1)

    print('Azure CLI is running with version {}.'.format(az_cli_version))
    print('Azure Container Registry CLI is running with version {}.'.format(acr_cli_version))

def _health_check_environment():
    _get_docker_version()
    _get_cli_version()

def _get_registry_status(cmd, registry_name):
    registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name)
    login_server = registry.login_server
    
    output = getoutput("nslookup " + login_server)
    lines = output.split('\n')
    ip = ""
    regex = re.compile(r'([0-9.b]+)')

    for line in lines:
        if line.startswith("Address:"):
            ip = regex.search(line).group(1)
    
    if ip == "":
        raise CLIError("Could not connect to {}.".format(login_server)
            + "Please make sure that the registry is reachable from this environment.")
    else:
        print("DNS lookup to {} at IP {}: OK."
            .format(login_server, ip))

def _health_check_connectivity(cmd, registry_name):
    _get_registry_status(cmd, registry_name)

def acr_health_check(cmd,
                     connectivity,
                     environment,
                     all_checks,
                     registry_name=None):

    if connectivity or all_checks:
        _health_check_connectivity(cmd, registry_name)
    
    if environment or all_checks:
        _health_check_environment()