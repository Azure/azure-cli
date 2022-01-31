# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import argparse
from azure.cli.core.azclierror import ArgumentUsageError

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.commands import parameters
from knack.util import CLIError
try:
    from urllib.parse import urlparse, urlsplit
except ImportError:
    from urlparse import urlparse, urlsplit  # pylint: disable=import-error

MSI_LOCAL_ID = '[system]'


def process_ts_create_or_update_namespace(namespace):
    from azure.cli.core.commands.validators import validate_tags
    validate_tags(namespace)
    if namespace.template_file and not os.path.isfile(namespace.template_file):
        raise CLIError('Please enter a valid file path')


def _validate_template_spec(namespace):
    if namespace.template_spec is None:
        if (namespace.name is None or namespace.resource_group_name is None):
            raise CLIError('incorrect usage: Please enter '
                           'a resource group and resource name or a resource ID for --template-spec')
    else:
        from azure.mgmt.core.tools import is_valid_resource_id
        namespace.template_spec = namespace.template_spec.strip("\"")
        if not is_valid_resource_id(namespace.template_spec):
            raise CLIError('--template-spec is not a valid resource ID.')


def _validate_template_spec_out(namespace):
    _validate_template_spec(namespace)
    if namespace.output_folder and not os.path.isdir(namespace.output_folder):
        raise CLIError('Please enter a valid output folder')

def validate_deployment_stack_files(namespace):
    if namespace.template_file and not os.path.isfile(namespace.template_file):
        raise InvalidArgumentValueError('Please enter a valid template file path')


def _validate_deployment_name_with_template_specs(namespace):
    # If missing,try come out with a name associated with the template name
    if namespace.deployment_name is None:
        template_filename = None
        if namespace.template_file and os.path.isfile(namespace.template_file):
            template_filename = namespace.template_file
        if namespace.template_uri and urlparse(namespace.template_uri).scheme:
            template_filename = urlsplit(namespace.template_uri).path
        if namespace.template_spec:
            from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
            namespace.template_spec = namespace.template_spec.strip("\"")
            if not is_valid_resource_id(namespace.template_spec):
                raise CLIError('--template-spec is not a valid resource ID.')
            if namespace.template_spec.__contains__("versions") is False:
                raise CLIError('Please enter a valid template spec version ID.')
            template_filename = parse_resource_id(namespace.template_spec).get('resource_name')
        if template_filename:
            template_filename = os.path.basename(template_filename)
            namespace.deployment_name = os.path.splitext(template_filename)[0]
        else:
            namespace.deployment_name = 'deployment1'


def _validate_deployment_name(namespace):
    # If missing,try come out with a name associated with the template name
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


def process_deployment_create_namespace(namespace):
    try:
        if [bool(namespace.template_uri), bool(namespace.template_file),
                bool(namespace.template_spec)].count(True) != 1:
            raise CLIError('incorrect usage: Chose only one of'
                           ' --template-file FILE | --template-uri URI | --template-spec ID to pass in')
    except Exception:  # pylint: disable=broad-except
        if [bool(namespace.template_uri), bool(namespace.template_file)].count(True) != 1:
            raise CLIError('incorrect usage: Chose only one of'
                           ' --template-file FILE | --template-uri URI')
    if(bool(namespace.template_uri) or bool(namespace.template_file)):
        _validate_deployment_name(namespace)
    else:
        _validate_deployment_name_with_template_specs(namespace)


def internal_validate_lock_parameters(namespace, resource_group, resource_provider_namespace,
                                      parent_resource_path, resource_type, resource_name):
    if resource_group is None:
        if resource_name is not None:
            from msrestazure.tools import parse_resource_id, is_valid_resource_id
            if not is_valid_resource_id(resource_name):
                raise CLIError('--resource is not a valid resource ID. '
                               '--resource as a resource name is ignored if --resource-group is not given.')
            # resource-name is an ID, populate namespace
            id_dict = parse_resource_id(resource_name)
            for id_part in ['resource_name', 'resource_type', 'resource_group']:
                setattr(namespace, id_part, id_dict.get(id_part))
            setattr(namespace, 'resource_provider_namespace', id_dict.get('resource_namespace'))
            setattr(namespace, 'parent_resource_path', id_dict.get('resource_parent').strip('/'))

        if resource_type is not None:
            raise CLIError('--resource-type is ignored if --resource-group is not given.')
        if resource_provider_namespace is not None:
            raise CLIError('--namespace is ignored if --resource-group is not given.')
        if parent_resource_path is not None:
            raise CLIError('--parent is ignored if --resource-group is not given.')
        return

    if resource_name is None:
        if resource_type is not None:
            raise CLIError('--resource-type is ignored if --resource is not given.')
        if resource_provider_namespace is not None:
            raise CLIError('--namespace is ignored if --resource is not given.')
        if parent_resource_path is not None:
            raise CLIError('--parent is ignored if --resource is not given.')
        return

    if not resource_type:
        raise CLIError('--resource-type is required if the name, --resource, is present')

    parts = resource_type.split('/')
    if resource_provider_namespace is None:
        if len(parts) == 1:
            raise CLIError('A resource namespace is required if the name, --resource, is present.'
                           'Expected <namespace>/<type> or --namespace=<namespace>')
    elif len(parts) != 1:
        raise CLIError('Resource namespace specified in both --resource-type and --namespace')


