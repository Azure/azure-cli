#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments

from __future__ import print_function
from sys import stderr

from azure.mgmt.storage.models import Kind
from azure.storage.models import Logging, Metrics, CorsRule, RetentionPolicy
from azure.storage.blob import BlockBlobService
from azure.storage.blob.baseblobservice import BaseBlobService
from azure.storage.file import FileService
from azure.storage.table import TableService
from azure.storage.queue import QueueService

from azure.cli.core._util import CLIError

from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, generic_data_service_factory)

def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        percent_done = current * 100 / total
        message += '{: >5.1f}'.format(percent_done)
        print('\b' * len(message) + message, end='', file=stderr)
        stderr.flush()
        if current == total:
            print('', file=stderr)

# CUSTOM METHODS

def list_storage_accounts(resource_group_name=None):
    """ List storage accounts within a subscription or resource group. """
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    scf = storage_client_factory()
    if resource_group_name:
        accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
    else:
        accounts = scf.storage_accounts.list()
    return list(accounts)

def show_storage_account_usage():
    """ Show the current count and limit of the storage accounts under the subscription. """
    scf = storage_client_factory()
    return next((x for x in scf.usage.list() if x.name.value == 'StorageAccounts'), None) #pylint: disable=no-member

# pylint: disable=line-too-long
def show_storage_account_connection_string(
        resource_group_name, account_name, protocol='https', blob_endpoint=None,
        file_endpoint=None, queue_endpoint=None, table_endpoint=None, key_name='primary'):
    """ Generate connection string for a storage account."""
    scf = storage_client_factory()
    keys = scf.storage_accounts.list_keys(resource_group_name, account_name).keys #pylint: disable=no-member
    connection_string = 'DefaultEndpointsProtocol={};AccountName={};AccountKey={}'.format(
        protocol,
        account_name,
        keys[0].value if key_name == 'primary' else keys[1].value) #pylint: disable=no-member
    connection_string = '{}{}'.format(connection_string, ';BlobEndpoint={}'.format(blob_endpoint) if blob_endpoint else '')
    connection_string = '{}{}'.format(connection_string, ';FileEndpoint={}'.format(file_endpoint) if file_endpoint else '')
    connection_string = '{}{}'.format(connection_string, ';QueueEndpoint={}'.format(queue_endpoint) if queue_endpoint else '')
    connection_string = '{}{}'.format(connection_string, ';TableEndpoint={}'.format(table_endpoint) if table_endpoint else '')
    return {'connectionString': connection_string}

def create_storage_account(resource_group_name, account_name, sku, location,
                           kind=Kind.storage.value, tags=None, custom_domain=None,
                           encryption=None, access_tier=None):
    ''' Create a storage account. '''
    from azure.mgmt.storage.models import \
        (StorageAccountCreateParameters, Sku, CustomDomain, Encryption, AccessTier)
    scf = storage_client_factory()
    params = StorageAccountCreateParameters(
        sku=Sku(sku),
        kind=Kind(kind),
        location=location,
        tags=tags,
        custom_domain=CustomDomain(custom_domain) if custom_domain else None,
        encryption=encryption,
        access_tier=AccessTier(access_tier) if access_tier else None)
    return scf.storage_accounts.create(resource_group_name, account_name, params)

def set_storage_account_properties(
        resource_group_name, account_name, sku=None, tags=None, custom_domain=None,
        encryption=None, access_tier=None):
    ''' Update storage account property (only one at a time).'''
    from azure.mgmt.storage.models import \
        (StorageAccountUpdateParameters, Sku, CustomDomain, Encryption, AccessTier)
    scf = storage_client_factory()
    params = StorageAccountUpdateParameters(
        sku=Sku(sku) if sku else None,
        tags=tags,
        custom_domain=CustomDomain(custom_domain) if custom_domain else None,
        encryption=encryption,
        access_tier=AccessTier(access_tier) if access_tier else None)
    return scf.storage_accounts.update(resource_group_name, account_name, params)

def upload_blob( # pylint: disable=too-many-locals
        client, container_name, blob_name, file_path, blob_type=None,
        content_settings=None, metadata=None, validate_content=False, maxsize_condition=None,
        max_connections=2, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
    '''Upload a blob to a container.'''
    def upload_append_blob():
        if not client.exists(container_name, blob_name):
            client.create_blob(
                container_name=container_name,
                blob_name=blob_name,
                content_settings=content_settings,
                metadata=metadata,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_match=if_match,
                if_none_match=if_none_match,
                timeout=timeout)
        return client.append_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=_update_progress,
            validate_content=validate_content,
            maxsize_condition=maxsize_condition,
            lease_id=lease_id,
            timeout=timeout)

    def upload_block_blob():
        return client.create_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=_update_progress,
            content_settings=content_settings,
            metadata=metadata,
            validate_content=validate_content,
            max_connections=max_connections,
            lease_id=lease_id,
            if_modified_since=if_modified_since,
            if_unmodified_since=if_unmodified_since,
            if_match=if_match,
            if_none_match=if_none_match,
            timeout=timeout
        )

    type_func = {
        'append': upload_append_blob,
        'block': upload_block_blob,
        'page': upload_block_blob  # same implementation
    }
    return type_func[blob_type]()
