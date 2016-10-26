#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import platform

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type)
from azure.cli.core._util import CLIError

def _get_default_install_location(exeName):
    system = platform.system()
    if system == 'Windows':
        install_location = 'C:\\Program Files\\{}.exe'.format(exeName)
    elif system == 'Linux' or system == 'Darwin':
        install_location = '/usr/local/bin/{}'.format(exeName)
    else:
        raise CLIError('Proxy server ({}) does not exist on the cluster.'.format(system))
    return install_location

register_cli_argument('acs dcos browse', 'name', name_type)
register_cli_argument('acs dcos browse', 'resource_group_name', resource_group_name_type)
register_cli_argument('acs dcos install-cli', 'install_location',
                      options_list=('--install-location',),
                      default=_get_default_install_location('dcos'))
