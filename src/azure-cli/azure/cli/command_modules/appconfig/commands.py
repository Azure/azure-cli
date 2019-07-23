# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import cf_configstore, cf_configstore_operations
from ._format import (configstore_credential_format,
                      configstore_output_format,
                      keyvalue_entry_format)


def load_command_table(self, _):

    configstore_custom_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.appconfig.custom#{}',
        table_transformer=configstore_output_format,
        client_factory=cf_configstore
    )

    configstore_credential_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.appconfig.custom#{}',
        table_transformer=configstore_credential_format,
        client_factory=cf_configstore
    )

    configstore_keyvalue_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.appconfig.keyvalue#{}',
        table_transformer=keyvalue_entry_format,
        client_factory=cf_configstore_operations
    )

    # Management Plane Commands
    with self.command_group('appconfig', configstore_custom_util, is_preview=True) as g:
        g.command('create', 'create_configstore')
        g.command('delete', 'delete_configstore')
        g.command('update', 'update_configstore')
        g.command('list', 'list_configstore')
        g.command('show', 'show_configstore')
        g.generic_update_command('update',
                                 getter_name='configstore_update_get',
                                 setter_name='configstore_update_set',
                                 custom_func_name='configstore_update_custom')

    with self.command_group('appconfig credential', configstore_credential_util) as g:
        g.command('list', 'list_credential')
        g.command('regenerate', 'regenerate_credential')

    with self.command_group('appconfig revision', configstore_keyvalue_util) as g:
        g.command('list', 'list_revision')

    # Data Plane Commands
    with self.command_group('appconfig kv', configstore_keyvalue_util) as g:
        g.command('set', 'set_key')
        g.command('delete', 'delete_key')
        g.command('show', 'show_key')
        g.command('list', 'list_key')
        g.command('lock', 'lock_key')
        g.command('unlock', 'unlock_key')
        g.command('restore', 'restore_key')
        g.command('import', 'import_config')
        g.command('export', 'export_config')
