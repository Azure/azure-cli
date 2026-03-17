# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value
from azure.cli.command_modules.network.aaz.latest.network.lb.inbound_nat_pool._create import Create as _LBInboundNatPoolCreate


class LBInboundNatPoolCreate(_LBInboundNatPoolCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError("Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")
