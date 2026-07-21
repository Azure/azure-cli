# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, disable=protected-access
from collections import Counter, OrderedDict
from knack.log import get_logger
from azure.cli.core.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file
from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file
from azure.cli.core.aaz import register_command
from azure.core.exceptions import HttpResponseError

from .aaz.latest.network.private_dns.link.vnet import Create as _PrivateDNSLinkVNetCreate
from .aaz.latest.network.private_dns.zone import Create as _PrivateDNSZoneCreate, Show as PrivateDNSZoneShow
from .aaz.latest.network.private_dns.record_set import Create as _RecordSetCreate, Delete as _RecordSetDelete, \
    ListByType as _RecordSetList, Show as _RecordSetShow, Update as _RecordSetUpdate

logger = get_logger(__name__)


# pylint: disable=too-many-statements, too-many-locals, too-many-branches
def import_zone(cmd, resource_group_name, private_zone_name, file_name):
    from azure.cli.core.util import read_file_content
    import sys
    from azure.mgmt.privatedns.models import RecordSet

    from azure.cli.core.azclierror import FileOperationError, UnclassifiedUserFault
    try:
        file_text = read_file_content(file_name)
    except FileNotFoundError:
        raise FileOperationError("No such file: " + str(file_name))
    except IsADirectoryError:
        raise FileOperationError("Is a directory: " + str(file_name))
    except PermissionError:
        raise FileOperationError("Permission denied: " + str(file_name))
    except OSError as e:
        raise UnclassifiedUserFault(e)

    zone_obj = parse_zone_file(file_text, private_zone_name)
    origin = private_zone_name
    record_sets = {}

    for record_set_name in zone_obj:
        for record_set_type in zone_obj[record_set_name]:
            record_set_obj = zone_obj[record_set_name][record_set_type]

            if record_set_type == 'soa':
                origin = record_set_name.rstrip('.')

            if not isinstance(record_set_obj, list):
                record_set_obj = [record_set_obj]

            for entry in record_set_obj:

                record_set_ttl = entry['ttl']
                record_set_key = '{}{}'.format(record_set_name.lower(), record_set_type)

                record = _build_record(cmd, entry)
                if not record:
                    logger.warning('Cannot import %s. RecordType is not found. Skipping...', entry['delim'].lower())
                    continue

                record_set = record_sets.get(record_set_key, None)
                if not record_set:

                    # Workaround for issue #2824
                    relative_record_set_name = record_set_name.rstrip('.')
                    if not relative_record_set_name.endswith(origin):
                        logger.warning(
                            'Cannot import %s. Only records relative to origin may be '
                            'imported at this time. Skipping...', relative_record_set_name)
                        continue

                    record_set = RecordSet(ttl=record_set_ttl)
                    record_sets[record_set_key] = record_set
                _add_record(record_set, record, record_set_type, is_list=record_set_type.lower() not in ['soa', 'cname'])

    total_records = 0
    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = rs_name[:-(len(origin) + 1)] if rs_name != origin else '@'
        try:
            record_count = len(getattr(rs, _type_to_property_name(rs_type)))
        except TypeError:
            record_count = 1
        total_records += record_count
    cum_records = 0

    from azure.mgmt.privatedns import PrivateDnsManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient)

    print('== BEGINNING ZONE IMPORT: {} ==\n'.format(private_zone_name), file=sys.stderr)

    try:
        PrivateDNSZoneShow(cli_ctx=cmd.cli_ctx)(command_args={
            "name": private_zone_name,
            "resource_group": resource_group_name
        })

        logger.warning("Zone %s already exists in resource group %s.", private_zone_name, resource_group_name)
    except HttpResponseError:
        poller = PrivateDNSZoneCreate(cli_ctx=cmd.cli_ctx)(command_args={
            "name": private_zone_name,
            "resource_group": resource_group_name
        })
        result = LongRunningOperation(cmd.cli_ctx)(poller)
        if result["provisioningState"] != 'Succeeded':
            raise CLIError('Error occured while creating or updating private dns zone.')

    for key, rs in record_sets.items():

        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = '@' if rs_name == origin else rs_name
        if rs_name.endswith(origin):
            rs_name = rs_name[:-(len(origin) + 1)]

        try:
            record_count = len(getattr(rs, _type_to_property_name(rs_type)))
        except TypeError:
            record_count = 1
        if rs_name == '@' and rs_type == 'soa':
            root_soa = client.record_sets.get(resource_group_name, private_zone_name, 'soa', '@')
            rs.soa_record.host = root_soa.soa_record.host
            rs_name = '@'
        try:
            client.record_sets.create_or_update(
                resource_group_name, private_zone_name, rs_type, rs_name, rs)
            cum_records += record_count
            print("({}/{}) Imported {} records of type '{}' and name '{}'"
                  .format(cum_records, total_records, record_count, rs_type, rs_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
    print("\n== {}/{} RECORDS IMPORTED SUCCESSFULLY: '{}' =="
          .format(cum_records, total_records, private_zone_name), file=sys.stderr)


# pylint: disable=too-many-branches
def export_zone(cmd, resource_group_name, private_zone_name, file_name=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from time import localtime, strftime
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record_sets_soa = client.list_by_type(resource_group_name, private_zone_name, "soa")
    record_sets_all = client.list(resource_group_name, private_zone_name)
    zone_obj = OrderedDict({
        '$origin': private_zone_name.rstrip('.') + '.',
        'resource-group': resource_group_name,
        'zone-name': private_zone_name.rstrip('.'),
        'datetime': strftime('%a, %d %b %Y %X %z', localtime())
    })

    for record_set in record_sets_soa:
        record_type = record_set.type.rsplit('/', 1)[1].lower()
        if record_type == 'soa':
            record_set_name = record_set.name
            record_data = getattr(record_set, _type_to_property_name(record_type), None)

            if not isinstance(record_data, list):
                record_data = [record_data]

            for record in record_data:

                record_obj = {'ttl': record_set.ttl}

                if record_type == 'soa':
                    zone_obj[record_set_name] = OrderedDict()
                    zone_obj[record_set_name][record_type] = []
                    record_obj.update({
                        'mname': record.host.rstrip('.') + '.',
                        'rname': record.email.rstrip('.') + '.',
                        'serial': int(record.serial_number), 'refresh': record.refresh_time,
                        'retry': record.retry_time, 'expire': record.expire_time,
                        'minimum': record.minimum_ttl
                    })
                    zone_obj['$ttl'] = record.minimum_ttl
                    zone_obj[record_set_name][record_type].append(record_obj)

    for record_set in record_sets_all:
        record_type = record_set.type.rsplit('/', 1)[1].lower()
        record_set_name = record_set.name
        record_data = getattr(record_set, _type_to_property_name(record_type), None)

        # ignore empty record sets
        if not record_data:
            continue

        if not isinstance(record_data, list):
            record_data = [record_data]

        if record_set_name not in zone_obj:
            zone_obj[record_set_name] = OrderedDict()

        for record in record_data:

            record_obj = {'ttl': record_set.ttl}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []

            if record_type == 'aaaa':
                record_obj.update({'ip': record.ipv6_address})
            elif record_type == 'a':
                record_obj.update({'ip': record.ipv4_address})
            elif record_type == 'caa':
                record_obj.update({'val': record.value, 'tag': record.tag, 'flags': record.flags})
            elif record_type == 'cname':
                record_obj.update({'alias': record.cname.rstrip('.') + '.'})
            elif record_type == 'mx':
                record_obj.update({'preference': record.preference, 'host': record.exchange})
            elif record_type == 'ns':
                record_obj.update({'host': record.nsdname})
            elif record_type == 'ptr':
                record_obj.update({'host': record.ptrdname})
            elif record_type == 'soa':
                continue
            elif record_type == 'srv':
                record_obj.update({'priority': record.priority, 'weight': record.weight,
                                   'port': record.port, 'target': record.target})
            elif record_type == 'txt':
                record_obj.update({'txt': ''.join(record.value)})

            zone_obj[record_set_name][record_type].append(record_obj)

    zone_file_content = make_zone_file(zone_obj)
    print(zone_file_content)
    if file_name:
        try:
            with open(file_name, 'w') as f:
                f.write(zone_file_content)
        except OSError:
            raise CLIError('Unable to export to file: {}'.format(file_name))


# pylint: disable=too-many-return-statements, inconsistent-return-statements, unused-argument
def _build_record(cmd, data):
    from azure.mgmt.privatedns.models import AaaaRecord, ARecord, CnameRecord, MxRecord, PtrRecord, SoaRecord, SrvRecord, TxtRecord
    record_type = data['delim'].lower()
    try:
        if record_type == 'aaaa':
            return AaaaRecord(ipv6_address=data['ip'])
        if record_type == 'a':
            return ARecord(ipv4_address=data['ip'])
        if record_type == 'cname':
            return CnameRecord(cname=data['alias'])
        if record_type == 'mx':
            return MxRecord(preference=data['preference'], exchange=data['host'])
        if record_type == 'ptr':
            return PtrRecord(ptrdname=data['host'])
        if record_type == 'soa':
            return SoaRecord(host=data['host'], email=data['email'], serial_number=data['serial'],
                             refresh_time=data['refresh'], retry_time=data['retry'], expire_time=data['expire'],
                             minimum_ttl=data['minimum'])
        if record_type == 'srv':
            return SrvRecord(
                priority=int(data['priority']), weight=int(data['weight']), port=int(data['port']),
                target=data['target'])
        if record_type in ['txt', 'spf']:
            text_data = data['txt']
            return TxtRecord(value=text_data) if isinstance(text_data, list) else TxtRecord(value=[text_data])
    except KeyError as ke:
        raise CLIError("The {} record '{}' is missing a property.  {}"
                       .format(record_type, data['name'], ke))


class PrivateDNSZoneCreate(_PrivateDNSZoneCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.if_none_match._registered = False
        args_schema.location._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.name.to_serialized_data().endswith(".local"):
            logger.warning(
                "Please be aware that DNS names ending with `.local` are reserved for use with multicast DNS and "
                "may not work as expected with some operating systems. "
                "For details refer to your operating systems documentation."
            )
        args.location = "global"
        args.if_none_match = "*"


class PrivateDNSLinkVNetCreate(_PrivateDNSLinkVNetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.virtual_network._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{}"
        )
        args_schema.registration_enabled._required = True
        args_schema.virtual_network._required = True
        args_schema.if_none_match._registered = False
        args_schema.location._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = "global"
        args.if_none_match = "*"


# region RecordSetCreate
class RecordSetCreate(_RecordSetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False
        args_schema.if_none_match._registered = False
        args_schema.a_records._registered = False
        args_schema.aaaa_records._registered = False
        args_schema.cname_record._registered = False
        args_schema.mx_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.txt_records._registered = False

        return args_schema


@register_command("network private-dns record-set a create")
class RecordSetACreate(RecordSetCreate):
    """ Create an empty A record set.

    :example: Create an empty A record set.
        az network private-dns record-set a create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"
        args.if_none_match = "*"


@register_command("network private-dns record-set aaaa create")
class RecordSetAAAACreate(RecordSetCreate):
    """ Create an empty AAAA record set.

    :example: Create an empty AAAA record set.
        az network private-dns record-set aaaa create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"
        args.if_none_match = "*"


@register_command("network private-dns record-set cname create")
class RecordSetCNAMECreate(RecordSetCreate):
    """ Create an empty CNAME record set.

    :example: Create an empty CNAME record set.
        az network private-dns record-set cname create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"
        args.if_none_match = "*"


@register_command("network private-dns record-set mx create")
class RecordSetMXCreate(RecordSetCreate):
    """ Create an empty MX record set.

    :example: Create an empty MX record set.
        az network private-dns record-set mx create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"
        args.if_none_match = "*"


@register_command("network private-dns record-set ptr create")
class RecordSetPTRCreate(RecordSetCreate):
    """ Create an empty PTR record set.

    :example: Create an empty PTR record set.
        az network private-dns record-set ptr create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"
        args.if_none_match = "*"


@register_command("network private-dns record-set srv create")
class RecordSetSRVCreate(RecordSetCreate):
    """ Create an empty SRV record set.

    :example: Create an empty SRV record set.
        az network private-dns record-set srv create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"
        args.if_none_match = "*"


@register_command("network private-dns record-set txt create")
class RecordSetTXTCreate(RecordSetCreate):
    """ Create an empty TXT record set.

    :example: Create an empty TXT record set.
        az network private-dns record-set txt create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"
        args.if_none_match = "*"
# endregion RecordSetCreate


# region RecordSetDelete
class RecordSetDelete(_RecordSetDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema


@register_command("network private-dns record-set a delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetADelete(RecordSetDelete):
    """ Delete an A record set and all associated records.

    :example: Delete an A record set and all associated records.
        az network private-dns record-set a delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network private-dns record-set aaaa delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetAAAADelete(RecordSetDelete):
    """ Delete an AAAA record set and all associated records.

    :example: Delete an AAAA record set and all associated records.
        az network private-dns record-set aaaa delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network private-dns record-set cname delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetCNAMEDelete(RecordSetDelete):
    """ Delete a CNAME record set and its associated record.

    :example: Delete a CNAME record set and its associated record.
        az network private-dns record-set cname delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"


@register_command("network private-dns record-set mx delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetMXDelete(RecordSetDelete):
    """ Delete an MX record set and all associated records.

    :example: Delete an MX record set and all associated records.
        az network private-dns record-set mx delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network private-dns record-set ptr delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetPTRDelete(RecordSetDelete):
    """ Delete a PTR record set and all associated records.

    :example: Delete a PTR record set and all associated records.
        az network private-dns record-set ptr delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network private-dns record-set srv delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetSRVDelete(RecordSetDelete):
    """ Delete an SRV record set and all associated records.

    :example: Delete an SRV record set and all associated records.
        az network private-dns record-set srv delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network private-dns record-set txt delete", confirmation="Are you sure you want to perform this operation?")
class RecordSetTXTDelete(RecordSetDelete):
    """ Delete a TXT record set and all associated records.

    :example: Delete a TXT record set and all associated records.
        az network private-dns record-set txt delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"
# endregion RecordSetDelete


# region RecordSetList
class RecordSetList(_RecordSetList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema


@register_command("network private-dns record-set a list")
class RecordSetAList(RecordSetList):
    """ List all A record sets in a zone.

    :example: List all A record sets in a zone.
        az network private-dns record-set a list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network private-dns record-set aaaa list")
class RecordSetAAAAList(RecordSetList):
    """ List all AAAA record sets in a zone.

    :example: List all AAAA record sets in a zone.
        az network private-dns record-set aaaa list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network private-dns record-set cname list")
class RecordSetCNAMEList(RecordSetList):
    """ List the CNAME record set in a zone.

    :example: List the CNAME record set in a zone.
        az network private-dns record-set cname list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"


@register_command("network private-dns record-set mx list")
class RecordSetMXList(RecordSetList):
    """ List all MX record sets in a zone.

    :example: List all MX record sets in a zone.
        az network private-dns record-set mx list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network private-dns record-set ptr list")
class RecordSetPTRList(RecordSetList):
    """ List all PTR record sets in a zone.

    :example: List all PTR record sets in a zone.
        az network private-dns record-set ptr list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


@register_command("network private-dns record-set srv list")
class RecordSetSRVList(RecordSetList):
    """ List all SRV record sets in a zone.

    :example: List all SRV record sets in a zone.
        az network private-dns record-set srv list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network private-dns record-set txt list")
class RecordSetTXTList(RecordSetList):
    """ List all TXT record sets in a zone.

    :example: List all TXT record sets in a zone.
        az network private-dns record-set txt list -g MyResourceGroup -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"
# endregion RecordSetList


# region RecordSetShow
class RecordSetShow(_RecordSetShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema


@register_command("network private-dns record-set a show")
class RecordSetAShow(RecordSetShow):
    """ Get the details of an A record set.

    :example: Get the details of an A record set.
        az network private-dns record-set a show -g MyResourceGroup -n MyRecordSet -z www.mysite.com
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network private-dns record-set aaaa show")
class RecordSetAAAAShow(RecordSetShow):
    """ Get the details of an AAAA record set.

    :example: Get the details of an AAAA record set.
        az network private-dns record-set aaaa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network private-dns record-set cname show")
class RecordSetCNAMEShow(RecordSetShow):
    """ Get the details of a CNAME record set.

    :example: Get the details of a CNAME record set.
        az network private-dns record-set cname show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"


@register_command("network private-dns record-set mx show")
class RecordSetMXShow(RecordSetShow):
    """ Get the details of an MX record set.

    :example: Get the details of an MX record set.
        az network private-dns record-set mx show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network private-dns record-set ptr show")
class RecordSetPTRShow(RecordSetShow):
    """ Get the details of a PTR record set.

    :example: Get the details of a PTR record set.
        az network private-dns record-set ptr show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


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


@register_command("network private-dns record-set srv show")
class RecordSetSRVShow(RecordSetShow):
    """ Get the details of an SRV record set.

    :example: Get the details of an SRV record set.
        az network private-dns record-set srv show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network private-dns record-set txt show")
class RecordSetTXTShow(RecordSetShow):
    """ Get the details of a TXT record set.

    :example: Get the details of a TXT record set.
        az network private-dns record-set txt show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"
# endregion RecordSetShow


# region RecordSetUpdate
class RecordSetUpdate(_RecordSetUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False
        args_schema.a_records._registered = False
        args_schema.aaaa_records._registered = False
        args_schema.cname_record._registered = False
        args_schema.mx_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.txt_records._registered = False

        return args_schema


@register_command("network private-dns record-set a update")
class RecordSetAUpdate(RecordSetUpdate):
    """ Update an A record set.

    :example: Update an A record set.
        az network private-dns record-set a update -g MyResourceGroup -n MyRecordSet -z www.mysite.com --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "A"


@register_command("network private-dns record-set aaaa update")
class RecordSetAAAAUpdate(RecordSetUpdate):
    """ Update an AAAA record set.

    :example: Update an AAAA record set.
        az network private-dns record-set aaaa update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "AAAA"


@register_command("network private-dns record-set cname update")
class RecordSetCNAMEUpdate(RecordSetUpdate):
    """ Update a CNAME record set.

    :example: Update a CNAME record set.
        az network private-dns record-set cname update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "CNAME"


@register_command("network private-dns record-set mx update")
class RecordSetMXUpdate(RecordSetUpdate):
    """ Update an MX record set.

    :example: Update an MX record set.
        az network private-dns record-set mx update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "MX"


@register_command("network private-dns record-set ptr update")
class RecordSetPTRUpdate(RecordSetUpdate):
    """ Update a PTR record set.

    :example: Update a PTR record set.
        az network private-dns record-set ptr update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "PTR"


class RecordSetSOAUpdate(RecordSetUpdate):
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SOA"


@register_command("network private-dns record-set srv update")
class RecordSetSRVUpdate(RecordSetUpdate):
    """ Update an SRV record set.

    :example: Update an SRV record set.
        az network private-dns record-set srv update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SRV"


@register_command("network private-dns record-set txt update")
class RecordSetTXTUpdate(RecordSetUpdate):
    """ Update a TXT record set.

    :example: Update a TXT record set.
        az network private-dns record-set txt update -g MyResourceGroup -z www.mysite.com -n MyRecordSet --metadata owner=WebTeam
    """
    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "TXT"
# endregion RecordSetUpdate


def _type_to_property_name(key):
    type_dict = {
        'a': 'a_records',
        'aaaa': 'aaaa_records',
        'cname': 'cname_record',
        'mx': 'mx_records',
        'ptr': 'ptr_records',
        'soa': 'soa_record',
        'srv': 'srv_records',
        'txt': 'txt_records',
    }
    return type_dict[key.lower()]


def _add_record(record_set, record, record_type, is_list=False):
    record_property = _type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is None:
            setattr(record_set, record_property, [])
            record_list = getattr(record_set, record_property)
        record_list.append(record)
    else:
        setattr(record_set, record_property, record)


def _to_snake(s):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _convert_to_snake_case(element):
    if isinstance(element, dict):
        ret = {}
        for k, v in element.items():
            ret[_to_snake(k)] = _convert_to_snake_case(v)

        return ret

    if isinstance(element, list):
        return [_convert_to_snake_case(i) for i in element]

    return element


def _record_show_func(record_type):
    return globals()["RecordSet{}Show".format(record_type.upper())]


def _record_create_func(record_type):
    return globals()["RecordSet{}Create".format(record_type.upper())]


def _record_delete_func(record_type):
    return globals()["RecordSet{}Delete".format(record_type.upper())]


def _record_update_func(record_type):
    return globals()["RecordSet{}Update".format(record_type.upper())]


def _privatedns_type_to_property_name(key):
    type_dict = {
        # `record_type`: (`snake_case`, `camel_case`)
        'a': ('a_records', "aRecords"),
        'aaaa': ('aaaa_records', "aaaaRecords"),
        'cname': ('cname_record', "cnameRecord"),
        'mx': ('mx_records', "mxRecords"),
        'ptr': ('ptr_records', "ptrRecords"),
        'soa': ('soa_record', "soaRecord"),
        'srv': ('srv_records', "srvRecords"),
        'txt': ('txt_records', "txtRecords")
    }
    return type_dict[key.lower()]


def _privatedns_add_record(record_set, record, record_type, is_list=False):
    record_property, _ = _privatedns_type_to_property_name(record_type)

    if is_list:
        record_list = record_set.setdefault(record_property, [])
        record_list.append(record)
    else:
        record_set[record_property] = record


def _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=True):
    record_snake, record_camel = _privatedns_type_to_property_name(record_type)
    is_empty = False

    try:
        _record_show = _record_show_func(record_type)
        ret = _record_show(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "zone_name": private_zone_name,
            "record_type": record_type,
            "name": relative_record_set_name
        })
        record_set = {}
        record_set["ttl"] = ret.get("ttl", None)
        record_set[record_snake] = ret.get(record_camel, None)
        record_set = _convert_to_snake_case(record_set)
    except HttpResponseError:
        record_set = {"ttl": 3600}
        is_empty = True

    _privatedns_add_record(record_set, record, record_type, is_list)

    if is_empty:
        _record_create = _record_create_func(record_type)
        return _record_create(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "zone_name": private_zone_name,
            "record_type": record_type,
            "name": relative_record_set_name,
            **record_set
        })

    _record_update = _record_update_func(record_type)
    return _record_update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": private_zone_name,
        "record_type": record_type,
        "name": relative_record_set_name,
        **record_set
    })


def add_privatedns_aaaa_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv6_address):
    record = {"ipv6_address": ipv6_address}
    record_type = 'aaaa'
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_a_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv4_address):
    record = {"ipv4_address": ipv4_address}
    record_type = 'a'
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_mx_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, preference, exchange):
    record = {"preference": int(preference), "exchange": exchange}
    record_type = 'mx'
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_ptr_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, dname):
    record = {"ptrdname": dname}
    record_type = 'ptr'
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_srv_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, priority, weight, port, target):
    record = {"priority": priority, "weight": weight, "port": port, "target": target}
    record_type = 'srv'
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_txt_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, value):
    record = {"value": value}
    record_type = 'txt'
    long_text = ''.join(x for x in record["value"])
    original_len = len(long_text)
    record["value"] = []
    while len(long_text) > 255:
        record["value"].append(long_text[:255])
        long_text = long_text[255:]
    record["value"].append(long_text)
    final_str = ''.join(record["value"])
    final_len = len(final_str)
    assert original_len == final_len
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_cname_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, cname):
    record = {"cname": cname}
    record_type = 'cname'
    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=False)