upload_blob.__doc__ = BlockBlobService.create_blob_from_path.__doc__

def _get_service_container_type(client):
    if isinstance(client, BlockBlobService):
        return 'container'
    elif isinstance(client, FileService):
        return 'share'
    elif isinstance(client, TableService):
        return 'table'
    elif isinstance(client, QueueService):
        return 'queue'
    else:
        raise ValueError('Unsupported service {}'.format(type(client)))

def _get_acl(client, container_name, **kwargs):
    container = _get_service_container_type(client)
    get_acl = getattr(client, 'get_{}_acl'.format(container))
    lease_id = kwargs.get('lease_id', None)
    return get_acl(container_name, lease_id=lease_id) if lease_id else get_acl(container_name)

def _set_acl(client, container_name, acl, **kwargs):
    container = _get_service_container_type(client)
    set_acl = getattr(client, 'set_{}_acl'.format(container))
    lease_id = kwargs.get('lease_id', None)
    return set_acl(container_name, acl, lease_id=lease_id) if lease_id \
        else set_acl(container_name, acl)

def create_acl_policy(
        client, container_name, policy_name, start=None, expiry=None, permission=None, **kwargs):
    ''' Create a stored access policy on the containing object '''
    from azure.storage.models import AccessPolicy
    acl = _get_acl(client, container_name, **kwargs)
    acl[policy_name] = AccessPolicy(permission, expiry, start)
    return _set_acl(client, container_name, acl, **kwargs)

def get_acl_policy(client, container_name, policy_name, **kwargs):
    ''' Show a stored access policy on a containing object '''
    from azure.storage.models import AccessPolicy
    acl = _get_acl(client, container_name, **kwargs)
    return acl.get(policy_name)

def list_acl_policies(client, container_name, **kwargs):
    ''' List stored access policies on a containing object '''
    return _get_acl(client, container_name, **kwargs)

def set_acl_policy(client, container_name, policy_name, start=None, expiry=None, permission=None,
                   **kwargs):
    ''' Set a stored access policy on a containing object '''
    from azure.storage.models import AccessPolicy
    if not (start or expiry or permission):
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(client, container_name, **kwargs)
    try:
        policy = acl[policy_name]
        policy.start = start or policy.start
        policy.expiry = expiry or policy.expiry
        policy.permission = permission or policy.permission
    except KeyError:
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(client, container_name, acl, **kwargs)

def delete_acl_policy(client, container_name, policy_name, **kwargs):
    ''' Delete a stored access policy on a containing object '''
    acl = _get_acl(client, container_name, **kwargs)
    del acl[policy_name]
    return _set_acl(client, container_name, acl, **kwargs)

def insert_table_entity(client, table_name, entity, if_exists='fail', timeout=None):
    if if_exists == 'fail':
        client.insert_entity(table_name, entity, timeout)
    elif if_exists == 'merge':
        client.insert_or_merge_entity(table_name, entity, timeout)
    elif if_exists == 'replace':
        client.insert_or_replace_entity(table_name, entity, timeout)
    else:
        raise CLIError("Unrecognized value '{}' for --if-exists".format(if_exists))

