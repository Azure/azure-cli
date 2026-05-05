# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.monitor.aaz.latest.monitor.autoscale._show import Show as _AutoScaleShow


class AutoScaleShow(_AutoScaleShow):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        # When the name field conflicts, the name in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.properties.name):
            self.ctx.vars.instance.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
