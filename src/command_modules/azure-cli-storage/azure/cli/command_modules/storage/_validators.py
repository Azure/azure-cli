#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
from collections import OrderedDict
from datetime import datetime
import os
import re

from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.cli.commands.validators import validate_key_value_pairs

from azure.mgmt.storage import StorageManagementClient
from azure.storage.models import ResourceTypes, Services
from azure.storage.table import TablePermissions

# region PARAMETER VALIDATORS

def validate_client_parameters(namespace):
    """ Retrieves storage connection parameters from environment variables and parses out
    connection string into account name and key """
    n = namespace

    if not n.connection_string:
        n.connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')

    # if connection string supplied or in environment variables, extract account key and name
    if n.connection_string:
        conn_dict = validate_key_value_pairs(n.connection_string)
        n.account_name = conn_dict['AccountName']
        n.account_key = conn_dict['AccountKey']

    # otherwise, simply try to retrieve the remaining variables from environment variables
    if not n.account_name:
        n.account_name = os.environ.get('AZURE_STORAGE_ACCOUNT')
    if not n.account_key:
        n.account_key = os.environ.get('AZURE_STORAGE_KEY')
    if not n.sas_token:
        n.sas_token = os.environ.get('AZURE_SAS_TOKEN')

    # if account name is specified but no key, attempt to query
    if n.account_name and not n.account_key:
        scf = get_mgmt_service_client(StorageManagementClient)
        acc_id = next((x for x in scf.storage_accounts.list() if x.name == n.account_name), None).id
        if acc_id:
            from azure.cli.commands.arm import parse_resource_id
            rg = parse_resource_id(acc_id)['resource_group']
            n.account_key = \
                scf.storage_accounts.list_keys(rg, n.account_name).keys[0].value #pylint: disable=no-member

def get_content_setting_validator(settings_class):
    def validator(namespace):
        namespace.content_settings = settings_class(
            content_type=namespace.content_type,
            content_disposition=namespace.content_disposition,
            content_encoding=namespace.content_encoding,
            content_language=namespace.content_language,
            content_md5=namespace.content_md5,
            cache_control=namespace.content_cache_control
        )
        del namespace.content_type,
        del namespace.content_disposition,
        del namespace.content_encoding,
        del namespace.content_language,
        del namespace.content_md5,
        del namespace.content_cache_control
    return validator

def validate_encryption(namespace):
    ''' Builds up the encryption object for storage account operations based on the
    list of services passed in. '''
    if namespace.encryption:
        from azure.mgmt.storage.models import Encryption, EncryptionServices, EncryptionService
        services = {service: EncryptionService(True) for service in namespace.encryption}
        namespace.encryption = Encryption(EncryptionServices(**services))

def validate_entity(namespace):
    ''' Converts a list of key value pairs into a dictionary. Ensures that required
    RowKey and PartitionKey are converted to the correct case and included. '''
    values = dict(x.split('=', 1) for x in namespace.entity)
    keys = values.keys()
    for key in keys:
        if key.lower() == 'rowkey':
            val = values[key]
            del values[key]
            values['RowKey'] = val
        elif key.lower() == 'partitionkey':
            val = values[key]
            del values[key]
            values['PartitionKey'] = val
    keys = values.keys()
    missing_keys = 'RowKey ' if 'RowKey' not in keys else ''
    missing_keys = '{}PartitionKey'.format(missing_keys) \
        if 'PartitionKey' not in keys else missing_keys
    if missing_keys:
        raise argparse.ArgumentError(
            None, 'incorrect usage: entity requires: {}'.format(missing_keys))

    def cast_val(key, val):
        """ Attempts to cast numeric values (except RowKey and PartitionKey) to numbers so they
        can be queried correctly. """
        if key in ['PartitionKey', 'RowKey']:
            return val

        def try_cast(to_type):
            try:
                return to_type(val)
            except ValueError:
                return None
        return try_cast(int) or try_cast(float) or val

    # ensure numbers are converted from strings so querying will work correctly
    values = {key: cast_val(key, val) for key, val in values.items()}
    namespace.entity = values

