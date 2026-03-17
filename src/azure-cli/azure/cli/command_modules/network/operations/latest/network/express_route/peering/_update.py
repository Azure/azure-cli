# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.express_route.peering._update import Update as _ExpressRoutePeeringUpdate


class ExpressRoutePeeringUpdate(_ExpressRoutePeeringUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ip_version = AAZStrArg(
            options=['--ip-version'],
            arg_group="Microsoft Peering",
            help="The IP version to update Microsoft Peering settings for. Allowed values: IPv4, IPv6. Default: IPv4.",
            default='IPv4'
        )
        args_schema.route_filter._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/routeFilters/{}",
        )
        # taken from Xplat. No enums in SDK
        args_schema.routing_registry_name.enum = AAZArgEnum({"ARIN": "ARIN", "APNIC": "APNIC", "AFRINIC": "AFRINIC", "LACNIC": "LACNIC", "RIPENCC": "RIPENCC", "RADB": "RADB", "ALTDB": "ALTDB", "LEVEL3": "LEVEL3"})
        args_schema.ipv6_peering_config._registered = False
        args_schema.peering_type._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.ip_version.to_serialized_data().lower() == 'ipv6':
            microsoft_config = {}
            args.ipv6_peering_config = {}
            if has_value(args.primary_peer_subnet):
                args.ipv6_peering_config['primary_peer_address_prefix'] = args.primary_peer_subnet
                args.primary_peer_subnet = None
            if has_value(args.secondary_peer_subnet):
                args.ipv6_peering_config['secondary_peer_address_prefix'] = args.secondary_peer_subnet
                args.secondary_peer_subnet = None
            if has_value(args.advertised_public_prefixes):
                microsoft_config['advertised_public_prefixes'] = args.advertised_public_prefixes
                args.advertised_public_prefixes = None
            if has_value(args.customer_asn):
                microsoft_config['customer_asn'] = args.customer_asn
                args.customer_asn = None
            if has_value(args.routing_registry_name):
                microsoft_config['routing_registry_name'] = args.routing_registry_name
                args.routing_registry_name = None
            if has_value(args.route_filter):
                args.ipv6_peering_config['route_filter'] = args.route_filter
                args.route_filter = None
            if microsoft_config is not None:
                args.ipv6_peering_config['microsoft_peering_config'] = microsoft_config