class ServiceProperties(object):

    def __init__(self, name, service):

        self.name = name
        self.service = service
        self.client = None

    def init_client(self, account_name=None, account_key=None, connection_string=None,
                    sas_token=None):
        if not self.client:
            self.client = generic_data_service_factory(
                self.service, account_name, account_key, connection_string, sas_token)

    def get_service_properties(self):
        if not self.client:
            raise CLIError('Must call init_client before attempting get_service_properties!')
        return getattr(self.client, 'get_{}_service_properties'.format(self.name))

    def set_service_properties(self):
        if not self.client:
            raise CLIError('Must call init_client before attempting set_service_properties!')
        return getattr(self.client, 'set_{}_service_properties'.format(self.name))

    def get_logging(self, account_name=None, account_key=None, connection_string=None,
                    sas_token=None, timeout=None):
        self.init_client(account_name, account_key, connection_string, sas_token)
        return self.get_service_properties()(timeout=timeout).__dict__['logging']

    def set_logging(self, read, write, delete, retention, account_name=None, account_key=None,
                    connection_string=None, sas_token=None, timeout=None):
        self.init_client(account_name, account_key, connection_string, sas_token)
        retention_policy = RetentionPolicy(
            enabled=retention != 0,
            days=retention
        )
        logging = Logging(delete, read, write, retention_policy)
        return self.set_service_properties()(logging=logging, timeout=timeout)

    def get_cors(self, account_name=None, account_key=None, connection_string=None,
                 sas_token=None, timeout=None):
        self.init_client(account_name, account_key, connection_string, sas_token)
        return self.get_service_properties()(timeout=timeout).__dict__['cors']

    def add_cors(self, origins, methods, max_age, exposed_headers=None, allowed_headers=None,
                 account_name=None, account_key=None, connection_string=None, sas_token=None,
                 timeout=None):
        cors = self.get_cors(account_name, account_key, connection_string, sas_token, timeout)
        new_rule = CorsRule(origins, methods, max_age, exposed_headers, allowed_headers)
        cors.append(new_rule)
        return self.set_service_properties()(cors=cors, timeout=timeout)

    def clear_cors(self, account_name=None, account_key=None, connection_string=None,
                   sas_token=None, timeout=None):
        self.init_client(account_name, account_key, connection_string, sas_token)
        return self.set_service_properties()(cors=[], timeout=timeout)

    def get_metrics(self, interval, account_name=None, account_key=None, connection_string=None,
                    sas_token=None, timeout=None):
        self.init_client(account_name, account_key, connection_string, sas_token)
        props = self.get_service_properties()(timeout=timeout)
        metrics = {}
        if interval == 'both':
            metrics['hour'] = props.__dict__['hour_metrics']
            metrics['minute'] = props.__dict__['minute_metrics']
        else:
            metrics[interval] = props.__dict__['{}_metrics'.format(interval)]
        return metrics

    def set_metrics(self, retention, hour, minute, api=None, account_name=None, account_key=None,
                    connection_string=None, sas_token=None, timeout=None):
        self.init_client(account_name, account_key, connection_string, sas_token)
        retention_policy = RetentionPolicy(
            enabled=retention != 0,
            days=retention
        )
        hour_metrics = Metrics(hour, api, retention_policy) if hour is not None else None
        minute_metrics = Metrics(minute, api, retention_policy) if minute is not None else None
        return self.set_service_properties()(
            hour_metrics=hour_metrics, minute_metrics=minute_metrics, timeout=timeout)

SERVICES = {
    'b': ServiceProperties('blob', BaseBlobService),
    'f': ServiceProperties('file', FileService),
    'q': ServiceProperties('queue', QueueService),
    't': ServiceProperties('table', TableService)
}

def list_cors(services='bfqt', account_name=None, account_key=None, connection_string=None,
              sas_token=None, timeout=None):
    results = {}
    for character in services:
        properties = SERVICES[character]
        results[properties.name] = properties.get_cors(
            account_name, account_key, connection_string, sas_token, timeout)
    return results

def add_cors(services, origins, methods, max_age=0, exposed_headers=None, allowed_headers=None,
             account_name=None, account_key=None, connection_string=None, sas_token=None,
             timeout=None):
    for character in services:
        properties = SERVICES[character]
        properties.add_cors(
            origins, methods, max_age, exposed_headers, allowed_headers, account_name, account_key,
            connection_string, sas_token, timeout)
    return None

def clear_cors(services, account_name=None, account_key=None, connection_string=None,
               sas_token=None, timeout=None):
    for character in services:
        properties = SERVICES[character]
        properties.clear_cors(
            account_name, account_key, connection_string, sas_token, timeout)
    return None


def set_logging(services, log, retention, account_name=None, account_key=None,
                connection_string=None, sas_token=None, timeout=None):
    for character in services:
        properties = SERVICES[character]
        properties.set_logging(
            'r' in log, 'w' in log, 'd' in log, retention, account_name, account_key,
            connection_string, sas_token, timeout)
    return None

def set_metrics(services, retention, hour=None, minute=None, api=None, account_name=None,
                account_key=None, connection_string=None, sas_token=None, timeout=None):
    for character in services:
        properties = SERVICES[character]
        properties.set_metrics(
            retention, hour, minute, api, account_name, account_key, connection_string,
            sas_token, timeout)
    return None

def get_logging(services='bqt', account_name=None, account_key=None, connection_string=None,
                sas_token=None, timeout=None):
    results = {}
    for character in services:
        properties = SERVICES[character]
        results[properties.name] = properties.get_logging(
            account_name, account_key, connection_string, sas_token, timeout)
    return results

def get_metrics(services='bfqt', interval='both', account_name=None, account_key=None,
                connection_string=None, sas_token=None, timeout=None):
    results = {}
    for character in services:
        properties = SERVICES[character]
        results[properties.name] = properties.get_metrics(
            interval, account_name, account_key, connection_string, sas_token, timeout)
    return results
