# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger

from azure.cli.core.aaz import has_value, register_command, AAZResourceIdArgFormat, AAZListArg, AAZResourceIdArg
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from ..aaz.latest.network.dns.record_set import Update as _RecordSetUpdate, Show as _RecordSetShow, \
    ListByType as _RecordSetListByType, Delete as _RecordSetDelete, Create as _RecordSetCreate
from ..aaz.latest.network.dns import ListReferences as _DNSListReferences

logger = get_logger(__name__)


@register_command("network dns list-references")
class DNSListReferences(_DNSListReferences):
    """ Returns the DNS records specified by the referencing targetResourceIds.

    :example: Returns the DNS records specified by the referencing targetResourceIds.
        az network dns list-references --parameters "/subscriptions/**921/resourceGroups/MyResourceGroup/providers/Microsoft.Network/trafficManagerProfiles/MyTrafficManager"
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_resources._registered = False

        args_schema.parameters = AAZListArg(
            options=["--parameters"],
            help="A space-separated list of resource IDs for which referencing dns records need to be queried.",
        )

        parameters = args_schema.parameters
        parameters.Element = AAZResourceIdArg()

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.target_resources = assign_aaz_list_arg(
            args.target_resources,
            args.parameters,
            element_transformer=lambda _, x: {"id": x})


# region RecordSetUpdate
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
        args_schema.ds_records._registered = False
        args_schema.mx_records._registered = False
        args_schema.naptr_records._registered = False
        args_schema.ns_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.tlsa_records._registered = False
        args_schema.txt_records._registered = False

        args_schema.naptr_records._registered = False
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


@register_command("network dns record-set ds update")
class RecordSetDSUpdate(RecordSetUpdate):
    """ Update an DS record set.

    :example: Update an DS record set.
        az network dns record-set ds update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "DS"


@register_command("network dns record-set mx update")
class RecordSetMXUpdate(RecordSetUpdate):
    """ Update an MX record set.

    :example: Update an MX record set.
        az network dns record-set mx update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network dns record-set naptr update")
class RecordSetNAPTRUpdate(RecordSetUpdate):
    """ Update an NAPTR record set.

    :example: Update an NAPTR record set.
        az network dns record-set naptr update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NAPTR"


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


@register_command("network dns record-set tlsa update")
class RecordSetTLSAUpdate(RecordSetUpdate):
    """ Update a TLSA record set.

    :example: Update a TLSA record set.
        az network dns record-set tlsa update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TLSA"


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


@register_command("network dns record-set cname update")
class RecordSetCNAMEUpdate(RecordSetUpdate):
    """ Update a CNAME record set.

    :example: Update a CNAME record set.
        az network dns record-set cname update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"
# endregion RecordSetUpdate


