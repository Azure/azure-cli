# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.rewrite_rule._create import Create as _AGRewriteRuleCreate


class AGRewriteRuleCreate(_AGRewriteRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.request_headers = AAZDictArg(
            options=["--request-headers"],
            help="Space-separated list of HEADER=VALUE pairs. "
                 "Values from: `az network application-gateway rewrite-rule list-request-headers`.",
        )
        args_schema.request_headers.Element = AAZStrArg()
        args_schema.response_headers = AAZDictArg(
            options=["--response-headers"],
            help="Space-separated list of HEADER=VALUE pairs. "
                 "Values from: `az network application-gateway rewrite-rule list-response-headers`.",
        )
        args_schema.response_headers.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.request_headers):
            configurations = []
            for k, v in args.request_headers.items():
                configurations.append({"header_name": k, "header_value": v})
            args.request_header_configurations = configurations
        if has_value(args.response_headers):
            configurations = []
            for k, v in args.response_headers.items():
                configurations.append({"header_name": k, "header_value": v})
            args.response_header_configurations = configurations
