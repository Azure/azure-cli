# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client, \
    prepare_client_kwargs_track2
from azure.cli.core.profiles import ResourceType, get_sdk

MISSING_CREDENTIALS_ERROR_MESSAGE = """
Missing credentials to access storage service. The following variations are accepted:
    (1) account name and key (--account-name and --account-key options or
        set AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY environment variables)
    (2) account name and SAS token (--sas-token option used with either the --account-name
        option or AZURE_STORAGE_ACCOUNT environment variable)
    (3) account name (--account-name option or AZURE_STORAGE_ACCOUNT environment variable;
        this will make calls to query for a storage account key using login credentials)
    (4) connection string (--connection-string option or
        set AZURE_STORAGE_CONNECTION_STRING environment variable); some shells will require
        quoting to preserve literal character interpretation.
"""


def get_storage_data_service_client(cli_ctx, service, name=None, key=None, connection_string=None, sas_token=None,
                                    socket_timeout=None, token_credential=None, location_mode=None):
    return get_data_service_client(cli_ctx, service, name, key, connection_string, sas_token,
                                   socket_timeout=socket_timeout,
                                   token_credential=token_credential,
                                   endpoint_suffix=cli_ctx.cloud.suffixes.storage_endpoint,
                                   location_mode=location_mode)


def storage_client_factory(cli_ctx, **_):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)


def multi_service_properties_factory(cli_ctx, kwargs):
    """Create multiple data services properties instance based on the services option"""
    from .services_wrapper import ServiceProperties

    services = kwargs.pop('services', [])

    def create_service(service):
        service_to_param = {'b': ['blob', cf_blob_service], 'f': ['file', cf_share_service],
                            'q': ['queue', cf_queue_service],
                            't': ['table', cf_table_service]}
        name, client = service_to_param[service]
        return ServiceProperties(cli_ctx, name, client(cli_ctx, ori_kwargs.copy()))

    ori_kwargs = kwargs.copy()

    for i in ['connection_string', 'account_name', 'account_key', 'sas_token', 'account_url', 'token_credential']:
        kwargs.pop(i, None)

    return [create_service(s) for s in services]


def cf_sa(cli_ctx, _):
    return storage_client_factory(cli_ctx).storage_accounts


def cf_sa_blob_inventory(cli_ctx, _):
    return storage_client_factory(cli_ctx).blob_inventory_policies


def cf_sa_for_keys(cli_ctx, _):
    from knack.log import get_logger
    logger = get_logger(__name__)
    logger.debug('Disable HTTP logging to avoid having storage keys in debug logs')
    client = storage_client_factory(cli_ctx)
    return client.storage_accounts


def cf_mgmt_policy(cli_ctx, _):
    return storage_client_factory(cli_ctx).management_policies


def cf_blob_container_mgmt(cli_ctx, _):
    return storage_client_factory(cli_ctx).blob_containers


def cf_mgmt_blob_services(cli_ctx, _):
    return storage_client_factory(cli_ctx).blob_services


def cf_mgmt_file_services(cli_ctx, _):
    return storage_client_factory(cli_ctx).file_services


def cf_mgmt_file_shares(cli_ctx, _):
    return storage_client_factory(cli_ctx).file_shares


def cf_private_link(cli_ctx, _):
    return storage_client_factory(cli_ctx).private_link_resources


def cf_private_endpoint(cli_ctx, _):
    return storage_client_factory(cli_ctx).private_endpoint_connections


def cf_mgmt_encryption_scope(cli_ctx, _):
    return storage_client_factory(cli_ctx).encryption_scopes


def get_account_url(cli_ctx, account_name, service):
    from knack.util import CLIError
    if account_name is None:
        raise CLIError("Please provide storage account name or connection string.")
    storage_endpoint = cli_ctx.cloud.suffixes.storage_endpoint
    return "https://{}.{}.{}".format(account_name, service, storage_endpoint)