def get_file_path_validator(default_file_param=None):
    """ Creates a namespace validator that splits out 'path' into 'directory_name' and 'file_name'.
    Allows another path-type parameter to be named which can supply a default filename. """
    def validator(namespace):
        path = namespace.path
        dir_name, file_name = os.path.split(path) if path else (None, '')

        if default_file_param and '.' not in file_name:
            dir_name = path
            file_name = os.path.split(getattr(namespace, default_file_param))[1]
        namespace.directory_name = dir_name
        namespace.file_name = file_name
        del namespace.path
    return validator

def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)

def get_permission_help_string(permission_class):
    allowed_values = [x.lower() for x in dir(permission_class) if not x.startswith('__')]
    return ' '.join(['({}){}'.format(x[0], x[1:]) for x in allowed_values])

def get_permission_validator(permission_class):

    allowed_values = [x.lower() for x in dir(permission_class) if not x.startswith('__')]
    allowed_string = ''.join(x[0] for x in allowed_values)

    def validator(namespace):
        if namespace.permission:
            if set(namespace.permission) - set(allowed_string):
                help_string = get_permission_help_string(permission_class)
                raise ValueError(
                    'valid values are {} or a combination thereof.'.format(help_string))
            namespace.permission = permission_class(_str=namespace.permission)
    return validator

def table_permission_validator(namespace):
    """ A special case for table because the SDK associates the QUERY permission with 'r' """
    if namespace.permission:
        if set(namespace.permission) - set('raud'):
            help_string = '(r)ead/query (a)dd (u)pdate (d)elete'
            raise ValueError('valid values are {} or a combination thereof.'.format(help_string))
        namespace.permission = TablePermissions(_str=namespace.permission)

def validate_select(namespace):
    if namespace.select:
        namespace.select = ','.join(namespace.select)

# endregion

# region COMMAND VALIDATORS

def process_file_download_namespace(namespace):

    get_file_path_validator()(namespace)

    dest = namespace.file_path
    if not dest or os.path.isdir(dest):
        namespace.file_path = os.path.join(dest, namespace.file_name) \
            if dest else namespace.file_name

def process_logging_update_namespace(namespace):
    services = namespace.services
    if set(services) - set('bqt'):
        raise ValueError('--services: valid values are (b)lob (q)ueue '
                         '(t)able or a combination thereof (ex: bt).')
    log = namespace.log
    if set(log) - set('rwd'):
        raise ValueError('--log: valid values are (r)ead (w)rite (d)elete '
                         'or a combination thereof (ex: rw).')

def process_metric_update_namespace(namespace):
    namespace.hour = namespace.hour == 'enable'
    namespace.minute = namespace.minute == 'enable'
    namespace.api = namespace.api == 'enable' if namespace.api else None
    if namespace.hour is None and namespace.minute is None:
        raise argparse.ArgumentError(
            None, 'incorrect usage: must specify --hour and/or --minute')
    if (namespace.hour or namespace.minute) and namespace.api is None:
        raise argparse.ArgumentError(
            None, 'incorrect usage: specify --api when hour or minute metrics are enabled')

# endregion

# region TYPES

def datetime_string_type(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format).strftime(date_format)

def datetime_type(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format)

def ipv4_range_type(string):
    ''' Validates an IPv4 address or address range. '''
    ip_format = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    if not re.match("^{}$".format(ip_format), string):
        if not re.match("^{}-{}$".format(ip_format, ip_format), string):
            raise ValueError
    return string

def resource_type_type(string):
    ''' Validates that resource types string contains only a combination
    of (s)ervice, (c)ontainer, (o)bject '''
    if set(string) - set("sco"):
        raise ValueError
    return ResourceTypes(_str=''.join(set(string)))

