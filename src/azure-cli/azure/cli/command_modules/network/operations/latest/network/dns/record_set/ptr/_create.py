# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.operations.latest.network.dns.record_set._base import RecordSetCreate


@register_command("network dns record-set ptr create")
class RecordSetPTRCreate(RecordSetCreate):
    """ Create a PTR record set.

    :example: Create a PTR record set.
        az network dns record-set ptr create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"