def _config_location_mode(kwargs, client_kwargs):
    location_mode = kwargs.pop('location_mode', None)
    if location_mode:
        client_kwargs['_location_mode'] = location_mode
    return client_kwargs


def cf_blob_service(cli_ctx, kwargs):
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs = _config_location_mode(kwargs, client_kwargs)
    t_blob_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                             '_blob_service_client#BlobServiceClient')
    connection_string = kwargs.pop('connection_string', None)
    account_name = kwargs.pop('account_name', None)
    account_url = kwargs.pop('account_url', None)
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)

    if connection_string:
        try:
            return t_blob_service.from_connection_string(conn_str=connection_string, **client_kwargs)
        except ValueError as err:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            raise InvalidArgumentValueError('Invalid connection string: {}, err detail: {}'
                                            .format(connection_string, str(err)),
                                            recommendation='Try `az storage account show-connection-string` '
                                                           'to get a valid connection string')
    if not account_url:
        account_url = get_account_url(cli_ctx, account_name=account_name, service='blob')

    credential = account_key or sas_token or token_credential
    if sas_token and 'sduoid=' in sas_token and token_credential:
        credential = token_credential
        account_url = account_url + '?' + sas_token

    if account_name and account_key:
        # For non-standard account URL such as Edge Zone, account_name can't be parsed from account_url. Use credential
        # dict instead.
        credential = {'account_key': account_key, 'account_name': account_name}

    return t_blob_service(account_url=account_url, credential=credential,
                          connection_timeout=kwargs.pop('connection_timeout', None), **client_kwargs)


def get_credential(client_url, kwargs):
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)
    credential = account_key or sas_token or token_credential
    if sas_token and 'sduoid=' in sas_token and token_credential:
        credential = token_credential
        client_url = client_url + '?' + sas_token
    return client_url, credential


def cf_blob_client(cli_ctx, kwargs):
    # track2 partial migration
    if kwargs.get('blob_url'):
        t_blob_client = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_BLOB, '_blob_client#BlobClient')
        blob_url, credential = get_credential(kwargs.pop('blob_url'), kwargs)
        # del unused kwargs
        kwargs.pop('connection_string')
        kwargs.pop('account_name')
        kwargs.pop('account_url')
        kwargs.pop('container_name')
        kwargs.pop('blob_name')
        return t_blob_client.from_blob_url(blob_url=blob_url,
                                           credential=credential,
                                           snapshot=kwargs.pop('snapshot', None),
                                           connection_timeout=kwargs.pop('connection_timeout', None))
    if 'blob_url' in kwargs:
        kwargs.pop('blob_url')

    return cf_blob_service(cli_ctx, kwargs).get_blob_client(container=kwargs.pop('container_name'),
                                                            blob=kwargs.pop('blob_name'),
                                                            snapshot=kwargs.pop('snapshot', None))


def cf_blob_lease_client(cli_ctx, kwargs):
    t_lease_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_BLOB, '_lease#BlobLeaseClient')
    blob_client = cf_blob_service(cli_ctx, kwargs).get_blob_client(container=kwargs.pop('container_name', None),
                                                                   blob=kwargs.pop('blob_name', None))
    return t_lease_service(client=blob_client, lease_id=kwargs.pop('lease_id', None))


def cf_container_client(cli_ctx, kwargs):
    return cf_blob_service(cli_ctx, kwargs).get_container_client(container=kwargs.pop('container_name', None))


def cf_container_lease_client(cli_ctx, kwargs):
    t_lease_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_BLOB, '_lease#BlobLeaseClient')
    container_client = cf_container_client(cli_ctx, kwargs)
    return t_lease_service(client=container_client, lease_id=kwargs.pop('lease_id', None))


