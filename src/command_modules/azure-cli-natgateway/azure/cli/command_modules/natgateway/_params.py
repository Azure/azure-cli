# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_resource_name_completion_list,
    resource_group_name_type,
    tags_type)

from azure.mgmt.network.models import KeyType


def load_arguments(self, _):

    (LoadBalancerSkuName) = self.get_models('LoadBalancerSkuName')

    # Argument Definition
    maps_name_type = CLIArgumentType(options_list=['--name', '-n'],
                                     completer=get_resource_name_completion_list('Microsoft.Network/natgateways'),
                                     help='The name of the nat gateway')

    # Parameter Registration
    with self.argument_context('network nat-gateway', arg_group='Network') as c:
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), arg_group='Network')
        c.argument('public_ip_prefix_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPPrefixes'), id_part='name', help='The name of the public IP prefix.')
        c.argument('idle_timeout_in_minutes', help='Idle timeout in minutes.', type=int)
        c.argument('sku', min_api='2017-08-01', help='Load balancer SKU', arg_type=get_enum_type(LoadBalancerSkuName, default='standard'))
