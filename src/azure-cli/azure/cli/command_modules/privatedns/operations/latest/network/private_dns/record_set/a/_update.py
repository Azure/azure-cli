# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.aaz import register_command

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetUpdate


@register_command("network private-dns record-set a update")
class RecordSetAUpdate(RecordSetUpdate):
    """ Update an A record set.

    :example: Update an A record set.
        az network private-dns record-set a update -g MyResourceGroup -n MyRecordSet -z www.mysite.com --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"
