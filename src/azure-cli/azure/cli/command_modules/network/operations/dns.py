# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger

from azure.cli.core.aaz import has_value, register_command, AAZResourceIdArgFormat
from ..aaz.latest.network.dns.record_set import Update as _RecordSetUpdate

logger = get_logger(__name__)


class RecordSetUpdate(_RecordSetUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_resource._fmt = AAZResourceIdArgFormat()

        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        args_schema.ttl._registered = False
        args_schema.a_records._registered = False
        args_schema.aaaa_records._registered = False
        args_schema.caa_records._registered = False
        args_schema.cname_record._registered = False
        args_schema.mx_records._registered = False
        args_schema.ns_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.txt_records._registered = False
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.target_resource.id):
            instance.properties.target_resource = None


@register_command("network dns record-set a update")
class RecordSetAUpdate(RecordSetUpdate):
    """ Update an A record set.

    :example: Update an A record set.
        az network dns record-set a update -g MyResourceGroup -n MyRecordSet -z www.mysite.com --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network dns record-set aaaa update")
class RecordSetAAAAUpdate(RecordSetUpdate):
    """ Update an AAAA record set.

    :example: Update an AAAA record set.
        az network dns record-set aaaa update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network dns record-set mx update")
class RecordSetMXUpdate(RecordSetUpdate):
    """ Update an MX record set.

    :example: Update an MX record set.
        az network dns record-set mx update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network dns record-set ns update")
class RecordSetNSUpdate(RecordSetUpdate):
    """ Update an NS record set.

    :example: Update an NS record set.
        az network dns record-set ns update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NS"


@register_command("network dns record-set ptr update")
class RecordSetPTRUpdate(RecordSetUpdate):
    """ Update a PTR record set.

    :example: Update a PTR record set.
        az network dns record-set ptr update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network dns record-set srv update")
class RecordSetSRVUpdate(RecordSetUpdate):
    """ Update an SRV record set.

    :example: Update an SRV record set.
        az network dns record-set srv update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network dns record-set txt update")
class RecordSetTXTUpdate(RecordSetUpdate):
    """ Update a TXT record set.

    :example: Update a TXT record set.
        az network dns record-set txt update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"


@register_command("network dns record-set caa update")
class RecordSetCAAUpdate(RecordSetUpdate):
    """ Update a CAA record set.

    :example: Update a CAA record set.
        az network dns record-set caa update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CAA"
