from os import environ

from azure.cli.commands import (COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, extend_parameter)
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._validators import validate_key_value_pairs
from azure.cli._locale import L

from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType

from azure.storage.blob import PublicAccess, BlockBlobService, PageBlobService, AppendBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from ._validators import (
    validate_container_permission, validate_datetime, validate_datetime_as_string, validate_id,
    validate_ip_range, validate_resource_types, validate_services, validate_lease_duration,
    validate_quota)

# FACTORIES

def storage_client_factory(**_):
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

def file_data_service_factory(**kwargs):
    return get_data_service_client(
        FileService,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def blob_data_service_factory(**kwargs):
    blob_type = kwargs.get('blob_type')
    blob_service = blob_types.get(blob_type, BlockBlobService)
    return get_data_service_client(
        blob_service,
        kwargs.pop('account_name', None),
        kwargs.pop('account_key', None),
        connection_string=kwargs.pop('connection_string', None),
        sas_token=kwargs.pop('sas_token', None))

def cloud_storage_account_service_factory(**kwargs):
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    sas_token = kwargs.pop('sas_token', None)
    connection_string = kwargs.pop('connection_string', None)
    if connection_string:
        # CloudStorageAccount doesn't accept connection string directly, so we must parse
        # out the account name and key manually
        conn_dict = validate_key_value_pairs(connection_string)
        account_name = conn_dict['AccountName']
        account_key = conn_dict['AccountKey']
    return CloudStorageAccount(account_name, account_key, sas_token)

# HELPER METHODS

def get_account_name(string):
    return string if string != 'query' else environ.get('AZURE_STORAGE_ACCOUNT')

def get_account_key(string):
    return string if string != 'query' else environ.get('AZURE_STORAGE_KEY')

def get_connection_string(string):
    return string if string != 'query' else environ.get('AZURE_STORAGE_CONNECTION_STRING')

def get_sas_token(string):
    return string if string != 'query' else environ.get('AZURE_SAS_TOKEN')

# PARAMETER CHOICE LISTS

storage_account_key_options = ['key1', 'key2']

# TODO: update this once enums are supported in commands first-class (task #115175885)
storage_account_types = {'Standard_LRS': AccountType.standard_lrs,
                         'Standard_ZRS': AccountType.standard_zrs,
                         'Standard_GRS': AccountType.standard_grs,
                         'Standard_RAGRS': AccountType.standard_ragrs,
                         'Premium_LRS': AccountType.premium_lrs}

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None, 'blob': PublicAccess.Blob, 'container': PublicAccess.Container}

lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
    lease_duration_values['min'],
    lease_duration_values['max'],
    lease_duration_values['infinite'])

blob_types = {'block': BlockBlobService, 'page': PageBlobService, 'append': AppendBlobService}

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
PARAMETER_ALIASES.update({
    'account_key': {
        'name': '--account-key -k',
        'help': L('the storage account key'),
        'type': get_account_key,
        'default': 'query'
    },
    'account_name': {
        'name': '--account-name -n',
        'help': L('the storage account name'),
        'type': get_account_name,
        'default': 'query'
    },
    'account_type': {
        'name': '--account-type',
        'choices': storage_account_types
    },
    'blob_name': {
        'name': '--blob-name -b',
        'help': L('the name of the blob'),
    },
    'blob_type': {
        'name': '--blob-type',
        'choices': blob_types.keys()
    },
    'container_name': {
        'name': '--container-name -c',
    },
    'connection_string': {
        'name': '--connection-string',
        'help': L('the storage connection string'),
        'type': get_connection_string,
        'default': 'query'
    },
    'directory_name': {
        'name': '--directory-name -d'
    },
    'expiry': {
        'name': '--expiry',
        'help': L('expiration UTC datetime of SAS token (Y-m-d\'T\'H:M\'Z\')'),
        'type': validate_datetime_as_string
    },
    'if_modified_since': {
        'name': '--if-modified-since',
        'help': L('alter only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')'),
        'type': validate_datetime,
    },
    'id': {
        'name': '--id',
        'help': L('stored access policy id (up to 64 characters)'),
        'type': validate_id
    },
    'if_unmodified_since': {
        'name': '--if-unmodified-since',
        'help': L('alter only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')'),
        'type': validate_datetime,
    },
    'ip': {
        'name': '--ip',
        'help': L('specifies the IP address or range of IP addresses from which to accept ' + \
                  'requests.'),
        'type': validate_ip_range
    },
    'lease_break_period': {
        'name': '--lease-break-period',
        'metavar': 'DURATION',
        'help': L('break period. 15-60 seconds or -1 for infinite.'),
        'type': validate_lease_duration
    },
    'lease_duration': {
        'name': '--lease-duration',
        'metavar': 'DURATION',
        'help': L('lease duration. 15-60 seconds or -1 for infinite.'),
        'type': validate_lease_duration
    },
    'lease_id': {
        'name': '--lease-id',
        'metavar': 'ID',
        'help': L('lease ID in GUID format.')
    },
    'metadata': {
        'name': '--metadata',
        'metavar': 'METADATA',
        'type': validate_key_value_pairs,
        'help': L('metadata in "a=b;c=d" format')
    },
    'optional_resource_group_name':
        extend_parameter(GLOBAL_COMMON_PARAMETERS['resource_group_name'], required=False),
    'permission': {
        'name': '--permission',
        'help': L('permissions granted: (r)ead (w)rite (d)elete (l)ist. Can be combined.'),
        'metavar': 'PERMISSION',
        # TODO: This will be problematic because the other sas types take different permissions
        'type': validate_container_permission
    },
    'public_access': {
        'name': '--public-access',
        'metavar': 'SPECIFIERS',
        'choices': ['blob', 'container']
    },
    'quota': {
        'name': '--quota',
        'type': validate_quota
    },
    'resource_types': {
        'name': '--resource-types',
        'help': L('the resource types the SAS is applicable for. Allowed values: (s)ervice ' + \
                  '(c)ontainer (o)bject. Can be combined.'),
        'type': validate_resource_types
    },
    'sas_token': {
        'name': '--sas-token',
        'help': L('a shared access signature token'),
        'type': get_sas_token,
        'default': 'query'
    },
    'services': {
        'name': '--services',
        'help': L('the storage services the SAS is applicable for. Allowed values: (b)lob ' + \
                  '(f)ile (q)ueue (t)able. Can be combined.'),
        'type': validate_services
    },
    'share_name': {
        'name': '--share-name -s',
        'help': L('the name of the file share'),
    },
    'signed_identifiers': {
        'name': '--signed-identifiers',
        'help': L(''),
        'metavar': 'IDENTIFIERS'
    },
    'start': {
        'name': '--start',
        'help': L('start UTC datetime of SAS token (Y-m-d\'T\'H:M\'Z\'). Defaults to time ' + \
                  'of request.'),
        'type': validate_datetime_as_string
    },
    'timeout': {
        'name': '--timeout',
        'help': L('timeout in seconds'),
        'type': int
    },
    'use_http': {
        'name': '--use-http',
        'help': L('specifies that http should be the default endpoint protocol'),
        'action': 'store_const',
        'const': 'http'
    },
})

# SUPPLEMENTAL (EXTRA) PARAMETER SETS

STORAGE_DATA_CLIENT_ARGS = {
    'account_name': PARAMETER_ALIASES['account_name'],
    'account_key': PARAMETER_ALIASES['account_key'],
    'connection_string': PARAMETER_ALIASES['connection_string'],
    'sas_token': PARAMETER_ALIASES['sas_token']
}
