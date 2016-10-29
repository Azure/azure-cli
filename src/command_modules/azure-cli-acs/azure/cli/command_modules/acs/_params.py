#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import platform

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type)

def _get_default_install_location(exe_name):
    system = platform.system()
    if system == 'Windows':
        program_files = os.environ.get('ProgramFiles')
        if not program_files:
            return None
        install_location = '{}\\{}.exe'.format(program_files, exe_name)
    elif system == 'Linux' or system == 'Darwin':
        install_location = '/usr/local/bin/{}'.format(exe_name)
    else:
        install_location = None
    return install_location

register_cli_argument('acs dcos browse', 'name', name_type)
register_cli_argument('acs dcos browse', 'resource_group_name', resource_group_name_type)
register_cli_argument('acs dcos install-cli', 'install_location',
                      options_list=('--install-location',),
                      default=_get_default_install_location('dcos'))
register_cli_argument('acs dcos install-cli', 'client_version',
                      options_list=('--client-version',),
                      default='1.8')
