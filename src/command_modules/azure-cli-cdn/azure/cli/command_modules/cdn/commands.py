# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from ._client_factory import cf_cdn


def custom(sub_path):
    return'azure.cli.command_modules.cdn.custom#{}'.format(sub_path)


def mgmt(sub_path):
    return 'azure.mgmt.cdn#CdnManagementClient.{}'.format(sub_path)


def endpoint(sub_path):
    return 'azure.mgmt.cdn.operations.endpoints_operations#EndpointsOperations.{}'.format(sub_path)


def profile(sub_path):
    return 'azure.mgmt.cdn.operations.profiles_operations#ProfilesOperations.{}'.format(sub_path)


def domain(sub_path):
    path = 'azure.mgmt.cdn.operations.custom_domains_operations#CustomDomainsOperations.{}'
    return path.format(sub_path)


def origin(sub_path):
    return 'azure.mgmt.cdn.operations.origins_operations#OriginsOperations.{}'.format(sub_path)


def edge(sub_path):
    return 'azure.mgmt.cdn.operations.edge_nodes_operations#EdgeNodesOperations.{}'.format(sub_path)


def command(cmd, method, formatter=custom):
    cli_command(__name__, cmd, formatter(method), cf_cdn)


def endpoint_command(name, method=None, use_custom=False):
    formatter = custom if use_custom else endpoint
    command('cdn endpoint {}'.format(name), method or name, formatter)


def generic_endpoint_command(name, custom_handler):
    cli_generic_update_command(__name__,
                               'cdn endpoint {}'.format(name),
                               endpoint('get'),
                               endpoint('update'),
                               cf_cdn,
                               setter_arg_name='endpoint_update_properties',
                               custom_function_op=custom(custom_handler))


def generic_profile_command(name, custom_handler):
    cli_generic_update_command(__name__,
                               'cdn profile {}'.format(name),
                               profile('get'),
                               profile('update'),
                               cf_cdn,
                               setter_arg_name='profile_update_properties',
                               custom_function_op=custom(custom_handler))


def profile_command(name, method=None, use_custom=False):
    formatter = custom if use_custom else profile
    command('cdn profile {}'.format(name), method or name, formatter)


def domain_command(name, method=None, use_custom=False):
    formatter = custom if use_custom else domain
    command('cdn custom-domain {}'.format(name), method or name, formatter)


def origin_command(name, method=None, use_custom=False):
    formatter = custom if use_custom else origin
    command('cdn origin {}'.format(name), method or name, formatter)


def edge_command(name, method=None, use_custom=False):
    formatter = custom if use_custom else edge
    command('cdn edge-node {}'.format(name), method or name, formatter)


cli_command(__name__, 'cdn name-exists', mgmt('check_name_availability'), cf_cdn)
cli_command(__name__, 'cdn usage', mgmt('check_resource_usage'), cf_cdn)

endpoint_command('show', 'get')
for c in ['start', 'stop', 'delete']:
    endpoint_command(c)
endpoint_command('list', 'list_by_profile')
endpoint_command('load', 'load_content')
endpoint_command('purge', 'purge_content')
endpoint_command('validate-custom-domain', 'validate_custom_domain')
endpoint_command('create', 'create_endpoint', use_custom=True)
generic_endpoint_command('update', 'update_endpoint')

profile_command('show', 'get')
profile_command('usage', 'list_resource_usage')
profile_command('delete')
profile_command('list', 'list_profiles', use_custom=True)
profile_command('create', 'create_profile', use_custom=True)
generic_profile_command('update', 'update_profile')

domain_command('show', 'get')
domain_command('list', 'list_by_endpoint')
for c in ['delete', 'create']:
    domain_command(c)

origin_command('show', 'get')
origin_command('list', 'list_by_endpoint')

edge_command('list')