def update_privatedns_soa_record(cmd, resource_group_name, private_zone_name, host=None, email=None,
                                 serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                                 minimum_ttl=None):
    relative_record_set_name = '@'
    record_type = 'soa'

    record_set = RecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": private_zone_name,
        "record_type": record_type,
        "name": relative_record_set_name
    })

    record_camal = record_set["soaRecord"]
    record = {}
    record["host"] = host or record_camal.get("host", None)
    record["email"] = email or record_camal.get("email", None)
    record["serial_number"] = serial_number or record_camal.get("serialNumber", None)
    record["refresh_time"] = refresh_time or record_camal.get("refreshTime", None)
    record["retry_time"] = retry_time or record_camal.get("retryTime", None)
    record["expire_time"] = expire_time or record_camal.get("expireTime", None)
    record["minimum_ttl"] = minimum_ttl or record_camal.get("minimumTTL", None)

    return _privatedns_add_save_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=False)


def remove_privatedns_aaaa_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv6_address, keep_empty_record_set=False):
    record = {"ipv6_address": ipv6_address}
    record_type = 'aaaa'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_a_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv4_address, keep_empty_record_set=False):
    record = {"ipv4_address": ipv4_address}
    record_type = 'a'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_cname_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, cname, keep_empty_record_set=False):
    record = {"cname": cname}
    record_type = 'cname'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_mx_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, preference, exchange, keep_empty_record_set=False):
    record = {"preference": int(preference), "exchange": exchange}
    record_type = 'mx'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_ptr_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, dname, keep_empty_record_set=False):
    record = {"ptrdname": dname}
    record_type = 'ptr'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_srv_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, priority, weight, port, target, keep_empty_record_set=False):
    record = {"priority": priority, "weight": weight, "port": port, "target": target}
    record_type = 'srv'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_txt_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, value, keep_empty_record_set=False):
    record = {"value": value}
    record_type = 'txt'
    return _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def _privatedns_remove_record(cmd, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set, is_list=True):
    record_snake, record_camel = _privatedns_type_to_property_name(record_type)
    _record_show = _record_show_func(record_type)
    ret = _record_show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": private_zone_name,
        "record_type": record_type,
        "name": relative_record_set_name
    })
    record_set = {}
    record_set["ttl"] = ret.get("ttl", None)
    record_set[record_snake] = ret.get(record_camel, None)
    record_set = _convert_to_snake_case(record_set)

    if is_list:
        record_list = record_set[record_snake]
        if record_list is not None:
            keep_list = [r for r in record_list if not dict_matches_filter(r, record)]
            if len(keep_list) == len(record_list):
                raise CLIError('Record {} not found.'.format(str(record)))

            record_set[record_snake] = keep_list
    else:
        record_set[record_snake] = None

    if is_list:
        records_remaining = len(record_set[record_snake]) if record_set[record_snake] is not None else 0
    else:
        records_remaining = 1 if record_set[record_snake] is not None else 0

    if not records_remaining and not keep_empty_record_set:
        logger.info('Removing empty %s record set: %s', record_type, relative_record_set_name)

        _record_delete = _record_delete_func(record_type)
        return _record_delete(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "zone_name": private_zone_name,
            "record_type": record_type,
            "name": relative_record_set_name
        })

    _record_update = _record_update_func(record_type)
    return _record_update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": private_zone_name,
        "record_type": record_type,
        "name": relative_record_set_name,
        **record_set
    })


def dict_matches_filter(d, filter_dict):
    sentinel = object()
    return all(not filter_dict.get(key, None)
               or str(filter_dict[key]) == str(d.get(key, sentinel)) # noqa
               or lists_match(filter_dict[key], d.get(key, [])) for key in filter_dict)  # noqa


# pylint: disable=too-many-function-args
def lists_match(l1, l2):
    try:
        return Counter(l1) == Counter(l2)
    except TypeError:
        return False
