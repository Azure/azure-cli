# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetUpdate


class RecordSetSOAUpdate(RecordSetUpdate):
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SOA"
