# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,line-too-long

from __future__ import print_function

from azure.cli.core.decorators import transfer_doc
from azure.cli.core.util import CLIError
from azure.cli.core.profiles import get_sdk, supported_api_version, ResourceType

from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, generic_data_service_factory)
from azure.cli.core.application import APPLICATION


Logging, Metrics, CorsRule, \
    AccessPolicy, RetentionPolicy = get_sdk(ResourceType.DATA_STORAGE,
                                            'Logging',
                                            'Metrics',
                                            'CorsRule',
                                            'AccessPolicy',
                                            'RetentionPolicy',
                                            mod='models')


BlockBlobService, BaseBlobService, \
    FileService, FileProperties, \
    DirectoryProperties, TableService, \
    QueueService = get_sdk(ResourceType.DATA_STORAGE,
                           'blob#BlockBlobService',
                           'blob.baseblobservice#BaseBlobService',
                           'file#FileService',
                           'file.models#FileProperties',
                           'file.models#DirectoryProperties',
                           'table#TableService',
                           'queue#QueueService')


# pylint: disable=too-many-function-args
def _update_progress(current, total):
    HOOK = APPLICATION.get_progress_controller(True)

    if total:
        HOOK.add(message='Alive', value=current, total_val=total)
        if total == current:
            HOOK.end()


# CUSTOM METHODS

def create_storage_account(resource_group_name, account_name, sku, location=None,
                           kind=None, tags=None, custom_domain=None,
                           encryption=None, access_tier=None):
    StorageAccountCreateParameters, Kind, Sku, CustomDomain, AccessTier = get_sdk(
        ResourceType.MGMT_STORAGE,
        'StorageAccountCreateParameters',
        'Kind',
        'Sku',
        'CustomDomain',
        'AccessTier',
        mod='models')
    scf = storage_client_factory()
    params = StorageAccountCreateParameters(
        sku=Sku(sku),
        kind=Kind(kind),
        location=location,
        tags=tags,
        custom_domain=CustomDomain(custom_domain, None) if custom_domain else None,
        encryption=encryption,
        access_tier=AccessTier(access_tier) if access_tier else None)
    return scf.storage_accounts.create(resource_group_name, account_name, params)


def create_storage_account_with_account_type(resource_group_name, account_name, account_type,
                                             location=None, tags=None):
    StorageAccountCreateParameters, AccountType = get_sdk(
        ResourceType.MGMT_STORAGE,
        'StorageAccountCreateParameters',
        'AccountType',
        mod='models')
    scf = storage_client_factory()
    params = StorageAccountCreateParameters(location, AccountType(account_type), tags)
    return scf.storage_accounts.create(resource_group_name, account_name, params)


def update_storage_account(instance, sku=None, tags=None, custom_domain=None,
                           use_subdomain=None, encryption=None, access_tier=None):
    StorageAccountUpdateParameters, Sku, CustomDomain, AccessTier = get_sdk(
        ResourceType.MGMT_STORAGE,
        'StorageAccountUpdateParameters',
        'Sku',
        'CustomDomain',
        'AccessTier',
        mod='models')
    domain = instance.custom_domain
    if custom_domain is not None:
        domain = CustomDomain(custom_domain)
        if use_subdomain is not None:
            domain.name = use_subdomain == 'true'

    params = StorageAccountUpdateParameters(
        sku=Sku(sku) if sku is not None else instance.sku,
        tags=tags if tags is not None else instance.tags,
        custom_domain=domain,
        encryption=encryption if encryption is not None else instance.encryption,
        access_tier=AccessTier(access_tier) if access_tier is not None else instance.access_tier
    )
    return params


@transfer_doc(FileService.list_directories_and_files)
def list_share_files(client, share_name, directory_name=None, timeout=None,
                     exclude_dir=False):
    generator = client.list_directories_and_files(share_name, directory_name,
                                                  timeout=timeout)
    if exclude_dir:
        return list(f for f in generator if isinstance(f.properties, FileProperties))

    return generator


@transfer_doc(FileService.list_directories_and_files)
def list_share_directories(client, share_name, directory_name=None, timeout=None):
    generator = client.list_directories_and_files(share_name, directory_name,
                                                  timeout=timeout)
    return list(f for f in generator if isinstance(f.properties, DirectoryProperties))


def list_storage_accounts(resource_group_name=None):
    """ List storage accounts within a subscription or resource group. """
    scf = storage_client_factory()
    if resource_group_name:
        accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
    else:
        accounts = scf.storage_accounts.list()
    return list(accounts)


def show_storage_account_usage():
    """ Show the current count and limit of the storage accounts under the subscription. """
    scf = storage_client_factory()
    return next((x for x in scf.usage.list() if x.name.value == 'StorageAccounts'), None)  # pylint: disable=no-member


