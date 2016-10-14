#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from .custom import (list_clouds, show_cloud, register_cloud, unregister_cloud)

cli_command('cloud list', list_clouds)
cli_command('cloud show', show_cloud)
cli_command('cloud register', register_cloud)
cli_command('cloud unregister', unregister_cloud)
