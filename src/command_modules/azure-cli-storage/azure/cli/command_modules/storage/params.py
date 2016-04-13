from datetime import datetime
from os import environ
import re

from azure.storage.models import ResourceTypes, Services
from azure.storage.blob.models import ContainerPermissions

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from azure.cli._locale import L

# HELPER METHODS

def extend_parameter(parameter_metadata, **kwargs):
    modified_parameter_metadata = parameter_metadata.copy()
    modified_parameter_metadata.update(kwargs)
    return modified_parameter_metadata

def _parse_container_permission(string):
    ''' Validates that permission string contains only a combination
    of (r)ead, (w)rite, (d)elete, (l)ist. '''
    if set(string) - set("rwdl"):
        raise ValueError
    return ContainerPermissions(_str=''.join(set(string)))

def _parse_datetime(string):
    ''' Validates UTC datettime in format 'Y-m-d_H:M:S'. '''
    date_format = '%Y-%m-%d_%H:%M:%S'
    return datetime.strptime(string, date_format)

def _parse_ip_range(string):
    ''' Validates an IP address or IP address range. '''
    ip_format = "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    if not re.match("^{}$".format(ip_format), string):
        if not re.match("^{}-{}$".format(ip_format, ip_format), string):
            raise ValueError
    return string

def _parse_key_value_pairs(string):
    ''' Validates key-value pairs in the following format: a=b;c=d '''
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=') for x in kv_list)
    return result

def _parse_resource_types(string):
    ''' Validates that resource types string contains only a combination
    of (s)ervice, (c)ontainer, (o)bject '''
    if set(string) - set("sco"):
        raise ValueError
    return ResourceTypes(_str=''.join(set(string)))

def _parse_services(string):
    ''' Validates that services string contains only a combination
    of (b)lob, (q)ueue, (t)able, (f)ile '''
    if set(string) - set("bqtf"):
        raise ValueError
    return Services(_str=''.join(set(string)))
    

def _parse_tags(string):
    ''' Validates the string containers only key-value pairs and single
    tags in the format: a=b;c '''
    result = None
    if string:
        result = _parse_key_value_pairs(string)
        s_list = [x for x in string.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
PARAMETER_ALIASES.update({
    'account_key': {
        'name': '--account-key -k',
        'help': L('the storage account key'),
        # While account key *may* actually be required if the environment variable hasn't been
        # specified, it is only required unless the connection string has been specified
        'required': False,
        'default': environ.get('AZURE_STORAGE_ACCESS_KEY')
    },
    'account_name': {
        'name': '--account-name -n',
        'help': L('the storage account name'),
        # While account name *may* actually be required if the environment variable hasn't been
        # specified, it is only required unless the connection string has been specified
        'required': False,
        'default': environ.get('AZURE_STORAGE_ACCOUNT')
    },
    'account_name_required': {
        # this is used only to obtain the connection string. Thus, the env variable default
        # does not apply and this is a required parameter
        'name': '--account-name -n',
        'help': L('the storage account name'),
        'required': True
    },
    'blob_name': {
        'name': '--blob-name -b',
        'help': L('the name of the blob'),
        'required': True
    },
    'container_name': {
        'name': '--container-name -c',
        'required': True
    },
    'connection_string': {
        'name': '--connection-string',
        'help': L('the storage connection string'),
        # You can either specify connection string or name/key. There is no convenient way
        # to express this kind of relationship in argparse...
        # TODO: Move to exclusive group
        'required': False,
        'default': environ.get('AZURE_STORAGE_CONNECTION_STRING')
    },
    'expiry': {
        'name': '--expiry',
        'help': L('expiration UTC datetime of SAS token ("Y-m-d_H:M:S")'),
        'type': _parse_datetime
    },
    'if_modified_since': {
        'name': '--if-modified-since',
        'help': L('alter only if modified since supplied UTC datetime ("Y-m-d_H:M:S")'),
        'type': _parse_datetime,
        'required': False,
    },
    'if_unmodified_since': {
        'name': '--if-unmodified-since',
        'help': L('alter only if unmodified since supplied UTC datetime ("Y-m-d_H:M:S")'),
        'type': _parse_datetime,
        'required': False,
    },
    'ip': {
        'name': '--ip',
        'help': L('specifies the IP address or range of IP addresses from which to accept ' + \
                  'requests.'),
        'type': _parse_ip_range
    },
    'lease_id': {
        'name': '--lease-id',
        'metavar': 'LEASE ID',
        'help': L('Lease ID in GUID format.')        
    },
    'metadata': {
        'name': '--metadata',
        'metavar': 'METADATA',
        'type': _parse_key_value_pairs,
        'help': L('metadata in "a=b;c=d" format')
    },
    'optional_resource_group_name':
        extend_parameter(GLOBAL_COMMON_PARAMETERS['resource_group_name'], required=False),
    'permission': {
        'name': '--permission',
        'help': L('permissions granted: (r)ead (w)rite (d)elete (l)ist. Can be combined.'),
        'metavar': 'PERMISSION',
        # TODO: This will be problematic because the other sas types take different permissions
        'type': _parse_container_permission
    },
    'resource_types': {
        'name': '--resource-types',
        'help': L('the resource types the SAS is applicable for. Allowed values: (s)ervice (c)ontainer (o)bject. Can be combined.'),
        'type': _parse_resource_types
    },
    'services': {
        'name': '--services',
        'help': L('the storage services the SAS is applicable for. Allowed values: (b)lob (f)ile (q)ueue (t)able. Can be combined.'),
        'type': _parse_services
    },
    'share_name': {
        'name': '--share-name',
        'help': L('the name of the file share'),
        'required': True,
    },
    'start': {
        'name': '--start',
        'help': L('start UTC datetime of SAS token ("Y-m-d_H:M:S"). Defaults to time of request.'),
        'type': _parse_datetime
    },
    'tags' : {
        'name': '--tags',
        'metavar': 'TAGS',
        'help': L('individual and/or key/value pair tags in "a=b;c" format'),
        'required': False,
        'type': _parse_tags
    },
    'timeout': {
        'name': '--timeout',
        'help': L('timeout in seconds'),
        'required': False,
        'type': int
    }
})

# SUPPLEMENTAL (EXTRA) PARAMETER SETS

STORAGE_DATA_CLIENT_ARGS = {
    'account_name': PARAMETER_ALIASES['account_name'],
    'account_key': PARAMETER_ALIASES['account_key'],
    'connection_string': PARAMETER_ALIASES['connection_string'],
}
