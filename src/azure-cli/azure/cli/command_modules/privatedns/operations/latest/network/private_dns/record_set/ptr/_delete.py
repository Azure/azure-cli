# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import register_command

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetDelete


@register_command(
    "network private-dns record-set ptr delete",
    confirmation="Are you sure you want to perform this operation?"
)
class RecordSetPTRDelete(RecordSetDelete):
    """ Delete a PTR record set and all associated records.

    :example: Delete a PTR record set and all associated records.
        az network private-dns record-set ptr delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"
