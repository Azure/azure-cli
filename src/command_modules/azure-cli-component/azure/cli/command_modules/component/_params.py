#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.commands import register_cli_argument

# BASIC PARAMETER CONFIGURATION

# pylint: disable=line-too-long
register_cli_argument('component', 'component_name', options_list=('--name', '-n'), help='Name of component')
register_cli_argument('component', 'force', options_list=('--force', '-f'), help='Supress delete confirmation prompt', action='store_true')
register_cli_argument('component', 'link', options_list=('--link', '-l'), help='If a url or path to an html file, parse for links to archives. If local path or file:// url that\'s a directory, then look for archives in the directory listing.')
register_cli_argument('component', 'private', options_list=('--private', '-p'), help='Get from the project PyPI server', action='store_true')
register_cli_argument('component', 'version', help='Component version (otherwise latest)')
