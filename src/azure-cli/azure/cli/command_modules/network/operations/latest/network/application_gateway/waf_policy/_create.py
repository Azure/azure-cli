# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.application_gateway.waf_policy._create import Create as _WAFCreate


class WAFCreate(_WAFCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rule_set_type = AAZStrArg(
            options=["--type"],
            help="Type of the web application firewall rule set.",
            default="Microsoft_DefaultRuleSet",
            enum={
                "Microsoft_BotManagerRuleSet": "Microsoft_BotManagerRuleSet",
                "Microsoft_DefaultRuleSet": "Microsoft_DefaultRuleSet",
                "OWASP": "OWASP",
                "Microsoft_HTTPDDoSRuleSet": "Microsoft_HTTPDDoSRuleSet"
            },
        )
        args_schema.rule_set_version = AAZStrArg(
            options=["--version"],
            help="Version of the web application firewall rule set type. "
                 "0.1, 1.0, and 1.1 are used for Microsoft_BotManagerRuleSet",
            default="2.1"
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        managed_rule_set = {
            "rule_set_type": args.rule_set_type,
            "rule_set_version": args.rule_set_version
        }
        managed_rule_definition = {
            "managed_rule_sets": [managed_rule_set]
        }
        args.managed_rules = managed_rule_definition
