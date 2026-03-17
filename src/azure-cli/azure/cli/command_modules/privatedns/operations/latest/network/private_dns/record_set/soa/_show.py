# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
from azure.cli.core.aaz import register_command

from azure.cli.command_modules.privatedns.operations.latest.network.private_dns.record_set._base import RecordSetShow


@register_command("network private-dns record-set soa show")
class RecordSetSOAShow(RecordSetShow):
    """ Get the details of an SOA record.

    :example: Get the details of an SOA record.
        az network private-dns record-set soa show -g MyResourceGroup -z www.mysite.com
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._required = False
        args_schema.name._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.name = "@"
        args.record_type = "SOA"
