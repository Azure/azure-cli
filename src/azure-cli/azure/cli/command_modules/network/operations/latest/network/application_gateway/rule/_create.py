# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.rule._create import Create as _RuleCreate


class RuleCreate(_RuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.http_listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/httpListeners/{}",
        )
        args_schema.http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        args_schema.url_path_map._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/urlPathMaps/{}",
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not has_value(args.address_pool) and not has_value(args.redirect_config):
            address_pools = instance.properties.backend_address_pools
            if len(address_pools) == 1:
                args.address_pool = instance.properties.backend_address_pools[0].id
            elif len(address_pools) > 1:
                err_msg = "Multiple backend address pools found. Specify --address-pool explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.http_settings) and not has_value(args.redirect_config):
            settings = instance.properties.backend_http_settings_collection
            if len(settings) == 1:
                args.http_settings = instance.properties.backend_http_settings_collection[0].id
            elif len(settings) > 1:
                err_msg = "Multiple backend settings found. Specify --http-settings explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.http_listener):
            listeners = instance.properties.http_listeners
            if len(listeners) == 1:
                args.http_listener = instance.properties.http_listeners[0].id
            elif len(listeners) > 1:
                err_msg = "Multiple HTTP listeners found. Specify --http-listener explicitly."
                raise ArgumentUsageError(err_msg)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
