# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_subscription_id


def validate_public_ip_prefixes(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if not namespace.public_ip_prefixes:
        return

    public_ip_prefix_ids = []
    SubResource = cmd.get_models('SubResource')
    for prefix in namespace.public_ip_prefixes:
        if not is_valid_resource_id(prefix):
            prefix = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                name=prefix,
                namespace='Microsoft.Network',
                type='publicIPPrefixes')
        public_ip_prefix_ids.append(SubResource(id=prefix))
    namespace.public_ip_prefixes = public_ip_prefix_ids


def validate_public_ip_addresses(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if not namespace.public_ip_addresses:
        return

    public_ip_address_ids = []
    SubResource = cmd.get_models('SubResource')
    for address in namespace.public_ip_addresses:
        if not is_valid_resource_id(address):
            address = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                name=address,
                namespace='Microsoft.Network',
                type='publicIPAddresses')
        public_ip_address_ids.append(SubResource(id=address))
    namespace.public_ip_addresses = public_ip_address_ids
