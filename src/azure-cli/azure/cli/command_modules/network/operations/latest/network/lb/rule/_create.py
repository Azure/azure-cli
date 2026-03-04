# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZListArg, AAZResourceIdArg
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from azure.cli.command_modules.network.aaz.latest.network.lb.rule._create import Create as _LBRuleCreate


class LBRuleCreate(_LBRuleCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )
        # list argument accept one element: `--backend-pool-name PoolName`
        args_schema.backend_pools = AAZListArg(
            options=["--backend-pools-name", "--backend-pool-name"],
            arg_group="Properties",
            help="List of ID or name of the backend address pools. Multiple pools are only supported by Gateway SKU load balancer. If only one exists, omit to use as default."
        )
        args_schema.backend_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            )
        )

        args_schema.protocol._required = True
        args_schema.frontend_port._required = True
        args_schema.backend_port._required = True
        args_schema.backend_address_pools._registered = False
        return args_schema

    def pre_instance_create(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError(
                    "Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")
        if not has_value(args.backend_pools):
            instance = self.ctx.vars.instance
            backend_address_pools = instance.properties.backend_address_pools
            if len(backend_address_pools) == 1:
                args.backend_pools = [instance.properties.backend_address_pools[0].id]
            elif len(backend_address_pools) > 1:
                raise ArgumentUsageError(
                    "Multiple BackendAddressPools found in loadbalancer. Specify --backend-pool-name explicitly.")
        args.backend_address_pools = assign_aaz_list_arg(
            args.backend_address_pools, args.backend_pools,
            element_transformer=lambda _, id: {"id": id}
        )

    def post_instance_create(self, instance):
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
