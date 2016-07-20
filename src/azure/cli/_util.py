#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
import platform

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

class CLIError(Exception):
    """Base class for exceptions that occur during
    normal operation of the application.
    Typically due to user error and can be resolved by the user.
    """
    pass

def normalize_newlines(str_to_normalize):
    return str_to_normalize.replace('\r\n', '\n')

def show_version_info_exit(out_file):
    from pip import get_installed_distributions
    installed_dists = get_installed_distributions(local_only=True)

    cli_info = None
    for dist in installed_dists:
        if dist.key == CLI_PACKAGE_NAME:
            cli_info = {'name': dist.key, 'version': dist.version}
            break

    if cli_info:
        print('{} ({})'.format(cli_info['name'], cli_info['version']), file=out_file)

    component_version_info = sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''),
                                      'version': dist.version}
                                     for dist in installed_dists
                                     if dist.key.startswith(COMPONENT_PREFIX)],
                                    key=lambda x: x['name'])

    print(file=out_file)
    print('\n'.join(['{} ({})'.format(c['name'], c['version']) for c in component_version_info]),
          file=out_file)
    print(file=out_file)
    print('Python ({}) {}'.format(platform.system(), sys.version), file=out_file)
    sys.exit(0)
