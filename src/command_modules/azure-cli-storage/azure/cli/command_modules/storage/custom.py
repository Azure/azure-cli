from __future__ import print_function
from sys import stderr

from azure.storage.blob import PublicAccess, BlockBlobService, AppendBlobService, PageBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType
from azure.mgmt.storage.operations import StorageAccountsOperations

from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli._locale import L

from ._params import PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS
from ._validators import validate_key_value_pairs


def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        percent_done = current * 100 / total
        message += '{: >5.1f}'.format(percent_done)
        print('\b' * len(message) + message, end='', file=stderr)
        stderr.flush()
        if current == total:
            print('', file=stderr)

class ConvenienceStorageAccountCommands(object):

    def __init__(self, _):
        pass

    def list(self, resource_group_name=None):
        ''' List storage accounts. '''
        from azure.mgmt.storage.models import StorageAccount
        from msrestazure.azure_active_directory import UserPassCredentials
        scf = _storage_client_factory(None)
        if resource_group_name:
            accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
        else:
            accounts = scf.storage_accounts.list()
        return list(accounts)

    _key_options = ['key1', 'key2']
    def renew_keys(self, resource_group_name, account_name, key=_key_options):
        ''' Regenerate one or both keys for a storage account.
        :param str key:Key to renew.'''
        scf = _storage_client_factory(None)
        for k in key if isinstance(key, list) else [key]:
            result = scf.storage_accounts.regenerate_key(
                resource_group_name=resource_group_name,
                account_name=account_name,
                key_name=k)
        return result

    def usage(self):
        ''' Show the current count and limit of the storage accounts under the subscription. '''
        scf = _storage_client_factory(None)
        return next((x for x in scf.usage.list() if x.name.value == 'StorageAccounts'), None)

    def connection_string(self, resource_group_name, account_name, use_http='https'):
        ''' Show the connection string for a storage account.
        :param str use_http:use http as the default endpoint protocol '''
        scf = _storage_client_factory(None)
        keys = scf.storage_accounts.list_keys(resource_group_name, account_name)
        connection_string = 'DefaultEndpointsProtocol={};AccountName={};AccountKey={}'.format(
            use_http,
            account_name,
            keys.key1) #pylint: disable=no-member
        return {'ConnectionString':connection_string}

    # TODO: update this once enums are supported in commands first-class (task #115175885)
    _storage_account_types = {'Standard_LRS': AccountType.standard_lrs,
                             'Standard_ZRS': AccountType.standard_zrs,
                             'Standard_GRS': AccountType.standard_grs,
                             'Standard_RAGRS': AccountType.standard_ragrs,
                             'Premium_LRS': AccountType.premium_lrs}
    def create(self, resource_group_name, account_name, location, account_type, tags=None):
        ''' Create a storage account. '''        
        from azure.mgmt.storage.models import StorageAccountCreateParameters
        scf = _storage_client_factory(None)
        params = StorageAccountCreateParameters(location, account_type, tags)
        op = LongRunningOperation('Creating storage account', 'Storage account created')
        poller = scf.storage_accounts.create(resource_group_name, account_name, params)
        return op(poller)

    def set(self, resource_group_name, account_name,
            account_type=None, tags=None, custom_domain=None, subdomain=None):
        ''' Update storage account property (only one at a time).
        :param str custom_domain:the custom domain name
        :param str subdomain:use indirect CNAME validation'''
        from azure.mgmt.storage.models import StorageAccountUpdateParameters, CustomDomain
        scf = _storage_client_factory(None)
        params = StorageAccountUpdateParameters(tags, account_type, custom_domain)
        return scf.storage_accounts.update(resource_group_name, account_name, params)

