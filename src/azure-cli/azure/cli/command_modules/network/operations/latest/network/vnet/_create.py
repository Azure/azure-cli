# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.vnet._create import Create as _VNetCreate


class VNetCreate(_VNetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.edge_zone = AAZStrArg(
            options=["--edge-zone"],
            help="The name of edge zone.",
        )
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
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/ddosProtectionPlans/{}",
        )
        # filter arguments
        args_schema.extended_location._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.edge_zone):
            args.extended_location.name = args.edge_zone
            args.extended_location.type = "EdgeZone"

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

        if has_value(args.ipam_pool_prefix_allocations):
            args.address_prefixes = []

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {"newVNet": result}
