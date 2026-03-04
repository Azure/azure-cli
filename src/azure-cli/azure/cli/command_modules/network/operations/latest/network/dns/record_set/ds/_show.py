# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.operations.latest.network.dns.record_set._base import RecordSetShow


@register_command("network dns record-set ds show")
class RecordSetDSShow(RecordSetShow):
    """ Get an DS record set.

    :example: Get an DS record set.
        az network dns record-set ds show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "DS"
