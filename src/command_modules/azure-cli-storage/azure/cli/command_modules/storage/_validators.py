from datetime import datetime
import os
import re

from azure.cli.commands.validators import validate_key_value_pairs
from azure.storage.models import ResourceTypes, Services
from azure.storage.blob.models import ContainerPermissions

def validate_container_permission(string):
    ''' Validates that permission string contains only a combination
    of (r)ead, (w)rite, (d)elete, (l)ist. '''
    if set(string) - set('rwdl'):
        raise ValueError('valid values are (r)ead, (w)rite, (d)elete, (l)ist or a combination ' + \
                         'thereof (ex: rw)')
    return ContainerPermissions(_str=''.join(set(string)))

def validate_datetime_as_string(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format).strftime(date_format)

def validate_datetime(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format)

def validate_lease_duration(string):
    ''' Validates that duration falls between 15 and 60 or -1 '''
    int_val = int(string)
    if (int_val < 15 and int_val != -1) or int_val > 60:
        raise ValueError
    return int_val

def validate_id(string):
    if len(string) > 64:
        raise ValueError

def validate_ip_range(string):
    ''' Validates an IP address or IP address range. '''
    ip_format = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    if not re.match("^{}$".format(ip_format), string):
        if not re.match("^{}-{}$".format(ip_format, ip_format), string):
            raise ValueError
    return string

def validate_quota(string):
    ''' Validates that share service quota is between 1-5. '''
    val = int(string)
    if val < 1 or val > 5:
        raise ValueError('share quota must be between 1 and 5')
    return string

def validate_resource_types(string):
    ''' Validates that resource types string contains only a combination
    of (s)ervice, (c)ontainer, (o)bject '''
    if set(string) - set("sco"):
        raise ValueError
    return ResourceTypes(_str=''.join(set(string)))

def validate_services(string):
    ''' Validates that services string contains only a combination
    of (b)lob, (q)ueue, (t)able, (f)ile '''
    if set(string) - set("bqtf"):
        raise ValueError
    return Services(_str=''.join(set(string)))

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
