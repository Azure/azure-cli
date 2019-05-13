
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from azure.cli.core.commands.client_factory import get_subscription_id


def validate_public_ip_addresses(resource):
    from msrestazure.tools import is_valid_resource_id, resource_id

    def _validate_public_ip_addresses(cmd, namespace):
        SubResource = cmd.get_models('SubResource')
        subscription_id = get_subscription_id(cmd.cli_ctx)

        resource_group = namespace.resource_group_name
        names_or_ids = getattr(namespace, resource)
        ids = []

        if names_or_ids == [''] or not names_or_ids:
            return

        for val in names_or_ids:
            if not is_valid_resource_id(val):
                val = resource_id(
                    subscription=subscription_id,
                    resource_group=resource_group,
                    namespace='Microsoft.Network', type='publicIPAddresses',
                    name=val
                )
            ids.append(SubResource(id=val))
        setattr(namespace, resource, ids)

    return _validate_public_ip_addresses


def validate_public_ip_prefixes(resource):
    from msrestazure.tools import is_valid_resource_id, resource_id

    def _validate_public_ip_prefixes(cmd, namespace):
        SubResource = cmd.get_models('SubResource')
        subscription_id = get_subscription_id(cmd.cli_ctx)

        resource_group = namespace.resource_group_name
        names_or_ids = getattr(namespace, resource)
        ids = []

        if names_or_ids == [''] or not names_or_ids:
            return

        for val in names_or_ids:
            if not is_valid_resource_id(val):
                val = resource_id(
                    subscription=subscription_id,
                    resource_group=resource_group,
                    namespace='Microsoft.Network', type='publicIPPrefixes',
                    name=val
                )
            ids.append(SubResource(id=val))
        setattr(namespace, resource, ids)

    return _validate_public_ip_prefixes
