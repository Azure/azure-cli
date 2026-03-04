# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.listener._update import Update as _ListenerUpdate


class ListenerUpdate(_ListenerUpdate):
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
        args_schema.frontend_port._nullable = False
        args_schema.protocol._registered = False
        return args_schema

    def post_instance_update(self, instance):
        instance.properties.protocol = "Tls" if has_value(instance.properties.ssl_certificate) else "Tcp"
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.ssl_certificate.id):
            instance.properties.ssl_certificate = None
        if not has_value(instance.properties.ssl_profile.id):
            instance.properties.ssl_profile = None
