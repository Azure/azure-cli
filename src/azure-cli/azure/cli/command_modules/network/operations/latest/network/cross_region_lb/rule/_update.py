# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value, AAZResourceIdArg
from azure.cli.command_modules.network.aaz.latest.network.lb.rule._update import Update as _LBRuleUpdate


@register_command("network cross-region-lb rule update")
class CrossRegionLoadBalancerRuleUpdate(_LBRuleUpdate):
    """Update a load balancing rule.

    :example:  Update a load balancing rule to change the protocol to UDP.
        az network cross-region-lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Udp

    :example: Update a load balancing rule to support HA ports.
        az network cross-region-lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol All --frontend-port 0 --backend-port 0
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
            nullable=True,
            help="ID or name of the backend address pools. If only one exists, omit to use as default."
        )

        args_schema.protocol._nullable = False
        args_schema.frontend_port._nullable = False
        args_schema.backend_port._nullable = False
        args_schema.backend_address_pools._registered = False
        args_schema.disable_outbound_snat._registered = False   # it's not required for cross-region-lb
        args_schema.idle_timeout_in_minutes._registered = False
        args_schema.enable_tcp_reset._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.backend_pool):
            backend_pool = args.backend_pool.to_serialized_data()
            if backend_pool is None:
                args.backend_address_pools = []  # remove backend pool
            else:
                args.backend_address_pools = [{"id": backend_pool}]

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None
        # always remove backend_address_pool in update request, service will fill this property based on backend_address_pools property.
        instance.properties.backend_address_pool = None
