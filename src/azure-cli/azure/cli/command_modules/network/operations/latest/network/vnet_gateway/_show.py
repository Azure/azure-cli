# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway._show import Show as _VNetGatewayShow


class VNetGatewayShow(_VNetGatewayShow):
    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined

        # resolve flatten conflict
        # when the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        props = self.ctx.vars.instance.properties
        if has_value(props.nat_rules):
            for rule in props.nat_rules:
                if has_value(rule.properties) and has_value(rule.properties.type):
                    rule.properties.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)

        return result
