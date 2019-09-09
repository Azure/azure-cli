# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import msrest
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
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


def log_response_securely(policy_object, request, response, **kwargs):
    # logic here was cloned from msrest.pipeline.SansIOHTTPPolicy
    if kwargs.get("enable_http_logger", policy_object.enable_http_logger):
        if 'listKeys?' in request.http_request.url and response.http_response.status_code == 200:
            import logging
            _LOGGER = logging.getLogger(__name__)
            if not _LOGGER.isEnabledFor(logging.DEBUG):
                return

            _LOGGER.debug("Response status: %r", response.http_response.status_code)
            _LOGGER.debug("Response headers:")
            for res_header, value in response.http_response.headers.items():
                _LOGGER.debug("    %r: %r", res_header, value)

            _LOGGER.debug("Response content: *****REDACTED")
        else:
            msrest.http_logger.log_response(None, request.http_request, response.http_response, result=response)


def get_storage_data_service_client(cli_ctx, service, name=None, key=None, connection_string=None, sas_token=None,
                                    socket_timeout=None, token_credential=None):
    return get_data_service_client(cli_ctx, service, name, key, connection_string, sas_token,
                                   socket_timeout=socket_timeout,
                                   token_credential=token_credential,
                                   endpoint_suffix=cli_ctx.cloud.suffixes.storage_endpoint)


def generic_data_service_factory(cli_ctx, service, name=None, key=None, connection_string=None, sas_token=None,
                                 socket_timeout=None, token_credential=None):
    try:
        return get_storage_data_service_client(cli_ctx, service, name, key, connection_string, sas_token,
                                               socket_timeout, token_credential)
    except ValueError as val_exception:
        _ERROR_STORAGE_MISSING_INFO = get_sdk(cli_ctx, ResourceType.DATA_STORAGE,
                                              'common._error#_ERROR_STORAGE_MISSING_INFO')
        message = str(val_exception)
        if message == _ERROR_STORAGE_MISSING_INFO:
            message = MISSING_CREDENTIALS_ERROR_MESSAGE
        from knack.util import CLIError
        raise CLIError(message)


def storage_client_factory(cli_ctx, **_):
    msrest.pipeline.universal.HTTPLogger.on_response = log_response_securely
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)
    return client


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
    from azure.cli.command_modules.storage.sdkutil import get_blob_service_by_type
    blob_type = kwargs.get('blob_type')
    blob_service = get_blob_service_by_type(cli_ctx, blob_type) or get_blob_service_by_type(cli_ctx, 'block')

    return generic_data_service_factory(cli_ctx, blob_service, kwargs.pop('account_name', None),
                                        kwargs.pop('account_key', None),
                                        connection_string=kwargs.pop('connection_string', None),
                                        sas_token=kwargs.pop('sas_token', None),
                                        socket_timeout=kwargs.pop('socket_timeout', None),
                                        token_credential=kwargs.pop('token_credential', None))


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


def cf_mgmt_policy(cli_ctx, _):
    return storage_client_factory(cli_ctx).management_policies


def cf_blob_container_mgmt(cli_ctx, _):
    return storage_client_factory(cli_ctx).blob_containers


def cf_blob_data_gen_update(cli_ctx, kwargs):
    return blob_data_service_factory(cli_ctx, kwargs.copy())
