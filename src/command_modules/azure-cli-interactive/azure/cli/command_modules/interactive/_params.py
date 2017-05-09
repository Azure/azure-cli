# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import register_cli_argument

from azclishell.color_styles import get_options as style_options

register_cli_argument('interactive', 'style', options_list=('--style', '-s'),
                      help='The colors of the shell.', choices=style_options())