def show_storage_account_connection_string(
        resource_group_name, account_name, protocol='https', blob_endpoint=None,
        file_endpoint=None, queue_endpoint=None, table_endpoint=None, key_name='primary'):
    """ Generate connection string for a storage account."""
    from azure.cli.core._profile import CLOUD
    scf = storage_client_factory()
    obj = scf.storage_accounts.list_keys(resource_group_name, account_name)  # pylint: disable=no-member
    try:
        keys = [obj.keys[0].value, obj.keys[1].value]  # pylint: disable=no-member
    except AttributeError:
        # Older API versions have a slightly different structure
        keys = [obj.key1, obj.key2]  # pylint: disable=no-member

    endpoint_suffix = CLOUD.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={};AccountName={};AccountKey={}'.format(
        protocol,
        endpoint_suffix,
        account_name,
        keys[0] if key_name == 'primary' else keys[1])  # pylint: disable=no-member
    connection_string = '{}{}'.format(connection_string, ';BlobEndpoint={}'.format(blob_endpoint) if blob_endpoint else '')
    connection_string = '{}{}'.format(connection_string, ';FileEndpoint={}'.format(file_endpoint) if file_endpoint else '')
    connection_string = '{}{}'.format(connection_string, ';QueueEndpoint={}'.format(queue_endpoint) if queue_endpoint else '')
    connection_string = '{}{}'.format(connection_string, ';TableEndpoint={}'.format(table_endpoint) if table_endpoint else '')
    return {'connectionString': connection_string}


@transfer_doc(BlockBlobService.create_blob_from_path)
def upload_blob(  # pylint: disable=too-many-locals
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

        append_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': _update_progress,
            'maxsize_condition': maxsize_condition,
            'lease_id': lease_id,
            'timeout': timeout
        }

        if supported_api_version(ResourceType.DATA_STORAGE, min_api='2016-05-31'):
            append_blob_args['validate_content'] = validate_content

        return client.append_blob_from_path(**append_blob_args)

    def upload_block_blob():
        import os

        # increase the block size to 100MB when the file is larger than 200GB
        if os.path.isfile(file_path) and os.stat(file_path).st_size > 200 * 1024 * 1024 * 1024:
            client.MAX_BLOCK_SIZE = 100 * 1024 * 1024
            client.MAX_SINGLE_PUT_SIZE = 256 * 1024 * 1024

        create_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': _update_progress,
            'content_settings': content_settings,
            'metadata': metadata,
            'max_connections': max_connections,
            'lease_id': lease_id,
            'if_modified_since': if_modified_since,
            'if_unmodified_since': if_unmodified_since,
            'if_match': if_match,
            'if_none_match': if_none_match,
            'timeout': timeout
        }

        if supported_api_version(ResourceType.DATA_STORAGE, min_api='2016-05-31'):
            create_blob_args['validate_content'] = validate_content

        return client.create_blob_from_path(**create_blob_args)

    type_func = {
        'append': upload_append_blob,
        'block': upload_block_blob,
        'page': upload_block_blob  # same implementation
    }
    return type_func[blob_type]()


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
    get_acl_fn = getattr(client, 'get_{}_acl'.format(container))
    lease_id = kwargs.get('lease_id', None)
    return get_acl_fn(container_name, lease_id=lease_id) if lease_id else get_acl_fn(container_name)


def _set_acl(client, container_name, acl, **kwargs):
    try:
        method_name = 'set_{}_acl'.format(_get_service_container_type(client))
        method = getattr(client, method_name)
        return method(container_name, acl, **kwargs)
    except TypeError:
        raise CLIError("Failed to invoke SDK method {}. The installed azure SDK may not be"
                       "compatible to this version of Azure CLI.".format(method_name))
    except AttributeError:
        raise CLIError("Failed to get function {} from {}. The installed azure SDK may not be "
                       "compatible to this version of Azure CLI.".format(client.__class__.__name__,
                                                                         method_name))


def create_acl_policy(client, container_name, policy_name, start=None, expiry=None,
                      permission=None, **kwargs):
    """Create a stored access policy on the containing object"""
    acl = _get_acl(client, container_name, **kwargs)
    acl[policy_name] = AccessPolicy(permission, expiry, start)
    if hasattr(acl, 'public_access'):
        kwargs['public_access'] = getattr(acl, 'public_access')

    return _set_acl(client, container_name, acl, **kwargs)


def get_acl_policy(client, container_name, policy_name, **kwargs):
    """Show a stored access policy on a containing object"""
    acl = _get_acl(client, container_name, **kwargs)
    return acl.get(policy_name)


def list_acl_policies(client, container_name, **kwargs):
    """List stored access policies on a containing object"""
    return _get_acl(client, container_name, **kwargs)


def set_acl_policy(client, container_name, policy_name, start=None, expiry=None, permission=None,
                   **kwargs):
    """Set a stored access policy on a containing object"""
    if not (start or expiry or permission):
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(client, container_name, **kwargs)
    try:
        policy = acl[policy_name]
        policy.start = start or policy.start
        policy.expiry = expiry or policy.expiry
        policy.permission = permission or policy.permission
        if hasattr(acl, 'public_access'):
            kwargs['public_access'] = getattr(acl, 'public_access')

    except KeyError:
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(client, container_name, acl, **kwargs)


def delete_acl_policy(client, container_name, policy_name, **kwargs):
    ''' Delete a stored access policy on a containing object '''
    acl = _get_acl(client, container_name, **kwargs)
    del acl[policy_name]
    if hasattr(acl, 'public_access'):
        kwargs['public_access'] = getattr(acl, 'public_access')

    return _set_acl(client, container_name, acl, **kwargs)


def insert_table_entity(client, table_name, entity, if_exists='fail', timeout=None):
    if if_exists == 'fail':
        return client.insert_entity(table_name, entity, timeout)
    elif if_exists == 'merge':
        return client.insert_or_merge_entity(table_name, entity, timeout)
    elif if_exists == 'replace':
        return client.insert_or_replace_entity(table_name, entity, timeout)
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
