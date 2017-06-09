# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

try:
    from urllib.parse import urlparse, urlsplit
except ImportError:
    from urlparse import urlparse, urlsplit  # pylint: disable=import-error


from azure.cli.core.util import CLIError


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


def validate_deployment_parameters(namespace):

    from azure.cli.core.util import shell_safe_json_parse, get_file_json

    def _try_parse_json_object(value):
        try:
            parsed = shell_safe_json_parse(value)
            return parsed.get('parameters', parsed)
        except CLIError:
            return None

    def _try_load_file_object(value):
        if os.path.isfile(value):
            parsed = get_file_json(value, throw_on_empty=False)
            return parsed.get('parameters', parsed)
        return None

    def _try_parse_key_value_object(parameters, value):
        try:
            key, value = value.split('=', 1)
        except ValueError:
            return False

        try:
            parameters[key] = {'value': shell_safe_json_parse(value)}
        except (ValueError, CLIError):
            parameters[key] = {'value': value}

        return True

    parameters = {}
    for params in namespace.parameters or []:
        for item in params:
            if not _try_parse_key_value_object(parameters, item):
                param_obj = _try_load_file_object(item) or _try_parse_json_object(item)
                if not param_obj:
                    raise CLIError('Unable to parse parameter: {}'.format(item))
                parameters.update(param_obj)

    namespace.parameters = parameters


def process_deployment_create_namespace(namespace):
    if (namespace.template_uri and namespace.template_file) or \
            (not namespace.template_uri and not namespace.template_file):
        raise CLIError('incorrect usage: --template-file FILE | --template-uri URI')
    _validate_deployment_name(namespace)


def internal_validate_lock_parameters(resource_group_name, resource_provider_namespace,
                                      parent_resource_path, resource_type, resource_name):
    if resource_group_name is None:
        if resource_name is not None:
            raise CLIError('--resource-name is ignored if --resource-group is not given.')
        if resource_type is not None:
            raise CLIError('--resource-type is ignored if --resource-group is not given.')
        if resource_provider_namespace is not None:
            raise CLIError('--namespace is ignored if --resource-group is not given.')
        if parent_resource_path is not None:
            raise CLIError('--parent is ignored if --resource-group is not given.')
        return

    if resource_name is None:
        if resource_type is not None:
            raise CLIError('--resource-type is ignored if --resource-name is not given.')
        if resource_provider_namespace is not None:
            raise CLIError('--namespace is ignored if --resource-name is not given.')
        if parent_resource_path is not None:
            raise CLIError('--parent is ignored if --resource-name is not given.')
        return

    if not resource_type:
        raise CLIError('--resource-type is required if --resource-name is present')

    parts = resource_type.split('/')
    if resource_provider_namespace is None:
        if len(parts) == 1:
            raise CLIError('A resource namespace is required if --resource-name is present.'
                           'Expected <namespace>/<type> or --namespace=<namespace>')
    elif len(parts) != 1:
        raise CLIError('Resource namespace specified in both --resource-type and --namespace')


def validate_lock_parameters(namespace):
    internal_validate_lock_parameters(getattr(namespace, 'resource_group_name', None),
                                      getattr(namespace, 'resource_provider_namespace', None),
                                      getattr(namespace, 'parent_resource_path', None),
                                      getattr(namespace, 'resource_type', None),
                                      getattr(namespace, 'resource_name', None))
