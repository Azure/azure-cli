#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.storage import StorageManagementClient

from azure.storage import CloudStorageAccount
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.storage.table import TableService
from azure.storage.queue import QueueService
from azure.storage._error import _ERROR_STORAGE_MISSING_INFO

from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
from azure.cli.core.commands import CLIError
from azure.cli.core.cloud import CloudSuffix
from azure.cli.core._profile import CLOUD

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
                                   endpoint_suffix=CLOUD.suffixes[CloudSuffix.STORAGE_ENDPOINT])

def generic_data_service_factory(service, name=None, key=None, connection_string=None,
                                 sas_token=None):
    try:
        return get_storage_data_service_client(service, name, key, connection_string, sas_token)
    except ValueError as val_exception:
        message = str(val_exception)
        if message == _ERROR_STORAGE_MISSING_INFO:
            message = NO_CREDENTIALS_ERROR_MESSAGE
        raise CLIError(message)

def storage_client_factory(**_):
    return get_mgmt_service_client(StorageManagementClient)

def file_data_service_factory(kwargs):
    return generic_data_service_factory(
        FileService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def blob_data_service_factory(kwargs):
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
    return generic_data_service_factory(
        TableService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def queue_data_service_factory(kwargs):
    return generic_data_service_factory(
        QueueService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def cloud_storage_account_service_factory(kwargs):
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    sas_token = kwargs.pop('sas_token', None)
    connection_string = kwargs.pop('connection_string', None) # pylint: disable=unused-variable
    return CloudStorageAccount(account_name, account_key, sas_token)
