# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .custom import get_docker_command
from ._utils import get_registry_by_name

def _get_docker_version():
    from subprocess import PIPE, Popen, getoutput
    docker_command = get_docker_command()
    output = getoutput(docker_command + ' --version')
    print(output)

def _get_cli_version():
    from subprocess import PIPE, Popen, getoutput
    output = getoutput('az --version')
    print(output)

def _health_check_environment():
    _get_docker_version()
    _get_cli_version()

def _health_check_connectivity(registry_name):
    print("connectivity!")

def acr_health_check(cmd,
                     connectivity,
                     environment,
                     all_checks,
                     registry_name=None):

    if connectivity or all_checks:
        _health_check_connectivity(registry_name)
    
    if environment or all_checks:
        _health_check_environment()