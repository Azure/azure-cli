# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import get_default_location_from_resource_group

from azure.cli.core.commands.parameters import zone_type

from ._validators import (validate_public_ip_addresses, validate_public_ip_prefixes)
# pylint: disable=line-too-long


def load_arguments(self, _):
    with self.argument_context('network nat gateway') as c:
        c.argument('nat_gateway_name', id_part='name', options_list=['--name', '-n'], help='Name of the NAT gateway.')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('public_ip_addresses', nargs='+', help='Space-separated list of public IP addresses (names or IDs).', validator=validate_public_ip_addresses)
        c.argument('public_ip_prefixes', nargs='+', help='Space-separated list of public IP prefixes (names or IDs).', validator=validate_public_ip_prefixes)
        c.argument('idle_timeout', help='Idle timeout in minutes.')
        c.argument('zone', zone_type)
        c.ignore('expand')
