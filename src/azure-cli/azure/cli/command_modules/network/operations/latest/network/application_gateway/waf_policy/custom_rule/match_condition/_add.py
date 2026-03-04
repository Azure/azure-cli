# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.waf_policy.custom_rule.match_condition._add import Add as _WAFCustomRuleMatchConditionAdd


class WAFCustomRuleMatchConditionAdd(_WAFCustomRuleMatchConditionAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.match_variables = AAZListArg(
            options=["--match-variables"],
            help="Space-separated list of variables to use when matching. Variable values: RemoteAddr, RequestMethod, "
                 "QueryString, PostArgs, RequestUri, RequestHeaders, RequestBody, RequestCookies.",
            required=True,
        )
        args_schema.match_variables.Element = AAZStrArg()
        # filter arguments
        args_schema.variables._required = False
        args_schema.variables._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        variables = []
        for variable in args.match_variables:
            try:
                name, selector = str(variable).split(".", 1)
            except ValueError:
                name, selector = variable, None
            variables.append({
                "variable_name": name,
                "selector": selector,
            })
        args.variables = variables
        # validate
        if str(args.operator).lower() == "any" and has_value(args.values):
            raise ArgumentUsageError("\"Any\" operator does not require --values.")
        if str(args.operator).lower() != "any" and not has_value(args.values):
            raise ArgumentUsageError("Non-any operator requires --values.")
