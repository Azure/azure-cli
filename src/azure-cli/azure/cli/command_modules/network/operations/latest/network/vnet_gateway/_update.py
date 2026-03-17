# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.custom import RootCertFormat
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway._update import Update as _VnetGatewayUpdate
from knack.log import get_logger

logger = get_logger(__name__)


class VnetGatewayUpdate(_VnetGatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZFileArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(options=['--public-ip-addresses', '--public-ip-address'],
                                                     help="Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway.",
                                                     nullable=True)
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
                                                fmt=RootCertFormat(), nullable=True)
        args_schema.root_cert_name = AAZStrArg(options=['--root-cert-name'], arg_group="Root Cert Authentication",
                                               help="Root certificate name.", nullable=True,)
        args_schema.gateway_default_site._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/localNetworkGateways/{}"
        )
        args_schema.enable_high_bandwidth_vpn_gateway._registered = False
        args_schema.virtual_network_gateway_migration_status._registered = False
        args_schema.ip_configurations._registered = False
        args_schema.active._registered = False
        args_schema.vpn_client_root_certificates._registered = False
        args_schema.sku_tier._registered = False
        args_schema.vpn_client_ipsec_policies._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

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
