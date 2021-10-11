# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.extension.operations import list_extensions
from ._transformers import (
    transform_support_types,
    transform_linker_properties
)
from ._resource_config import (
    SOURCE_RESOURCES,
    TARGET_RESOURCES,
    SOURCE_RESOURCES_IN_EXTENSION
)


def load_command_table(self, _):

    from azure.cli.command_modules.serviceconnector._client_factory import cf_linker
    connection_type = CliCommandType(
        operations_tmpl='azure.mgmt.servicelinker.operations._linker_operations#LinkerOperations.{}',
        client_factory=cf_linker)

    # names of CLI installed extensions
    installed_extensions = [item.get('name') for item in list_extensions()]
    for source in SOURCE_RESOURCES:
        # if source resource is released as an extension, load our command groups
        # only when the extension is installed
        if source not in SOURCE_RESOURCES_IN_EXTENSION or source.value in installed_extensions:
            with self.command_group('{} connection'.format(source.value),
                                    connection_type, client_factory=cf_linker) as og:
                og.custom_command('list', 'connection_list')
                og.custom_show_command('show', 'connection_show', transform=transform_linker_properties)
                og.custom_command('delete', 'connection_delete', confirmation=True, supports_no_wait=True)
                og.custom_command('list-configuration', 'connection_list_configuration')
                og.custom_command('validate', 'connection_validate')
                og.custom_command('list-support-types', 'connection_list_support_types',
                                  table_transformer=transform_support_types)
                og.custom_wait_command('wait', 'connection_show')

            for target in TARGET_RESOURCES:
                with self.command_group('{} connection create'.format(source.value),
                                        connection_type, client_factory=cf_linker) as ig:
                    ig.custom_command(target.value, 'connection_create',
                                      supports_no_wait=True, transform=transform_linker_properties)
                with self.command_group('{} connection update'.format(source.value),
                                        connection_type, client_factory=cf_linker) as ig:
                    ig.custom_command(target.value, 'connection_update',
                                      supports_no_wait=True, transform=transform_linker_properties)
