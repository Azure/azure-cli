# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from __future__ import print_function
from collections import Counter, OrderedDict
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import parse_resource_id
from azure.cli.core.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file
from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file

logger = get_logger(__name__)


# pylint: disable=line-too-long
def list_privatedns_zones(cmd, resource_group_name=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).private_zones
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


# pylint: disable=too-many-statements, too-many-locals
def import_zone(cmd, resource_group_name, private_zone_name, file_name):
    from azure.cli.core.util import read_file_content
    import sys
    from azure.mgmt.privatedns.models import RecordSet

    file_text = read_file_content(file_name)
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
                _privatedns_add_record(record_set, record, record_set_type, is_list=record_set_type.lower() not in ['soa', 'cname'])

    total_records = 0
    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = rs_name[:-(len(origin) + 1)] if rs_name != origin else '@'
        try:
            record_count = len(getattr(rs, _privatedns_type_to_property_name(rs_type)))
        except TypeError:
            record_count = 1
        total_records += record_count
    cum_records = 0

    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import PrivateZone
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient)

    print('== BEGINNING ZONE IMPORT: {} ==\n'.format(private_zone_name), file=sys.stderr)

    if private_zone_name.endswith(".local"):
        logger.warning(("Please be aware that DNS names ending with .local are reserved for use with multicast DNS "
                        "and may not work as expected with some operating systems. For details refer to your operating systems documentation."))
    zone = PrivateZone(location='global')
    result = LongRunningOperation(cmd.cli_ctx)(client.private_zones.create_or_update(resource_group_name, private_zone_name, zone))
    if result.provisioning_state != 'Succeeded':
        raise CLIError('Error occured while creating or updating private dns zone.')

    for key, rs in record_sets.items():

        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = '@' if rs_name == origin else rs_name
        if rs_name.endswith(origin):
            rs_name = rs_name[:-(len(origin) + 1)]

        try:
            record_count = len(getattr(rs, _privatedns_type_to_property_name(rs_type)))
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
        except CloudError as ex:
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
            record_data = getattr(record_set, _privatedns_type_to_property_name(record_type), None)

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
        record_data = getattr(record_set, _privatedns_type_to_property_name(record_type), None)

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
        except IOError:
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


def create_privatedns_zone(cmd, resource_group_name, private_zone_name, tags=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import PrivateZone
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).private_zones
    if private_zone_name.endswith(".local"):
        logger.warning(("Please be aware that DNS names ending with .local are reserved for use with multicast DNS "
                        "and may not work as expected with some operating systems. For details refer to your operating systems documentation."))
    zone = PrivateZone(location='global', tags=tags)
    return client.create_or_update(resource_group_name, private_zone_name, zone, if_none_match='*')


def update_privatedns_zone(instance, tags=None):
    if tags is not None:
        instance.tags = tags
    return instance


def create_privatedns_link(cmd, resource_group_name, private_zone_name, virtual_network_link_name, virtual_network, registration_enabled, tags=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import VirtualNetworkLink
    link = VirtualNetworkLink(location='global', tags=tags)

    if registration_enabled is not None:
        link.registration_enabled = registration_enabled
        aux_subscription = parse_resource_id(virtual_network.id)['subscription']

    if virtual_network is not None:
        link.virtual_network = virtual_network

    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient, aux_subscriptions=[aux_subscription]).virtual_network_links
    return client.create_or_update(resource_group_name, private_zone_name, virtual_network_link_name, link, if_none_match='*')


def update_privatedns_link(cmd, resource_group_name, private_zone_name, virtual_network_link_name, registration_enabled=None, tags=None, if_match=None, **kwargs):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    link = kwargs['parameters']

    if registration_enabled is not None:
        link.registration_enabled = registration_enabled

    if tags is not None:
        link.tags = tags

    aux_subscription = parse_resource_id(link.virtual_network.id)['subscription']
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient, aux_subscriptions=[aux_subscription]).virtual_network_links
    return client.update(resource_group_name, private_zone_name, virtual_network_link_name, link, if_match=if_match)


def create_privatedns_record_set(cmd, resource_group_name, private_zone_name, relative_record_set_name, record_type, metadata=None, ttl=3600):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import RecordSet
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record_set = RecordSet(ttl=ttl, metadata=metadata)
    return client.create_or_update(resource_group_name, private_zone_name, record_type, relative_record_set_name, record_set, if_none_match='*')


