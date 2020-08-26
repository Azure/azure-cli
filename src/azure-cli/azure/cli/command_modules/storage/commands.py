# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.storage._client_factory import (cf_sa, cf_blob_container_mgmt, blob_data_service_factory,
                                                               page_blob_service_factory, file_data_service_factory,
                                                               queue_data_service_factory, table_data_service_factory,
                                                               cloud_storage_account_service_factory,
                                                               multi_service_properties_factory,
                                                               cf_mgmt_policy,
                                                               cf_blob_data_gen_update, cf_sa_for_keys,
                                                               cf_mgmt_blob_services, cf_mgmt_file_shares,
                                                               cf_private_link, cf_private_endpoint,
                                                               cf_mgmt_encryption_scope, cf_mgmt_file_services,
                                                               cf_adls_file_system, cf_adls_directory,
                                                               cf_adls_file, cf_adls_service,
                                                               cf_blob_client, cf_blob_lease_client,
                                                               cf_or_policy)
from azure.cli.command_modules.storage.sdkutil import cosmosdb_table_exists
from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.arm import show_exception_handler
from azure.cli.core.profiles import ResourceType


def load_command_table(self, _):  # pylint: disable=too-many-locals, too-many-statements
    storage_account_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#StorageAccountsOperations.{}',
        client_factory=cf_sa,
        resource_type=ResourceType.MGMT_STORAGE
    )

    blob_service_mgmt_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#BlobServicesOperations.{}',
        client_factory=cf_mgmt_blob_services,
        resource_type=ResourceType.MGMT_STORAGE
    )

    file_service_mgmt_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#FileServicesOperations.{}',
        client_factory=cf_mgmt_file_services,
        resource_type=ResourceType.MGMT_STORAGE
    )

    file_shares_mgmt_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#FileSharesOperations.{}',
        client_factory=cf_mgmt_file_shares,
        resource_type=ResourceType.MGMT_STORAGE
    )

    storage_account_sdk_keys = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#StorageAccountsOperations.{}',
        client_factory=cf_sa_for_keys,
        resource_type=ResourceType.MGMT_STORAGE
    )

    private_link_resource_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#PrivateLinkResourcesOperations.{}',
        client_factory=cf_private_link,
        resource_type=ResourceType.MGMT_STORAGE
    )

    private_endpoint_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=cf_private_endpoint,
        resource_type=ResourceType.MGMT_STORAGE
    )

    private_endpoint_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.storage.operations.account#{}',
        client_factory=cf_private_endpoint,
        resource_type=ResourceType.MGMT_STORAGE)

    storage_account_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.storage.operations.account#{}',
        client_factory=cf_sa)

    cloud_data_plane_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storage.common#CloudStorageAccount.{}',
        client_factory=cloud_storage_account_service_factory
    )

    block_blob_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storage.blob.blockblobservice#BlockBlobService.{}',
        client_factory=blob_data_service_factory,
        resource_type=ResourceType.DATA_STORAGE)

    def get_custom_sdk(custom_module, client_factory, resource_type=ResourceType.DATA_STORAGE):
        """Returns a CliCommandType instance with specified operation template based on the given custom module name.
        This is useful when the command is not defined in the default 'custom' module but instead in a module under
        'operations' package."""
        return CliCommandType(
            operations_tmpl='azure.cli.command_modules.storage.operations.{}#'.format(
                custom_module) + '{}',
            client_factory=client_factory,
            resource_type=resource_type
        )

    with self.command_group('storage', command_type=block_blob_sdk,
                            custom_command_type=get_custom_sdk('azcopy', blob_data_service_factory)) as g:
        g.storage_custom_command('remove', 'storage_remove', is_preview=True)

    with self.command_group('storage', custom_command_type=get_custom_sdk('azcopy', None)) as g:
        g.custom_command('copy', 'storage_copy', is_preview=True)

    with self.command_group('storage account', storage_account_sdk, resource_type=ResourceType.MGMT_STORAGE,
                            custom_command_type=storage_account_custom_type) as g:
        g.command('check-name', 'check_name_availability')
        g.custom_command('create', 'create_storage_account')
        g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get_properties')
        g.custom_command('list', 'list_storage_accounts')
        g.custom_command(
            'show-usage', 'show_storage_account_usage', min_api='2018-02-01')
        g.custom_command(
            'show-usage', 'show_storage_account_usage_no_location', max_api='2017-10-01')
        g.custom_command('show-connection-string',
                         'show_storage_account_connection_string')
        g.generic_update_command('update', getter_name='get_properties', setter_name='update',
                                 custom_func_name='update_storage_account', min_api='2016-12-01')
        failover_confirmation = """
        The secondary cluster will become the primary cluster after failover. Please understand the following impact to your storage account before you initiate the failover:
            1. Please check the Last Sync Time using `az storage account show` with `--expand geoReplicationStats` and check the "geoReplicationStats" property. This is the data you may lose if you initiate the failover.
            2. After the failover, your storage account type will be converted to locally redundant storage (LRS). You can convert your account to use geo-redundant storage (GRS).
            3. Once you re-enable GRS/GZRS for your storage account, Microsoft will replicate data to your new secondary region. Replication time is dependent on the amount of data to replicate. Please note that there are bandwidth charges for the bootstrap. Please refer to doc: https://azure.microsoft.com/pricing/details/bandwidth/
        """
        g.command('failover', 'failover', supports_no_wait=True, is_preview=True, min_api='2018-07-01',
                  confirmation=failover_confirmation)

    with self.command_group('storage account', storage_account_sdk_keys, resource_type=ResourceType.MGMT_STORAGE) as g:
        from ._validators import validate_key_name
        g.command('keys renew', 'regenerate_key', validator=validate_key_name,
                  transform=lambda x: getattr(x, 'keys', x))
        g.command('keys list', 'list_keys',
                  transform=lambda x: getattr(x, 'keys', x))
        g.command('revoke-delegation-keys', 'revoke_user_delegation_keys', min_api='2019-04-01')

    with self.command_group('storage account', cloud_data_plane_sdk) as g:
        g.storage_command('generate-sas', 'generate_shared_access_signature')

    encryption_scope_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#EncryptionScopesOperations.{}',
        client_factory=cf_mgmt_encryption_scope,
        resource_type=ResourceType.MGMT_STORAGE
    )

    encryption_scope_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.storage.operations.account#{}',
        client_factory=cf_mgmt_encryption_scope,
        resource_type=ResourceType.MGMT_STORAGE
    )

    with self.command_group('storage account encryption-scope', encryption_scope_sdk,
                            custom_command_type=encryption_scope_custom_type, is_preview=True,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2019-06-01') as g:

        g.custom_command('create', 'create_encryption_scope')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('update', 'update_encryption_scope')

    management_policy_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#ManagementPoliciesOperations.{}',
        client_factory=cf_mgmt_policy,
        resource_type=ResourceType.MGMT_STORAGE
    )

    management_policy_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.storage.operations.account#{}',
        client_factory=cf_mgmt_policy)

    storage_blob_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.storage.operations.blob#{}',
        client_factory=cf_sa,
        resource_type=ResourceType.MGMT_STORAGE)

    with self.command_group('storage account management-policy', management_policy_sdk,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2018-11-01',
                            custom_command_type=management_policy_custom_type) as g:
        g.show_command('show', 'get')
        g.custom_command('create', 'create_management_policies')
        g.generic_update_command('update', getter_name='get',
                                 setter_name='update_management_policies',
                                 setter_type=management_policy_custom_type)
        g.command('delete', 'delete')

    with self.command_group('storage account network-rule', storage_account_sdk,
                            custom_command_type=storage_account_custom_type,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2017-06-01') as g:
        g.custom_command('add', 'add_network_rule')
        g.custom_command('list', 'list_network_rules')
        g.custom_command('remove', 'remove_network_rule')

    or_policy_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#ObjectReplicationPoliciesOperations.{}',
        client_factory=cf_or_policy,
        resource_type=ResourceType.MGMT_STORAGE)

    or_policy_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.storage.operations.account#{}',
        client_factory=cf_or_policy)

    with self.command_group('storage account or-policy', or_policy_sdk, is_preview=True,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2019-06-01',
                            custom_command_type=or_policy_custom_type) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('create', 'create_or_policy')
        g.generic_update_command('update', setter_name='update_or_policy', setter_type=or_policy_custom_type)
        g.command('delete', 'delete')

    with self.command_group('storage account or-policy rule', or_policy_sdk, is_preview=True,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2019-06-01',
                            custom_command_type=or_policy_custom_type) as g:
        g.custom_show_command('show', 'get_or_rule')
        g.custom_command('list', 'list_or_rules')
        g.custom_command('add', 'add_or_rule')
        g.custom_command('update', 'update_or_rule')
        g.custom_command('remove', 'remove_or_rule')

    with self.command_group('storage account private-endpoint-connection', private_endpoint_sdk,
                            custom_command_type=private_endpoint_custom_type, is_preview=True,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2019-06-01') as g:
        from ._validators import validate_private_endpoint_connection_id
        g.command('delete', 'delete', confirmation=True, validator=validate_private_endpoint_connection_id)
        g.show_command('show', 'get', validator=validate_private_endpoint_connection_id)
        g.custom_command('approve', 'approve_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)

    with self.command_group('storage account private-link-resource', private_link_resource_sdk,
                            resource_type=ResourceType.MGMT_STORAGE) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.command('list', 'list_by_storage_account', is_preview=True, min_api='2019-06-01',
                  transform=gen_dict_to_list_transform(key="value"))

    with self.command_group('storage account blob-service-properties', blob_service_mgmt_sdk,
                            custom_command_type=storage_account_custom_type,
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2018-07-01', is_preview=True) as g:
        g.show_command('show', 'get_service_properties')
        g.generic_update_command('update',
                                 getter_name='get_service_properties',
                                 setter_name='set_service_properties',
                                 custom_func_name='update_blob_service_properties')

    with self.command_group('storage account file-service-properties', file_service_mgmt_sdk,
                            custom_command_type=get_custom_sdk('account', client_factory=cf_mgmt_file_services,
                                                               resource_type=ResourceType.MGMT_STORAGE),
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2019-06-01', is_preview=True) as g:
        g.show_command('show', 'get_service_properties')
        g.custom_command('update', 'update_file_service_properties')

    with self.command_group('storage logging', get_custom_sdk('logging', multi_service_properties_factory)) as g:
        from ._transformers import transform_logging_list_output
        g.storage_command('update', 'set_logging')
        g.storage_command('show', 'get_logging',
                          table_transformer=transform_logging_list_output,
                          exception_handler=show_exception_handler)
        g.storage_command('off', 'disable_logging', is_preview=True)

    with self.command_group('storage metrics', get_custom_sdk('metrics', multi_service_properties_factory)) as g:
        from ._transformers import transform_metrics_list_output
        g.storage_command('update', 'set_metrics')
        g.storage_command('show', 'get_metrics',
                          table_transformer=transform_metrics_list_output,
                          exception_handler=show_exception_handler)

    base_blob_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storage.blob.baseblobservice#BaseBlobService.{}',
        client_factory=blob_data_service_factory,
        resource_type=ResourceType.DATA_STORAGE)

    blob_client_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storagev2.blob._blob_client#BlobClient.{}',
        client_factory=cf_blob_client,
        resource_type=ResourceType.DATA_STORAGE_BLOB
    )

    with self.command_group('storage blob', blob_client_sdk, resource_type=ResourceType.DATA_STORAGE_BLOB,
                            min_api='2019-02-02',
                            custom_command_type=get_custom_sdk('blob', client_factory=cf_blob_client,
                                                               resource_type=ResourceType.DATA_STORAGE_BLOB)) as g:
        from ._transformers import transform_blob_json_output
        from ._format import transform_blob_output
        g.storage_custom_command_oauth('show', 'show_blob_v2', transform=transform_blob_json_output,
                                       table_transformer=transform_blob_output,
                                       exception_handler=show_exception_handler)
        g.storage_custom_command_oauth('set-tier', 'set_blob_tier_v2')

    blob_lease_client_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storagev2.blob._lease#BlobLeaseClient.{}',
        client_factory=cf_blob_lease_client,
        resource_type=ResourceType.DATA_STORAGE_BLOB
    )

    with self.command_group('storage blob lease', blob_lease_client_sdk, resource_type=ResourceType.DATA_STORAGE_BLOB,
                            min_api='2019-02-02',
                            custom_command_type=get_custom_sdk('blob', client_factory=cf_blob_lease_client,
                                                               resource_type=ResourceType.DATA_STORAGE_BLOB)) as g:
        g.storage_custom_command_oauth('acquire', 'acquire_blob_lease')
        g.storage_command_oauth('break', 'break_lease')
        g.storage_command_oauth('change', 'change')
        g.storage_custom_command_oauth('renew', 'renew_blob_lease')
        g.storage_command_oauth('release', 'release')

    with self.command_group('storage blob', command_type=block_blob_sdk,
                            custom_command_type=get_custom_sdk('blob', blob_data_service_factory)) as g:
        from ._format import transform_boolean_for_table, transform_blob_output
        from ._transformers import (transform_storage_list_output, transform_url,
                                    create_boolean_result_output_transformer)
        from ._validators import (process_blob_download_batch_parameters, process_blob_delete_batch_parameters,
                                  process_blob_upload_batch_parameters)

        g.storage_custom_command_oauth('list', 'list_blobs', table_transformer=transform_blob_output)
        g.storage_command_oauth(
            'download', 'get_blob_to_path', table_transformer=transform_blob_output)
        g.storage_custom_command_oauth('generate-sas', 'generate_sas_blob_uri')
        g.storage_custom_command_oauth(
            'url', 'create_blob_url', transform=transform_url)
        g.storage_command_oauth('snapshot', 'snapshot_blob')
        g.storage_command_oauth('update', 'set_blob_properties')
        g.storage_command_oauth(
            'exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_command_oauth('delete', 'delete_blob')
        g.storage_command_oauth('undelete', 'undelete_blob',
                                transform=create_boolean_result_output_transformer(
                                    'undeleted'),
                                table_transformer=transform_boolean_for_table, min_api='2017-07-29')
        g.storage_custom_command_oauth('upload', 'upload_blob',
                                       doc_string_source='blob#BlockBlobService.create_blob_from_path')
        g.storage_custom_command_oauth('upload-batch', 'storage_blob_upload_batch',
                                       validator=process_blob_upload_batch_parameters)
        g.storage_custom_command_oauth('download-batch', 'storage_blob_download_batch',
                                       validator=process_blob_download_batch_parameters)
        g.storage_custom_command_oauth('delete-batch', 'storage_blob_delete_batch',
                                       validator=process_blob_delete_batch_parameters)
        g.storage_command_oauth(
            'metadata show', 'get_blob_metadata', exception_handler=show_exception_handler)
        g.storage_command_oauth('metadata update', 'set_blob_metadata')
        g.storage_command_oauth('copy start', 'copy_blob')
        g.storage_command_oauth('copy cancel', 'abort_copy_blob')
        g.storage_custom_command_oauth(
            'copy start-batch', 'storage_blob_copy_batch')

    with self.command_group('storage blob',
                            custom_command_type=get_custom_sdk('blob', cf_blob_client)) as g:
        g.storage_custom_command_oauth('set-tier', 'set_blob_tier_v2')

    with self.command_group('storage blob', storage_account_sdk, resource_type=ResourceType.MGMT_STORAGE,
                            custom_command_type=storage_blob_custom_type) as g:
        g.custom_command('restore', 'restore_blob_ranges', min_api='2019-06-01', is_preview=True, supports_no_wait=True)

    with self.command_group('storage blob incremental-copy',
                            operations_tmpl='azure.multiapi.storage.blob.pageblobservice#PageBlobService.{}',
                            client_factory=page_blob_service_factory,
                            resource_type=ResourceType.DATA_STORAGE,
                            min_api='2016-05-31') as g:
        g.storage_command_oauth('start', 'incremental_copy_blob')

    with self.command_group('storage blob incremental-copy',
                            operations_tmpl='azure.multiapi.storage.blob.blockblobservice#BlockBlobService.{}',
                            client_factory=page_blob_service_factory,
                            resource_type=ResourceType.DATA_STORAGE,
                            min_api='2016-05-31') as g:
        g.storage_command_oauth('cancel', 'abort_copy_blob')

    with self.command_group('storage blob service-properties delete-policy', command_type=base_blob_sdk,
                            min_api='2017-07-29',
                            custom_command_type=get_custom_sdk('blob', blob_data_service_factory)) as g:
        g.storage_command_oauth('show', 'get_blob_service_properties',
                                transform=lambda x: getattr(
                                    x, 'delete_retention_policy', x),
                                exception_handler=show_exception_handler)
        g.storage_custom_command_oauth('update', 'set_delete_policy')

    with self.command_group('storage blob service-properties', command_type=base_blob_sdk) as g:
        g.storage_command_oauth(
            'show', 'get_blob_service_properties', exception_handler=show_exception_handler)
        g.storage_command_oauth('update', generic_update=True, getter_name='get_blob_service_properties',
                                setter_type=get_custom_sdk(
                                    'blob', cf_blob_data_gen_update),
                                setter_name='set_service_properties',
                                client_factory=cf_blob_data_gen_update)

    with self.command_group('storage blob', command_type=block_blob_sdk,
                            custom_command_type=get_custom_sdk('azcopy', blob_data_service_factory)) as g:
        g.storage_custom_command_oauth('sync', 'storage_blob_sync', is_preview=True)

    with self.command_group('storage container', command_type=block_blob_sdk,
                            custom_command_type=get_custom_sdk('blob', blob_data_service_factory)) as g:
        from azure.cli.command_modules.storage._transformers import (transform_storage_list_output,
                                                                     transform_container_permission_output,
                                                                     transform_acl_list_output)
        from azure.cli.command_modules.storage._format import (transform_container_list, transform_boolean_for_table,
                                                               transform_container_show)
        from ._validators import process_container_delete_parameters, validate_client_auth_parameter

        g.storage_command_oauth('list', 'list_containers', transform=transform_storage_list_output,
                                table_transformer=transform_container_list)
        g.storage_custom_command_oauth('delete', 'delete_container', validator=process_container_delete_parameters,
                                       transform=create_boolean_result_output_transformer(
                                           'deleted'),
                                       table_transformer=transform_boolean_for_table)
        g.storage_command_oauth('show', 'get_container_properties', table_transformer=transform_container_show,
                                exception_handler=show_exception_handler)
        g.storage_custom_command_oauth('create', 'create_container', validator=validate_client_auth_parameter,
                                       client_factory=None,
                                       transform=create_boolean_result_output_transformer('created'),
                                       table_transformer=transform_boolean_for_table)
        g.storage_custom_command_oauth('generate-sas', 'generate_container_shared_access_signature',
                                       min_api='2018-11-09')
        g.storage_command_oauth(
            'generate-sas', 'generate_container_shared_access_signature', max_api='2018-03-28')
        g.storage_command_oauth('exists', 'exists', transform=create_boolean_result_output_transformer('exists'),
                                table_transformer=transform_boolean_for_table)
        g.storage_command_oauth('set-permission', 'set_container_acl')
        g.storage_command_oauth('show-permission', 'get_container_acl',
                                transform=transform_container_permission_output)
        g.storage_command_oauth('metadata update', 'set_container_metadata')
        g.storage_command_oauth(
            'metadata show', 'get_container_metadata', exception_handler=show_exception_handler)

        g.storage_command_oauth('lease acquire', 'acquire_container_lease')
        g.storage_command_oauth('lease renew', 'renew_container_lease')
        g.storage_command_oauth('lease release', 'release_container_lease')
        g.storage_command_oauth('lease change', 'change_container_lease')
        g.storage_command_oauth('lease break', 'break_container_lease')

    with self.command_group('storage container', command_type=block_blob_sdk,
                            custom_command_type=get_custom_sdk('acl', blob_data_service_factory)) as g:
        g.storage_custom_command_oauth('policy create', 'create_acl_policy')
        g.storage_custom_command_oauth('policy delete', 'delete_acl_policy')
        g.storage_custom_command_oauth(
            'policy update', 'set_acl_policy', min_api='2017-04-17')
        g.storage_custom_command_oauth(
            'policy show', 'get_acl_policy', exception_handler=show_exception_handler)
        g.storage_custom_command_oauth(
            'policy list', 'list_acl_policies', table_transformer=transform_acl_list_output)

    blob_container_mgmt_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations#BlobContainersOperations.{}',
        client_factory=cf_blob_container_mgmt,
        resource_type=ResourceType.MGMT_STORAGE
    )

    with self.command_group('storage container immutability-policy', command_type=blob_container_mgmt_sdk,
                            min_api='2018-02-01') as g:
        from azure.cli.command_modules.storage._transformers import transform_immutability_policy
        g.show_command('show', 'get_immutability_policy',
                       transform=transform_immutability_policy)
        g.command('create', 'create_or_update_immutability_policy')
        g.command('delete', 'delete_immutability_policy',
                  transform=lambda x: None)
        g.command('lock', 'lock_immutability_policy')
        g.command('extend', 'extend_immutability_policy')

    with self.command_group('storage container legal-hold', command_type=blob_container_mgmt_sdk,
                            min_api='2018-02-01') as g:
        g.command('set', 'set_legal_hold')
        g.command('clear', 'clear_legal_hold')
        g.show_command(
            'show', 'get', transform=lambda x: getattr(x, 'legal_hold', x))

    file_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storage.file.fileservice#FileService.{}',
        client_factory=file_data_service_factory,
        resource_type=ResourceType.DATA_STORAGE)

    with self.command_group('storage share-rm', command_type=file_shares_mgmt_sdk,
                            custom_command_type=get_custom_sdk('file',
                                                               cf_mgmt_file_shares,
                                                               resource_type=ResourceType.MGMT_STORAGE),
                            resource_type=ResourceType.MGMT_STORAGE, min_api='2019-04-01', is_preview=True) as g:
        g.custom_command('create', 'create_share_rm')
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('exists', '_file_share_exists', transform=create_boolean_result_output_transformer('exists'))
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='update', setter_arg_name='file_share',
                                 custom_func_name='update_share_rm')

    with self.command_group('storage share', command_type=file_sdk,
                            custom_command_type=get_custom_sdk('file', file_data_service_factory)) as g:
        from ._format import (transform_share_list,
                              transform_boolean_for_table)
        g.storage_command('list', 'list_shares', transform=transform_storage_list_output,
                          table_transformer=transform_share_list)
        g.storage_command('create', 'create_share', transform=create_boolean_result_output_transformer('created'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command('delete', 'delete_share', transform=create_boolean_result_output_transformer('deleted'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command(
            'generate-sas', 'generate_share_shared_access_signature')
        g.storage_command('stats', 'get_share_stats')
        g.storage_command('show', 'get_share_properties',
                          exception_handler=show_exception_handler)
        g.storage_command('update', 'set_share_properties')
        g.storage_command('snapshot', 'snapshot_share', min_api='2017-04-17')
        g.storage_command(
            'exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_custom_command(
            'url', 'create_share_url', transform=transform_url)

        g.storage_command('metadata show', 'get_share_metadata',
                          exception_handler=show_exception_handler)
        g.storage_command('metadata update', 'set_share_metadata')

    with self.command_group('storage share policy', command_type=file_sdk,
                            custom_command_type=get_custom_sdk('acl', file_data_service_factory)) as g:
        g.storage_custom_command('create', 'create_acl_policy')
        g.storage_custom_command('delete', 'delete_acl_policy')
        g.storage_custom_command(
            'show', 'get_acl_policy', exception_handler=show_exception_handler)
        g.storage_custom_command(
            'list', 'list_acl_policies', table_transformer=transform_acl_list_output)
        g.storage_custom_command('update', 'set_acl_policy')

    with self.command_group('storage directory', command_type=file_sdk,
                            custom_command_type=get_custom_sdk('directory', file_data_service_factory)) as g:
        from ._format import transform_file_directory_result, transform_file_output

        g.storage_command('create', 'create_directory', transform=create_boolean_result_output_transformer('created'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command('delete', 'delete_directory', transform=create_boolean_result_output_transformer('deleted'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command('show', 'get_directory_properties', table_transformer=transform_file_output,
                          exception_handler=show_exception_handler)
        g.storage_command(
            'exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_command('metadata show', 'get_directory_metadata',
                          exception_handler=show_exception_handler)
        g.storage_command('metadata update', 'set_directory_metadata')
        g.storage_custom_command('list', 'list_share_directories',
                                 transform=transform_file_directory_result(
                                     self.cli_ctx),
                                 table_transformer=transform_file_output,
                                 doc_string_source='file#FileService.list_directories_and_files')

    with self.command_group('storage file', command_type=file_sdk,
                            custom_command_type=get_custom_sdk('file', file_data_service_factory)) as g:
        from ._format import transform_file_directory_result, transform_boolean_for_table, transform_file_output
        from ._transformers import transform_url
        g.storage_custom_command('list', 'list_share_files', transform=transform_file_directory_result(self.cli_ctx),
                                 table_transformer=transform_file_output,
                                 doc_string_source='file#FileService.list_directories_and_files')
        g.storage_command('delete', 'delete_file', transform=create_boolean_result_output_transformer('deleted'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command('resize', 'resize_file')
        g.storage_custom_command(
            'url', 'create_file_url', transform=transform_url)
        g.storage_command(
            'generate-sas', 'generate_file_shared_access_signature')
        g.storage_command('show', 'get_file_properties', table_transformer=transform_file_output,
                          exception_handler=show_exception_handler)
        g.storage_command('update', 'set_file_properties')
        g.storage_command(
            'exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_command('download', 'get_file_to_path')
        g.storage_command('upload', 'create_file_from_path')
        g.storage_command('metadata show', 'get_file_metadata',
                          exception_handler=show_exception_handler)
        g.storage_command('metadata update', 'set_file_metadata')
        g.storage_command('copy start', 'copy_file')
        g.storage_command('copy cancel', 'abort_copy_file')
        g.storage_custom_command('upload-batch', 'storage_file_upload_batch')
        g.storage_custom_command(
            'download-batch', 'storage_file_download_batch')
        g.storage_custom_command('delete-batch', 'storage_file_delete_batch')
        g.storage_custom_command('copy start-batch', 'storage_file_copy_batch')

    with self.command_group('storage cors', get_custom_sdk('cors', multi_service_properties_factory)) as g:
        from ._transformers import transform_cors_list_output

        g.storage_command('add', 'add_cors')
        g.storage_command('clear', 'clear_cors')
        g.storage_command('list', 'list_cors',
                          transform=transform_cors_list_output)

    queue_sdk = CliCommandType(operations_tmpl='azure.multiapi.storage.queue.queueservice#QueueService.{}',
                               client_factory=queue_data_service_factory,
                               resource_type=ResourceType.DATA_STORAGE)

    with self.command_group('storage queue', queue_sdk,
                            custom_command_type=get_custom_sdk('acl', queue_data_service_factory)) as g:
        from ._format import transform_boolean_for_table
        from ._transformers import create_boolean_result_output_transformer

        g.storage_command_oauth('list', 'list_queues',
                                transform=transform_storage_list_output)
        g.storage_command_oauth('create', 'create_queue', transform=create_boolean_result_output_transformer('created'),
                                table_transformer=transform_boolean_for_table)
        g.storage_command_oauth('delete', 'delete_queue', transform=create_boolean_result_output_transformer('deleted'),
                                table_transformer=transform_boolean_for_table)
        g.storage_command_oauth(
            'generate-sas', 'generate_queue_shared_access_signature')
        g.storage_command_oauth(
            'stats', 'get_queue_service_stats', min_api='2016-05-31')
        g.storage_command_oauth(
            'exists', 'exists', transform=create_boolean_result_output_transformer('exists'))

        g.storage_command_oauth(
            'metadata show', 'get_queue_metadata', exception_handler=show_exception_handler)
        g.storage_command_oauth('metadata update', 'set_queue_metadata')

        g.storage_custom_command_oauth('policy create', 'create_acl_policy')
        g.storage_custom_command_oauth('policy delete', 'delete_acl_policy')
        g.storage_custom_command_oauth(
            'policy show', 'get_acl_policy', exception_handler=show_exception_handler)
        g.storage_custom_command_oauth(
            'policy list', 'list_acl_policies', table_transformer=transform_acl_list_output)
        g.storage_custom_command_oauth('policy update', 'set_acl_policy')

    with self.command_group('storage message', queue_sdk) as g:
        from ._transformers import create_boolean_result_output_transformer
        from ._format import transform_message_show

        g.storage_command_oauth('put', 'put_message')
        g.storage_command_oauth('get', 'get_messages',
                                table_transformer=transform_message_show)
        g.storage_command_oauth('peek', 'peek_messages',
                                table_transformer=transform_message_show)
        g.storage_command_oauth('delete', 'delete_message',
                                transform=create_boolean_result_output_transformer(
                                    'deleted'),
                                table_transformer=transform_boolean_for_table)
        g.storage_command_oauth('clear', 'clear_messages')
        g.storage_command_oauth('update', 'update_message')

    if cosmosdb_table_exists(self.cli_ctx):
        table_sdk = CliCommandType(operations_tmpl='azure.multiapi.cosmosdb.table.tableservice#TableService.{}',
                                   client_factory=table_data_service_factory,
                                   resource_type=ResourceType.DATA_COSMOS_TABLE)
    else:
        table_sdk = CliCommandType(operations_tmpl='azure.multiapi.storage.table.tableservice#TableService.{}',
                                   client_factory=table_data_service_factory,
                                   resource_type=ResourceType.DATA_COSMOS_TABLE)

    with self.command_group('storage table', table_sdk,
                            custom_command_type=get_custom_sdk('acl', table_data_service_factory)) as g:
        from ._format import transform_boolean_for_table
        from ._transformers import create_boolean_result_output_transformer

        g.storage_command('create', 'create_table', transform=create_boolean_result_output_transformer('created'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command('delete', 'delete_table', transform=create_boolean_result_output_transformer('deleted'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command(
            'exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_command(
            'generate-sas', 'generate_table_shared_access_signature')
        g.storage_command('list', 'list_tables',
                          transform=transform_storage_list_output)
        g.storage_command('stats', 'get_table_service_stats',
                          min_api='2016-05-31')

        g.storage_custom_command('policy create', 'create_acl_policy')
        g.storage_custom_command('policy delete', 'delete_acl_policy')
        g.storage_custom_command(
            'policy show', 'get_acl_policy', exception_handler=show_exception_handler)
        g.storage_custom_command(
            'policy list', 'list_acl_policies', table_transformer=transform_acl_list_output)
        g.storage_custom_command('policy update', 'set_acl_policy')

    with self.command_group('storage entity', table_sdk,
                            custom_command_type=get_custom_sdk('table', table_data_service_factory)) as g:
        from ._format import transform_boolean_for_table, transform_entity_show
        from ._transformers import (create_boolean_result_output_transformer,
                                    transform_entity_query_output,
                                    transform_entities_result,
                                    transform_entity_result)

        g.storage_command('query',
                          'query_entities',
                          table_transformer=transform_entity_query_output,
                          transform=transform_entities_result)
        g.storage_command('replace', 'update_entity')
        g.storage_command('merge', 'merge_entity')
        g.storage_command('delete', 'delete_entity', transform=create_boolean_result_output_transformer('deleted'),
                          table_transformer=transform_boolean_for_table)
        g.storage_command('show', 'get_entity', table_transformer=transform_entity_show,
                          exception_handler=show_exception_handler,
                          transform=transform_entity_result)
        g.storage_custom_command('insert', 'insert_table_entity')

    adls_service_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storagev2.filedatalake._data_lake_service_client#DataLakeServiceClient.{}',
        client_factory=cf_adls_service,
        resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE
    )

    adls_fs_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storagev2.filedatalake._file_system_client#FileSystemClient.{}',
        client_factory=cf_adls_file_system,
        resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE
    )
    adls_directory_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storagev2.filedatalake._data_lake_directory_client#DataLakeDirectoryClient.{}',
        client_factory=cf_adls_directory,
        resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE
    )
    adls_file_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storagev2.filedatalake._data_lake_file_client#DataLakeFileClient.{}',
        client_factory=cf_adls_file,
        resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE
    )

    with self.command_group('storage fs', adls_fs_sdk, resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE,
                            custom_command_type=get_custom_sdk('filesystem', cf_adls_file_system),
                            min_api='2018-11-09') as g:
        from ._transformers import transform_fs_list_public_access_output, transform_fs_public_access_output, \
            transform_metadata
        g.storage_command_oauth('create', 'create_file_system')
        g.storage_command_oauth('list', 'list_file_systems', command_type=adls_service_sdk,
                                transform=transform_fs_list_public_access_output)
        g.storage_command_oauth('show', 'get_file_system_properties', exception_handler=show_exception_handler,
                                transform=transform_fs_public_access_output)
        g.storage_command_oauth('delete', 'delete_file_system', confirmation=True)
        g.storage_custom_command_oauth('exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_command_oauth('metadata update', 'set_file_system_metadata')
        g.storage_command_oauth('metadata show', 'get_file_system_properties', exception_handler=show_exception_handler,
                                transform=transform_metadata)

    with self.command_group('storage fs directory', adls_directory_sdk,
                            custom_command_type=get_custom_sdk('fs_directory', cf_adls_directory),
                            resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE, min_api='2018-11-09') as g:
        from ._transformers import transform_storage_list_output, transform_metadata
        g.storage_command_oauth('create', 'create_directory')
        g.storage_custom_command_oauth('exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_custom_command_oauth('show', 'get_directory_properties', exception_handler=show_exception_handler)
        g.storage_command_oauth('delete', 'delete_directory', confirmation=True)
        g.storage_command_oauth('move', 'rename_directory')
        g.storage_custom_command_oauth('list', 'list_fs_directories', client_factory=cf_adls_file_system,
                                       transform=transform_storage_list_output)
        g.storage_command_oauth('metadata update', 'set_metadata')
        g.storage_command_oauth('metadata show', 'get_directory_properties', exception_handler=show_exception_handler,
                                transform=transform_metadata)

    with self.command_group('storage fs file', adls_file_sdk, resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE,
                            custom_command_type=get_custom_sdk('fs_file', cf_adls_file), min_api='2018-11-09') as g:
        from ._transformers import transform_storage_list_output, create_boolean_result_output_transformer
        g.storage_command_oauth('create', 'create_file')
        g.storage_custom_command_oauth('upload', 'upload_file')
        g.storage_custom_command_oauth('exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_custom_command_oauth('append', 'append_file')
        g.storage_custom_command_oauth('download', 'download_file')
        g.storage_custom_command_oauth('show', 'get_file_properties', exception_handler=show_exception_handler)
        g.storage_custom_command_oauth('list', 'list_fs_files',
                                       custom_command_type=get_custom_sdk('fs_file', cf_adls_file_system),
                                       transform=transform_storage_list_output)
        g.storage_command_oauth('move', 'rename_file')
        g.storage_command_oauth('delete', 'delete_file', confirmation=True)
        g.storage_command_oauth('metadata update', 'set_metadata')
        g.storage_command_oauth('metadata show', 'get_file_properties', exception_handler=show_exception_handler,
                                transform=transform_metadata)

    with self.command_group('storage fs access', adls_directory_sdk,
                            resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE, min_api='2018-11-09') as g:
        from ._transformers import transform_fs_access_output
        g.storage_command_oauth('set', 'set_access_control')
        g.storage_command_oauth('show', 'get_access_control', transform=transform_fs_access_output)
