# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.core.azclierror import ResourceNotFoundError
from ._util import import_aaz_by_profile


logger = get_logger(__name__)


_VNet = import_aaz_by_profile("network.vnet")


class VNetCreate(_VNet.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # add subnet arguments
        args_schema.subnet_name = AAZStrArg(
            options=["--subnet-name"],
            arg_group="Subnet",
            help="Name of a new subnet to create within the VNet.",
        )
        args_schema.subnet_prefixes = AAZListArg(
            options=["--subnet-prefixes"],
            arg_group="Subnet",
            help="Space-separated list of address prefixes in CIDR format for the new subnet. If omitted, "
                 "automatically reserves a /24 (or as large as available) block within the VNet address space.",
        )
        args_schema.subnet_prefixes.Element = AAZStrArg()
        args_schema.subnet_nsg = AAZResourceIdArg(
            options=["--nsg", "--network-security-group"],
            arg_group="Subnet",
            help="Name or ID of a network security group (NSG).",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
        )
        # filter arguments
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.subnet_name):
            subnet = {"name": args.subnet_name}
            if not has_value(args.subnet_prefixes):
                # set default value
                address, bit_mask = str(args.address_prefixes[0]).split("/")
                subnet_mask = 24 if int(bit_mask) < 24 else bit_mask
                subnet["address_prefix"] = f"{address}/{subnet_mask}"
            elif len(args.subnet_prefixes) == 1:
                subnet["address_prefix"] = args.subnet_prefixes[0]
            else:
                subnet["address_prefixes"] = args.subnet_prefixes
            if has_value(args.subnet_nsg):
                subnet["network_security_group"] = {"id": args.subnet_nsg}
            args.subnets = [subnet]

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {"newVNet": result}


def list_available_ips(cmd, resource_group_name, virtual_network_name):
    Show = import_aaz_by_profile("network.vnet").Show
    vnet = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
    })

    start_ip = vnet["addressSpace"]["addressPrefixes"][0].split("/")[0]

    CheckIpAddress = import_aaz_by_profile("network.vnet").CheckIpAddress
    return CheckIpAddress(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
        "ip_address": start_ip,
    }).get("availableIPAddresses", [])


_VNetSubNet = import_aaz_by_profile("network.vnet.subnet")


class VNetSubnetCreate(_VNetSubNet.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.delegations = AAZListArg(
            options=["--delegations"],
            help="Space-separated list of services to whom the subnet should be delegated, e.g., Microsoft.Sql/servers."
        )
        args_schema.delegations.Element = AAZStrArg()
        # add endpoint/policy arguments
        args_schema.service_endpoints = AAZListArg(
            options=["--service-endpoints"],
            help="Space-separated list of services allowed private access to this subnet. "
                 "Values from: az network vnet list-endpoint-services.",
        )
        args_schema.service_endpoints.Element = AAZStrArg()
        args_schema.network_security_group._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/networkSecurityGroups/{}",
        )
        args_schema.route_table._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/routeTables/{}",
        )
        # filter arguments
        args_schema.endpoints._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.endpoints = assign_aaz_list_arg(
            args.endpoints,
            args.service_endpoints,
            element_transformer=lambda _, service_name: {"service": service_name}
        )


class VNetSubnetUpdate(_VNetSubNet.Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.delegations = AAZListArg(
            options=["--delegations"],
            help="Space-separated list of services to whom the subnet should be delegated, e.g., Microsoft.Sql/servers.",
            nullable=True,
        )
        args_schema.delegations.Element = AAZStrArg(
            nullable=True,
        )
        # add endpoint/policy arguments
        args_schema.service_endpoints = AAZListArg(
            options=["--service-endpoints"],
            help="Space-separated list of services allowed private access to this subnet. "
                 "Values from: az network vnet list-endpoint-services.",
            nullable=True,
        )
        args_schema.service_endpoints.Element = AAZStrArg(
            nullable=True,
        )
        # filter arguments
        args_schema.address_prefix._registered = False
        args_schema.endpoints._registered = False
        # handle detach logic
        args_schema.network_security_group._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/networkSecurityGroups/{}",
        )
        args_schema.route_table._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/routeTables/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.endpoints = assign_aaz_list_arg(
            args.endpoints,
            args.service_endpoints,
            element_transformer=lambda _, service_name: {"service": service_name}
        )

    def post_instance_update(self, instance):
        if not has_value(instance.properties.network_security_group.id):
            instance.properties.network_security_group = None
        if not has_value(instance.properties.route_table.id):
            instance.properties.route_table = None


def subnet_list_available_ips(cmd, resource_group_name, virtual_network_name, subnet_name):
    Show = import_aaz_by_profile("network.vnet.subnet").Show
    subnet = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": subnet_name,
        "resource_group": resource_group_name,
        "vnet_name": virtual_network_name,
    })

    try:
        address_prefix = subnet["addressPrefixes"][0]
    except KeyError:
        address_prefix = subnet["addressPrefix"]
    start_ip = address_prefix.split("/")[0]

    CheckIpAddress = import_aaz_by_profile("network.vnet").CheckIpAddress
    return CheckIpAddress(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
        "ip_address": start_ip,
    }).get("availableIPAddresses", [])


_VNetPeering = import_aaz_by_profile("network.vnet.peering")


class VNetPeeringCreate(_VNetPeering.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.remote_vnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}",
        )
        return args_schema


def sync_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name):
    Show = import_aaz_by_profile("network.vnet.peering").Show
    try:
        peering = Show(cli_ctx=cmd.cli_ctx)(command_args={
            "name": virtual_network_peering_name,
            "resource_group": resource_group_name,
            "vnet_name": virtual_network_name,
        })
    except ResourceNotFoundError:
        err_msg = f"Virtual network peering {virtual_network_name} doesn't exist."
        raise ResourceNotFoundError(err_msg)

    Create = import_aaz_by_profile("network.vnet.peering").Create
    return Create(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_peering_name,
        "resource_group": resource_group_name,
        "vnet_name": virtual_network_name,
        "remote_vnet": peering["remoteVirtualNetwork"].pop("id", None),
        "allow_vnet_access": peering.pop("allowVirtualNetworkAccess", None),
        "allow_gateway_transit": peering.pop("allowGatewayTransit", None),
        "allow_forwarded_traffic": peering.pop("allowForwardedTraffic", None),
        "use_remote_gateways": peering.pop("useRemoteGateways", None),
    })
