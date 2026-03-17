# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZListArg, AAZResourceIdArg
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from azure.cli.command_modules.network.aaz.latest.network.lb.rule._update import Update as _LBRuleUpdate


class LBRuleUpdate(_LBRuleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )

        args_schema.backend_pools = AAZListArg(
            options=["--backend-pools-name", "--backend-pool-name"],
            nullable=True,
            arg_group="Properties",
            help="List of ID or name of the backend address pools. Multiple pools are only supported by Gateway SKU load balancer."
        )

        args_schema.backend_pools.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            )
        )

        args_schema.protocol._nullable = False
        args_schema.frontend_port._nullable = False
        args_schema.backend_port._nullable = False
        args_schema.backend_address_pools._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        args.backend_address_pools = assign_aaz_list_arg(
            args.backend_address_pools, args.backend_pools,
            element_transformer=lambda _, id: {"id": id}
        )

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None
        # always remove backend_address_pool in update request, service will fill this property based on backend_address_pools property.
        instance.properties.backend_address_pool = None

        args = self.ctx.args
        if has_value(args.frontend_ip_name):
            curr_id = args.frontend_ip_name.to_serialized_data()
            curr_name = parse_resource_id(curr_id)["resource_name"] if is_valid_resource_id(curr_id) else curr_id

            parent = self.ctx.vars.instance
            frontend_ip_configurations = parent.properties.frontend_ip_configurations
            for fip in frontend_ip_configurations:
                if fip.name == curr_name:
                    if has_value(fip.properties.gateway_load_balancer):
                        rid = fip.properties.gateway_load_balancer.id.to_serialized_data()
                        self.ctx.update_aux_subscriptions(parse_resource_id(rid)["subscription"])
