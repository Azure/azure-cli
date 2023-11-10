# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger

from ._util import import_aaz_by_profile


logger = get_logger(__name__)


_Nsg = import_aaz_by_profile("network.nsg")
_NsgRule = import_aaz_by_profile("network.nsg.rule")


class NSGCreate(_Nsg.Create):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {"NewNSG": result}


class NSGRuleCreate(_NsgRule.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.priority._required = True
        return args_schema


def list_nsg_rules(cmd, resource_group_name, network_security_group_name, include_default=False):
    Show = import_aaz_by_profile("network.nsg").Show
    nsg = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": network_security_group_name
    })

    rules = nsg["securityRules"]
    return rules + nsg["defaultSecurityRules"] if include_default else rules
