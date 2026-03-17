# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.operations.latest.network.dns.record_set._base import RecordSetList


@register_command("network dns record-set ns list")
class RecordSetNSList(RecordSetList):
    """ List NS record sets in a zone.

    :example: List NS record sets in a zone.
        az network dns record-set ns list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NS"
