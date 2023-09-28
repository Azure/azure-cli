# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, no-self-use, line-too-long, protected-access, too-few-public-methods
from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat, AAZFileArg, \
    AAZFileArgBase64EncodeFormat, has_value
from knack.log import get_logger

from ._util import import_aaz_by_profile

logger = get_logger(__name__)


_VnetGateway = import_aaz_by_profile("network.vnet_gateway")


class VnetGatewayCreate(_VnetGateway.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(
            options=['--public-ip-addresses', '--public-ip-address'],
            required=True,
            help="Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway."
        )
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

        args_schema.root_cert_data = AAZFileArg(options=['--root-cert-data'], arg_group="Root Cert Authentication",
                                                help="Base64 contents of the root certificate file or file path.",
                                                fmt=AAZFileArgBase64EncodeFormat())
        args_schema.root_cert_name = AAZStrArg(options=['--root-cert-name'], arg_group="Root Cert Authentication",
                                               help="Root certificate name.")
        args_schema.gateway_default_site._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/localNetworkGateways/{}"
        )
        args_schema.ip_configurations._registered = False
        args_schema.active._registered = False
        args_schema.vpn_client_root_certificates._registered = False
        args_schema.sku_tier._registered = False
        args_schema.enable_bgp._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        subnet = args.vnet.to_serialized_data() + '/subnets/GatewaySubnet'
        args.sku_tier = args.sku
        args.active = len(args.public_ip_addresses) == 2

        args.ip_configurations = []
        if has_value(args.public_ip_addresses):
            public_ip_addresses = args.public_ip_addresses.to_serialized_data()
            ip_configuration = {}
            for i, public_ip in enumerate(public_ip_addresses):
                ip_configuration[i] = {'subnet': subnet, 'public_ip_address': public_ip,
                                       'private_ip_allocation_method': 'Dynamic',
                                       'name': 'vnetGatewayConfig{}'.format(i)}
                args.ip_configurations.append(ip_configuration[i])

        if has_value(args.asn) or has_value(args.bgp_peering_address) or has_value(args.peer_weight):
            args.enable_bgp = True
        else:
            args.asn = None
            args.bgp_peering_address = None
            args.peer_weight = None

        if has_value(args.address_prefixes) or has_value(args.client_protocol):
            import os
            if has_value(args.root_cert_data):
                path = os.path.expanduser(args.root_cert_data.to_serialized_data())
            else:
                path = None
            if has_value(args.root_cert_name):
                args.vpn_client_root_certificates = [{'name': args.root_cert_name, 'public_cert_data': path}]
            else:
                args.vpn_client_root_certificates = []

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {'vnetGateway': result}


class VnetGatewayUpdate(_VnetGateway.Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(
            options=['--public-ip-addresses', '--public-ip-address'],
            help="Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway."
        )
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}"
            ),
            nullable=True,
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            ),
        )
        args_schema.root_cert_data = AAZFileArg(options=['--root-cert-data'], arg_group="Root Cert Authentication",
                                                help="Base64 contents of the root certificate file or file path.",
                                                fmt=AAZFileArgBase64EncodeFormat(), nullable=True)
        args_schema.root_cert_name = AAZStrArg(options=['--root-cert-name'], arg_group="Root Cert Authentication",
                                               help="Root certificate name.", nullable=True,)
        args_schema.gateway_default_site._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/localNetworkGateways/{}"
        )
        args_schema.ip_configurations._registered = False
        args_schema.active._registered = False
        args_schema.vpn_client_root_certificates._registered = False
        args_schema.sku_tier._registered = False
        args_schema.vpn_client_ipsec_policies._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.root_cert_data):
            import os
            path = os.path.expanduser(args.root_cert_data.to_serialized_data())
            args.root_cert_data = path

        if has_value(args.sku):
            args.sku_tier = args.sku

    def pre_instance_update(self, instance):
        args = self.ctx.args
        if has_value(args.root_cert_data):
            collection = instance.properties.vpn_client_configuration.vpn_client_root_certificates.to_serialized_data()
            root_certificate = {'name': args.root_cert_name, 'public_cert_data': args.root_cert_data}
            value = args.root_cert_name.to_serialized_data()
            match = next((x for x in collection if getattr(x, 'name', None) == value), None)
            if match:
                collection.remove(match)
            collection.append(root_certificate)
            args.vpn_client_root_certificates = collection

        subnet_id = '{}/subnets/GatewaySubnet'.format(args.vnet) if has_value(args.vnet) else \
            instance.properties.ip_configurations[0].properties.subnet.id

        if has_value(args.vnet):
            if has_value(instance.properties.ip_configurations):
                for config in instance.properties.ip_configurations:
                    config.properties.subnet.id = subnet_id

        if has_value(args.public_ip_addresses):
            instance.properties.ip_configurations = []
            public_ip_addresses = args.public_ip_addresses.to_serialized_data()
            args.ip_configurations = []
            ip_configuration = {}
            for i, public_ip in enumerate(public_ip_addresses):
                ip_configuration[i] = {'subnet': subnet_id, 'public_ip_address': {'id': public_ip},
                                       'private_ip_allocation_method': 'Dynamic',
                                       'name': 'vnetGatewayConfig{}'.format(i)}
                args.ip_configurations.append(ip_configuration[i])

            # Update active-active/active-standby status
            active = len(args.public_ip_addresses) == 2
            if instance.properties.active_active and not active:
                logger.info('Placing gateway in active-standby mode.')
            elif not instance.properties.active_active and active:
                logger.info('Placing gateway in active-active mode.')
            args.active = active


