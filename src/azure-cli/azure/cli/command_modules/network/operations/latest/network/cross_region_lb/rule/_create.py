# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value, AAZResourceIdArg
from azure.cli.command_modules.network.aaz.latest.network.lb.rule._create import Create as _LBRuleCreate


@register_command("network cross-region-lb rule create")
class CrossRegionLoadBalancerRuleCreate(_LBRuleCreate):
    """Create a load balancing rule.

    :example: Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port.
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp --frontend-ip-name MyFrontEndIp --frontend-port 80 --backend-pool-name MyAddressPool --backend-port 80

    :example: Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port with the floating ip feature.
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp --frontend-ip-name MyFrontEndIp --frontend-port 80 --backend-pool-name MyAddressPool --backend-port 80 --floating-ip true

    :example: Create an HA ports load balancing rule that assigns a frontend IP and port to use all available backend IPs in a pool on the same port.
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyHAPortsRule --protocol All --frontend-port 0 --backend-port 0 --frontend-ip-name MyFrontendIp --backend-pool-name MyAddressPool
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )
        # not support multi backend pools because the loadbalance SKU is not Gateway
        args_schema.backend_pool = AAZResourceIdArg(
            options=["--backend-pool-name"],
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            ),
            arg_group="Properties",
            help="ID or name of the backend address pools. If only one exists, omit to use as default."
        )
        args_schema.idle_timeout_in_minutes._default = 4
        args_schema.enable_tcp_reset._default = False
        args_schema.protocol._required = True
        args_schema.frontend_port._required = True
        args_schema.backend_port._required = True
        args_schema.backend_address_pools._registered = False
        args_schema.disable_outbound_snat._registered = False   # it's not required for cross-region-lb
        args_schema.idle_timeout_in_minutes._registered = False
        args_schema.enable_tcp_reset._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError(
                    "Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")
        if not has_value(args.backend_pool):
            instance = self.ctx.vars.instance
            backend_address_pools = instance.properties.backend_address_pools
            if len(backend_address_pools) == 1:
                args.backend_pool = instance.properties.backend_address_pools[0].id
            elif len(backend_address_pools) > 1:
                raise ArgumentUsageError(
                    "Multiple BackendAddressPools found in loadbalancer. Specify --backend-pool-name explicitly.")
        if has_value(args.backend_pool):
            args.backend_address_pools = [{"id": args.backend_pool.to_serialized_data()}]