def services_type(string):
    ''' Validates that services string contains only a combination
    of (b)lob, (q)ueue, (t)able, (f)ile '''
    if set(string) - set("bqtf"):
        raise ValueError
    return Services(_str=''.join(set(string)))

# endregion

# region TRANSFORMS

def transform_acl_list_output(result):
    """ Transform to convert SDK output into a form that is more readily
    usable by the CLI and tools such as jpterm. """
    new_result = []
    for key in sorted(result.keys()):
        new_entry = OrderedDict()
        new_entry['Name'] = key
        new_entry['Start'] = result[key]['start']
        new_entry['Expiry'] = result[key]['expiry']
        new_entry['Permissions'] = result[key]['permission']
        new_result.append(new_entry)
    return new_result

def transform_cors_list_output(result):
    new_result = []
    for service in sorted(result.keys()):
        service_name = service
        for i, rule in enumerate(result[service]):
            new_entry = OrderedDict()
            new_entry['Service'] = service_name
            service_name = ''
            new_entry['Rule'] = i + 1
            new_entry['AllowedMethods'] = ', '.join((x for x in rule['allowedMethods']))
            new_entry['AllowedOrigins'] = ', '.join((x for x in rule['allowedOrigins']))
            new_entry['ExposedHeaders'] = ', '.join((x for x in rule['exposedHeaders']))
            new_entry['AllowedHeaders'] = ', '.join((x for x in rule['allowedHeaders']))
            new_entry['MaxAgeInSeconds'] = rule['maxAgeInSeconds']
            new_result.append(new_entry)
    return new_result

def transform_entity_query_output(result):
    new_results = []
    ignored_keys = ['etag', 'Timestamp', 'RowKey', 'PartitionKey']
    for row in result['items']:
        new_entry = OrderedDict()
        new_entry['PartitionKey'] = row['PartitionKey']
        new_entry['RowKey'] = row['RowKey']
        other_keys = sorted([x for x in row.keys() if x not in ignored_keys])
        for key in other_keys:
            new_entry[key] = row[key]
        new_results.append(new_entry)
    return new_results

def transform_file_list_output(result):
    """ Transform to convert SDK file/dir list output to something that
    more clearly distinguishes between files and directories. """
    new_result = []
    for item in result['items']:
        new_entry = OrderedDict()
        item_name = item['name']
        try:
            _ = item['properties']['contentLength']
            is_dir = False
        except KeyError:
            item_name = '{}/'.format(item_name)
            is_dir = True
        new_entry['Name'] = item_name
        new_entry['Type'] = 'dir' if is_dir else 'file'
        new_entry['ContentLength'] = '' if is_dir else item['properties']['contentLength']
        new_entry['LastModified'] = item['properties']['lastModified']
        new_result.append(new_entry)
    return sorted(new_result, key=lambda k: k['Name'])

def transform_logging_list_output(result):
    new_result = []
    for key in sorted(result.keys()):
        new_entry = OrderedDict()
        new_entry['Service'] = key
        new_entry['Read'] = result[key]['read']
        new_entry['Write'] = result[key]['write']
        new_entry['Delete'] = result[key]['delete']
        new_entry['RetentionPolicy'] = result[key]['retentionPolicy']['days']
        new_result.append(new_entry)
    return new_result

def transform_metrics_list_output(result):
    new_result = []
    for service in sorted(result.keys()):
        service_name = service
        for interval in sorted(result[service].keys()):
            item = result[service][interval]
            new_entry = OrderedDict()
            new_entry['Service'] = service_name
            service_name = ''
            new_entry['Interval'] = interval
            new_entry['Enabled'] = item['enabled']
            new_entry['IncludeApis'] = item['includeApis']
            new_entry['RetentionPolicy'] = item['retentionPolicy']['days']
            new_result.append(new_entry)
    return new_result

def transform_url(result):
    """ Ensures the resulting URL string does not contain extra / characters """
    result = re.sub('//', '/', result)
    result = re.sub('/', '//', result, count=1)
    return result

#endregion
