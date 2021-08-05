# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-statements


from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._format import (service_output_format)
from azure.cli.command_modules.apim._client_factory import (cf_service, cf_api, cf_product, cf_nv, cf_apiops,
                                                            cf_apirelease, cf_apirevision, cf_apiversionset)


def load_command_table(self, _):
    service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiManagementServiceOperations.{}',
        client_factory=cf_service
    )

    api_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiOperations.{}',
        client_factory=cf_api
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

    # pylint: disable=line-too-long
    with self.command_group('apim', service_sdk) as g:
        g.custom_command('create', 'create_apim', supports_no_wait=True, table_transformer=service_output_format)
        g.custom_show_command('show', 'get_apim', table_transformer=service_output_format)
        g.custom_command('list', 'list_apim', table_transformer=service_output_format)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='update_apim', getter_name='get', setter_name='create_or_update', supports_no_wait=True)
        g.custom_command('check-name', 'check_name_availability')
        g.custom_command('backup', 'apim_backup', supports_no_wait=True)
        g.custom_command('restore', 'apim_restore', supports_no_wait=True)
        g.custom_command('apply-network-updates', 'apim_apply_network_configuration_updates', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('apim api', api_sdk) as g:
        g.custom_command('import', 'import_apim_api', supports_no_wait=True)
        g.custom_command('create', 'create_apim_api', supports_no_wait=True)
        g.custom_show_command('show', 'get_apim_api')
        g.custom_command('list', 'list_apim_api')
        g.custom_command('delete', 'delete_apim_api', confirmation=True, supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='update_apim_api', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('apim product api', api_sdk) as g:
        g.custom_command('list', 'list_product_api')
        g.custom_command('check', 'check_product_exists')
        g.custom_command('add', 'add_product_api')
        g.custom_command('delete', 'delete_product_api')

    with self.command_group('apim product', product_sdk) as g:
        g.custom_command('list', 'list_products')
        g.custom_show_command('show', 'show_product')
        g.custom_command('create', 'create_product', supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='update_product', supports_no_wait=True)
        g.custom_command('delete', 'delete_product', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('apim nv', nv_sdk) as g:
        g.custom_command('create', 'create_apim_nv')
        g.custom_show_command('show', 'get_apim_nv')
        g.custom_command('list', 'list_apim_nv')
        g.custom_command('delete', 'delete_apim_nv', confirmation=True)
        g.custom_command('show-secret', 'get_apim_nv_secret')
        g.generic_update_command('update', custom_func_name='update_apim_nv')

    with self.command_group('apim api operation', apiops_sdk) as g:
        g.custom_command('list', 'list_api_operation')
        g.custom_show_command('show', 'get_api_operation')
        g.custom_command('create', 'create_api_operation')
        g.generic_update_command('update', custom_func_name='update_api_operation')
        g.custom_command('delete', 'delete_api_operation')

    with self.command_group('apim api release', apirel_sdk) as g:
        g.custom_command('list', 'list_api_release')
        g.custom_show_command('show', 'show_api_release')
        g.custom_command('create', 'create_api_release')
        g.generic_update_command('update', custom_func_name='update_api_release')
        g.custom_command('delete', 'delete_api_release')

    with self.command_group('apim api revision', apirev_sdk) as g:
        g.custom_command('list', 'list_api_revision')
        g.custom_command('create', 'create_apim_api_revision')

    with self.command_group('apim api versionset', apivs_sdk) as g:
        g.custom_command('list', 'list_api_vs')
        g.custom_show_command('show', 'show_api_vs')
        g.custom_command('create', 'create_api_vs')
        g.generic_update_command('update', custom_func_name='update_api_apivs')
        g.custom_command('delete', 'delete_api_vs')
