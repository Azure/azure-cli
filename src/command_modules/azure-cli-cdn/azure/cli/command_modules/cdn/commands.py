# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from ._client_factory import cf_cdn


def mgmt(sub_path):
    return 'azure.mgmt.cdn#CdnManagementClient.{}'.format(sub_path)


def endpoint(sub_path):
    return 'azure.mgmt.cdn.operations.endpoints_operations#{}'.format(sub_path)


def profile(sub_path):
    return 'azure.mgmt.cdn.operations.profiles_operations#{}'.format(sub_path)


def domain(sub_path):
    return 'azure.mgmt.cdn.operations.custom_domains_operations#{}'.format(sub_path)


def origin(sub_path):
    return 'azure.mgmt.cdn.operations.origins_operations#{}'.format(sub_path)


def edge(sub_path):
    return 'azure.mgmt.cdn.operations.edge_nodes_operations#{}'.format(sub_path)


def endpoint_command(name, method=None):
    cli_command(__name__,
                'cdn endpoint {}'.format(name),
                endpoint('EndpointsOperations.{}'.format(method or name)),
                cf_cdn)


def profile_command(name, method=None):
    cli_command(__name__,
                'cdn profile {}'.format(name),
                profile('ProfilesOperations.{}'.format(method or name)),
                cf_cdn)


def domain_command(name, method=None):
    cli_command(__name__,
                'cdn domain {}'.format(name),
                domain('CustomDomainsOperations.{}'.format(method or name)),
                cf_cdn)


def origin_command(name, method=None):
    cli_command(__name__,
                'cdn origin {}'.format(name),
                origin('OriginsOperations.{}'.format(method or name)),
                cf_cdn)


def edge_command(name, method=None):
    cli_command(__name__,
                'cdn edge-node {}'.format(name),
                edge('EdgeNodesOperations.{}'.format(method or name)),
                cf_cdn)


cli_command(__name__, 'cdn name-exists', mgmt('check_name_availability'), cf_cdn)
cli_command(__name__, 'cdn usage', mgmt('check_resource_usage'), cf_cdn)

endpoint_command('show', 'get')
endpoint_command('delete')

profile_command('show', 'get')
profile_command('delete')

domain_command('show', 'get')
domain_command('delete')

origin_command('show', 'get')
origin_command('list', 'list_by_endpoint')

edge_command('list')