def cf_adls_service(cli_ctx, kwargs):
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs = _config_location_mode(kwargs, client_kwargs)
    t_adls_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_FILEDATALAKE,
                             '_data_lake_service_client#DataLakeServiceClient')
    connection_string = kwargs.pop('connection_string', None)
    account_name = kwargs.pop('account_name', None)
    account_url = kwargs.pop('account_url', None)
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)

    location_mode = kwargs.pop('location_mode', None)
    if location_mode:
        client_kwargs['_location_mode'] = location_mode

    if connection_string:
        return t_adls_service.from_connection_string(conn_str=connection_string, **client_kwargs)
    if not account_url:
        account_url = get_account_url(cli_ctx, account_name=account_name, service='dfs')
    credential = account_key or sas_token or token_credential
    if sas_token and 'sduoid=' in sas_token and token_credential:
        credential = token_credential
        account_url = account_url + '?' + sas_token

    return t_adls_service(account_url=account_url, credential=credential, **client_kwargs)


def cf_adls_file_system(cli_ctx, kwargs):
    return cf_adls_service(cli_ctx, kwargs).get_file_system_client(file_system=kwargs.pop('file_system_name'))


def cf_adls_directory(cli_ctx, kwargs):
    return cf_adls_file_system(cli_ctx, kwargs).get_directory_client(directory=kwargs.pop('directory_path'))


def cf_adls_file(cli_ctx, kwargs):
    return cf_adls_service(cli_ctx, kwargs).get_file_client(file_system=kwargs.pop('file_system_name', None),
                                                            file_path=kwargs.pop('path', None))


def cf_or_policy(cli_ctx, _):
    return storage_client_factory(cli_ctx).object_replication_policies


def cf_queue_service(cli_ctx, kwargs):
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs = _config_location_mode(kwargs, client_kwargs)
    t_queue_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_QUEUE, '_queue_service_client#QueueServiceClient')
    connection_string = kwargs.pop('connection_string', None)
    account_name = kwargs.pop('account_name', None)
    account_url = kwargs.pop('account_url', None)
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)

    if connection_string:
        return t_queue_service.from_connection_string(conn_str=connection_string, **client_kwargs)
    if not account_url:
        account_url = get_account_url(cli_ctx, account_name=account_name, service='queue')
    credential = account_key or sas_token or token_credential
    if sas_token and 'sduoid=' in sas_token and token_credential:
        credential = token_credential
        account_url = account_url + '?' + sas_token

    return t_queue_service(account_url=account_url, credential=credential, **client_kwargs)


def cf_queue_client(cli_ctx, kwargs):
    return cf_queue_service(cli_ctx, kwargs).get_queue_client(queue=kwargs.pop('queue_name'))


def cf_table_service(cli_ctx, kwargs):
    from azure.data.tables._table_service_client import TableServiceClient
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs = _config_location_mode(kwargs, client_kwargs)
    connection_string = kwargs.pop('connection_string', None)
    account_name = kwargs.pop('account_name', None)
    account_url = kwargs.pop('account_url', None)
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)

    if connection_string:
        return TableServiceClient.from_connection_string(conn_str=connection_string, **client_kwargs)
    if not account_url:
        account_url = get_account_url(cli_ctx, account_name=account_name, service='table')
    if account_key:
        from azure.core.credentials import AzureNamedKeyCredential
        credential = AzureNamedKeyCredential(name=account_name, key=account_key)
    elif sas_token:
        from azure.core.credentials import AzureSasCredential
        credential = AzureSasCredential(signature=sas_token)
    else:
        credential = token_credential

    return TableServiceClient(endpoint=account_url, credential=credential, **client_kwargs)


def cf_table_client(cli_ctx, kwargs):
    return cf_table_service(cli_ctx, kwargs).get_table_client(table_name=kwargs.pop('table_name'))


