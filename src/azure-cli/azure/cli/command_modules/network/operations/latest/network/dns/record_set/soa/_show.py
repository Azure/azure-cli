# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.operations.latest.network.dns.record_set._base import RecordSetShow


@register_command("network dns record-set soa show")
class RecordSetSOAShow(RecordSetShow):
    """ Get a SOA record set.

    :example: Get a SOA record set.
        az network dns record-set soa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.name._required = False
        args_schema.name._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SOA"
        args.name = "@"
