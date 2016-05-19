import argparse

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, patch_aliases

from ._validators import validate_resource_type, validate_parent
from ._actions import ResourceResolveAPIAction

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'api_version': {
        'name': '--api-version',
        'help': 'The api version of the resource (omit for latest)',
        'required': False
    },
    'resource_provider_namespace': {
        'name': '--resource-provider-namespace',
        'help': argparse.SUPPRESS,
        'required': False
    },
    'resource_type': {
        'name': '--resource-type',
        'help': 'The resource type in <namespace>/<type> format',
        'type': validate_resource_type,
        'action': ResourceResolveAPIAction
    },
    'parent_resource_path': {
        'name': '--parent',
        'help': 'The parent resource type in <type>/<name> format',
        'type': validate_parent,
        'required': False
    }
})
