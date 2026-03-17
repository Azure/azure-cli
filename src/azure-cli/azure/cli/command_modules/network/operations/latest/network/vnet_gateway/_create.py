# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.custom import RootCertFormat
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway._create import Create as _VnetGatewayCreate


class VnetGatewayCreate(_VnetGatewayCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZFileArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(options=['--public-ip-addresses', '--public-ip-address'],
                                                     help="Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway.")
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}"
            )
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )
        args_schema.nat_rules.Element.external_mappings = AAZStrArg(
            options=["external-mappings"],
            help="Required.The private IP address external mapping for NAT.",
        )
        args_schema.nat_rules.Element.internal_mappings = AAZStrArg(
            options=["internal-mappings"],
            help="Required.The private IP address internal mapping for NAT.",
        )
        args_schema.root_cert_data = AAZFileArg(options=['--root-cert-data'], arg_group="Root Cert Authentication",
                                                help="Base64 contents of the root certificate file or file path.",
                                                fmt=RootCertFormat())
        args_schema.root_cert_name = AAZStrArg(options=['--root-cert-name'], arg_group="Root Cert Authentication",
                                               help="Root certificate name.")
        args_schema.gateway_default_site._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/localNetworkGateways/{}"
        )
        args_schema.virtual_network_gateway_migration_status._registered = False
        args_schema.ip_configurations._registered = False
        args_schema.edge_zone_type._registered = False
        args_schema.active._registered = False
        args_schema.vpn_client_root_certificates._registered = False
        args_schema.sku_tier._registered = False
        args_schema.enable_bgp._registered = False
        args_schema.nat_rules.Element.external_mappings_ip._registered = False
        args_schema.nat_rules.Element.internal_mappings_ip._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        subnet = args.vnet.to_serialized_data() + '/subnets/GatewaySubnet'
        args.sku_tier = args.sku
        if has_value(args.gateway_type) and args.gateway_type != "LocalGateway":
            args.active = len(args.public_ip_addresses) == 2
        else:
            args.active = False

        args.ip_configurations = []
        if args.gateway_type != "LocalGateway":
            if has_value(args.public_ip_addresses):
                public_ip_addresses = args.public_ip_addresses.to_serialized_data()
                ip_configuration = {}
                for i, public_ip in enumerate(public_ip_addresses):
                    ip_configuration[i] = {'subnet': subnet, 'public_ip_address': public_ip,
                                           'private_ip_allocation_method': 'Dynamic',
                                           'name': 'vnetGatewayConfig{}'.format(i)}
                    args.ip_configurations.append(ip_configuration[i])
            else:
                ip_configuration = {'subnet': subnet,
                                    'private_ip_allocation_method': 'Dynamic',
                                    'name': 'vnetGatewayConfig'}
                args.ip_configurations.append(ip_configuration)

        else:
            args.vpn_type = None
            args.sku = None
            args.sku_tier = None

        if has_value(args.asn) or has_value(args.bgp_peering_address) or has_value(args.peer_weight):
            args.enable_bgp = True
        else:
            args.asn = None
            args.bgp_peering_address = None
            args.peer_weight = None

        if has_value(args.nat_rules):
            rules = args.nat_rules.to_serialized_data()
            for rule in rules:
                if 'internal_mappings' in rule:
                    internal_mappings = rule['internal_mappings'].split(',')
                    rule['internal_mappings_ip'] = [{"address_space": internal_mapping} for internal_mapping in
                                                    internal_mappings]
                if 'external_mappings' in rule:
                    external_mappings = rule['external_mappings'].split(',')
                    rule['external_mappings_ip'] = [{"address_space": external_mapping} for external_mapping in
                                                    external_mappings]
            args.nat_rules = rules

        if has_value(args.address_prefixes) or has_value(args.client_protocol):
            if has_value(args.root_cert_data):
                data = args.root_cert_data.to_serialized_data()
            else:
                data = None
            if has_value(args.root_cert_name):
                args.vpn_client_root_certificates = [{'name': args.root_cert_name, 'public_cert_data': data}]
            else:
                args.vpn_client_root_certificates = []

        if has_value(args.edge_zone):
            args.edge_zone_type = 'EdgeZone'

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    # `properties.type` conflict with the `type` property when flatten `properties`
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {'vnetGateway': result}