def list_privatedns_record_set(cmd, resource_group_name, private_zone_name, record_type=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    if record_type is not None:
        return client.list_by_type(resource_group_name, private_zone_name, record_type)

    return client.list(resource_group_name, private_zone_name)


def _privatedns_type_to_property_name(key):
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


def _privatedns_add_record(record_set, record, record_type, is_list=False):
    record_property = _privatedns_type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is None:
            setattr(record_set, record_property, [])
            record_list = getattr(record_set, record_property)
        record_list.append(record)
    else:
        setattr(record_set, record_property, record)


def _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=True):
    from azure.mgmt.privatedns.models import RecordSet
    try:
        record_set = client.get(
            resource_group_name, private_zone_name, record_type, relative_record_set_name)
    except CloudError:
        record_set = RecordSet(ttl=3600)

    _privatedns_add_record(record_set, record, record_type, is_list)
    return client.create_or_update(resource_group_name, private_zone_name, record_type, relative_record_set_name, record_set)


def add_privatedns_aaaa_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv6_address):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import AaaaRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_a_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv4_address):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import ARecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_mx_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, preference, exchange):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import MxRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_ptr_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, dname):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import PtrRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_srv_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, priority, weight, port, target):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import SrvRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = SrvRecord(priority=priority, weight=weight,
                       port=port, target=target)
    record_type = 'srv'
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_txt_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, value):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import TxtRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = TxtRecord(value=value)
    record_type = 'txt'
    long_text = ''.join(x for x in record.value)
    original_len = len(long_text)
    record.value = []
    while len(long_text) > 255:
        record.value.append(long_text[:255])
        long_text = long_text[255:]
    record.value.append(long_text)
    final_str = ''.join(record.value)
    final_len = len(final_str)
    assert original_len == final_len
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name)


def add_privatedns_cname_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, cname):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import CnameRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=False)


def update_privatedns_record_set(instance, metadata=None):
    if metadata is not None:
        instance.metadata = metadata

    return instance


def update_privatedns_soa_record(cmd, resource_group_name, private_zone_name, host=None, email=None,
                                 serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                                 minimum_ttl=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    relative_record_set_name = '@'
    record_type = 'soa'

    record_set = client.get(
        resource_group_name, private_zone_name, record_type, relative_record_set_name)
    record = record_set.soa_record

    record.host = host or record.host
    record.email = email or record.email
    record.serial_number = serial_number or record.serial_number
    record.refresh_time = refresh_time or record.refresh_time
    record.retry_time = retry_time or record.retry_time
    record.expire_time = expire_time or record.expire_time
    record.minimum_ttl = minimum_ttl or record.minimum_ttl

    return _privatedns_add_save_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=False)


def remove_privatedns_aaaa_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv6_address, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import AaaaRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_a_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, ipv4_address, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import ARecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_cname_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, cname, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import CnameRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_mx_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, preference, exchange, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import MxRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_ptr_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, dname, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import PtrRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_srv_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, priority, weight, port, target, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import SrvRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = SrvRecord(priority=priority, weight=weight,
                       port=port, target=target)
    record_type = 'srv'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def remove_privatedns_txt_record(cmd, resource_group_name, private_zone_name, relative_record_set_name, value, keep_empty_record_set=False):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    from azure.mgmt.privatedns.models import TxtRecord
    client = get_mgmt_service_client(cmd.cli_ctx, PrivateDnsManagementClient).record_sets
    record = TxtRecord(value=value)
    record_type = 'txt'
    return _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set=keep_empty_record_set)


def _privatedns_remove_record(client, record, record_type, relative_record_set_name, resource_group_name, private_zone_name, keep_empty_record_set, is_list=True):
    record_set = client.get(
        resource_group_name, private_zone_name, record_type, relative_record_set_name)
    record_property = _privatedns_type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is not None:
            keep_list = [r for r in record_list
                         if not dict_matches_filter(r.__dict__, record.__dict__)]
            if len(keep_list) == len(record_list):
                raise CLIError('Record {} not found.'.format(str(record)))
            setattr(record_set, record_property, keep_list)
    else:
        setattr(record_set, record_property, None)

    if is_list:
        records_remaining = len(getattr(record_set, record_property))
    else:
        records_remaining = 1 if getattr(record_set, record_property) is not None else 0

    if not records_remaining and not keep_empty_record_set:
        logger.info('Removing empty %s record set: %s', record_type, relative_record_set_name)
        return client.delete(resource_group_name, private_zone_name, record_type, relative_record_set_name)

    return client.create_or_update(resource_group_name, private_zone_name, record_type, relative_record_set_name, record_set)


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
