# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.http_listener._update import Update as _HTTPListenerUpdate


class HTTPListenerUpdate(_HTTPListenerUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendIPConfigurations/{}",
        )
        args_schema.frontend_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendPorts/{}",
        )
        args_schema.ssl_cert._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslCertificates/{}",
        )
        args_schema.ssl_profile_id._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslProfiles/{}",
        )
        args_schema.waf_policy._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ApplicationGatewayWebApplicationFirewallPolicies/{}",
        )
        args_schema.frontend_port._nullable = False
        args_schema.protocol._registered = False
        args_schema.require_server_name_indication._registered = False
        return args_schema

    def post_instance_update(self, instance):
        instance.properties.protocol = "Https" if has_value(instance.properties.ssl_certificate) else "Http"
        cond1 = instance.properties.host_name
        cond2 = instance.properties.protocol.to_serialized_data().lower() == "https"
        instance.properties.require_server_name_indication = cond1 and cond2
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.ssl_certificate.id):
            instance.properties.ssl_certificate = None
        if not has_value(instance.properties.ssl_profile.id):
            instance.properties.ssl_profile = None
        if not has_value(instance.properties.firewall_policy.id):
            instance.properties.firewall_policy = None