class ConvenienceBlobServiceCommands(object):

    def __init__(self, _):
        pass

    # TODO: update this once enums are supported in commands first-class (task #115175885)
    _public_access_types = {'none': None,
                           'blob': PublicAccess.Blob,
                           'container': PublicAccess.Container}
    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
    def exists(self, container_name, snapshot=None, timeout=None):
        '''Check if a storage container exists.
        :param str snapshot:UTC datetime value which specifies a snapshot
        '''
        bds = _blob_data_service_factory(args)
        return bds.exists(
            container_name=container_name,
            snapshot=snapshot,
            timeout=timeout)

    _lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
    _lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
        _lease_duration_values['min'],
        _lease_duration_values['max'],
        _lease_duration_values['infinite'])

    _blob_types = {
        'block': BlockBlobService,
        'page': PageBlobService,
        'append': AppendBlobService
    }
    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)    
    def upload(self, container_name, blob_name, blob_type, upload_from,
               container_public_access=None, content_type=None, content_disposition=None,
               content_encoding=None, content_language=None, content_md5=None,
               content_cache_control=None): # pylint: disable=too-many-args
        '''Upload a blob to a container.
        :param str blob_type:type of blob to upload
        :param str upload_from:local path to upload from
        '''
        from azure.storage.blob import ContentSettings
        bds = _blob_data_service_factory(args)
        content_settings = ContentSettings(
            content_type=content_type,
            content_disposition=content_disposition,
            content_encoding=content_encoding,
            content_language=content_language,
            content_md5=content_md5,
            cache_control=content_cache_control
        )

        def upload_append_blob():
            if not bds.exists(container_name, blob_name):
                bds.create_blob(
                    container_name=container_name,
                    blob_name=blob_name,
                    content_settings=content_settings)
            return bds.append_blob_from_path(
                container_name=container_name,
                blob_name=blob_name,
                file_path=upload_from,
                progress_callback=_update_progress
            )

        def upload_block_blob():
            return bds.create_blob_from_path(
                container_name=container_name,
                blob_name=blob_name,
                file_path=upload_from,
                progress_callback=_update_progress,
                content_settings=content_settings
            )

        type_func = {
            'append': upload_append_blob,
            'block': upload_block_blob,
            'page': upload_block_blob  # same implementation
        }
        return type_func[blob_type]()

    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)    
    def download(self, container_name, blob_name, download_to):
        ''' Download the specified blob.
        :param str download_to:the file path to download to
        '''
        bds = _blob_data_service_factory(args)

        # show dot indicator of download progress (one for every 10%)
        bds.get_blob_to_path(container_name, blob_name, download_to,
                             progress_callback=_update_progress)
    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)    
    def exists(self, container_name, blob_name, snapshot=None, timeout=None):
        ''' Check if a storage blob exists. '''        
        bds = _blob_data_service_factory(args)
        return bds.exists(
            blob_name=blob_name,
            container_name=container_name,
            snapshot=snapshot,
            timeout=timeout)

class ConvenienceFileShareCommands(object):

    def __init__(self, _):
        pass

    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)    
    def share_exists(self, share_name):
        ''' Check if a file share exists.'''
        fds = _file_data_service_factory(args)
        return fds.exists(share_name=share_name)

    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)    
    def dir_exists(self, share_name, directory_name):
        ''' Check if a share directory exists.'''
        fds = _file_data_service_factory(args)
        return fds.exists(share_name=share_name, directory_name=directory_name)
    

    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
    def download(self, share_name, file_name, local_file_name, directory_name=None):
        ''' Download a file from a file share.
        :param str file_name:the file name
        :param str local_file_name:the path to the local file to download to'''
        fds = _file_data_service_factory(args)
        fds.get_file_to_path(share_name, directory_name, file_name, local_file_name,
                             progress_callback=_update_progress)

    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
    def file_exists(self, share_name, directory_name, file_name):
        ''' Check if a file exists at a specified path.
        :param str file_name:the file name to check
        :param str directory_name:subdirectory path to the file'''        
        fds = _file_data_service_factory(args)
        return fds.exists(share_name=share_name,
                          directory_name=directory_name,
                          file_name=file_name)

    @command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
    def upload(self, share_name, file_name, local_file_name, directory_name=None):
        ''' Upload a file to a file share path.
        :param str file_name:the destination file name
        :param str local_file_name:the path and file name to upload
        :param str directory_name:the destination directory to upload to'''
        fds = _file_data_service_factory(args)
        fds.create_file_from_path(share_name, directory_name, file_name, local_file_name,
                                  progress_callback=_update_progress)
