from datetime import datetime
import re

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

def validate_key_value_pairs(string):
    ''' Validates key-value pairs in the following format: a=b;c=d '''
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=', 1) for x in kv_list)
    return result

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

def validate_tags(string):
    ''' Validates the string containers only key-value pairs and single
    tags in the format: a=b;c '''
    result = None
    if string:
        result = validate_key_value_pairs(string)
        s_list = [x for x in string.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result
