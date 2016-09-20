#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument

# pylint: disable=line-too-long
register_cli_argument('component', 'component_name', options_list=('--name', '-n'), help='Name of component')
register_cli_argument('component', 'link', options_list=('--link', '-l'), help='If a url or path to an html file, parse for links to archives. If local path or file:// url that\'s a directory, then look for archives in the directory listing.')
register_cli_argument('component', 'private', help='Include packages from a private server.', action='store_true')
register_cli_argument('component', 'pre', help='Include pre-release versions', action='store_true')
register_cli_argument('component', 'show_logs', help='Show logs from packaging installing/updating', action='store_true')
register_cli_argument('component', 'additional_component', help='The name of an additional component to install')