def cf_share_service(cli_ctx, kwargs):
    from azure.cli.core.azclierror import RequiredArgumentMissingError
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs = _config_location_mode(kwargs, client_kwargs)
    t_share_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_FILESHARE, '_share_service_client#ShareServiceClient')
    connection_string = kwargs.pop('connection_string', None)
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)
    account_name = kwargs.pop('account_name', None)
    account_url = kwargs.pop('account_url', None)
    enable_file_backup_request_intent = kwargs.pop('enable_file_backup_request_intent', None)

    disallow_trailing_dot = kwargs.pop('disallow_trailing_dot', None)
    disallow_source_trailing_dot = kwargs.pop('disallow_source_trailing_dot', None)

    if disallow_trailing_dot is not None:
        client_kwargs["allow_trailing_dot"] = not disallow_trailing_dot
    if disallow_source_trailing_dot is not None:
        copy_url = kwargs.get("copy_source")
        import re
        if kwargs.get("source_share") or (copy_url and re.match(r"https?:\/\/.*?\.file\..*", copy_url)):
            client_kwargs["allow_source_trailing_dot"] = not disallow_source_trailing_dot

    if token_credential is not None and not enable_file_backup_request_intent:
        raise RequiredArgumentMissingError("--enable-file-backup-request-intent is required for file share OAuth")
    if enable_file_backup_request_intent:
        client_kwargs['token_intent'] = 'backup'
    if connection_string:
        return t_share_service.from_connection_string(conn_str=connection_string, **client_kwargs)
    if not account_url:
        account_url = get_account_url(cli_ctx, account_name=account_name, service='file')
    credential = account_key or sas_token or token_credential
    if sas_token and 'sduoid=' in sas_token and token_credential:
        credential = token_credential
        account_url = account_url + '?' + sas_token

    return t_share_service(account_url=account_url, credential=credential, **client_kwargs)


def cf_share_client(cli_ctx, kwargs):
    return cf_share_service(cli_ctx, kwargs).get_share_client(share=kwargs.pop('share_name'),
                                                              snapshot=kwargs.pop('snapshot', None))


def cf_share_directory_client(cli_ctx, kwargs):
    return cf_share_client(cli_ctx, kwargs).get_directory_client(directory_path=kwargs.pop('directory_path'))


def cf_share_file_client(cli_ctx, kwargs):
    if kwargs.get('file_url'):
        from azure.cli.core.azclierror import RequiredArgumentMissingError
        t_file_client = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_FILESHARE, '_file_client#ShareFileClient')
        token_credential = kwargs.get('token_credential')
        enable_file_backup_request_intent = kwargs.pop('enable_file_backup_request_intent', None)
        token_intent = 'backup' if enable_file_backup_request_intent else None
        if token_credential is not None and not enable_file_backup_request_intent:
            raise RequiredArgumentMissingError("--enable-file-backup-request-intent is required for file share OAuth")
        file_url, credential = get_credential(kwargs.pop('file_url'), kwargs)
        # del unused kwargs
        kwargs.pop('connection_string')
        kwargs.pop('account_name')
        kwargs.pop('account_url')
        kwargs.pop('share_name')
        kwargs.pop('directory_name')
        kwargs.pop('file_name')

        disallow_trailing_dot = kwargs.pop('disallow_trailing_dot', None)
        disallow_source_trailing_dot = kwargs.pop('disallow_source_trailing_dot', None)

        client_kwargs = {}
        if disallow_trailing_dot is not None:
            client_kwargs["allow_trailing_dot"] = not disallow_trailing_dot
        if disallow_source_trailing_dot is not None:
            copy_url = kwargs.get("copy_source")
            import re
            if kwargs.get("source_share") or (copy_url and re.match(r"https?:\/\/.*?\.file\..*", copy_url)):
                client_kwargs["allow_source_trailing_dot"] = not disallow_source_trailing_dot

        return t_file_client.from_file_url(file_url=file_url,
                                           credential=credential, token_intent=token_intent, **client_kwargs)
    if 'file_url' in kwargs:
        kwargs.pop('file_url')

    return cf_share_client(cli_ctx, kwargs).get_directory_client(directory_path=kwargs.pop('directory_name')).\
        get_file_client(file_name=kwargs.pop('file_name'))


def cf_local_users(cli_ctx, _):
    return storage_client_factory(cli_ctx).local_users
