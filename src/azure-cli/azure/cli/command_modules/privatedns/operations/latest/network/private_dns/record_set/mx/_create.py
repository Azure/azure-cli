# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import register_command

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetCreate


@register_command("network private-dns record-set mx create")
class RecordSetMXCreate(RecordSetCreate):
    """ Create an empty MX record set.

    :example: Create an empty MX record set.
        az network private-dns record-set mx create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"
        args.if_none_match = "*"
