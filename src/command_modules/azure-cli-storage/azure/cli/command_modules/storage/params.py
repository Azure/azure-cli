from os import environ

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from azure.cli._locale import L

# HELPER METHODS

def extend_parameter(parameter_metadata, **kwargs):
    modified_parameter_metadata = parameter_metadata.copy()
    modified_parameter_metadata.update(kwargs)
    return modified_parameter_metadata

def _parse_datetime(string):
    date_format = '%Y-%m-%d_%H:%M:%S'
    return datetime.strptime(string, date_format)

def _parse_key_value_pairs(string):
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=') for x in kv_list)
    return result

def _parse_tags(string):
    result = None
    if string:
        result = _parse_key_value_pairs(string)
        s_list = [x for x in string.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result

# BASIC PARAMETER CONFIGURATION

COMMON_PARAMETERS = GLOBAL_COMMON_PARAMETERS.copy()
COMMON_PARAMETERS.update({
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
    'share_name': {
        'name': '--share-name',
        'help': L('the name of the file share'),
        'required': True,
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
    'account_name': COMMON_PARAMETERS['account_name'],
    'account_key': COMMON_PARAMETERS['account_key'],
    'connection_string': COMMON_PARAMETERS['connection_string'],
}

# COMMON PARAMETER AUTOCOMMAND MASKS

LEASE_AUTOCOMMAND_ALIASES = {
    'lease_id': COMMON_PARAMETERS['lease_id']
}

METADATA_AUTOCOMMAND_ALIASES = {
    'metadata': COMMON_PARAMETERS['metadata']
}

COPY_AUTOCOMMAND_ALIASES = {
}

PROPERTIES_AUTOCOMMAND_ALIASES = {
}

SERVICE_PROPERTIES_AUTOCOMMAND_ALIASES = {
}

ACL_AUTOCOMMAND_ALIASES = {
}
