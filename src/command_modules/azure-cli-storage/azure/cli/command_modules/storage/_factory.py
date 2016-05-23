from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration

from azure.storage.blob import PublicAccess, BlockBlobService, PageBlobService, AppendBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from ._params import blob_types

def storage_client_factory(**_):
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

def file_data_service_factory(kwargs):
    return get_data_service_client(
        FileService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def blob_data_service_factory(kwargs):
    blob_type = kwargs.get('blob_type')
    blob_service = blob_types.get(blob_type, BlockBlobService)
    return get_data_service_client(
        blob_service,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def cloud_storage_account_service_factory(kwargs):
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    sas_token = kwargs.pop('sas_token', None)
    connection_string = kwargs.pop('connection_string', None)
    return CloudStorageAccount(account_name, account_key, sas_token)
