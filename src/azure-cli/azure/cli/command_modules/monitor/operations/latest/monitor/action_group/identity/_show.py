# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.command_modules.monitor.aaz.latest.monitor.action_group.identity._show \
    import Show as _AGIdentityShow


class AGIdentityShow(_AGIdentityShow):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.selectors.subresource.get(), client_flatten=True)
        return result
