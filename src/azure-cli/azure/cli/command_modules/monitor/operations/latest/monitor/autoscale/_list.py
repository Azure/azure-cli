# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.monitor.aaz.latest.monitor.autoscale._list import List as _AutoScaleList


class AutoScaleList(_AutoScaleList):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        # When the name field conflicts, the name in inner layer is ignored and the outer layer is applied
        for value in self.ctx.vars.instance.value:
            if has_value(value.properties):
                value.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link
