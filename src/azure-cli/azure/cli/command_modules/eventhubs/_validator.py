# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
from azure.cli.core.util import CLIError


def validate_storageaccount(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if namespace.storage_account:
        if not is_valid_resource_id(namespace.storage_account):
            namespace.storage_account = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage',
                type='storageAccounts',
                name=namespace.storage_account)


def validate_partner_namespace(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if namespace.partner_namespace:
        if not is_valid_resource_id(namespace.partner_namespace):
            namespace.partner_namespace = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.EventHub',
                type='namespaces',
                name=namespace.partner_namespace)


def validate_rights(namespace):
    if 'Manage' in namespace.rights:
        if 'Listen' not in namespace.rights or 'Send' not in namespace.rights:
            raise CLIError('Error : Assigning \'Manage\' to --rights requires \'Listen\' and \'Send\' to be included with. e.g. --rights Manage Send Listen')


def validate_clustercapcity(namespace):
    if namespace.capacity:
        if namespace.capacity != 1:
            raise CLIError('Error : Allowed values for Capacity of Cluster is \'1\'')


def validate_private_endpoint_connection_id(namespace):
    if namespace.connection_id:
        from azure.cli.core.util import parse_proxy_resource_id
        result = parse_proxy_resource_id(namespace.connection_id)
        namespace.resource_group_name = result['resource_group']
        namespace.namespace_name = result['name']
        namespace.private_endpoint_connection_name = result['child_name_1']

    if not all([namespace.namespace_name, namespace.resource_group_name, namespace.private_endpoint_connection_name]):
        raise CLIError('incorrect usage: [--id ID | --name NAME --account-name NAME]')

    del namespace.connection_id
