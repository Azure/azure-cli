# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.url_path_map._create import Create as _URLPathMapCreate


class URLPathMapCreate(_URLPathMapCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rule_name = AAZStrArg(
            options=["--rule-name"],
            arg_group="First Rule",
            help="Name of the rule for a URL path map.",
            default="default",
        )
        args_schema.paths = AAZListArg(
            options=["--paths"],
            arg_group="First Rule",
            help="Space-separated list of paths to associate with the rule. "
                 "Valid paths start and end with \"/\", e.g, \"/bar/\".",
            required=True,
        )
        args_schema.paths.Element = AAZStrArg()
        args_schema.address_pool = AAZResourceIdArg(
            options=["--address-pool"],
            arg_group="First Rule",
            help="Name or ID of the backend address pool to use with the created rule.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
        )
        args_schema.http_settings = AAZResourceIdArg(
            options=["--http-settings"],
            arg_group="First Rule",
            help="Name or ID of the HTTP settings to use with the created rule.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
            ),
        )
        args_schema.redirect_config = AAZResourceIdArg(
            options=["--redirect-config"],
            arg_group="First Rule",
            help="Name or ID of the redirect configuration to use with the created rule.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
            ),
        )
        args_schema.rewrite_rule_set = AAZResourceIdArg(
            options=["--rewrite-rule-set"],
            arg_group="First Rule",
            help="Name or ID of the rewrite rule set. If not specified, the default for the map will be used.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
            ),
        )
        args_schema.waf_policy = AAZResourceIdArg(
            options=["--waf-policy"],
            arg_group="First Rule",
            help="Name or ID of a web application firewall policy resource.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/ApplicationGatewayWebApplicationFirewallPolicies/{}",
            ),
        )
        # add templates for resource id
        args_schema.default_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.default_http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.default_redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.default_rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        rules = [{
            "name": args.rule_name,
            "paths": args.paths,
            "backend_address_pool": {"id": args.address_pool} if has_value(args.address_pool) else None,
            "backend_http_settings": {"id": args.http_settings} if has_value(args.http_settings) else None,
            "redirect_configuration": {"id": args.redirect_config} if has_value(args.redirect_config) else None,
            "rewrite_rule_set": {"id": args.rewrite_rule_set} if has_value(args.rewrite_rule_set) else None,
            "firewall_policy": {"id": args.waf_policy} if has_value(args.waf_policy) else None,
        }]
        args.rules = rules
