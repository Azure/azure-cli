# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def validate_component_version(namespace):
    if namespace.component_version:
        import re
        invalid_component_versions = [cv for cv in namespace.component_version if not re.match('^[^=]+=[^=]+$', cv)]
        if any(invalid_component_versions):
            raise ValueError('Component verions must be in the form component=version. '
                             'Invalid component version(s): {}'.format(', '.join(invalid_component_versions)))


# Validate storage account.
def validate_storage_account(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.storage_account:
        if not is_valid_resource_id(namespace.storage_account):
            namespace.storage_account = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage', type='storageAccounts',
                name=namespace.storage_account
            )


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    from knack.util import CLIError

    subnet = namespace.subnet
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        raise CLIError('usage error: [--subnet ID | --subnet NAME --vnet-name NAME]')
    delattr(namespace, 'vnet_name')


# Validate managed identity.
def validate_msi(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id

    if namespace.assign_identity is not None:
        if not is_valid_resource_id(namespace.assign_identity):
            namespace.assign_identity = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.ManagedIdentity',
                type='userAssignedIdentities',
                name=namespace.assign_identity
            )


# Validate managed identity to access storage account v2.
def validate_storage_msi(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id

    if namespace.storage_account_managed_identity is not None:
        if not is_valid_resource_id(namespace.storage_account_managed_identity):
            namespace.storage_account_managed_identity = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.ManagedIdentity',
                type='userAssignedIdentities',
                name=namespace.storage_account_managed_identity
            )


# Validate domain service.
def validate_domain_service(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id

    if namespace.domain:
        if not is_valid_resource_id(namespace.domain):
            namespace.domain = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.AAD',
                type='domainServices',
                name=namespace.domain
            )
