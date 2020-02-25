# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import cf_configstore, cf_configstore_operations
from ._format import (configstore_credential_format,
                      configstore_identity_format,
                      configstore_output_format,
                      keyvalue_entry_format,
                      featureflag_entry_format,
                      featurefilter_entry_format)


def load_command_table(self, _):

    configstore_custom_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.appconfig.custom#{}',
        table_transformer=configstore_output_format,
        client_factory=cf_configstore
    )

    configstore_identity_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.appconfig.custom#{}',
        table_transformer=configstore_identity_format,
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

    def get_custom_sdk(custom_module, client_factory, table_transformer):
        """Returns a CliCommandType instance with specified operation template based on the given custom module name.
        This is useful when the command is not defined in the default 'custom' module but instead in a module under
        'operations' package."""
        return CliCommandType(
            operations_tmpl='azure.cli.command_modules.appconfig.{}#'.format(custom_module) + '{}',
            client_factory=client_factory,
            table_transformer=table_transformer
        )

    # Management Plane Commands
    with self.command_group('appconfig', configstore_custom_util) as g:
        g.command('create', 'create_configstore')
        g.command('delete', 'delete_configstore')
        g.command('update', 'update_configstore')
        g.command('list', 'list_configstore')
        g.command('show', 'show_configstore')

    with self.command_group('appconfig credential', configstore_credential_util) as g:
        g.command('list', 'list_credential')
        g.command('regenerate', 'regenerate_credential')

    with self.command_group('appconfig identity', configstore_identity_util, is_preview=True) as g:
        g.command('assign', 'assign_managed_identity')
        g.command('remove', 'remove_managed_identity')
        g.command('show', 'show_managed_identity')

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
        g.command('set-keyvault', 'set_keyvault')

    # FeatureManagement Commands
    with self.command_group('appconfig feature',
                            custom_command_type=get_custom_sdk('feature',
                                                               cf_configstore_operations,
                                                               featureflag_entry_format),
                            is_preview=True) as g:
        g.custom_command('set', 'set_feature')
        g.custom_command('delete', 'delete_feature')
        g.custom_command('show', 'show_feature')
        g.custom_command('list', 'list_feature')
        g.custom_command('lock', 'lock_feature')
        g.custom_command('unlock', 'unlock_feature')
        g.custom_command('enable', 'enable_feature')
        g.custom_command('disable', 'disable_feature')

    with self.command_group('appconfig feature filter',
                            custom_command_type=get_custom_sdk('feature',
                                                               cf_configstore_operations,
                                                               featurefilter_entry_format)) as g:
        g.custom_command('add', 'add_filter')
        g.custom_command('delete', 'delete_filter')
        g.custom_command('show', 'show_filter')
        g.custom_command('list', 'list_filter')