_VpnClient = import_aaz_by_profile("network.vnet_gateway.vpn_client")


def generate_vpn_client(cmd, resource_group_name, virtual_network_gateway_name, processor_architecture=None,
                        authentication_method=None, radius_server_auth_certificate=None, client_root_certificates=None,
                        use_legacy=False):
    generate_args = {"name": virtual_network_gateway_name,
                     "resource_group": resource_group_name,
                     "processor_architecture": processor_architecture}
    if not use_legacy:
        generate_args['authentication_method'] = authentication_method
        generate_args['radius_server_auth_certificate'] = radius_server_auth_certificate
        generate_args['client_root_certificates'] = client_root_certificates
        return _VpnClient.GenerateVpnProfile(cli_ctx=cmd.cli_ctx)(command_args=generate_args)
    # legacy implementation
    return _VpnClient.Generate(cli_ctx=cmd.cli_ctx)(command_args=generate_args)


_RevokedCert = import_aaz_by_profile("network.vnet_gateway.revoked_cert")


class VnetGatewayRevokedCertCreate(_RevokedCert.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.thumbprint._required = True

        return args_schema


_RootCert = import_aaz_by_profile("network.vnet_gateway.root_cert")


class VnetGatewayRootCertCreate(_RootCert.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_cert_data = AAZFileArg(options=['--public-cert-data'],
                                                  help="Base64 contents of the root certificate file or file path.",
                                                  required=True,
                                                  fmt=AAZFileArgBase64EncodeFormat())
        args_schema.root_cert_data._required = False
        args_schema.root_cert_data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.public_cert_data):
            import os
            path = os.path.expanduser(args.public_cert_data.to_serialized_data())
        else:
            path = None
        args.root_cert_data = path


_IpsecPolicy = import_aaz_by_profile("network.vnet_gateway.ipsec_policy")


class VnetGatewayIpsecPolicyAdd(_IpsecPolicy.Add):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vpn_client_ipsec_policy_index._registered = False

        return args_schema


def clear_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name, no_wait=False):

    class VnetGatewayIpsecPoliciesClear(_VnetGateway.Update):

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(
                self.ctx.vars.instance.properties.vpn_client_configuration.vpn_client_ipsec_policies,
                client_flatten=True
            )
            return result

        def pre_instance_update(self, instance):
            instance.properties.vpn_client_configuration.vpn_client_ipsec_policies = None

    ipsec_policies_args = {
        "resource_group": resource_group_name,
        "name": gateway_name,
        "no_wait": no_wait
    }

    return VnetGatewayIpsecPoliciesClear(cli_ctx=cmd.cli_ctx)(command_args=ipsec_policies_args)
