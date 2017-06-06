# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
from azure.cli.core.commands import CLIError
from azure.cli.core._profile import CLOUD
from azure.cli.core.profiles import get_sdk, ResourceType

NO_CREDENTIALS_ERROR_MESSAGE = """
No credentials specifed to access storage service. Please provide any of the following:
    (1) account name and key (--account-name and --account-key options or
        set AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY environment variables)
    (2) connection string (--connection-string option or
        set AZURE_STORAGE_CONNECTION_STRING environment variable)
    (3) account name and SAS token (--sas-token option used with either the --account-name
        option or AZURE_STORAGE_ACCOUNT environment variable)
"""


def get_storage_data_service_client(service, name=None, key=None, connection_string=None,
                                    sas_token=None):
    return get_data_service_client(service,
                                   name,
                                   key,
                                   connection_string,
                                   sas_token,
                                   endpoint_suffix=CLOUD.suffixes.storage_endpoint)


def generic_data_service_factory(service, name=None, key=None, connection_string=None, sas_token=None):
    try:
        return get_storage_data_service_client(service, name, key, connection_string, sas_token)
    except ValueError as val_exception:
        _ERROR_STORAGE_MISSING_INFO = get_sdk(ResourceType.DATA_STORAGE, '_error#_ERROR_STORAGE_MISSING_INFO')
        message = str(val_exception)
        if message == _ERROR_STORAGE_MISSING_INFO:
            message = NO_CREDENTIALS_ERROR_MESSAGE
        raise CLIError(message)


def storage_client_factory(**_):
    return get_mgmt_service_client(ResourceType.MGMT_STORAGE)


def file_data_service_factory(kwargs):
    FileService = get_sdk(ResourceType.DATA_STORAGE, 'file#FileService')
    return generic_data_service_factory(
        FileService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))


def page_blob_service_factory(kwargs):
    PageBlobService = get_sdk(ResourceType.DATA_STORAGE,
                              'blob.pageblobservice#PageBlobService')
    return generic_data_service_factory(
        PageBlobService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))


def blob_data_service_factory(kwargs):
    BlockBlobService = get_sdk(ResourceType.DATA_STORAGE, 'blob#BlockBlobService')
    from ._params import blob_types
    blob_type = kwargs.get('blob_type')
    blob_service = blob_types.get(blob_type, BlockBlobService)
    return generic_data_service_factory(
        blob_service,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))


def table_data_service_factory(kwargs):
    TableService = get_sdk(ResourceType.DATA_STORAGE, 'table#TableService')
    return generic_data_service_factory(
        TableService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))


def queue_data_service_factory(kwargs):
    QueueService = get_sdk(ResourceType.DATA_STORAGE, 'queue#QueueService')
    return generic_data_service_factory(
        QueueService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))


def cloud_storage_account_service_factory(kwargs):
    CloudStorageAccount = get_sdk(ResourceType.DATA_STORAGE, '#CloudStorageAccount')
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    sas_token = kwargs.pop('sas_token', None)
    kwargs.pop('connection_string', None)
    return CloudStorageAccount(account_name, account_key, sas_token)


def multi_service_properties_factory(kwargs):
    """Create multiple data services properties instance based on the services option"""
    from .services_wrapper import ServiceProperties

    BaseBlobService, FileService, TableService, QueueService, = \
        get_sdk(ResourceType.DATA_STORAGE,
                'blob.baseblobservice#BaseBlobService', 'file#FileService', 'table#TableService', 'queue#QueueService')

    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    connection_string = kwargs.pop('connection_string', None)
    sas_token = kwargs.pop('sas_token', None)
    services = kwargs.pop('services', [])

    def get_creator(name, service_type):
        return lambda: ServiceProperties(name, service_type, account_name, account_key, connection_string, sas_token)

    creators = {
        'b': get_creator('blob', BaseBlobService),
        'f': get_creator('file', FileService),
        'q': get_creator('queue', QueueService),
        't': get_creator('table', TableService)
    }

    return [creators[s]() for s in services]
