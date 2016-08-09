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
from azure.storage.blob.models import ContainerPermissions
from azure.storage.table.models import TablePermissions
from azure.storage.queue.models import QueuePermissions

class IgnoreAction(argparse.Action): # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(None, 'unrecognized argument: {} {}'.format(
            option_string, values or ''))

def validate_container_permission(string):
    ''' Validates that permission string contains only a combination
    of (r)ead, (w)rite, (d)elete, (l)ist. '''
    if set(string) - set('rwdl'):
        raise ValueError('valid values are (r)ead, (w)rite, (d)elete, (l)ist or a combination ' + \
                         'thereof (ex: rw)')
    return ContainerPermissions(_str=''.join(set(string)))

def validate_table_permission(string):
    ''' Validates that permission string contains only a combination
    of (r)ead, (a)dd, (u)pdate, (d)elete. '''
    if set(string) - set('raud'):
        raise ValueError('valid values are (r)ead, (a)dd, (u)pdate, (d)elete or a combination ' + \
                         'thereof (ex: ra)')
    return TablePermissions(_str=''.join(set(string)))

def validate_queue_permission(string):
    ''' Validates that permission string contains only a combination
    of (r)ead, (a)dd, (u)pdate, (p)rocess [delete]. '''
    if set(string) - set('raup'):
        raise ValueError('valid values are (r)ead, (a)dd, (u)pdate, (p)rocess [delete] or a '
                         'combination thereof (ex: ra)')
    return QueuePermissions(_str=''.join(set(string)))

def validate_datetime_as_string(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format).strftime(date_format)

def validate_datetime(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format)

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
    namespace.entity = values

def validate_ip_range(string):
    ''' Validates an IP address or IP address range. '''
    ip_format = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    if not re.match("^{}$".format(ip_format), string):
        if not re.match("^{}-{}$".format(ip_format, ip_format), string):
            raise ValueError
    return string

def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)

def validate_resource_types(string):
    ''' Validates that resource types string contains only a combination
    of (s)ervice, (c)ontainer, (o)bject '''
    if set(string) - set("sco"):
        raise ValueError
    return ResourceTypes(_str=''.join(set(string)))

def validate_select(namespace):
    if namespace.select:
        namespace.select = ','.join(namespace.select)

def validate_services(string):
    ''' Validates that services string contains only a combination
    of (b)lob, (q)ueue, (t)able, (f)ile '''
    if set(string) - set("bqtf"):
        raise ValueError
    return Services(_str=''.join(set(string)))

def validate_unicode_string(string):
    try:
        # Python2
        return unicode(string)
    except NameError:
        # Python3
        return string

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

def transform_url(result):
    """ Ensures the resulting URL string does not contain extra / characters """
    result = re.sub('//', '/', result)
    result = re.sub('/', '//', result, count=1)
    return result
