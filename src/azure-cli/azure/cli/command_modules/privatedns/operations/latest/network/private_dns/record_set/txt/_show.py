# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import register_command

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetShow


@register_command("network private-dns record-set txt show")
class RecordSetTXTShow(RecordSetShow):
    """ Get the details of a TXT record set.

    :example: Get the details of a TXT record set.
        az network private-dns record-set txt show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"
