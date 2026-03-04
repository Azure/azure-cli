# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.routing_rule._create import Create as _RoutingRuleCreate


class RoutingRuleCreate(_RoutingRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/listeners/{}",
        )
        args_schema.settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendSettingsCollection/{}",
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not has_value(args.address_pool):
            address_pools = instance.properties.backend_address_pools
            if len(address_pools) == 1:
                args.address_pool = instance.properties.backend_address_pools[0].id
            elif len(address_pools) > 1:
                err_msg = "Multiple backend address pools found. Specify --address-pool explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.listener):
            listeners = instance.properties.listeners
            if len(listeners) == 1:
                args.listener = instance.properties.listeners[0].id
            elif len(listeners) > 1:
                err_msg = "Multiple listeners found. Specify --listener explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.settings):
            settings = instance.properties.backend_settings_collection
            if len(settings) == 1:
                args.settings = instance.properties.backend_settings_collection[0].id
            elif len(settings) > 1:
                err_msg = "Multiple backend settings found. Specify --settings explicitly."
                raise ArgumentUsageError(err_msg)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
