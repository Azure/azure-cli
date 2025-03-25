# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_group_deprecate, register_default_value_breaking_change, \
    register_argument_deprecate, register_other_breaking_change, register_logic_breaking_change, \
    register_command_deprecate


register_logic_breaking_change('postgres flexible-server create', 'Update default value of "--sku-name"',
                               detail='The default value will be changed from "Standard_D2s_v3" to a '
                               'supported sku based on regional capabilities.')
register_default_value_breaking_change('postgres flexible-server create', '--version', '16', '17')
register_default_value_breaking_change('postgres flexible-server create', '--create-default-database', 'Enabled',
                                       'Disabled')
register_argument_deprecate('postgres flexible-server create', '--active-directory-auth', '--microsoft-entra-auth')
register_argument_deprecate('postgres flexible-server update', '--active-directory-auth', '--microsoft-entra-auth')
register_command_group_deprecate('postgres flexible-server ad-admin', redirect='microsoft-entra-admin')
register_command_deprecate('postgres flexible-server replica stop-replication',
                           redirect='postgres flexible-server replica promote', hide=True)
register_other_breaking_change('postgres flexible-server update',
                               message='User confirmation will be needed for compute and storage updates '
                               'that trigger a restart of the server.')
