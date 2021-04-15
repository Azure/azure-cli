# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client, \
    prepare_client_kwargs_track2
from azure.cli.core.profiles import ResourceType, get_sdk

from azure.cli.command_modules.storage.sdkutil import get_table_data_type

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


def generic_data_service_factory(cli_ctx, service, name=None, key=None, connection_string=None, sas_token=None,
                                 socket_timeout=None, token_credential=None, location_mode=None):
    try:
        return get_storage_data_service_client(cli_ctx, service, name, key, connection_string, sas_token,
                                               socket_timeout, token_credential, location_mode=location_mode)
    except ValueError as val_exception:
        _ERROR_STORAGE_MISSING_INFO = get_sdk(cli_ctx, ResourceType.DATA_STORAGE,
                                              'common._error#_ERROR_STORAGE_MISSING_INFO')
        message = str(val_exception)
        if message == _ERROR_STORAGE_MISSING_INFO:
            message = MISSING_CREDENTIALS_ERROR_MESSAGE
        from knack.util import CLIError
        raise CLIError(message)


def storage_client_factory(cli_ctx, **_):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)


def file_data_service_factory(cli_ctx, kwargs):
    t_file_svc = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'file#FileService')
    return generic_data_service_factory(cli_ctx, t_file_svc, kwargs.pop('account_name', None),
                                        kwargs.pop('account_key', None),
                                        connection_string=kwargs.pop('connection_string', None),
                                        sas_token=kwargs.pop('sas_token', None))


def page_blob_service_factory(cli_ctx, kwargs):
    t_page_blob_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'blob.pageblobservice#PageBlobService')
    return generic_data_service_factory(cli_ctx, t_page_blob_service, kwargs.pop('account_name', None),
                                        kwargs.pop('account_key', None),
                                        connection_string=kwargs.pop('connection_string', None),
                                        sas_token=kwargs.pop('sas_token', None),
                                        token_credential=kwargs.pop('token_credential', None))


def blob_data_service_factory(cli_ctx, kwargs):
    if 'encryption_scope' in kwargs and kwargs['encryption_scope']:
        return cf_blob_client(cli_ctx, kwargs)
    from azure.cli.command_modules.storage.sdkutil import get_blob_service_by_type
    blob_type = kwargs.get('blob_type')
    blob_service = get_blob_service_by_type(cli_ctx, blob_type) or get_blob_service_by_type(cli_ctx, 'block')

    return generic_data_service_factory(cli_ctx, blob_service, kwargs.pop('account_name', None),
                                        kwargs.pop('account_key', None),
                                        connection_string=kwargs.pop('connection_string', None),
                                        sas_token=kwargs.pop('sas_token', None),
                                        socket_timeout=kwargs.pop('socket_timeout', None),
                                        token_credential=kwargs.pop('token_credential', None),
                                        location_mode=kwargs.pop('location_mode', None))


def table_data_service_factory(cli_ctx, kwargs):
    return generic_data_service_factory(cli_ctx,
                                        get_table_data_type(cli_ctx, 'table', 'TableService'),
                                        kwargs.pop('account_name', None),
                                        kwargs.pop('account_key', None),
                                        connection_string=kwargs.pop('connection_string', None),
                                        sas_token=kwargs.pop('sas_token', None))


def queue_data_service_factory(cli_ctx, kwargs):
    t_queue_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'queue#QueueService')
    return generic_data_service_factory(
        cli_ctx, t_queue_service,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None),
        token_credential=kwargs.pop('token_credential', None))


def cloud_storage_account_service_factory(cli_ctx, kwargs):
    t_cloud_storage_account = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'common#CloudStorageAccount')
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    sas_token = kwargs.pop('sas_token', None)
    kwargs.pop('connection_string', None)
    return t_cloud_storage_account(account_name, account_key, sas_token)


def multi_service_properties_factory(cli_ctx, kwargs):
    """Create multiple data services properties instance based on the services option"""
    from .services_wrapper import ServiceProperties

    t_base_blob_service, t_file_service, t_queue_service, = get_sdk(cli_ctx, ResourceType.DATA_STORAGE,
                                                                    'blob.baseblobservice#BaseBlobService',
                                                                    'file#FileService', 'queue#QueueService')

    t_table_service = get_table_data_type(cli_ctx, 'table', 'TableService')

    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    connection_string = kwargs.pop('connection_string', None)
    sas_token = kwargs.pop('sas_token', None)
    services = kwargs.pop('services', [])

    def get_creator(name, service_type):
        return lambda: ServiceProperties(cli_ctx, name, service_type, account_name, account_key, connection_string,
                                         sas_token)

    creators = {'b': get_creator('blob', t_base_blob_service), 'f': get_creator('file', t_file_service),
                'q': get_creator('queue', t_queue_service), 't': get_creator('table', t_table_service)}

    return [creators[s]() for s in services]


def cf_sa(cli_ctx, _):
    return storage_client_factory(cli_ctx).storage_accounts


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


def cf_blob_data_gen_update(cli_ctx, kwargs):
    return blob_data_service_factory(cli_ctx, kwargs.copy())


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

    account_url = get_account_url(cli_ctx, account_name=account_name, service='blob')
    credential = account_key or sas_token or token_credential

    return t_blob_service(account_url=account_url, credential=credential, **client_kwargs)


def cf_blob_client(cli_ctx, kwargs):
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


def cf_adls_service(cli_ctx, kwargs):
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs = _config_location_mode(kwargs, client_kwargs)
    t_adls_service = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_FILEDATALAKE,
                             '_data_lake_service_client#DataLakeServiceClient')
    connection_string = kwargs.pop('connection_string', None)
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)

    location_mode = kwargs.pop('location_mode', None)
    if location_mode:
        client_kwargs['_location_mode'] = location_mode

    if connection_string:
        return t_adls_service.from_connection_string(conn_str=connection_string, **client_kwargs)

    account_url = get_account_url(cli_ctx, account_name=account_name, service='dfs')
    credential = account_key or sas_token or token_credential

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
    account_key = kwargs.pop('account_key', None)
    token_credential = kwargs.pop('token_credential', None)
    sas_token = kwargs.pop('sas_token', None)

    if connection_string:
        return t_queue_service.from_connection_string(conn_str=connection_string, **client_kwargs)

    account_url = get_account_url(cli_ctx, account_name=account_name, service='queue')
    credential = account_key or sas_token or token_credential

    return t_queue_service(account_url=account_url, credential=credential, **client_kwargs)


def cf_queue_client(cli_ctx, kwargs):
    return cf_queue_service(cli_ctx, kwargs).get_queue_client(queue=kwargs.pop('queue_name'))
