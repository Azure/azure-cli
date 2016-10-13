#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import collections
import os
try:
    from urllib.parse import urlparse, urlsplit
except ImportError:
    from urlparse import urlparse, urlsplit # pylint: disable=import-error

from azure.cli.core.parser import IncorrectUsageError

from ._factory import _resource_client_factory

def validate_resource_type(string):
    ''' Validates that resource type is provided in <namespace>/<type> format '''
    type_comps = string.split('/')
    try:
        namespace_comp = type_comps[0]
        resource_comp = type_comps[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')
    ResourceType = collections.namedtuple('ResourceType', 'namespace type')
    return ResourceType(namespace=namespace_comp, type=resource_comp)

def validate_parent(string):
    ''' Validates that parent is provided in <type>/<name> format '''
    if not string:
        return string
    parent_comps = string.split('/')
    try:
        type_comp = parent_comps[0]
        name_comp = parent_comps[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --parent must be in <type>/<name> format.')
    ParentType = collections.namedtuple('ParentType', 'type name')
    return ParentType(type=type_comp, name=name_comp)

def validate_deployment_name(namespace):
    #If missing,try come out with a name associated with the template name
    if namespace.deployment_name is None:
        template_filename = None
        if namespace.template_file and os.path.isfile(namespace.template_file):
            template_filename = namespace.template_file
        if namespace.template_uri and urlparse(namespace.template_uri).scheme:
            template_filename = urlsplit(namespace.template_uri).path
        if template_filename:
            template_filename = os.path.basename(template_filename)
            namespace.deployment_name = os.path.splitext(template_filename)[0]
        else:
            namespace.deployment_name = 'deployment1'

def _resolve_api_version(rcf, resource_type, parent=None):

    provider = rcf.providers.get(resource_type.namespace)
    resource_type_str = '{}/{}'.format(parent.type, resource_type.type) \
        if parent else resource_type.type

    rt = [t for t in provider.resource_types if t.resource_type == resource_type_str]
    if not rt:
        raise IncorrectUsageError('Resource type {} not found.'
                                  .format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise IncorrectUsageError(
            'API version is required and could not be resolved for resource {}/{}'
            .format(resource_type.namespace, resource_type.type))

def resolve_resource_parameters(namespace):
    n = namespace

    param_set = set(['resource_type', 'api_version',
                     'resource_provider_namespace', 'parent_resource_path'])
    if not param_set.issubset(set(n.__dict__.keys())):
        return

    resource_tuple = n.resource_type
    parent_tuple = n.parent_resource_path

    rcf = _resource_client_factory()
    n.api_version = n.api_version or _resolve_api_version(rcf, resource_tuple, parent_tuple)
    n.resource_type = resource_tuple.type
    n.resource_provider_namespace = resource_tuple.namespace
    n.parent_resource_path = '{}/{}'.format(parent_tuple.type, parent_tuple.name) \
        if parent_tuple else ''
