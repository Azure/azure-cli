# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=import-error
from azure.mgmt.core.tools import is_valid_resource_id, resource_id
from azure.cli.core.commands.client_factory import get_subscription_id


# pylint: disable=inconsistent-return-statements
def privatedns_zone_name_type(value):
    if value:
        return value[:-1] if value[-1] == '.' else value


def validate_privatedns_metadata(ns):
    def _validate_metadata_single(string):
        result = {}
        if string:
            comps = string.split('=', 1)
            result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
        return result

    if isinstance(ns.metadata, list):
        metadata_dict = {}
        for item in ns.metadata:
            metadata_dict.update(_validate_metadata_single(item))
        ns.metadata = metadata_dict


def get_vnet_validator(cmd, namespace):
    SubResource = cmd.get_models('SubResource')
    subscription_id = get_subscription_id(cmd.cli_ctx)

    resource_group = namespace.resource_group_name
    name_or_id = namespace.virtual_network

    if name_or_id is None:
        return

    if not is_valid_resource_id(name_or_id):
        name_or_id = resource_id(
            subscription=subscription_id,
            resource_group=resource_group,
            namespace='Microsoft.Network', type='virtualNetworks',
            name=name_or_id
        )

    namespace.virtual_network = SubResource(id=name_or_id)


def validate_privatedns_record_type(namespace):
    tokens = namespace.command.split(' ')
    types = ['a', 'aaaa', 'cname', 'mx', 'ptr', 'soa', 'srv', 'txt']
    for token in tokens:
        if token in types:
            namespace.record_type = token
            return
