# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZStrArg, AAZArgEnum
from azure.cli.command_modules.network.aaz.latest.network.lb.frontend_ip._create import Create as _LBFrontendIPCreate

from knack.log import get_logger

logger = get_logger(__name__)


class LBFrontendIPCreate(_LBFrontendIPCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            arg_group="Properties",
            options=['--vnet-name'],
            help="The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id)."
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIpPrefixes/{}",
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}",
        )
        args_schema.gateway_lb._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )

        args_schema.zones.Element.enum = AAZArgEnum({
            "1": "1",
            "2": "2",
            "3": "3",
        })
        args_schema.private_ip_allocation_method._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.subnet) and has_value(args.public_ip_address):
            raise ArgumentUsageError(
                'incorrect usage: --subnet NAME --vnet-name NAME | '
                '--subnet ID | --public-ip-address NAME_OR_ID')

        if not has_value(args.public_ip_address):
            logger.warning(
                "Please note that the default public IP used for LB frontend will be changed from Basic to Standard "
                "in the future."
            )

        if has_value(args.private_ip_address):
            args.private_ip_allocation_method = 'Static'
        else:
            args.private_ip_allocation_method = 'Dynamic'