def validate_lock_parameters(namespace):
    internal_validate_lock_parameters(namespace,
                                      getattr(namespace, 'resource_group', None),
                                      getattr(namespace, 'resource_provider_namespace', None),
                                      getattr(namespace, 'parent_resource_path', None),
                                      getattr(namespace, 'resource_type', None),
                                      getattr(namespace, 'resource_name', None))


def _parse_lock_id(id_arg):
    """
    Lock ids look very different from regular resource ids, this function uses a regular expression
    that parses a lock's id and extracts the following parameters if available:
    -lock_name: the lock's name; always present in a lock id
    -resource_group: the name of the resource group; present in group/resource level locks
    -resource_provider_namespace: the resource provider; present in resource level locks
    -resource_type: the resource type; present in resource level locks
    -resource_name: the resource name; present in resource level locks
    -parent_resource_path: the resource's parent path; present in child resources such as subnets
    """
    regex = re.compile(
        '/subscriptions/[^/]*(/resource[gG]roups/(?P<resource_group>[^/]*)'
        '(/providers/(?P<resource_provider_namespace>[^/]*)'
        '(/(?P<parent_resource_path>.*))?/(?P<resource_type>[^/]*)/(?P<resource_name>[^/]*))?)?'
        '/providers/Microsoft.Authorization/locks/(?P<lock_name>[^/]*)')

    return regex.match(id_arg).groupdict()


def validate_subscription_lock(namespace):
    if getattr(namespace, 'ids', None):
        for lock_id in getattr(namespace, 'ids'):
            if _parse_lock_id(lock_id).get('resource_group'):
                raise CLIError('{} is not a valid subscription-level lock id.'.format(lock_id))


def validate_group_lock(namespace):
    if getattr(namespace, 'ids', None):
        for lock_id in getattr(namespace, 'ids'):
            lock_id_dict = _parse_lock_id(lock_id)
            if not lock_id_dict.get('resource_group') or lock_id_dict.get('resource_name'):
                raise CLIError('{} is not a valid group-level lock id.'.format(lock_id))
    else:
        if not getattr(namespace, 'resource_group', None):
            raise CLIError('Missing required --resource-group/-g parameter.')


def validate_resource_lock(namespace):
    if getattr(namespace, 'ids', None):
        for lock_id in getattr(namespace, 'ids'):
            lock_id_dict = _parse_lock_id(lock_id)
            if not all((lock_id_dict.get(param)) for param in ['resource_group',
                                                               'resource_provider_namespace',
                                                               'resource_type',
                                                               'resource_name']):
                raise CLIError('{} is not a valid resource-level lock id.'.format(lock_id))
    else:
        if not getattr(namespace, 'resource_name', None):
            raise CLIError('Missing required {} parameter.'.format('resource_name'))
        kwargs = {}
        for param in ['resource_group', 'resource_name', 'resource_provider_namespace', 'parent_resource_path',
                      'resource_type']:
            kwargs[param] = getattr(namespace, param, None)
        internal_validate_lock_parameters(namespace, **kwargs)


def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)


def process_assign_identity_namespace(cmd, namespace):
    validate_msi(cmd, namespace, from_identity_command=True)


def process_assignment_create_namespace(cmd, namespace):
    validate_msi(cmd, namespace)


def validate_msi(cmd, namespace, from_identity_command=False):
    identities = None
    if from_identity_command:
        if namespace.mi_system_assigned is not None or namespace.mi_user_assigned is None:
            identities = [MSI_LOCAL_ID]
            if namespace.mi_user_assigned is not None:
                raise ArgumentUsageError(
                    'Only one type of managed identity is allowed. '
                    'Please use either --mi-system-assigned or --mi-user-assigned')
    else:
        if namespace.mi_system_assigned is not None or namespace.assign_identity is not None:
            identities = [MSI_LOCAL_ID]
            if namespace.mi_user_assigned is not None:
                raise ArgumentUsageError(
                    'Only one type of managed identity is allowed. '
                    'Please use either --mi-system-assigned or --mi-user-assigned')

    if namespace.mi_user_assigned is not None:
        identities = [namespace.mi_user_assigned]

    if identities is not None:
        user_assigned_identities = [x for x in identities if x != MSI_LOCAL_ID]
        if user_assigned_identities and not cmd.supported_api_version(min_api='2021-06-01'):
            raise ArgumentUsageError(
                'User assigned identity is only available under profile '
                'with minimum Authorization API version of 2021-06-01')

        if not namespace.identity_scope and getattr(namespace.identity_role, 'is_default', None) is None:
            raise ArgumentUsageError(
                "'--role {}' is not applicable as the '--identity-scope' is not provided"
                .format(namespace.identity_role))

        if namespace.identity_scope:
            if identities and MSI_LOCAL_ID not in identities:
                raise ArgumentUsageError(
                    "'--identity-scope'/'--role' is only applicable when assigning a system identity")

    elif namespace.identity_scope or getattr(namespace.identity_role, 'is_default', None) is None:
        raise ArgumentUsageError(
            "'--identity-scope'/'--role' is only applicable when assigning a system identity")


# pylint: disable=too-few-public-methods
class RollbackAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, 'rollback_on_error', '' if not values else values)
