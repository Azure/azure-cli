# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from knack.log import get_logger
from ._transformers import (
    transform_support_types,
    transform_linkers_properties,
    transform_linker_properties,
    transform_validation_result,
    transform_local_linker_properties
)
from ._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES,
    SUPPORTED_AUTH_TYPE,
    TARGET_RESOURCES_DEPRECATED
)
from ._utils import should_load_source


logger = get_logger(__name__)


def load_command_table(self, _):  # pylint: disable=too-many-statements

    from azure.cli.command_modules.serviceconnector._client_factory import (
        cf_linker,
        cf_connector,
        cf_configuration_names
    )
    connection_type = CliCommandType(
        operations_tmpl='azure.mgmt.servicelinker.operations._linker_operations#LinkerOperations.{}',
        client_factory=cf_linker)
    local_connection_type = CliCommandType(
        operations_tmpl='azure.mgmt.servicelinker.operations._connector_operations#ConnectorOperations.{}',
        client_factory=cf_connector)

    for source in SOURCE_RESOURCES:
        # if source resource is released as an extension, load our command groups
        # only when the extension is installed
        if should_load_source(source):
            is_preview_source = source == RESOURCE.KubernetesCluster

            with self.command_group('{} connection'.format(source.value), connection_type,
                                    client_factory=cf_linker, is_preview=is_preview_source) as og:
                og.custom_command('list', 'connection_list', transform=transform_linkers_properties)
                og.custom_show_command('show', 'connection_show', transform=transform_linker_properties)
                og.custom_command('delete', 'connection_delete', confirmation=True, supports_no_wait=True)
                og.custom_command('list-configuration', 'connection_list_configuration')
                og.custom_command('validate', 'connection_validate', transform=transform_validation_result)
                og.custom_command('list-support-types', 'connection_list_support_types',
                                  table_transformer=transform_support_types)
                og.custom_wait_command('wait', 'connection_show')

            # use SUPPORTED_AUTH_TYPE to decide target resource, as some
            # target resources are not avialable for certain source resource
            supported_target_resources = list(SUPPORTED_AUTH_TYPE.get(source).keys())
            if RESOURCE.ConfluentKafka in supported_target_resources:
                supported_target_resources.remove(RESOURCE.ConfluentKafka)
            else:
                logger.warning("ConfluentKafka is not in supported target resources for %s", source.value)
            for target in supported_target_resources:
                with self.command_group('{} connection create'.format(source.value),
                                        connection_type, client_factory=cf_linker) as ig:
                    if target in TARGET_RESOURCES_DEPRECATED:
                        ig.custom_command(target.value, 'connection_create', deprecate_info=self.deprecate(hide=False),
                                          supports_no_wait=True, transform=transform_linker_properties)
                    else:
                        ig.custom_command(target.value, 'connection_create',
                                          supports_no_wait=True, transform=transform_linker_properties)
                with self.command_group('{} connection update'.format(source.value),
                                        connection_type, client_factory=cf_linker) as ig:
                    if target in TARGET_RESOURCES_DEPRECATED:
                        ig.custom_command(target.value, 'connection_update', deprecate_info=self.deprecate(hide=False),
                                          supports_no_wait=True, transform=transform_linker_properties)
                    else:
                        ig.custom_command(target.value, 'connection_update',
                                          supports_no_wait=True, transform=transform_linker_properties)

            # special target resource, independent implementation
            target = RESOURCE.ConfluentKafka
            with self.command_group('{} connection create'.format(source.value),
                                    connection_type, client_factory=cf_linker) as ig:
                ig.custom_command(target.value, 'connection_create_kafka', supports_no_wait=True)
            with self.command_group('{} connection update'.format(source.value),
                                    connection_type, client_factory=cf_linker) as ig:
                ig.custom_command(target.value, 'connection_update_kafka', supports_no_wait=True)

    # local connection
    with self.command_group('connection', connection_type,
                            client_factory=cf_connector) as og:
        og.custom_command('list', 'local_connection_list')
        og.custom_show_command(
            'show', 'local_connection_show', transform=transform_local_linker_properties)
        og.custom_command('delete', 'local_connection_delete',
                          confirmation=True, supports_no_wait=True)
        og.custom_command('generate-configuration',
                          'local_connection_generate_configuration')
        og.custom_command('validate', 'local_connection_validate',
                          transform=transform_validation_result)
        og.custom_command('list-support-types', 'connection_list_support_types',
                          table_transformer=transform_support_types)
        og.custom_wait_command('wait', 'local_connection_show')

    supported_target_resources = list(
        SUPPORTED_AUTH_TYPE.get(RESOURCE.Local).keys())
    if RESOURCE.ConfluentKafka in supported_target_resources:
        supported_target_resources.remove(RESOURCE.ConfluentKafka)
    else:
        logger.warning("ConfluentKafka is not in supported target resources for %s", RESOURCE.Local.value)
    for target in supported_target_resources:
        with self.command_group('connection preview-configuration', client_factory=cf_configuration_names) as ig:
            ig.custom_command(target.value, 'connection_preview_configuration')
        with self.command_group('connection create',
                                local_connection_type, client_factory=cf_connector) as ig:
            ig.custom_command(target.value, 'local_connection_create',
                              supports_no_wait=True, transform=transform_local_linker_properties)
        with self.command_group('connection update',
                                local_connection_type, client_factory=cf_connector) as ig:
            ig.custom_command(target.value, 'local_connection_update',
                              supports_no_wait=True, transform=transform_local_linker_properties)

    # special target resource, independent implementation
    target = RESOURCE.ConfluentKafka
    with self.command_group('connection create',
                            local_connection_type, client_factory=cf_connector) as ig:
        ig.custom_command(
            target.value, 'local_connection_create_kafka', supports_no_wait=True)
    with self.command_group('connection update',
                            local_connection_type, client_factory=cf_connector) as ig:
        ig.custom_command(
            target.value, 'local_connection_update_kafka', supports_no_wait=True)
    with self.command_group('connection preview-configuration', client_factory=cf_configuration_names) as ig:
        ig.custom_command(target.value, 'connection_preview_configuration')
