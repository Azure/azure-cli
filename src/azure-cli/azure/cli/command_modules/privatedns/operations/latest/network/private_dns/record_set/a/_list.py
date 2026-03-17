# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import register_command

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetList


@register_command("network private-dns record-set a list")
class RecordSetAList(RecordSetList):
    """ List all A record sets in a zone.

    :example: List all A record sets in a zone.
        az network private-dns record-set a list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"
