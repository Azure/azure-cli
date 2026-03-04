# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway.nat_rule._list import List as _VnetGatewayNatRuleShow


class VnetGatewayNatRuleShow(_VnetGatewayNatRuleShow):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.selectors.subresource.required(), client_flatten=True)
        return result
