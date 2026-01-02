# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_argument_deprecate, register_command_group_deprecate

register_argument_deprecate('postgres flexible-server create', '--high-availability', redirect='--zonal-resiliency')
register_argument_deprecate('postgres flexible-server update', '--high-availability', redirect='--zonal-resiliency')
register_command_group_deprecate(command_group='postgres flexible-server index-tuning',
                                 redirect='postgres flexible-server autonomous-tuning',
                                 message='Index tuning feature has now expanded its capabilities to support '
                                 'other automatically generated recommendations which are covered by the '
                                 'new command.')
