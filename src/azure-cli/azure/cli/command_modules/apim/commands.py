# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-statements


from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._format import (service_output_format)
from azure.cli.command_modules.apim._client_factory import (cf_service, cf_api, cf_product, cf_nv, cf_apiops,
                                                            cf_apirelease, cf_apirevision, cf_apiversionset,
                                                            cf_apischema, cf_ds)


def load_command_table(self, _):
    service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiManagementServiceOperations.{}',
        client_factory=cf_service
    )

    api_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiOperations.{}',
        client_factory=cf_api
    )

    api_schema = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiSchemaOperations.{}',
        client_factory=cf_apischema
    )

    product_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ProductOperations.{}',
        client_factory=cf_product
    )

    nv_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#NamedValueOperations.{}',
        client_factory=cf_nv
    )

    apiops_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiOperationOperations.{}',
        client_factory=cf_apiops
    )

    apirel_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiReleaseOperations.{}',
        client_factory=cf_apirelease
    )

    apirev_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiRevisionOperations.{}',
        client_factory=cf_apirevision
    )

    apivs_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiVersionSetOperations.{}',
        client_factory=cf_apiversionset
    )

    apids_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#DeletedServicesOperations.{}',
        client_factory=cf_ds
    )

    # pylint: disable=line-too-long
    with self.command_group('apim', service_sdk) as g:
        g.custom_command('create', 'apim_create', supports_no_wait=True,
                         table_transformer=service_output_format)
        g.custom_show_command('show', 'apim_get',
                              table_transformer=service_output_format)
        g.custom_command('list', 'apim_list',
                         table_transformer=service_output_format)
        g.command('delete', 'begin_delete',
                  confirmation=True, supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='apim_update', getter_name='get',
                                 setter_name='begin_create_or_update', supports_no_wait=True)
        g.custom_command('check-name', 'apim_check_name_availability')
        g.custom_command('backup', 'apim_backup', supports_no_wait=True)
        g.custom_command('restore', 'apim_restore', supports_no_wait=True)
        g.custom_command('apply-network-updates',
                         'apim_apply_network_configuration_updates', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('apim api', api_sdk) as g:
        g.custom_command('import', 'apim_api_import', supports_no_wait=True)
        g.custom_command('create', 'apim_api_create', supports_no_wait=True)
        g.custom_show_command('show', 'apim_api_get')
        g.custom_command('list', 'apim_api_list')
        g.custom_command('delete', 'apim_api_delete',
                         confirmation=True, supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='apim_api_update',
                                 setter_name='begin_create_or_update', getter_name='get', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('apim product api', api_sdk) as g:
        g.custom_command('list', 'apim_product_api_list')
        g.custom_command('check', 'apim_product_api_check_association')
        g.custom_command('add', 'apim_product_api_add')
        g.custom_command('delete', 'apim_product_api_delete')

    with self.command_group('apim api schema', api_schema) as g:
        g.custom_command('create', 'apim_api_schema_create', supports_no_wait=True)
        g.custom_command('delete', 'apim_api_schema_delete', confirmation=True, supports_no_wait=True)
        g.custom_show_command('show', 'apim_api_schema_get')
        g.custom_command('list', 'apim_api_schema_list')
        g.custom_command('get-etag', 'apim_api_schema_entity')
        g.wait_command('wait')

    with self.command_group('apim product', product_sdk) as g:
        g.custom_command('list', 'apim_product_list')
        g.custom_show_command('show', 'apim_product_show')
        g.custom_command('create', 'apim_product_create', supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='apim_product_update', supports_no_wait=True)
        g.custom_command('delete', 'apim_product_delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('apim nv', nv_sdk) as g:
        g.custom_command('create', 'apim_nv_create', supports_no_wait=True)
        g.custom_show_command('show', 'apim_nv_get')
        g.custom_command('list', 'apim_nv_list')
        g.custom_command('delete', 'apim_nv_delete', confirmation=True)
        g.custom_command('show-secret', 'apim_nv_show_secret')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='apim_nv_update')

    with self.command_group('apim api operation', apiops_sdk) as g:
        g.custom_command('list', 'apim_api_operation_list')
        g.custom_show_command('show', 'apim_api_operation_get')
        g.custom_command('create', 'apim_api_operation_create')
        g.generic_update_command('update', custom_func_name='apim_api_operation_update')
        g.custom_command('delete', 'apim_api_operation_delete')

    with self.command_group('apim api release', apirel_sdk) as g:
        g.custom_command('list', 'apim_api_release_list')
        g.custom_show_command('show', 'apim_api_release_show')
        g.custom_command('create', 'apim_api_release_create')
        g.generic_update_command('update', custom_func_name='apim_api_release_update')
        g.custom_command('delete', 'apim_api_release_delete')

    with self.command_group('apim api revision', apirev_sdk) as g:
        g.custom_command('list', 'apim_api_revision_list')
        g.custom_command('create', 'apim_api_revision_create')

    with self.command_group('apim api versionset', apivs_sdk) as g:
        g.custom_command('list', 'apim_api_vs_list')
        g.custom_show_command('show', 'apim_api_vs_show')
        g.custom_command('create', 'apim_api_vs_create')
        g.generic_update_command('update', custom_func_name='apim_api_vs_update')
        g.custom_command('delete', 'apim_api_vs_delete')

    with self.command_group('apim deletedservice', apids_sdk) as g:
        g.custom_command('list', 'apim_ds_list')
        g.custom_show_command('show', 'apim_ds_get')
        g.custom_command('purge', 'apim_ds_purge')