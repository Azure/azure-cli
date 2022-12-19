# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub import \
    Create as _EventHubEntityCreate, \
    Update as _EventHubEntityUpdate


class EventHubEntityCreate(_EventHubEntityCreate):
    def pre_operations(self):
        args = self.ctx.args
        if bool(args.enable_capture) is True and not args.encoding:
            args.encoding = 'Avro'


# pylint:disable=too-many-locals
class EventHubEntityUpdate(_EventHubEntityUpdate):
    def pre_operations(self):
        args = self.ctx.args
        from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub._show import Show

        eventhub = Show(cli_ctx=self.cli_ctx)(command_args={
                      "resource_group": args.resource_group,
                      "namespace_name": args.namespace_name,
                      "eventhub_name": args.eventhub_name
                    })

        if bool(args.enable_capture) is True and not args.encoding and 'captureDescription' not in eventhub:
            args.encoding = 'Avro'