# region RecordSetShow
class RecordSetShow(_RecordSetShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema


@register_command("network dns record-set a show")
class RecordSetAShow(RecordSetShow):
    """ Get an A record set.

    :example: Get an A record set.
        az network dns record-set a show -g MyResourceGroup -n MyRecordSet -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network dns record-set aaaa show")
class RecordSetAAAAShow(RecordSetShow):
    """ Get an AAAA record set.

    :example: Get an AAAA record set.
        az network dns record-set aaaa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network dns record-set ds show")
class RecordSetDSShow(RecordSetShow):
    """ Get an DS record set.

    :example: Get an DS record set.
        az network dns record-set ds show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "DS"


@register_command("network dns record-set mx show")
class RecordSetMXShow(RecordSetShow):
    """ Get an MX record set.

    :example: Get an MX record set.
        az network dns record-set mx show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network dns record-set naptr show")
class RecordSetNAPTRShow(RecordSetShow):
    """ Get an NAPTR record set.

    :example: Get an NAPTR record set.
        az network dns record-set naptr show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NAPTR"


@register_command("network dns record-set ns show")
class RecordSetNSShow(RecordSetShow):
    """ Get an NS record set.

    :example: Get an NS record set.
        az network dns record-set ns show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NS"


@register_command("network dns record-set ptr show")
class RecordSetPTRShow(RecordSetShow):
    """ Get a PTR record set.

    :example: Get a PTR record set.
        az network dns record-set ptr show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network dns record-set srv show")
class RecordSetSRVShow(RecordSetShow):
    """ Get an SRV record set.

    :example: Get an SRV record set.
        az network dns record-set srv show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network dns record-set tlsa show")
class RecordSetTLSAShow(RecordSetShow):
    """ Get a TLSA record set.

    :example: Get a TLSA record set.
        az network dns record-set tlsa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TLSA"


@register_command("network dns record-set txt show")
class RecordSetTXTShow(RecordSetShow):
    """ Get a TXT record set.

    :example: Get a TXT record set.
        az network dns record-set txt show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"


@register_command("network dns record-set caa show")
class RecordSetCAAShow(RecordSetShow):
    """ Get a CAA record set.

    :example: Get a CAA record set.
        az network dns record-set caa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CAA"


@register_command("network dns record-set cname show")
class RecordSetCNAMEShow(RecordSetShow):
    """ Get a CNAME record set.

    :example: Get a CNAME record set.
        az network dns record-set cname show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"


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
# endregion RecordSetShow


# region RecordSetList
class RecordSetList(_RecordSetListByType):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema


@register_command("network dns record-set a list")
class RecordSetAList(RecordSetList):
    """ List A record sets in a zone.

    :example: List A record sets in a zone.
        az network dns record-set a list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network dns record-set aaaa list")
class RecordSetAAAAList(RecordSetList):
    """ List AAAA record sets in a zone.

    :example: List AAAA record sets in a zone.
        az network dns record-set aaaa list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network dns record-set ds list")
class RecordSetDSList(RecordSetList):
    """ List DS record sets in a zone.

    :example: List DS record sets in a zone.
        az network dns record-set ds list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "DS"


@register_command("network dns record-set mx list")
class RecordSetMXList(RecordSetList):
    """ List MX record sets in a zone.

    :example: List MX record sets in a zone.
        az network dns record-set mx list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network dns record-set naptr list")
class RecordSetNAPTRList(RecordSetList):
    """ List NAPTR record sets in a zone.

    :example: List NAPTR record sets in a zone.
        az network dns record-set naptr list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NAPTR"


@register_command("network dns record-set ns list")
class RecordSetNSList(RecordSetList):
    """ List NS record sets in a zone.

    :example: List NS record sets in a zone.
        az network dns record-set ns list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NS"


@register_command("network dns record-set ptr list")
class RecordSetPTRList(RecordSetList):
    """ List PTR record sets in a zone.

    :example: List PTR record sets in a zone.
        az network dns record-set ptr list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network dns record-set srv list")
class RecordSetSRVList(RecordSetList):
    """ List SRV record sets in a zone.

    :example: List SRV record sets in a zone.
        az network dns record-set srv list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network dns record-set tlsa list")
class RecordSetTLSAList(RecordSetList):
    """ List TLSA record sets in a zone.

    :example: List TLSA record sets in a zone.
        az network dns record-set tlsa list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TLSA"


@register_command("network dns record-set txt list")
class RecordSetTXTList(RecordSetList):
    """ List TXT record sets in a zone.

    :example: List TXT record sets in a zone.
        az network dns record-set txt list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"


@register_command("network dns record-set caa list")
class RecordSetCAAList(RecordSetList):
    """ List CAA record sets in a zone.

    :example: List CAA record sets in a zone.
        az network dns record-set caa list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CAA"


@register_command("network dns record-set cname list")
class RecordSetCNAMEList(RecordSetList):
    """ List CNAME record sets in a zone.

    :example: List CNAME record sets in a zone.
        az network dns record-set cname list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"
# endregion RecordSetList


# region RecordSetDelete
class RecordSetDelete(_RecordSetDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema


@register_command("network dns record-set a delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetADelete(RecordSetDelete):
    """ Delete an A record set.

    :example: Delete an A record set.
        az network dns record-set a delete -g MyResourceGroup -n MyRecordSet -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network dns record-set aaaa delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetAAAADelete(RecordSetDelete):
    """ Delete an AAAA record set.

    :example: Delete an AAAA record set.
        az network dns record-set aaaa delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network dns record-set ds delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetDSDelete(RecordSetDelete):
    """ Delete an DS record set.

    :example: Delete an DS record set.
        az network dns record-set ds delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "DS"


@register_command("network dns record-set mx delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetMXDelete(RecordSetDelete):
    """ Delete an MX record set.

    :example: Delete an MX record set.
        az network dns record-set mx delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network dns record-set naptr delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetNAPTRDelete(RecordSetDelete):
    """ Delete an NAPTR record set.

    :example: Delete an NAPTR record set.
        az network dns record-set naptr delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NAPTR"


@register_command("network dns record-set ns delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetNSDelete(RecordSetDelete):
    """ Delete an NS record set.

    :example: Delete an NS record set.
        az network dns record-set ns delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NS"


@register_command("network dns record-set ptr delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetPTRDelete(RecordSetDelete):
    """ Delete a PTR record set.

    :example: Delete a PTR record set.
        az network dns record-set ptr delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network dns record-set srv delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetSRVDelete(RecordSetDelete):
    """ Delete an SRV record set.

    :example: Delete an SRV record set.
        az network dns record-set srv delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network dns record-set tlsa delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetTLSADelete(RecordSetDelete):
    """ Delete a TLSA record set.

    :example: Delete a TLSA record set.
        az network dns record-set tlsa delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TLSA"


@register_command("network dns record-set txt delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetTXTDelete(RecordSetDelete):
    """ Delete a TXT record set.

    :example: Delete a TXT record set.
        az network dns record-set txt delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"


@register_command("network dns record-set caa delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetCAADelete(RecordSetDelete):
    """ Delete a CAA record set.

    :example: Delete a CAA record set.
        az network dns record-set caa delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CAA"


@register_command("network dns record-set cname delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetCNAMEDelete(RecordSetDelete):
    """ Delete a CNAME record set.

    :example: Delete a CNAME record set.
        az network dns record-set cname delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"
# endregion RecordSetDelete


# region RecordSetCreate
class RecordSetCreate(_RecordSetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_resource._fmt = AAZResourceIdArgFormat()

        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        args_schema.a_records._registered = False
        args_schema.aaaa_records._registered = False
        args_schema.caa_records._registered = False
        args_schema.cname_record._registered = False
        args_schema.ds_records._registered = False
        args_schema.mx_records._registered = False
        args_schema.ns_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.tlsa_records._registered = False
        args_schema.txt_records._registered = False

        args_schema.naptr_records._registered = False
        return args_schema


@register_command("network dns record-set a create")
class RecordSetACreate(RecordSetCreate):
    """ Create an A record set.

    :example: Create an A record set.
        az network dns record-set a create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network dns record-set aaaa create")
class RecordSetAAAACreate(RecordSetCreate):
    """ Create an AAAA record set.

    :example: Create an AAAA record set.
        az network dns record-set aaaa create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network dns record-set ds create")
class RecordSetDSCreate(RecordSetCreate):
    """ Create an DS record set.

    :example: Create an DS record set.
        az network dns record-set ds create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "DS"


@register_command("network dns record-set mx create")
class RecordSetMXCreate(RecordSetCreate):
    """ Create an MX record set.

    :example: Create an MX record set.
        az network dns record-set mx create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network dns record-set naptr create")
class RecordSetNAPTRCreate(RecordSetCreate):
    """ Create an NAPTR record set.

    :example: Create an NAPTR record set.
        az network dns record-set naptr create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NAPTR"


@register_command("network dns record-set ns create")
class RecordSetNSCreate(RecordSetCreate):
    """ Create an NS record set.

    :example: Create an NS record set.
        az network dns record-set ns create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "NS"


@register_command("network dns record-set ptr create")
class RecordSetPTRCreate(RecordSetCreate):
    """ Create a PTR record set.

    :example: Create a PTR record set.
        az network dns record-set ptr create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network dns record-set srv create")
class RecordSetSRVCreate(RecordSetCreate):
    """ Create an SRV record set.

    :example: Create an SRV record set.
        az network dns record-set srv create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network dns record-set tlsa create")
class RecordSetTLSACreate(RecordSetCreate):
    """ Create a TLSA record set.

    :example: Create a TLSA record set.
        az network dns record-set tlsa create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TLSA"


@register_command("network dns record-set txt create")
class RecordSetTXTCreate(RecordSetCreate):
    """ Create a TXT record set.

    :example: Create a TXT record set.
        az network dns record-set txt create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"


@register_command("network dns record-set caa create")
class RecordSetCAACreate(RecordSetCreate):
    """ Create a CAA record set.

    :example: Create a CAA record set.
        az network dns record-set caa create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CAA"


@register_command("network dns record-set cname create")
class RecordSetCNAMECreate(RecordSetCreate):
    """ Create a CNAME record set.

    :example: Create a CNAME record set.
        az network dns record-set cname create -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"


class RecordSetSOACreate(RecordSetCreate):
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SOA"
# endregion RecordSetCreate
