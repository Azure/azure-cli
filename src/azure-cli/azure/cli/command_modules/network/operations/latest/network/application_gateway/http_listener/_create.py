# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.http_listener._create import Create as _HTTPListenerCreate


class HTTPListenerCreate(_HTTPListenerCreate):
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
        args_schema.frontend_port._required = True
        args_schema.protocol._registered = False
        args_schema.require_server_name_indication._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.ssl_cert):
            args.protocol = "Https"
            args.require_server_name_indication = True if has_value(args.host_name) else None
        else:
            args.protocol = "Http"

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                err_msg = "Multiple frontend IP configurations found. Specify --frontend-ip explicitly."
                raise ArgumentUsageError(err_msg)
