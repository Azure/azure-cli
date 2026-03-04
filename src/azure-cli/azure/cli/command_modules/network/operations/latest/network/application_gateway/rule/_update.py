# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.rule._update import Update as _RuleUpdate


class RuleUpdate(_RuleUpdate):
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

    def post_instance_update(self, instance):
        if not has_value(instance.properties.backend_address_pool.id):
            instance.properties.backend_address_pool = None
        if not has_value(instance.properties.backend_http_settings.id):
            instance.properties.backend_http_settings = None
        if not has_value(instance.properties.http_listener.id):
            instance.properties.http_listener = None
        if not has_value(instance.properties.redirect_configuration.id):
            instance.properties.redirect_configuration = None
        if not has_value(instance.properties.rewrite_rule_set.id):
            instance.properties.rewrite_rule_set = None
        if not has_value(instance.properties.url_path_map.id):
            instance.properties.url_path_map = None
