# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import Counter, OrderedDict

from msrestazure.tools import parse_resource_id, is_valid_resource_id, resource_id

from knack.log import get_logger

# pylint: disable=no-self-use,no-member,too-many-lines,unused-argument
from azure.cli.core.commands import cached_get, cached_put, upsert_to_collection, get_property
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client

from azure.cli.core.util import CLIError, sdk_no_wait, find_child_item, find_child_collection
from azure.cli.core.azclierror import RequiredArgumentMissingError, UnrecognizedArgumentError, ResourceNotFoundError, \
    ArgumentUsageError, MutuallyExclusiveArgumentError
from azure.cli.core.profiles import ResourceType, supported_api_version

from azure.cli.command_modules.network.azure_stack._client_factory import network_client_factory
from azure.cli.command_modules.network.azure_stack.zone_file.parse_zone_file import parse_zone_file
from azure.cli.command_modules.network.azure_stack.zone_file.make_zone_file import make_zone_file

logger = get_logger(__name__)


# region Utility methods
def _log_pprint_template(template):
    import json
    logger.info('==== BEGIN TEMPLATE ====')
    logger.info(json.dumps(template, indent=2))
    logger.info('==== END TEMPLATE ====')


def _get_default_name(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, True)


def _get_default_id(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, False)


def _get_default_value(balancer, property_name, option_name, return_name):
    values = [x.id for x in getattr(balancer, property_name)]
    if len(values) > 1:
        raise CLIError("Multiple possible values found for '{0}': {1}\nSpecify '{0}' "
                       "explicitly.".format(option_name, ', '.join(values)))
    if not values:
        raise CLIError("No existing values found for '{0}'. Create one first and try "
                       "again.".format(option_name))
    return values[0].rsplit('/', 1)[1] if return_name else values[0]

# endregion


# region Generic list commands
def _generic_list(cli_ctx, operation_name, resource_group_name):
    ncf = network_client_factory(cli_ctx)
    operation_group = getattr(ncf, operation_name)
    if resource_group_name:
        return operation_group.list(resource_group_name)

    return operation_group.list_all()


def list_vnet(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'virtual_networks', resource_group_name)


def list_express_route_circuits(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'express_route_circuits', resource_group_name)


def create_express_route_auth(cmd, resource_group_name, circuit_name, authorization_name):
    ExpressRouteCircuitAuthorization = cmd.get_models('ExpressRouteCircuitAuthorization')

    client = network_client_factory(cmd.cli_ctx).express_route_circuit_authorizations
    return client.begin_create_or_update(resource_group_name,
                                         circuit_name,
                                         authorization_name,
                                         ExpressRouteCircuitAuthorization())


def list_lbs(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'load_balancers', resource_group_name)


def list_nics(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'network_interfaces', resource_group_name)


def list_custom_ip_prefixes(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'custom_ip_prefixes', resource_group_name)


def list_route_tables(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'route_tables', resource_group_name)


def list_network_watchers(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'network_watchers', resource_group_name)

# endregion


# region ApplicationGateways
# pylint: disable=too-many-locals
def _is_v2_sku(sku):
    return 'v2' in sku


# pylint: disable=too-many-statements
# region DdosProtectionPlans
def create_ddos_plan(cmd, resource_group_name, ddos_plan_name, location=None, tags=None, vnets=None):
    from azure.cli.core.commands import LongRunningOperation
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Create
    Create_Ddos_Protection = Create(cli_ctx=cmd.cli_ctx)
    args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    if location:
        args['location'] = location
    if tags:
        args['tags'] = tags
    if not vnets:
        # if no VNETs can do a simple PUT
        return Create_Ddos_Protection(args)

    # if VNETs specified, have to create the protection plan and then add the VNETs
    plan_id = LongRunningOperation(cmd.cli_ctx)(Create_Ddos_Protection(args))['id']

    SubResource = cmd.get_models('SubResource')
    logger.info('Attempting to attach VNets to newly created DDoS protection plan.')
    for vnet_subresource in vnets:
        vnet_client = network_client_factory(cmd.cli_ctx).virtual_networks
        id_parts = parse_resource_id(vnet_subresource.id)
        vnet = vnet_client.get(id_parts['resource_group'], id_parts['name'])
        vnet.ddos_protection_plan = SubResource(id=plan_id)
        vnet_client.begin_create_or_update(id_parts['resource_group'], id_parts['name'], vnet)

    show_args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Show
    Show_Ddos_Protection = Show(cli_ctx=cmd.cli_ctx)
    return Show_Ddos_Protection(show_args)


def update_ddos_plan(cmd, resource_group_name, ddos_plan_name, tags=None, vnets=None):
    SubResource = cmd.get_models('SubResource')
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Update
    Update_Ddos_Protection = Update(cli_ctx=cmd.cli_ctx)
    args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    if tags is not None:
        args['tags'] = tags
    if vnets is not None:
        from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Show
        show_args = {
            "name": ddos_plan_name,
            "resource_group": resource_group_name,
        }
        Show_Ddos_Protection = Show(cli_ctx=cmd.cli_ctx)
        show_args = Show_Ddos_Protection(show_args)
        logger.info('Attempting to update the VNets attached to the DDoS protection plan.')
        vnet_ids = set([])
        if len(vnets) == 1 and not vnets[0]:
            pass
        else:
            vnet_ids = {x.id for x in vnets}
        if 'virtualNetworks' in show_args:
            existing_vnet_ids = {x['id'] for x in show_args['virtualNetworks']}
        else:
            existing_vnet_ids = set([])
        client = network_client_factory(cmd.cli_ctx).virtual_networks
        for vnet_id in vnet_ids.difference(existing_vnet_ids):
            logger.info("Adding VNet '%s' to plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            vnet = client.get(id_parts['resource_group'], id_parts['name'])
            vnet.ddos_protection_plan = SubResource(id=show_args['id'])
            client.begin_create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
        for vnet_id in existing_vnet_ids.difference(vnet_ids):
            logger.info("Removing VNet '%s' from plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            vnet = client.get(id_parts['resource_group'], id_parts['name'])
            vnet.ddos_protection_plan = None
            client.begin_create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
    return Update_Ddos_Protection(args)


def list_ddos_plans(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).ddos_protection_plans
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()
# endregion


# region DNS Commands
# add delegation name server record for the created child zone in it's parent zone.
def add_dns_delegation(cmd, child_zone, parent_zone, child_rg, child_zone_name):
    """
     :param child_zone: the zone object corresponding to the child that is created.
     :param parent_zone: the parent zone name / FQDN of the parent zone.
                         if parent zone name is mentioned, assume current subscription and resource group.
     :param child_rg: resource group of the child zone
     :param child_zone_name: name of the child zone
    """
    import sys
    from azure.core.exceptions import HttpResponseError
    parent_rg = child_rg
    parent_subscription_id = None
    parent_zone_name = parent_zone

    if is_valid_resource_id(parent_zone):
        id_parts = parse_resource_id(parent_zone)
        parent_rg = id_parts['resource_group']
        parent_subscription_id = id_parts['subscription']
        parent_zone_name = id_parts['name']

    if all([parent_zone_name, parent_rg, child_zone_name, child_zone]) and child_zone_name.endswith(parent_zone_name):
        record_set_name = child_zone_name.replace('.' + parent_zone_name, '')
        try:
            for dname in child_zone.name_servers:
                add_dns_ns_record(cmd, parent_rg, parent_zone_name, record_set_name, dname, parent_subscription_id)
            print('Delegation added succesfully in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
            print('Could not add delegation in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)


def create_dns_zone(cmd, client, resource_group_name, zone_name, parent_zone_name=None, tags=None,
                    if_none_match=False, zone_type='Public', resolution_vnets=None, registration_vnets=None):
    Zone = cmd.get_models('Zone', resource_type=ResourceType.MGMT_NETWORK_DNS)
    zone = Zone(location='global', tags=tags)

    if hasattr(zone, 'zone_type'):
        zone.zone_type = zone_type
        zone.registration_virtual_networks = registration_vnets
        zone.resolution_virtual_networks = resolution_vnets

    created_zone = client.create_or_update(resource_group_name, zone_name, zone,
                                           if_none_match='*' if if_none_match else None)

    if cmd.supported_api_version(min_api='2016-04-01') and parent_zone_name is not None:
        logger.info('Attempting to add delegation in the parent zone')
        add_dns_delegation(cmd, created_zone, parent_zone_name, resource_group_name, zone_name)
    return created_zone


def update_dns_zone(instance, tags=None, zone_type=None, resolution_vnets=None, registration_vnets=None):

    if tags is not None:
        instance.tags = tags

    if zone_type:
        instance.zone_type = zone_type

    if resolution_vnets == ['']:
        instance.resolution_virtual_networks = None
    elif resolution_vnets:
        instance.resolution_virtual_networks = resolution_vnets

    if registration_vnets == ['']:
        instance.registration_virtual_networks = None
    elif registration_vnets:
        instance.registration_virtual_networks = registration_vnets
    return instance


def list_dns_zones(cmd, resource_group_name=None):
    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).zones
    if resource_group_name:
        return ncf.list_by_resource_group(resource_group_name)
    return ncf.list()


def create_dns_record_set(cmd, resource_group_name, zone_name, record_set_name, record_set_type,
                          metadata=None, if_match=None, if_none_match=None, ttl=3600, target_resource=None):

    RecordSet = cmd.get_models('RecordSet', resource_type=ResourceType.MGMT_NETWORK_DNS)
    SubResource = cmd.get_models('SubResource', resource_type=ResourceType.MGMT_NETWORK)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = RecordSet(
        ttl=ttl,
        metadata=metadata,
        target_resource=SubResource(id=target_resource) if target_resource else None
    )
    return client.create_or_update(resource_group_name, zone_name, record_set_name,
                                   record_set_type, record_set, if_match=if_match,
                                   if_none_match='*' if if_none_match else None)


def list_dns_record_set(client, resource_group_name, zone_name, record_type=None):
    if record_type:
        return client.list_by_type(resource_group_name, zone_name, record_type)

    return client.list_by_dns_zone(resource_group_name, zone_name)


def update_dns_record_set(instance, cmd, metadata=None, target_resource=None):
    if metadata is not None:
        instance.metadata = metadata
    if target_resource == '':
        instance.target_resource = None
    elif target_resource is not None:
        SubResource = cmd.get_models('SubResource')
        instance.target_resource = SubResource(id=target_resource)
    return instance


def _type_to_property_name(key):
    type_dict = {
        'a': 'a_records',
        'aaaa': 'aaaa_records',
        'caa': 'caa_records',
        'cname': 'cname_record',
        'mx': 'mx_records',
        'ns': 'ns_records',
        'ptr': 'ptr_records',
        'soa': 'soa_record',
        'spf': 'txt_records',
        'srv': 'srv_records',
        'txt': 'txt_records',
        'alias': 'target_resource',
    }
    return type_dict[key.lower()]


def export_zone(cmd, resource_group_name, zone_name, file_name=None):  # pylint: disable=too-many-branches
    from time import localtime, strftime

    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS)
    record_sets = client.record_sets.list_by_dns_zone(resource_group_name, zone_name)

    zone_obj = OrderedDict({
        '$origin': zone_name.rstrip('.') + '.',
        'resource-group': resource_group_name,
        'zone-name': zone_name.rstrip('.'),
        'datetime': strftime('%a, %d %b %Y %X %z', localtime())
    })

    for record_set in record_sets:
        record_type = record_set.type.rsplit('/', 1)[1].lower()
        record_set_name = record_set.name
        record_data = getattr(record_set, _type_to_property_name(record_type), None)

        if not record_data:
            record_data = []
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
                record_obj.update({'preference': record.preference, 'host': record.exchange.rstrip('.') + '.'})
            elif record_type == 'ns':
                record_obj.update({'host': record.nsdname.rstrip('.') + '.'})
            elif record_type == 'ptr':
                record_obj.update({'host': record.ptrdname.rstrip('.') + '.'})
            elif record_type == 'soa':
                record_obj.update({
                    'mname': record.host.rstrip('.') + '.',
                    'rname': record.email.rstrip('.') + '.',
                    'serial': int(record.serial_number), 'refresh': record.refresh_time,
                    'retry': record.retry_time, 'expire': record.expire_time,
                    'minimum': record.minimum_ttl
                })
                zone_obj['$ttl'] = record.minimum_ttl
            elif record_type == 'srv':
                record_obj.update({'priority': record.priority, 'weight': record.weight,
                                   'port': record.port, 'target': record.target.rstrip('.') + '.'})
            elif record_type == 'txt':
                record_obj.update({'txt': ''.join(record.value)})
            zone_obj[record_set_name][record_type].append(record_obj)

        if len(record_data) == 0:
            record_obj = {'ttl': record_set.ttl}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []
            # Checking for alias record
            if (record_type == 'a' or record_type == 'aaaa' or record_type == 'cname') and record_set.target_resource.id:
                target_resource_id = record_set.target_resource.id
                record_obj.update({'target-resource-id': record_type.upper() + " " + target_resource_id})
                record_type = 'alias'
                if record_type not in zone_obj[record_set_name]:
                    zone_obj[record_set_name][record_type] = []
            elif record_type == 'aaaa' or record_type == 'a':
                record_obj.update({'ip': ''})
            elif record_type == 'cname':
                record_obj.update({'alias': ''})
            zone_obj[record_set_name][record_type].append(record_obj)
    zone_file_content = make_zone_file(zone_obj)
    print(zone_file_content)
    if file_name:
        try:
            with open(file_name, 'w') as f:
                f.write(zone_file_content)
        except IOError:
            raise CLIError('Unable to export to file: {}'.format(file_name))


# pylint: disable=too-many-return-statements, inconsistent-return-statements, too-many-branches
def _build_record(cmd, data):
    (
        AaaaRecord,
        ARecord,
        CaaRecord,
        CnameRecord,
        MxRecord,
        NsRecord,
        PtrRecord,
        SoaRecord,
        SrvRecord,
        TxtRecord,
        SubResource,
    ) = cmd.get_models(
        "AaaaRecord",
        "ARecord",
        "CaaRecord",
        "CnameRecord",
        "MxRecord",
        "NsRecord",
        "PtrRecord",
        "SoaRecord",
        "SrvRecord",
        "TxtRecord",
        "SubResource",
        resource_type=ResourceType.MGMT_NETWORK_DNS,
    )
    record_type = data['delim'].lower()
    try:
        if record_type == 'aaaa':
            return AaaaRecord(ipv6_address=data['ip'])
        if record_type == 'a':
            return ARecord(ipv4_address=data['ip'])
        if (record_type == 'caa' and
                supported_api_version(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS, min_api='2018-03-01-preview')):
            return CaaRecord(value=data['val'], flags=int(data['flags']), tag=data['tag'])
        if record_type == 'cname':
            return CnameRecord(cname=data['alias'])
        if record_type == 'mx':
            return MxRecord(preference=data['preference'], exchange=data['host'])
        if record_type == 'ns':
            return NsRecord(nsdname=data['host'])
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
        if record_type == 'alias':
            return SubResource(id=data["resourceId"])
    except KeyError as ke:
        raise CLIError("The {} record '{}' is missing a property.  {}"
                       .format(record_type, data['name'], ke))


# pylint: disable=too-many-statements
def import_zone(cmd, resource_group_name, zone_name, file_name):
    from azure.cli.core.util import read_file_content
    from azure.core.exceptions import HttpResponseError
    import sys
    logger.warning("In the future, zone name will be case insensitive.")
    RecordSet = cmd.get_models('RecordSet', resource_type=ResourceType.MGMT_NETWORK_DNS)

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

    zone_obj = parse_zone_file(file_text, zone_name)

    origin = zone_name
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
                alias_record_type = entry.get("aliasDelim", None)

                if alias_record_type:
                    alias_record_type = alias_record_type.lower()
                    record_set_key = '{}{}'.format(record_set_name.lower(), alias_record_type)

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
                _add_record(record_set, record, record_set_type,
                            is_list=record_set_type.lower() not in ['soa', 'cname', 'alias'])

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

    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS)
    print('== BEGINNING ZONE IMPORT: {} ==\n'.format(zone_name), file=sys.stderr)

    Zone = cmd.get_models('Zone', resource_type=ResourceType.MGMT_NETWORK_DNS)
    client.zones.create_or_update(resource_group_name, zone_name, Zone(location='global'))
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
            root_soa = client.record_sets.get(resource_group_name, zone_name, '@', 'SOA')
            rs.soa_record.host = root_soa.soa_record.host
            rs_name = '@'
        elif rs_name == '@' and rs_type == 'ns':
            root_ns = client.record_sets.get(resource_group_name, zone_name, '@', 'NS')
            root_ns.ttl = rs.ttl
            rs = root_ns
            rs_type = rs.type.rsplit('/', 1)[1]
        try:
            client.record_sets.create_or_update(
                resource_group_name, zone_name, rs_name, rs_type, rs)
            cum_records += record_count
            print("({}/{}) Imported {} records of type '{}' and name '{}'"
                  .format(cum_records, total_records, record_count, rs_type, rs_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
    print("\n== {}/{} RECORDS IMPORTED SUCCESSFULLY: '{}' =="
          .format(cum_records, total_records, zone_name), file=sys.stderr)


def add_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                        ttl=3600, if_none_match=None):
    AaaaRecord = cmd.get_models('AaaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                     ttl=3600, if_none_match=None):
    ARecord = cmd.get_models('ARecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name, 'arecords',
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value, flags, tag,
                       ttl=3600, if_none_match=None):
    CaaRecord = cmd.get_models('CaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CaaRecord(flags=flags, tag=tag, value=value)
    record_type = 'caa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname, ttl=3600, if_none_match=None):
    CnameRecord = cmd.get_models('CnameRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, ttl=ttl, if_none_match=if_none_match)


def add_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                      ttl=3600, if_none_match=None):
    MxRecord = cmd.get_models('MxRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                      subscription_id=None, ttl=3600, if_none_match=None):
    NsRecord = cmd.get_models('NsRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = NsRecord(nsdname=dname)
    record_type = 'ns'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            subscription_id=subscription_id, ttl=ttl, if_none_match=if_none_match)


def add_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname, ttl=3600, if_none_match=None):
    PtrRecord = cmd.get_models('PtrRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def update_dns_soa_record(cmd, resource_group_name, zone_name, host=None, email=None,
                          serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                          minimum_ttl=3600, if_none_match=None):
    record_set_name = '@'
    record_type = 'soa'

    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    record = record_set.soa_record

    record.host = host or record.host
    record.email = email or record.email
    record.serial_number = serial_number or record.serial_number
    record.refresh_time = refresh_time or record.refresh_time
    record.retry_time = retry_time or record.retry_time
    record.expire_time = expire_time or record.expire_time
    record.minimum_ttl = minimum_ttl or record.minimum_ttl

    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, if_none_match=if_none_match)


def add_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                       port, target, if_none_match=None):
    SrvRecord = cmd.get_models('SrvRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = SrvRecord(priority=priority, weight=weight, port=port, target=target)
    record_type = 'srv'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def add_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value, if_none_match=None):
    TxtRecord = cmd.get_models('TxtRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
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
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def remove_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                           keep_empty_record_set=False):
    AaaaRecord = cmd.get_models('AaaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                        keep_empty_record_set=False):
    ARecord = cmd.get_models('ARecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          flags, tag, keep_empty_record_set=False):
    CaaRecord = cmd.get_models('CaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CaaRecord(flags=flags, tag=tag, value=value)
    record_type = 'caa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname,
                            keep_empty_record_set=False):
    CnameRecord = cmd.get_models('CnameRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                         keep_empty_record_set=False):
    MxRecord = cmd.get_models('MxRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                         keep_empty_record_set=False):
    NsRecord = cmd.get_models('NsRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = NsRecord(nsdname=dname)
    record_type = 'ns'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                          keep_empty_record_set=False):
    PtrRecord = cmd.get_models('PtrRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                          port, target, keep_empty_record_set=False):
    SrvRecord = cmd.get_models('SrvRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = SrvRecord(priority=priority, weight=weight, port=port, target=target)
    record_type = 'srv'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          keep_empty_record_set=False):
    TxtRecord = cmd.get_models('TxtRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = TxtRecord(value=value)
    record_type = 'txt'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def _check_a_record_exist(record, exist_list):
    for r in exist_list:
        if r.ipv4_address == record.ipv4_address:
            return True
    return False


def _check_aaaa_record_exist(record, exist_list):
    for r in exist_list:
        if r.ipv6_address == record.ipv6_address:
            return True
    return False


def _check_caa_record_exist(record, exist_list):
    for r in exist_list:
        if (r.flags == record.flags and
                r.tag == record.tag and
                r.value == record.value):
            return True
    return False


def _check_cname_record_exist(record, exist_list):
    for r in exist_list:
        if r.cname == record.cname:
            return True
    return False


def _check_mx_record_exist(record, exist_list):
    for r in exist_list:
        if (r.preference == record.preference and
                r.exchange == record.exchange):
            return True
    return False


def _check_ns_record_exist(record, exist_list):
    for r in exist_list:
        if r.nsdname == record.nsdname:
            return True
    return False


def _check_ptr_record_exist(record, exist_list):
    for r in exist_list:
        if r.ptrdname == record.ptrdname:
            return True
    return False


def _check_srv_record_exist(record, exist_list):
    for r in exist_list:
        if (r.priority == record.priority and
                r.weight == record.weight and
                r.port == record.port and
                r.target == record.target):
            return True
    return False


def _check_txt_record_exist(record, exist_list):
    for r in exist_list:
        if r.value == record.value:
            return True
    return False


def _record_exist_func(record_type):
    return globals()["_check_{}_record_exist".format(record_type)]


def _add_record(record_set, record, record_type, is_list=False):
    record_property = _type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is None:
            setattr(record_set, record_property, [])
            record_list = getattr(record_set, record_property)

        _record_exist = _record_exist_func(record_type)
        if not _record_exist(record, record_list):
            record_list.append(record)
    else:
        setattr(record_set, record_property, record)


def _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                     is_list=True, subscription_id=None, ttl=None, if_none_match=None):
    from azure.core.exceptions import HttpResponseError
    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS,
                                  subscription_id=subscription_id).record_sets

    try:
        record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    except HttpResponseError:
        RecordSet = cmd.get_models('RecordSet', resource_type=ResourceType.MGMT_NETWORK_DNS)
        record_set = RecordSet(ttl=3600)

    if ttl is not None:
        record_set.ttl = ttl

    _add_record(record_set, record, record_type, is_list)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_type, record_set,
                                if_none_match='*' if if_none_match else None)


def _remove_record(cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                   keep_empty_record_set, is_list=True):
    ncf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    record_property = _type_to_property_name(record_type)

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
        logger.info('Removing empty %s record set: %s', record_type, record_set_name)
        return ncf.delete(resource_group_name, zone_name, record_set_name, record_type)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name, record_type, record_set)


def dict_matches_filter(d, filter_dict):
    sentinel = object()
    return all(not filter_dict.get(key, None) or
               str(filter_dict[key]) == str(d.get(key, sentinel)) or
               lists_match(filter_dict[key], d.get(key, []))
               for key in filter_dict)


def lists_match(l1, l2):
    try:
        return Counter(l1) == Counter(l2)  # pylint: disable=too-many-function-args
    except TypeError:
        return False
# endregion


# region ExpressRoutes
def create_express_route(cmd, circuit_name, resource_group_name, bandwidth_in_mbps, peering_location,
                         service_provider_name, location=None, tags=None, no_wait=False,
                         sku_family=None, sku_tier=None, allow_global_reach=None, express_route_port=None,
                         allow_classic_operations=None):
    ExpressRouteCircuit, ExpressRouteCircuitSku, ExpressRouteCircuitServiceProviderProperties, SubResource = \
        cmd.get_models(
            'ExpressRouteCircuit', 'ExpressRouteCircuitSku', 'ExpressRouteCircuitServiceProviderProperties',
            'SubResource')
    client = network_client_factory(cmd.cli_ctx).express_route_circuits
    sku_name = '{}_{}'.format(sku_tier, sku_family)
    circuit = ExpressRouteCircuit(
        location=location, tags=tags,
        service_provider_properties=ExpressRouteCircuitServiceProviderProperties(
            service_provider_name=service_provider_name,
            peering_location=peering_location,
            bandwidth_in_mbps=bandwidth_in_mbps if not express_route_port else None),
        sku=ExpressRouteCircuitSku(name=sku_name, tier=sku_tier, family=sku_family),
        allow_global_reach=allow_global_reach,
        bandwidth_in_gbps=(int(bandwidth_in_mbps) / 1000) if express_route_port else None
    )
    if cmd.supported_api_version(min_api='2010-07-01') and allow_classic_operations is not None:
        circuit.allow_classic_operations = allow_classic_operations
    if cmd.supported_api_version(min_api='2018-08-01') and express_route_port:
        circuit.express_route_port = SubResource(id=express_route_port)
        circuit.service_provider_properties = None
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, circuit_name, circuit)


def update_express_route(instance, cmd, bandwidth_in_mbps=None, peering_location=None,
                         service_provider_name=None, sku_family=None, sku_tier=None, tags=None,
                         allow_global_reach=None, express_route_port=None,
                         allow_classic_operations=None):

    with cmd.update_context(instance) as c:
        c.set_param('allow_classic_operations', allow_classic_operations)
        c.set_param('tags', tags)
        c.set_param('allow_global_reach', allow_global_reach)

    with cmd.update_context(instance.sku) as c:
        c.set_param('family', sku_family)
        c.set_param('tier', sku_tier)

    with cmd.update_context(instance.service_provider_properties) as c:
        c.set_param('peering_location', peering_location)
        c.set_param('service_provider_name', service_provider_name)

    if express_route_port is not None:
        SubResource = cmd.get_models('SubResource')
        instance.express_route_port = SubResource(id=express_route_port)
        instance.service_provider_properties = None

    if bandwidth_in_mbps is not None:
        if not instance.express_route_port:
            instance.service_provider_properties.bandwith_in_mbps = float(bandwidth_in_mbps)
        else:
            instance.bandwidth_in_gbps = (float(bandwidth_in_mbps) / 1000)

    return instance


def create_express_route_peering_connection(cmd, resource_group_name, circuit_name, peering_name, connection_name,
                                            peer_circuit, address_prefix, authorization_key=None):
    client = network_client_factory(cmd.cli_ctx).express_route_circuit_connections
    ExpressRouteCircuitConnection, SubResource = cmd.get_models('ExpressRouteCircuitConnection', 'SubResource')
    source_circuit = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Network',
        type='expressRouteCircuits',
        name=circuit_name,
        child_type_1='peerings',
        child_name_1=peering_name
    )
    conn = ExpressRouteCircuitConnection(
        express_route_circuit_peering=SubResource(id=source_circuit),
        peer_express_route_circuit_peering=SubResource(id=peer_circuit),
        address_prefix=address_prefix,
        authorization_key=authorization_key
    )
    return client.begin_create_or_update(resource_group_name, circuit_name, peering_name, connection_name, conn)


def set_express_route_peering_connection_config(cmd, resource_group_name, circuit_name, peering_name, connection_name,
                                                address_prefix):
    client = network_client_factory(cmd.cli_ctx).express_route_circuit_connections

    # Get Conn
    try:
        conn = client.get(resource_group_name, circuit_name, peering_name, connection_name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError("Peering Connection {} doesn't exist".format(connection_name))

    Ipv6CircuitConnectionConfig = cmd.get_models('Ipv6CircuitConnectionConfig')

    ipv6_config = Ipv6CircuitConnectionConfig(
        address_prefix=address_prefix
    )
    conn.ipv6_circuit_connection_config = ipv6_config

    return client.begin_create_or_update(resource_group_name, circuit_name, peering_name, connection_name, conn)


def remove_express_route_peering_connection_config(cmd, resource_group_name, circuit_name, peering_name,
                                                   connection_name):
    client = network_client_factory(cmd.cli_ctx).express_route_circuit_connections

    # Get Conn
    try:
        conn = client.get(resource_group_name, circuit_name, peering_name, connection_name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError("Peering Connection {} doesn't exist".format(connection_name))

    conn.ipv6_circuit_connection_config = None

    return client.begin_create_or_update(resource_group_name, circuit_name, peering_name, connection_name, conn)


def _validate_ipv6_address_prefixes(prefixes):
    from ipaddress import ip_network, IPv6Network
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    version = None
    for prefix in prefixes:
        try:
            network = ip_network(prefix)
            if version is None:
                version = type(network)
            else:
                if not isinstance(network, version):  # pylint: disable=isinstance-second-argument-not-valid-type
                    raise CLIError("usage error: '{}' incompatible mix of IPv4 and IPv6 address prefixes."
                                   .format(prefixes))
        except ValueError:
            raise CLIError("usage error: prefix '{}' is not recognized as an IPv4 or IPv6 address prefix."
                           .format(prefix))
    return version == IPv6Network


def create_express_route_peering(
        cmd, client, resource_group_name, circuit_name, peering_type, peer_asn, vlan_id,
        primary_peer_address_prefix, secondary_peer_address_prefix, shared_key=None,
        advertised_public_prefixes=None, customer_asn=None, routing_registry_name=None,
        route_filter=None, legacy_mode=None, ip_version='IPv4'):
    (ExpressRouteCircuitPeering, ExpressRouteCircuitPeeringConfig, RouteFilter) = \
        cmd.get_models('ExpressRouteCircuitPeering', 'ExpressRouteCircuitPeeringConfig', 'RouteFilter')

    if cmd.supported_api_version(min_api='2018-02-01'):
        ExpressRoutePeeringType = cmd.get_models('ExpressRoutePeeringType')
    else:
        ExpressRoutePeeringType = cmd.get_models('ExpressRouteCircuitPeeringType')

    if ip_version == 'IPv6' and cmd.supported_api_version(min_api='2020-08-01'):
        Ipv6ExpressRouteCircuitPeeringConfig = cmd.get_models('Ipv6ExpressRouteCircuitPeeringConfig')
        if peering_type == ExpressRoutePeeringType.microsoft_peering.value:
            microsoft_config = ExpressRouteCircuitPeeringConfig(advertised_public_prefixes=advertised_public_prefixes,
                                                                customer_asn=customer_asn,
                                                                routing_registry_name=routing_registry_name)
        else:
            microsoft_config = None
        ipv6 = Ipv6ExpressRouteCircuitPeeringConfig(primary_peer_address_prefix=primary_peer_address_prefix,
                                                    secondary_peer_address_prefix=secondary_peer_address_prefix,
                                                    microsoft_peering_config=microsoft_config,
                                                    route_filter=route_filter)
        peering = ExpressRouteCircuitPeering(peering_type=peering_type, ipv6_peering_config=ipv6, peer_asn=peer_asn,
                                             vlan_id=vlan_id)

    else:
        peering = ExpressRouteCircuitPeering(
            peering_type=peering_type, peer_asn=peer_asn, vlan_id=vlan_id,
            primary_peer_address_prefix=primary_peer_address_prefix,
            secondary_peer_address_prefix=secondary_peer_address_prefix,
            shared_key=shared_key)

        if peering_type == ExpressRoutePeeringType.microsoft_peering.value:
            peering.microsoft_peering_config = ExpressRouteCircuitPeeringConfig(
                advertised_public_prefixes=advertised_public_prefixes,
                customer_asn=customer_asn,
                routing_registry_name=routing_registry_name)
        if cmd.supported_api_version(min_api='2016-12-01') and route_filter:
            peering.route_filter = RouteFilter(id=route_filter)
        if cmd.supported_api_version(min_api='2017-10-01') and legacy_mode is not None:
            peering.microsoft_peering_config.legacy_mode = legacy_mode

    return client.begin_create_or_update(resource_group_name, circuit_name, peering_type, peering)


def _create_or_update_ipv6_peering(cmd, config, primary_peer_address_prefix, secondary_peer_address_prefix,
                                   route_filter, advertised_public_prefixes, customer_asn, routing_registry_name):
    if config:
        # update scenario
        with cmd.update_context(config) as c:
            c.set_param('primary_peer_address_prefix', primary_peer_address_prefix)
            c.set_param('secondary_peer_address_prefix', secondary_peer_address_prefix)
            c.set_param('advertised_public_prefixes', advertised_public_prefixes)
            c.set_param('customer_asn', customer_asn)
            c.set_param('routing_registry_name', routing_registry_name)

        if route_filter:
            RouteFilter = cmd.get_models('RouteFilter')
            config.route_filter = RouteFilter(id=route_filter)
    else:
        # create scenario

        IPv6Config, MicrosoftPeeringConfig = cmd.get_models(
            'Ipv6ExpressRouteCircuitPeeringConfig', 'ExpressRouteCircuitPeeringConfig')
        microsoft_config = MicrosoftPeeringConfig(advertised_public_prefixes=advertised_public_prefixes,
                                                  customer_asn=customer_asn,
                                                  routing_registry_name=routing_registry_name)
        config = IPv6Config(primary_peer_address_prefix=primary_peer_address_prefix,
                            secondary_peer_address_prefix=secondary_peer_address_prefix,
                            microsoft_peering_config=microsoft_config,
                            route_filter=route_filter)

    return config


def update_express_route_peering(cmd, instance, peer_asn=None, primary_peer_address_prefix=None,
                                 secondary_peer_address_prefix=None, vlan_id=None, shared_key=None,
                                 advertised_public_prefixes=None, customer_asn=None,
                                 routing_registry_name=None, route_filter=None, ip_version='IPv4',
                                 legacy_mode=None):

    # update settings common to all peering types
    with cmd.update_context(instance) as c:
        c.set_param('peer_asn', peer_asn)
        c.set_param('vlan_id', vlan_id)
        c.set_param('shared_key', shared_key)

    if ip_version == 'IPv6':
        # update is the only way to add IPv6 peering options
        instance.ipv6_peering_config = _create_or_update_ipv6_peering(cmd, instance.ipv6_peering_config,
                                                                      primary_peer_address_prefix,
                                                                      secondary_peer_address_prefix, route_filter,
                                                                      advertised_public_prefixes, customer_asn,
                                                                      routing_registry_name)
    else:
        # IPv4 Microsoft Peering (or non-Microsoft Peering)
        with cmd.update_context(instance) as c:
            c.set_param('primary_peer_address_prefix', primary_peer_address_prefix)
            c.set_param('secondary_peer_address_prefix', secondary_peer_address_prefix)

        if route_filter is not None:
            RouteFilter = cmd.get_models('RouteFilter')
            instance.route_filter = RouteFilter(id=route_filter)

        try:
            with cmd.update_context(instance.microsoft_peering_config) as c:
                c.set_param('advertised_public_prefixes', advertised_public_prefixes)
                c.set_param('customer_asn', customer_asn)
                c.set_param('routing_registry_name', routing_registry_name)
                c.set_param('legacy_mode', legacy_mode)
        except AttributeError:
            raise CLIError('--advertised-public-prefixes, --customer-asn, --routing-registry-name and '
                           '--legacy-mode are only applicable for Microsoft Peering.')
    return instance
# endregion


# region ExpressRoute Connection
# pylint: disable=unused-argument
def create_express_route_connection(cmd, resource_group_name, express_route_gateway_name, connection_name,
                                    peering, circuit_name=None, authorization_key=None, routing_weight=None,
                                    enable_internet_security=None, associated_route_table=None,
                                    propagated_route_tables=None, labels=None):
    ExpressRouteConnection, SubResource, RoutingConfiguration, PropagatedRouteTable\
        = cmd.get_models('ExpressRouteConnection', 'SubResource', 'RoutingConfiguration', 'PropagatedRouteTable')
    client = network_client_factory(cmd.cli_ctx).express_route_connections

    propagated_route_tables = PropagatedRouteTable(
        labels=labels,
        ids=[SubResource(id=propagated_route_table) for propagated_route_table in
             propagated_route_tables] if propagated_route_tables else None
    )
    routing_configuration = RoutingConfiguration(
        associated_route_table=SubResource(id=associated_route_table),
        propagated_route_tables=propagated_route_tables
    )
    connection = ExpressRouteConnection(
        name=connection_name,
        express_route_circuit_peering=SubResource(id=peering) if peering else None,
        authorization_key=authorization_key,
        routing_weight=routing_weight,
        routing_configuration=routing_configuration
    )

    if enable_internet_security and cmd.supported_api_version(min_api='2019-09-01'):
        connection.enable_internet_security = enable_internet_security

    return client.begin_create_or_update(resource_group_name, express_route_gateway_name, connection_name, connection)


# pylint: disable=unused-argument
def update_express_route_connection(instance, cmd, circuit_name=None, peering=None, authorization_key=None,
                                    routing_weight=None, enable_internet_security=None, associated_route_table=None,
                                    propagated_route_tables=None, labels=None):
    SubResource = cmd.get_models('SubResource')
    if peering is not None:
        instance.express_route_connection_id = SubResource(id=peering)
    if authorization_key is not None:
        instance.authorization_key = authorization_key
    if routing_weight is not None:
        instance.routing_weight = routing_weight
    if enable_internet_security is not None and cmd.supported_api_version(min_api='2019-09-01'):
        instance.enable_internet_security = enable_internet_security
    if associated_route_table is not None or propagated_route_tables is not None or labels is not None:
        if instance.routing_configuration is None:
            RoutingConfiguration = cmd.get_models('RoutingConfiguration')
            instance.routing_configuration = RoutingConfiguration()
        if associated_route_table is not None:
            instance.routing_configuration.associated_route_table = SubResource(id=associated_route_table)
        if propagated_route_tables is not None or labels is not None:
            if instance.routing_configuration.propagated_route_tables is None:
                PropagatedRouteTable = cmd.get_models('PropagatedRouteTable')
                instance.routing_configuration.propagated_route_tables = PropagatedRouteTable()
            if propagated_route_tables is not None:
                instance.routing_configuration.propagated_route_tables.ids = [SubResource(id=propagated_route_table) for propagated_route_table in propagated_route_tables]  # pylint: disable=line-too-long
            if labels is not None:
                instance.routing_configuration.propagated_route_tables.labels = labels

    return instance
# endregion


# region ExpressRoute Gateways
def create_express_route_gateway(cmd, resource_group_name, express_route_gateway_name, location=None, tags=None,
                                 min_val=2, max_val=None, virtual_hub=None):
    ExpressRouteGateway, SubResource = cmd.get_models('ExpressRouteGateway', 'SubResource')
    client = network_client_factory(cmd.cli_ctx).express_route_gateways
    gateway = ExpressRouteGateway(
        location=location,
        tags=tags,
        virtual_hub=SubResource(id=virtual_hub) if virtual_hub else None
    )
    if min or max:
        gateway.auto_scale_configuration = {'bounds': {'min': min_val, 'max': max_val}}
    return client.begin_create_or_update(resource_group_name, express_route_gateway_name, gateway)


def update_express_route_gateway(instance, cmd, tags=None, min_val=None, max_val=None):

    def _ensure_autoscale():
        if not instance.auto_scale_configuration:
            ExpressRouteGatewayPropertiesAutoScaleConfiguration, \
                ExpressRouteGatewayPropertiesAutoScaleConfigurationBounds = cmd.get_models(
                    'ExpressRouteGatewayPropertiesAutoScaleConfiguration',
                    'ExpressRouteGatewayPropertiesAutoScaleConfigurationBounds')
            instance.auto_scale_configuration = ExpressRouteGatewayPropertiesAutoScaleConfiguration(
                bounds=ExpressRouteGatewayPropertiesAutoScaleConfigurationBounds(min=min, max=max))

    if tags is not None:
        instance.tags = tags
    if min is not None:
        _ensure_autoscale()
        instance.auto_scale_configuration.bounds.min = min_val
    if max is not None:
        _ensure_autoscale()
        instance.auto_scale_configuration.bounds.max = max_val
    return instance


def list_express_route_gateways(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).express_route_gateways
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()
# endregion


# region ExpressRoute ports
def create_express_route_port(cmd, resource_group_name, express_route_port_name, location=None, tags=None,
                              peering_location=None, bandwidth_in_gbps=None, encapsulation=None):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ExpressRoutePort = cmd.get_models('ExpressRoutePort')
    if bandwidth_in_gbps is not None:
        bandwidth_in_gbps = int(bandwidth_in_gbps)
    port = ExpressRoutePort(
        location=location,
        tags=tags,
        peering_location=peering_location,
        bandwidth_in_gbps=bandwidth_in_gbps,
        encapsulation=encapsulation
    )
    return client.begin_create_or_update(resource_group_name, express_route_port_name, port)


def update_express_route_port(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags, True)
    return instance


def download_generated_loa_as_pdf(cmd,
                                  resource_group_name,
                                  express_route_port_name,
                                  customer_name,
                                  file_path='loa.pdf'):
    import os
    import base64

    dirname, basename = os.path.dirname(file_path), os.path.basename(file_path)

    if basename == '':
        basename = 'loa.pdf'
    elif basename.endswith('.pdf') is False:
        basename = basename + '.pdf'

    file_path = os.path.join(dirname, basename)
    generate_express_route_ports_loa_request =\
        cmd.get_models('GenerateExpressRoutePortsLOARequest')(customer_name=customer_name)
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    response = client.generate_loa(resource_group_name, express_route_port_name,
                                   generate_express_route_ports_loa_request)

    encoded_content = base64.b64decode(response.encoded_content)

    from azure.cli.core.azclierror import FileOperationError
    try:
        with open(file_path, 'wb') as f:
            f.write(encoded_content)
    except OSError as ex:
        raise FileOperationError(ex)

    logger.warning("The generated letter of authorization is saved at %s", file_path)


def list_express_route_ports(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def assign_express_route_port_identity(cmd, resource_group_name, express_route_port_name,
                                       user_assigned_identity, no_wait=False):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ports = client.get(resource_group_name, express_route_port_name)

    ManagedServiceIdentity, ManagedServiceIdentityUserAssignedIdentitiesValue = \
        cmd.get_models('ManagedServiceIdentity', 'Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties')  # pylint: disable=line-too-long

    user_assigned_identity_instance = ManagedServiceIdentityUserAssignedIdentitiesValue()
    user_assigned_identities_instance = dict()
    user_assigned_identities_instance[user_assigned_identity] = user_assigned_identity_instance

    identity_instance = ManagedServiceIdentity(type="UserAssigned",
                                               user_assigned_identities=user_assigned_identities_instance)
    ports.identity = identity_instance

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, express_route_port_name, ports)


def remove_express_route_port_identity(cmd, resource_group_name, express_route_port_name, no_wait=False):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ports = client.get(resource_group_name, express_route_port_name)

    if ports.identity is None:
        logger.warning("The identity of the ExpressRoute Port doesn't exist.")
        return ports

    ports.identity = None

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, express_route_port_name, ports)


def show_express_route_port_identity(cmd, resource_group_name, express_route_port_name):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ports = client.get(resource_group_name, express_route_port_name)
    return ports.identity


def update_express_route_port_link(cmd, instance, parent, express_route_port_name, link_name,
                                   macsec_cak_secret_identifier=None, macsec_ckn_secret_identifier=None,
                                   macsec_sci_state=None, macsec_cipher=None, admin_state=None):
    """
    :param cmd:
    :param instance: an instance of ExpressRoutePort
    :param express_route_port_name:
    :param link_name:
    :param macsec_cak_secret_identifier:
    :param macsec_ckn_secret_identifier:
    :param macsec_cipher:
    :param admin_state:
    :return:
    """
    if any([macsec_cak_secret_identifier, macsec_ckn_secret_identifier, macsec_cipher, macsec_sci_state]):
        instance.mac_sec_config.cak_secret_identifier = macsec_cak_secret_identifier
        instance.mac_sec_config.ckn_secret_identifier = macsec_ckn_secret_identifier

        # TODO https://github.com/Azure/azure-rest-api-specs/issues/7569
        # need to remove this conversion when the issue is fixed.
        if macsec_cipher is not None:
            macsec_ciphers_tmp = {'gcm-aes-128': 'GcmAes128', 'gcm-aes-256': 'GcmAes256'}
            macsec_cipher = macsec_ciphers_tmp.get(macsec_cipher, macsec_cipher)
        instance.mac_sec_config.cipher = macsec_cipher
        instance.mac_sec_config.sci_state = macsec_sci_state

    if admin_state is not None:
        instance.admin_state = admin_state

    return parent
# endregion


# region PrivateEndpoint
def create_private_endpoint(cmd, resource_group_name, private_endpoint_name, subnet,
                            private_connection_resource_id, connection_name, group_ids=None,
                            virtual_network_name=None, tags=None, location=None,
                            request_message=None, manual_request=None, edge_zone=None,
                            ip_configurations=None, application_security_groups=None, custom_interface_name=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    PrivateEndpoint, Subnet, PrivateLinkServiceConnection = cmd.get_models('PrivateEndpoint',
                                                                           'Subnet',
                                                                           'PrivateLinkServiceConnection')
    pls_connection = PrivateLinkServiceConnection(private_link_service_id=private_connection_resource_id,
                                                  group_ids=group_ids,
                                                  request_message=request_message,
                                                  name=connection_name)
    private_endpoint = PrivateEndpoint(
        location=location,
        tags=tags,
        subnet=Subnet(id=subnet)
    )

    if manual_request:
        private_endpoint.manual_private_link_service_connections = [pls_connection]
    else:
        private_endpoint.private_link_service_connections = [pls_connection]

    if edge_zone:
        private_endpoint.extended_location = _edge_zone_model(cmd, edge_zone)

    if cmd.supported_api_version(min_api='2021-05-01'):
        if ip_configurations:
            PrivateEndpointIPConfiguration = cmd.get_models("PrivateEndpointIPConfiguration")
            for prop in ip_configurations:
                ip_config = PrivateEndpointIPConfiguration(**prop)
                try:
                    private_endpoint.ip_configurations.append(ip_config)
                except AttributeError:
                    private_endpoint.ip_configurations = [ip_config]
        if application_security_groups:
            ApplicationSecurityGroup = cmd.get_models("ApplicationSecurityGroup")
            for prop in application_security_groups:
                asg = ApplicationSecurityGroup(**prop)
                try:
                    private_endpoint.application_security_groups.append(asg)
                except AttributeError:
                    private_endpoint.application_security_groups = [asg]
        if custom_interface_name:
            private_endpoint.custom_network_interface_name = custom_interface_name

    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def update_private_endpoint(instance, cmd, tags=None, request_message=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)

    if request_message is not None:
        if instance.private_link_service_connections:
            instance.private_link_service_connections[0].request_message = request_message
        else:
            instance.manual_private_link_service_connections[0].request_message = request_message

    return instance


def list_private_endpoints(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_by_subscription()


def create_private_endpoint_private_dns_zone_group(cmd, resource_group_name, private_endpoint_name,
                                                   private_dns_zone_group_name,
                                                   private_dns_zone_name, private_dns_zone):
    client = network_client_factory(cmd.cli_ctx).private_dns_zone_groups
    PrivateDnsZoneGroup, PrivateDnsZoneConfig = cmd.get_models('PrivateDnsZoneGroup', 'PrivateDnsZoneConfig')
    private_dns_zone_group = PrivateDnsZoneGroup(name=private_dns_zone_group_name,
                                                 private_dns_zone_configs=[PrivateDnsZoneConfig(private_dns_zone_id=private_dns_zone,  # pylint: disable=line-too-long
                                                                                                name=private_dns_zone_name)])  # pylint: disable=line-too-long
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         private_endpoint_name=private_endpoint_name,
                                         private_dns_zone_group_name=private_dns_zone_group_name,
                                         parameters=private_dns_zone_group)


def add_private_endpoint_private_dns_zone(cmd, resource_group_name, private_endpoint_name,
                                          private_dns_zone_group_name,
                                          private_dns_zone_name, private_dns_zone):
    client = network_client_factory(cmd.cli_ctx).private_dns_zone_groups
    PrivateDnsZoneConfig = cmd.get_models('PrivateDnsZoneConfig')
    private_dns_zone_group = client.get(resource_group_name=resource_group_name,
                                        private_endpoint_name=private_endpoint_name,
                                        private_dns_zone_group_name=private_dns_zone_group_name)
    private_dns_zone = PrivateDnsZoneConfig(private_dns_zone_id=private_dns_zone, name=private_dns_zone_name)
    private_dns_zone_group.private_dns_zone_configs.append(private_dns_zone)
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         private_endpoint_name=private_endpoint_name,
                                         private_dns_zone_group_name=private_dns_zone_group_name,
                                         parameters=private_dns_zone_group)


def remove_private_endpoint_private_dns_zone(cmd, resource_group_name, private_endpoint_name,
                                             private_dns_zone_group_name,
                                             private_dns_zone_name):
    client = network_client_factory(cmd.cli_ctx).private_dns_zone_groups
    private_dns_zone_group = client.get(resource_group_name=resource_group_name,
                                        private_endpoint_name=private_endpoint_name,
                                        private_dns_zone_group_name=private_dns_zone_group_name)
    private_dns_zone_configs = [item for item in private_dns_zone_group.private_dns_zone_configs if item.name != private_dns_zone_name]  # pylint: disable=line-too-long
    private_dns_zone_group.private_dns_zone_configs = private_dns_zone_configs
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         private_endpoint_name=private_endpoint_name,
                                         private_dns_zone_group_name=private_dns_zone_group_name,
                                         parameters=private_dns_zone_group)


def add_private_endpoint_ip_config(cmd, resource_group_name, private_endpoint_name,
                                   ip_config_name=None, group_id=None, member_name=None, private_ip_address=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    PrivateEndpointIPConfiguration = cmd.get_models("PrivateEndpointIPConfiguration")
    ip_config = PrivateEndpointIPConfiguration(
        name=ip_config_name,
        group_id=group_id,
        member_name=member_name,
        private_ip_address=private_ip_address
    )
    private_endpoint.ip_configurations.append(ip_config)
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def remove_private_endpoint_ip_config(cmd, resource_group_name, private_endpoint_name, ip_config_name):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    ip_config = None
    for item in private_endpoint.ip_configurations:
        if item.name == ip_config_name:
            ip_config = item
            break
    if ip_config is None:
        logger.warning("IP Configuration %s doesn't exist.", ip_config_name)
        return private_endpoint
    private_endpoint.ip_configurations.remove(ip_config)
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def list_private_endpoint_ip_config(cmd, resource_group_name, private_endpoint_name):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)
    return private_endpoint.ip_configurations


def add_private_endpoint_asg(cmd, resource_group_name, private_endpoint_name, application_security_group_id=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    ApplicationSecurityGroup = cmd.get_models("ApplicationSecurityGroup")
    asg = ApplicationSecurityGroup(id=application_security_group_id)
    try:
        private_endpoint.application_security_groups.append(asg)
    except AttributeError:
        private_endpoint.application_security_groups = [asg]
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def remove_private_endpoint_asg(cmd, resource_group_name, private_endpoint_name, application_security_group_id):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    asg = None
    for item in private_endpoint.application_security_groups:
        if item.id == application_security_group_id:
            asg = item
            break
    if asg is None:
        logger.warning("Application security group %s doesn't exist.", application_security_group_id)
        return private_endpoint
    private_endpoint.application_security_groups.remove(asg)
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def list_private_endpoint_asg(cmd, resource_group_name, private_endpoint_name):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)
    return private_endpoint.application_security_groups
# endregion


# region PrivateLinkService
def create_private_link_service(cmd, resource_group_name, service_name, subnet, frontend_ip_configurations,
                                private_ip_address=None, private_ip_allocation_method=None,
                                private_ip_address_version=None,
                                virtual_network_name=None, public_ip_address=None,
                                location=None, tags=None, load_balancer_name=None,
                                visibility=None, auto_approval=None, fqdns=None,
                                enable_proxy_protocol=None, edge_zone=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    FrontendIPConfiguration, PrivateLinkService, PrivateLinkServiceIpConfiguration, PublicIPAddress, Subnet = \
        cmd.get_models('FrontendIPConfiguration', 'PrivateLinkService', 'PrivateLinkServiceIpConfiguration',
                       'PublicIPAddress', 'Subnet')
    pls_ip_config = PrivateLinkServiceIpConfiguration(
        name='{}_ipconfig_0'.format(service_name),
        private_ip_address=private_ip_address,
        private_ip_allocation_method=private_ip_allocation_method,
        private_ip_address_version=private_ip_address_version,
        subnet=subnet and Subnet(id=subnet),
        public_ip_address=public_ip_address and PublicIPAddress(id=public_ip_address)
    )
    link_service = PrivateLinkService(
        location=location,
        load_balancer_frontend_ip_configurations=frontend_ip_configurations and [
            FrontendIPConfiguration(id=ip_config) for ip_config in frontend_ip_configurations
        ],
        ip_configurations=[pls_ip_config],
        visbility=visibility,
        auto_approval=auto_approval,
        fqdns=fqdns,
        tags=tags,
        enable_proxy_protocol=enable_proxy_protocol
    )
    if edge_zone:
        link_service.extended_location = _edge_zone_model(cmd, edge_zone)
    return client.begin_create_or_update(resource_group_name, service_name, link_service)


def update_private_link_service(instance, cmd, tags=None, frontend_ip_configurations=None, load_balancer_name=None,
                                visibility=None, auto_approval=None, fqdns=None, enable_proxy_protocol=None):
    FrontendIPConfiguration = cmd.get_models('FrontendIPConfiguration')
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
        c.set_param('load_balancer_frontend_ip_configurations', frontend_ip_configurations and [
            FrontendIPConfiguration(id=ip_config) for ip_config in frontend_ip_configurations
        ])
        c.set_param('visibility', visibility)
        c.set_param('auto_approval', auto_approval)
        c.set_param('fqdns', fqdns)
        c.set_param('enable_proxy_protocol', enable_proxy_protocol)
    return instance


def list_private_link_services(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_by_subscription()


def update_private_endpoint_connection(cmd, resource_group_name, service_name, pe_connection_name,
                                       connection_status, description=None, action_required=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    PrivateEndpointConnection, PrivateLinkServiceConnectionState = cmd.get_models('PrivateEndpointConnection',
                                                                                  'PrivateLinkServiceConnectionState')
    connection_state = PrivateLinkServiceConnectionState(
        status=connection_status,
        description=description,
        actions_required=action_required
    )
    pe_connection = PrivateEndpointConnection(
        private_link_service_connection_state=connection_state
    )
    return client.update_private_endpoint_connection(resource_group_name, service_name, pe_connection_name, pe_connection)  # pylint: disable=line-too-long


def add_private_link_services_ipconfig(cmd, resource_group_name, service_name,
                                       private_ip_address=None, private_ip_allocation_method=None,
                                       private_ip_address_version=None,
                                       subnet=None, virtual_network_name=None, public_ip_address=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    PrivateLinkServiceIpConfiguration, PublicIPAddress, Subnet = cmd.get_models('PrivateLinkServiceIpConfiguration',
                                                                                'PublicIPAddress',
                                                                                'Subnet')
    link_service = client.get(resource_group_name, service_name)
    if link_service is None:
        raise CLIError("Private link service should be existed. Please create it first.")
    ip_name_index = len(link_service.ip_configurations)
    ip_config = PrivateLinkServiceIpConfiguration(
        name='{0}_ipconfig_{1}'.format(service_name, ip_name_index),
        private_ip_address=private_ip_address,
        private_ip_allocation_method=private_ip_allocation_method,
        private_ip_address_version=private_ip_address_version,
        subnet=subnet and Subnet(id=subnet),
        public_ip_address=public_ip_address and PublicIPAddress(id=public_ip_address)
    )
    link_service.ip_configurations.append(ip_config)
    return client.begin_create_or_update(resource_group_name, service_name, link_service)


def remove_private_link_services_ipconfig(cmd, resource_group_name, service_name, ip_config_name):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    link_service = client.get(resource_group_name, service_name)
    if link_service is None:
        raise CLIError("Private link service should be existed. Please create it first.")
    ip_config = None
    for item in link_service.ip_configurations:
        if item.name == ip_config_name:
            ip_config = item
            break
    if ip_config is None:  # pylint: disable=no-else-return
        logger.warning("%s ip configuration doesn't exist", ip_config_name)
        return link_service
    else:
        link_service.ip_configurations.remove(ip_config)
        return client.begin_create_or_update(resource_group_name, service_name, link_service)
# endregion


def _edge_zone_model(cmd, edge_zone):
    ExtendedLocation, ExtendedLocationTypes = cmd.get_models('ExtendedLocation', 'ExtendedLocationTypes')
    return ExtendedLocation(name=edge_zone, type=ExtendedLocationTypes.EDGE_ZONE)


# region LoadBalancers
def create_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                         backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                         private_ip_address=None, public_ip_address=None,
                         public_ip_address_allocation=None,
                         public_ip_dns_name=None, subnet=None, subnet_address_prefix='10.0.0.0/24',
                         virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                         public_ip_address_type=None, subnet_type=None, validate=False,
                         no_wait=False, sku=None, frontend_ip_zone=None, public_ip_zone=None,
                         private_ip_address_version=None, edge_zone=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network.azure_stack._template_builder import (
        build_load_balancer_resource, build_public_ip_resource, build_vnet_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

    if public_ip_address is None:
        logger.warning(
            "Please note that the default public IP used for creation will be changed from Basic to Standard "
            "in the future."
        )

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = 'Static' if (sku and sku.lower() == 'standard') else 'Dynamic'

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None
    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if edge_zone and cmd.supported_api_version(min_api='2020-08-01'):
        edge_zone_type = 'EdgeZone'
    else:
        edge_zone_type = None

    if subnet_type == 'new':
        lb_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(virtual_network_name))
        vnet = build_vnet_resource(
            cmd, virtual_network_name, location, tags, vnet_address_prefix, subnet,
            subnet_address_prefix)
        master_template.add_resource(vnet)
        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(
            network_id_template, virtual_network_name, subnet)

    if public_ip_address_type == 'new':
        lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              public_ip_dns_name,
                                                              sku, public_ip_zone, None, edge_zone, edge_zone_type))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, subnet_id, private_ip_address, private_ip_allocation, sku,
        frontend_ip_zone, private_ip_address_version, None, edge_zone, edge_zone_type)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def list_load_balancer_nic(cmd, resource_group_name, load_balancer_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_network_interfaces
    return client.list(resource_group_name, load_balancer_name)


def list_load_balancer_mapping(cmd, resource_group_name, load_balancer_name, backend_pool_name, request):
    client = network_client_factory(cmd.cli_ctx).load_balancers
    return client.begin_list_inbound_nat_rule_port_mappings(
        resource_group_name,
        load_balancer_name,
        backend_pool_name,
        request
    )


def create_lb_inbound_nat_rule(
        cmd, resource_group_name, load_balancer_name, item_name, protocol, backend_port, frontend_port=None,
        frontend_ip_name=None, floating_ip=None, idle_timeout=None, enable_tcp_reset=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_pool_name=None):
    InboundNatRule, SubResource = cmd.get_models('InboundNatRule', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    frontend_ip = get_property(lb.frontend_ip_configurations, frontend_ip_name)  # pylint: disable=no-member
    new_rule = InboundNatRule(
        name=item_name, protocol=protocol,
        frontend_port=frontend_port, backend_port=backend_port,
        frontend_ip_configuration=frontend_ip,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout,
        enable_tcp_reset=enable_tcp_reset)
    if frontend_port_range_end and cmd.supported_api_version('2021-03-01'):
        new_rule.frontend_port_range_end = frontend_port_range_end
    if frontend_port_range_start and cmd.supported_api_version('2021-03-01'):
        new_rule.frontend_port_range_start = frontend_port_range_start
    if backend_pool_name and cmd.supported_api_version('2021-03-01'):
        backend_pool_id = get_property(lb.backend_address_pools, backend_pool_name).id
        new_rule.backend_address_pool = SubResource(id=backend_pool_id)
    upsert_to_collection(lb, 'inbound_nat_rules', new_rule, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().inbound_nat_rules, item_name)


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def lb_get(client, resource_group_name, load_balancer_name):
    lb = client.get(resource_group_name, load_balancer_name)
    return lb_get_operation(lb)


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def lb_get_operation(lb):
    for item in lb.frontend_ip_configurations:
        if item.zones is not None and len(item.zones) >= 3 and item.subnet is None:
            item.zones = None

    return lb


def set_lb_inbound_nat_rule(
        cmd, instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, floating_ip=None, idle_timeout=None, enable_tcp_reset=None,
        frontend_port_range_start=None, frontend_port_range_end=None):
    if frontend_ip_name:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if enable_tcp_reset is not None:
        instance.enable_tcp_reset = enable_tcp_reset
    if frontend_port_range_start is not None and cmd.supported_api_version('2021-03-01'):
        instance.frontend_port_range_start = frontend_port_range_start
    if frontend_port_range_end is not None and cmd.supported_api_version('2021-03-01'):
        instance.frontend_port_range_end = frontend_port_range_end

    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port', frontend_port)
        c.set_param('backend_port', backend_port)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('enable_floating_ip', floating_ip)

    return parent


def create_lb_inbound_nat_pool(
        cmd, resource_group_name, load_balancer_name, item_name, protocol, frontend_port_range_start,
        frontend_port_range_end, backend_port, frontend_ip_name=None, enable_tcp_reset=None,
        floating_ip=None, idle_timeout=None):
    InboundNatPool = cmd.get_models('InboundNatPool')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    frontend_ip = get_property(lb.frontend_ip_configurations, frontend_ip_name) \
        if frontend_ip_name else None
    new_pool = InboundNatPool(
        name=item_name,
        protocol=protocol,
        frontend_ip_configuration=frontend_ip,
        frontend_port_range_start=frontend_port_range_start,
        frontend_port_range_end=frontend_port_range_end,
        backend_port=backend_port,
        enable_tcp_reset=enable_tcp_reset,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout)
    upsert_to_collection(lb, 'inbound_nat_pools', new_pool, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().inbound_nat_pools, item_name)


def set_lb_inbound_nat_pool(
        cmd, instance, parent, item_name, protocol=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_port=None,
        frontend_ip_name=None, enable_tcp_reset=None, floating_ip=None, idle_timeout=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port_range_start', frontend_port_range_start)
        c.set_param('frontend_port_range_end', frontend_port_range_end)
        c.set_param('backend_port', backend_port)
        c.set_param('enable_floating_ip', floating_ip)
        c.set_param('idle_timeout_in_minutes', idle_timeout)

    if enable_tcp_reset is not None:
        instance.enable_tcp_reset = enable_tcp_reset

    if frontend_ip_name == '':
        instance.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    return parent


def create_lb_frontend_ip_configuration(
        cmd, resource_group_name, load_balancer_name, item_name, public_ip_address=None,
        public_ip_prefix=None, subnet=None, virtual_network_name=None, private_ip_address=None,
        private_ip_address_version=None, private_ip_address_allocation=None, zone=None):
    FrontendIPConfiguration, SubResource, Subnet = cmd.get_models(
        'FrontendIPConfiguration', 'SubResource', 'Subnet')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)

    if public_ip_address is None:
        logger.warning(
            "Please note that the default public IP used for LB frontend will be changed from Basic to Standard "
            "in the future."
        )
    if private_ip_address_allocation is None:
        private_ip_address_allocation = 'static' if private_ip_address else 'dynamic'

    new_config = FrontendIPConfiguration(
        name=item_name,
        private_ip_address=private_ip_address,
        private_ip_address_version=private_ip_address_version,
        private_ip_allocation_method=private_ip_address_allocation,
        public_ip_address=SubResource(id=public_ip_address) if public_ip_address else None,
        public_ip_prefix=SubResource(id=public_ip_prefix) if public_ip_prefix else None,
        subnet=Subnet(id=subnet) if subnet else None)

    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        new_config.zones = zone

    upsert_to_collection(lb, 'frontend_ip_configurations', new_config, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().frontend_ip_configurations, item_name)


def update_lb_frontend_ip_configuration_setter(cmd, resource_group_name, load_balancer_name, parameters, gateway_lb):
    aux_subscriptions = []
    if is_valid_resource_id(gateway_lb):
        aux_subscriptions.append(parse_resource_id(gateway_lb)['subscription'])
    client = network_client_factory(cmd.cli_ctx, aux_subscriptions=aux_subscriptions).load_balancers
    return client.begin_create_or_update(resource_group_name, load_balancer_name, parameters)


def set_lb_frontend_ip_configuration(
        cmd, instance, parent, item_name, private_ip_address=None,
        private_ip_address_allocation=None, public_ip_address=None,
        subnet=None, virtual_network_name=None, public_ip_prefix=None, gateway_lb=None):
    PublicIPAddress, Subnet, SubResource = cmd.get_models('PublicIPAddress', 'Subnet', 'SubResource')
    if not private_ip_address:
        instance.private_ip_allocation_method = 'dynamic'
        instance.private_ip_address = None
    elif private_ip_address is not None:
        instance.private_ip_allocation_method = 'static'
        instance.private_ip_address = private_ip_address

    # Doesn't support update operation for now
    # if cmd.supported_api_version(min_api='2019-04-01'):
    #    instance.private_ip_address_version = private_ip_address_version

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(id=subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    if public_ip_prefix:
        instance.public_ip_prefix = SubResource(id=public_ip_prefix)
    if gateway_lb is not None:
        instance.gateway_load_balancer = None if gateway_lb == '' else SubResource(id=gateway_lb)

    return parent


def _process_vnet_name_and_id(vnet, cmd, resource_group_name):
    if vnet and not is_valid_resource_id(vnet):
        vnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet)
    return vnet


def _process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name):
    if subnet and not is_valid_resource_id(subnet):
        vnet = _process_vnet_name_and_id(vnet, cmd, resource_group_name)
        if vnet is None:
            raise UnrecognizedArgumentError('vnet should be provided when input subnet name instead of subnet id')

        subnet = vnet + f'/subnets/{subnet}'
    return subnet


# pylint: disable=too-many-branches
def create_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name,
                                   vnet=None, backend_addresses=None, backend_addresses_config_file=None,
                                   admin_state=None, drain_period=None):
    if backend_addresses and backend_addresses_config_file:
        raise CLIError('usage error: Only one of --backend-address and --backend-addresses-config-file can be provided at the same time.')  # pylint: disable=line-too-long
    if backend_addresses_config_file:
        if not isinstance(backend_addresses_config_file, list):
            raise CLIError('Config file must be a list. Please see example as a reference.')
        for addr in backend_addresses_config_file:
            if not isinstance(addr, dict):
                raise CLIError('Each address in config file must be a dictionary. Please see example as a reference.')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    (BackendAddressPool,
     LoadBalancerBackendAddress,
     Subnet,
     VirtualNetwork) = cmd.get_models('BackendAddressPool',
                                      'LoadBalancerBackendAddress',
                                      'Subnet',
                                      'VirtualNetwork')
    # Before 2020-03-01, service doesn't support the other rest method.
    # We have to use old one to keep backward compatibility.
    # Same for basic sku. service refuses that basic sku lb call the other rest method.
    if cmd.supported_api_version(max_api='2020-03-01') or lb.sku.name.lower() == 'basic':
        new_pool = BackendAddressPool(name=backend_address_pool_name)
        upsert_to_collection(lb, 'backend_address_pools', new_pool, 'name')
        poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
        return get_property(poller.result().backend_address_pools, backend_address_pool_name)

    addresses_pool = []
    if backend_addresses:
        addresses_pool.extend(backend_addresses)
    if backend_addresses_config_file:
        addresses_pool.extend(backend_addresses_config_file)
    for addr in addresses_pool:
        if 'virtual_network' not in addr and vnet:
            addr['virtual_network'] = vnet

    # pylint: disable=line-too-long
    if cmd.supported_api_version(min_api='2020-11-01'):  # pylint: disable=too-many-nested-blocks
        try:
            if addresses_pool:
                new_addresses = []
                for addr in addresses_pool:
                    # vnet      | subnet        |  status
                    # name/id   | name/id/null  |    ok
                    # null      | id            |    ok
                    if 'virtual_network' in addr:
                        if admin_state is not None:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                                 subnet=Subnet(id=_process_subnet_name_and_id(addr['subnet'], addr['virtual_network'], cmd, resource_group_name)) if 'subnet' in addr else None,
                                                                 ip_address=addr['ip_address'],
                                                                 admin_state=admin_state)
                        else:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                                 subnet=Subnet(id=_process_subnet_name_and_id(addr['subnet'], addr['virtual_network'], cmd, resource_group_name)) if 'subnet' in addr else None,
                                                                 ip_address=addr['ip_address'])
                    elif 'subnet' in addr and is_valid_resource_id(addr['subnet']):
                        if admin_state is not None:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 subnet=Subnet(id=addr['subnet']),
                                                                 ip_address=addr['ip_address'],
                                                                 admin_state=admin_state)
                        else:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 subnet=Subnet(id=addr['subnet']),
                                                                 ip_address=addr['ip_address'])
                    else:
                        raise KeyError

                    new_addresses.append(address)
            else:
                new_addresses = None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, ip-address, (vnet name and subnet '
                                            'name | subnet id) information.')
    else:
        try:
            new_addresses = [LoadBalancerBackendAddress(name=addr['name'],
                                                        virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                        ip_address=addr['ip_address']) for addr in addresses_pool] if addresses_pool else None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, vnet and ip-address information.')

    if drain_period is not None:
        new_pool = BackendAddressPool(name=backend_address_pool_name,
                                      load_balancer_backend_addresses=new_addresses,
                                      drain_period_in_seconds=drain_period)
    else:
        new_pool = BackendAddressPool(name=backend_address_pool_name,
                                      load_balancer_backend_addresses=new_addresses)

    # when sku is 'gateway', 'tunnelInterfaces' can't be None. Otherwise, service will respond error
    if cmd.supported_api_version(min_api='2021-02-01') and lb.sku.name.lower() == 'gateway':
        GatewayLoadBalancerTunnelInterface = cmd.get_models('GatewayLoadBalancerTunnelInterface')
        new_pool.tunnel_interfaces = [
            GatewayLoadBalancerTunnelInterface(type='Internal', protocol='VXLAN', identifier=900)]
    return ncf.load_balancer_backend_address_pools.begin_create_or_update(resource_group_name,
                                                                          load_balancer_name,
                                                                          backend_address_pool_name,
                                                                          new_pool)


def set_lb_backend_address_pool(cmd, instance, resource_group_name, vnet=None, backend_addresses=None,
                                backend_addresses_config_file=None, admin_state=None, drain_period=None):

    if backend_addresses and backend_addresses_config_file:
        raise CLIError('usage error: Only one of --backend-address and --backend-addresses-config-file can be provided at the same time.')  # pylint: disable=line-too-long
    if backend_addresses_config_file:
        if not isinstance(backend_addresses_config_file, list):
            raise CLIError('Config file must be a list. Please see example as a reference.')
        for addr in backend_addresses_config_file:
            if not isinstance(addr, dict):
                raise CLIError('Each address in config file must be a dictionary. Please see example as a reference.')

    (LoadBalancerBackendAddress,
     Subnet,
     VirtualNetwork) = cmd.get_models('LoadBalancerBackendAddress',
                                      'Subnet',
                                      'VirtualNetwork')

    addresses_pool = []
    if backend_addresses:
        addresses_pool.extend(backend_addresses)
    if backend_addresses_config_file:
        addresses_pool.extend(backend_addresses_config_file)
    for addr in addresses_pool:
        if 'virtual_network' not in addr and vnet:
            addr['virtual_network'] = vnet

    # pylint: disable=line-too-long
    if cmd.supported_api_version(min_api='2020-11-01'):  # pylint: disable=too-many-nested-blocks
        try:
            if addresses_pool:
                new_addresses = []
                for addr in addresses_pool:
                    # vnet      | subnet        |  status
                    # name/id   | name/id/null  |    ok
                    # null      | id            |    ok
                    if 'virtual_network' in addr:
                        if admin_state is not None:
                            address = LoadBalancerBackendAddress(name=addr['name'], virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                                 subnet=Subnet(id=_process_subnet_name_and_id(addr['subnet'], addr['virtual_network'], cmd, resource_group_name)) if 'subnet' in addr else None,
                                                                 ip_address=addr['ip_address'],
                                                                 admin_state=admin_state)
                        else:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                                 subnet=Subnet(id=_process_subnet_name_and_id(addr['subnet'], addr['virtual_network'], cmd, resource_group_name)) if 'subnet' in addr else None,
                                                                 ip_address=addr['ip_address'])
                    elif 'subnet' in addr and is_valid_resource_id(addr['subnet']):
                        if admin_state is not None:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 subnet=Subnet(id=addr['subnet']),
                                                                 ip_address=addr['ip_address'],
                                                                 admin_state=admin_state)
                        else:
                            address = LoadBalancerBackendAddress(name=addr['name'],
                                                                 subnet=Subnet(id=addr['subnet']),
                                                                 ip_address=addr['ip_address'])
                    else:
                        raise KeyError

                    new_addresses.append(address)
            else:
                new_addresses = None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, ip-address, (vnet name and subnet '
                                            'name | subnet id) information.')
    else:
        try:
            new_addresses = [LoadBalancerBackendAddress(name=addr['name'],
                                                        virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                        ip_address=addr['ip_address']) for addr in addresses_pool] if addresses_pool else None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, vnet and ip-address information.')

    if drain_period is not None:
        instance.drain_period_in_seconds = drain_period
    if new_addresses:
        instance.load_balancer_backend_addresses = new_addresses

    return instance


def delete_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name):
    from azure.cli.core.commands import LongRunningOperation
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)

    def delete_basic_lb_backend_address_pool():
        new_be_pools = [pool for pool in lb.backend_address_pools
                        if pool.name.lower() != backend_address_pool_name.lower()]
        lb.backend_address_pools = new_be_pools
        poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
        result = LongRunningOperation(cmd.cli_ctx)(poller).backend_address_pools
        if next((x for x in result if x.name.lower() == backend_address_pool_name.lower()), None):
            raise CLIError("Failed to delete '{}' on '{}'".format(backend_address_pool_name, load_balancer_name))

    if lb.sku.name.lower() == 'basic':
        delete_basic_lb_backend_address_pool()
        return None

    return ncf.load_balancer_backend_address_pools.begin_delete(resource_group_name,
                                                                load_balancer_name,
                                                                backend_address_pool_name)


# region cross-region lb
def create_cross_region_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                                      backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                                      public_ip_address=None, public_ip_address_allocation=None,
                                      public_ip_dns_name=None, public_ip_address_type=None, validate=False,
                                      no_wait=False, frontend_ip_zone=None, public_ip_zone=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network.azure_stack._template_builder import (
        build_load_balancer_resource, build_public_ip_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    IPAllocationMethod = cmd.get_models('IPAllocationMethod')

    sku = 'standard'
    tier = 'Global'

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = IPAllocationMethod.static.value if (sku and sku.lower() == 'standard') \
            else IPAllocationMethod.dynamic.value

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if public_ip_address_type == 'new':
        lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              public_ip_dns_name,
                                                              sku, public_ip_zone, tier))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, None, None, None, sku, frontend_ip_zone, None, tier)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def create_cross_region_lb_frontend_ip_configuration(
        cmd, resource_group_name, load_balancer_name, item_name, public_ip_address=None,
        public_ip_prefix=None, zone=None):
    FrontendIPConfiguration, SubResource = cmd.get_models(
        'FrontendIPConfiguration', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)

    new_config = FrontendIPConfiguration(
        name=item_name,
        public_ip_address=SubResource(id=public_ip_address) if public_ip_address else None,
        public_ip_prefix=SubResource(id=public_ip_prefix) if public_ip_prefix else None)

    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        new_config.zones = zone

    upsert_to_collection(lb, 'frontend_ip_configurations', new_config, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().frontend_ip_configurations, item_name)


def set_cross_region_lb_frontend_ip_configuration(
        cmd, instance, parent, item_name, public_ip_address=None, public_ip_prefix=None):
    PublicIPAddress, SubResource = cmd.get_models('PublicIPAddress', 'SubResource')

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    if public_ip_prefix:
        instance.public_ip_prefix = SubResource(id=public_ip_prefix)

    return parent


def create_cross_region_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name,
                                                backend_addresses=None, backend_addresses_config_file=None):
    if backend_addresses and backend_addresses_config_file:
        raise CLIError('usage error: Only one of --backend-address and --backend-addresses-config-file can be provided at the same time.')  # pylint: disable=line-too-long
    if backend_addresses_config_file:
        if not isinstance(backend_addresses_config_file, list):
            raise CLIError('Config file must be a list. Please see example as a reference.')
        for addr in backend_addresses_config_file:
            if not isinstance(addr, dict):
                raise CLIError('Each address in config file must be a dictionary. Please see example as a reference.')
    ncf = network_client_factory(cmd.cli_ctx)
    (BackendAddressPool,
     LoadBalancerBackendAddress,
     FrontendIPConfiguration) = cmd.get_models('BackendAddressPool',
                                               'LoadBalancerBackendAddress',
                                               'FrontendIPConfiguration')

    addresses_pool = []
    if backend_addresses:
        addresses_pool.extend(backend_addresses)
    if backend_addresses_config_file:
        addresses_pool.extend(backend_addresses_config_file)

    # pylint: disable=line-too-long
    try:
        new_addresses = [LoadBalancerBackendAddress(name=addr['name'],
                                                    load_balancer_frontend_ip_configuration=FrontendIPConfiguration(id=addr['frontend_ip_address'])) for addr in addresses_pool] if addresses_pool else None
    except KeyError:
        raise CLIError('Each backend address must have name and frontend_ip_configuration information.')
    new_pool = BackendAddressPool(name=backend_address_pool_name,
                                  load_balancer_backend_addresses=new_addresses)
    return ncf.load_balancer_backend_address_pools.begin_create_or_update(resource_group_name,
                                                                          load_balancer_name,
                                                                          backend_address_pool_name,
                                                                          new_pool)


def delete_cross_region_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name):  # pylint: disable=line-too-long
    ncf = network_client_factory(cmd.cli_ctx)

    return ncf.load_balancer_backend_address_pools.begin_delete(resource_group_name,
                                                                load_balancer_name,
                                                                backend_address_pool_name)


def add_cross_region_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name,
                                                     backend_address_pool_name, address_name, frontend_ip_address):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    # pylint: disable=line-too-long
    (LoadBalancerBackendAddress, FrontendIPConfiguration) = cmd.get_models('LoadBalancerBackendAddress', 'FrontendIPConfiguration')
    new_address = LoadBalancerBackendAddress(name=address_name,
                                             load_balancer_frontend_ip_configuration=FrontendIPConfiguration(id=frontend_ip_address) if frontend_ip_address else None)
    if address_pool.load_balancer_backend_addresses is None:
        address_pool.load_balancer_backend_addresses = []
    address_pool.load_balancer_backend_addresses.append(new_address)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def create_cross_region_lb_rule(
        cmd, resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name=None,
        backend_address_pool_name=None, probe_name=None, load_distribution='default',
        floating_ip=None, idle_timeout=None, enable_tcp_reset=None, backend_pools_name=None):
    LoadBalancingRule = cmd.get_models('LoadBalancingRule')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = cached_get(cmd, ncf.load_balancers.get, resource_group_name, load_balancer_name)
    lb = lb_get_operation(lb)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    if not backend_address_pool_name:
        backend_address_pool_name = _get_default_name(lb, 'backend_address_pools', '--backend-pool-name')
    new_rule = LoadBalancingRule(
        name=item_name,
        protocol=protocol,
        frontend_port=frontend_port,
        backend_port=backend_port,
        frontend_ip_configuration=get_property(lb.frontend_ip_configurations,
                                               frontend_ip_name),
        backend_address_pool=get_property(lb.backend_address_pools,
                                          backend_address_pool_name),
        probe=get_property(lb.probes, probe_name) if probe_name else None,
        load_distribution=load_distribution,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout,
        enable_tcp_reset=enable_tcp_reset)
    if backend_pools_name:
        new_rule.backend_address_pools = [get_property(lb.backend_address_pools, i) for i in backend_pools_name]
    upsert_to_collection(lb, 'load_balancing_rules', new_rule, 'name')
    poller = cached_put(cmd, ncf.load_balancers.begin_create_or_update, lb, resource_group_name, load_balancer_name)
    return get_property(poller.result().load_balancing_rules, item_name)


def set_cross_region_lb_rule(
        cmd, instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution=None, floating_ip=None, idle_timeout=None, enable_tcp_reset=None, backend_pools_name=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port', frontend_port)
        c.set_param('backend_port', backend_port)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('load_distribution', load_distribution)
        c.set_param('enable_tcp_reset', enable_tcp_reset)
        c.set_param('enable_floating_ip', floating_ip)

    if frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if backend_address_pool_name is not None:
        instance.backend_address_pool = \
            get_property(parent.backend_address_pools, backend_address_pool_name)
        # To keep compatible when bump version from '2020-11-01' to '2021-02-01'
        # https://github.com/Azure/azure-rest-api-specs/issues/14430
        if cmd.supported_api_version(min_api='2021-02-01') and not backend_pools_name:
            instance.backend_address_pools = [instance.backend_address_pool]
    if backend_pools_name is not None:
        instance.backend_address_pools = [get_property(parent.backend_address_pools, i) for i in backend_pools_name]

    if probe_name == '':
        instance.probe = None
    elif probe_name is not None:
        instance.probe = get_property(parent.probes, probe_name)

    return parent
# endregion


# pylint: disable=line-too-long
def add_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name, backend_address_pool_name,
                                        address_name, ip_address, vnet=None, subnet=None, admin_state=None):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    (LoadBalancerBackendAddress,
     Subnet,
     VirtualNetwork) = cmd.get_models('LoadBalancerBackendAddress',
                                      'Subnet',
                                      'VirtualNetwork')
    if cmd.supported_api_version(min_api='2020-11-01'):
        if vnet:
            if admin_state is not None:
                new_address = LoadBalancerBackendAddress(name=address_name,
                                                         subnet=Subnet(id=_process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name)) if subnet else None,
                                                         virtual_network=VirtualNetwork(id=vnet),
                                                         ip_address=ip_address if ip_address else None,
                                                         admin_state=admin_state)
            else:
                new_address = LoadBalancerBackendAddress(name=address_name,
                                                         subnet=Subnet(id=_process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name)) if subnet else None,
                                                         virtual_network=VirtualNetwork(id=vnet),
                                                         ip_address=ip_address if ip_address else None)
        elif is_valid_resource_id(subnet):
            if admin_state is not None:
                new_address = LoadBalancerBackendAddress(name=address_name,
                                                         subnet=Subnet(id=subnet),
                                                         ip_address=ip_address if ip_address else None,
                                                         admin_state=admin_state)
            else:
                new_address = LoadBalancerBackendAddress(name=address_name,
                                                         subnet=Subnet(id=subnet),
                                                         ip_address=ip_address if ip_address else None)
        else:
            raise UnrecognizedArgumentError('Each backend address must have name, ip-address, (vnet name and subnet name | subnet id) information.')

    else:
        new_address = LoadBalancerBackendAddress(name=address_name,
                                                 virtual_network=VirtualNetwork(id=vnet) if vnet else None,
                                                 ip_address=ip_address if ip_address else None)
    if address_pool.load_balancer_backend_addresses is None:
        address_pool.load_balancer_backend_addresses = []
    address_pool.load_balancer_backend_addresses.append(new_address)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def remove_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name,
                                           backend_address_pool_name, address_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    if address_pool.load_balancer_backend_addresses is None:
        address_pool.load_balancer_backend_addresses = []
    lb_addresses = [addr for addr in address_pool.load_balancer_backend_addresses if addr.name != address_name]
    address_pool.load_balancer_backend_addresses = lb_addresses
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def list_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name,
                                         backend_address_pool_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    return address_pool.load_balancer_backend_addresses


def create_lb_outbound_rule(cmd, resource_group_name, load_balancer_name, item_name,
                            backend_address_pool, frontend_ip_configurations, protocol,
                            outbound_ports=None, enable_tcp_reset=None, idle_timeout=None):
    OutboundRule, SubResource = cmd.get_models('OutboundRule', 'SubResource')
    client = network_client_factory(cmd.cli_ctx).load_balancers
    lb = lb_get(client, resource_group_name, load_balancer_name)
    rule = OutboundRule(
        protocol=protocol, enable_tcp_reset=enable_tcp_reset, idle_timeout_in_minutes=idle_timeout,
        backend_address_pool=SubResource(id=backend_address_pool),
        frontend_ip_configurations=[SubResource(id=x) for x in frontend_ip_configurations]
        if frontend_ip_configurations else None,
        allocated_outbound_ports=outbound_ports, name=item_name)
    upsert_to_collection(lb, 'outbound_rules', rule, 'name')
    poller = client.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().outbound_rules, item_name)


def set_lb_outbound_rule(instance, cmd, parent, item_name, protocol=None, outbound_ports=None,
                         idle_timeout=None, frontend_ip_configurations=None, enable_tcp_reset=None,
                         backend_address_pool=None):
    SubResource = cmd.get_models('SubResource')
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('allocated_outbound_ports', outbound_ports)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('enable_tcp_reset', enable_tcp_reset)
        c.set_param('backend_address_pool', SubResource(id=backend_address_pool)
                    if backend_address_pool else None)
        c.set_param('frontend_ip_configurations',
                    [SubResource(id=x) for x in frontend_ip_configurations] if frontend_ip_configurations else None)
    return parent


def create_lb_probe(cmd, resource_group_name, load_balancer_name, item_name, protocol, port,
                    path=None, interval=None, threshold=None):
    Probe = cmd.get_models('Probe')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    new_probe = Probe(
        protocol=protocol, port=port, interval_in_seconds=interval, number_of_probes=threshold,
        request_path=path, name=item_name)
    upsert_to_collection(lb, 'probes', new_probe, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().probes, item_name)


def set_lb_probe(cmd, instance, parent, item_name, protocol=None, port=None,
                 path=None, interval=None, threshold=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('port', port)
        c.set_param('request_path', path)
        c.set_param('interval_in_seconds', interval)
        c.set_param('number_of_probes', threshold)
    return parent


def create_lb_rule(
        cmd, resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name=None,
        backend_address_pool_name=None, probe_name=None, load_distribution='default',
        floating_ip=None, idle_timeout=None, enable_tcp_reset=None, disable_outbound_snat=None, backend_pools_name=None):
    LoadBalancingRule = cmd.get_models('LoadBalancingRule')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = cached_get(cmd, ncf.load_balancers.get, resource_group_name, load_balancer_name)
    lb = lb_get_operation(lb)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    # avoid break when backend_address_pool_name is None and backend_pools_name is not None
    if not backend_address_pool_name and backend_pools_name:
        backend_address_pool_name = backend_pools_name[0]
    if not backend_address_pool_name:
        backend_address_pool_name = _get_default_name(lb, 'backend_address_pools', '--backend-pool-name')
    new_rule = LoadBalancingRule(
        name=item_name,
        protocol=protocol,
        frontend_port=frontend_port,
        backend_port=backend_port,
        frontend_ip_configuration=get_property(lb.frontend_ip_configurations,
                                               frontend_ip_name),
        backend_address_pool=get_property(lb.backend_address_pools,
                                          backend_address_pool_name),
        probe=get_property(lb.probes, probe_name) if probe_name else None,
        load_distribution=load_distribution,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout,
        enable_tcp_reset=enable_tcp_reset,
        disable_outbound_snat=disable_outbound_snat)

    if backend_pools_name:
        new_rule.backend_address_pools = [get_property(lb.backend_address_pools, name) for name in backend_pools_name]
        # Otherwiase service will response error : (LoadBalancingRuleBackendAdressPoolAndBackendAddressPoolsCannotBeSetAtTheSameTimeWithDifferentValue) BackendAddressPool and BackendAddressPools[] in LoadBalancingRule rule2 cannot be set at the same time with different value.
        new_rule.backend_address_pool = None

    upsert_to_collection(lb, 'load_balancing_rules', new_rule, 'name')
    poller = cached_put(cmd, ncf.load_balancers.begin_create_or_update, lb, resource_group_name, load_balancer_name)
    return get_property(poller.result().load_balancing_rules, item_name)


def set_lb_rule(
        cmd, instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution='default', floating_ip=None, idle_timeout=None, enable_tcp_reset=None,
        disable_outbound_snat=None, backend_pools_name=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port', frontend_port)
        c.set_param('backend_port', backend_port)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('load_distribution', load_distribution)
        c.set_param('disable_outbound_snat', disable_outbound_snat)
        c.set_param('enable_tcp_reset', enable_tcp_reset)
        c.set_param('enable_floating_ip', floating_ip)

    if frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if backend_address_pool_name is not None:
        instance.backend_address_pool = \
            get_property(parent.backend_address_pools, backend_address_pool_name)
        # To keep compatible when bump version from '2020-11-01' to '2021-02-01'
        # https://github.com/Azure/azure-rest-api-specs/issues/14430
        if cmd.supported_api_version(min_api='2021-02-01') and not backend_pools_name:
            instance.backend_address_pools = [instance.backend_address_pool]
    if backend_pools_name is not None:
        instance.backend_address_pools = [get_property(parent.backend_address_pools, i) for i in backend_pools_name]
        # Otherwiase service will response error : (LoadBalancingRuleBackendAdressPoolAndBackendAddressPoolsCannotBeSetAtTheSameTimeWithDifferentValue) BackendAddressPool and BackendAddressPools[] in LoadBalancingRule rule2 cannot be set at the same time with different value.
        instance.backend_address_pool = None

    if probe_name == '':
        instance.probe = None
    elif probe_name is not None:
        instance.probe = get_property(parent.probes, probe_name)

    return parent


def add_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                 backend_address_pool_name, protocol, identifier, traffic_type, port=None):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    GatewayLoadBalancerTunnelInterface = cmd.get_models('GatewayLoadBalancerTunnelInterface')
    tunnel_interface = GatewayLoadBalancerTunnelInterface(port=port, identifier=identifier, protocol=protocol, type=traffic_type)
    if not address_pool.tunnel_interfaces:
        address_pool.tunnel_interfaces = []
    address_pool.tunnel_interfaces.append(tunnel_interface)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def update_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                    backend_address_pool_name, index, protocol=None, identifier=None, traffic_type=None, port=None):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    if index >= len(address_pool.tunnel_interfaces):
        raise UnrecognizedArgumentError(f'{index} is out of scope, please input proper index')

    item = address_pool.tunnel_interfaces[index]
    if protocol:
        item.protocol = protocol
    if identifier:
        item.identifier = identifier
    if port:
        item.port = port
    if traffic_type:
        item.type = traffic_type
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def remove_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                    backend_address_pool_name, index):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    if index >= len(address_pool.tunnel_interfaces):
        raise UnrecognizedArgumentError(f'{index} is out of scope, please input proper index')
    address_pool.tunnel_interfaces.pop(index)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def list_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                  backend_address_pool_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    return address_pool.tunnel_interfaces
# endregion


# region LocalGateways
def _validate_bgp_peering(cmd, instance, asn, bgp_peering_address, peer_weight):
    if any([asn, bgp_peering_address, peer_weight]):
        if instance.bgp_settings is not None:
            # update existing parameters selectively
            if asn is not None:
                instance.bgp_settings.asn = asn
            if peer_weight is not None:
                instance.bgp_settings.peer_weight = peer_weight
            if bgp_peering_address is not None:
                instance.bgp_settings.bgp_peering_address = bgp_peering_address
        elif asn:
            BgpSettings = cmd.get_models('BgpSettings')
            instance.bgp_settings = BgpSettings(asn, bgp_peering_address, peer_weight)
        else:
            raise CLIError(
                'incorrect usage: --asn ASN [--peer-weight WEIGHT --bgp-peering-address IP]')
# endregion


# region NetworkInterfaces (NIC)
def create_nic(cmd, resource_group_name, network_interface_name, subnet, location=None, tags=None,
               internal_dns_name_label=None, dns_servers=None, enable_ip_forwarding=False,
               load_balancer_backend_address_pool_ids=None,
               load_balancer_inbound_nat_rule_ids=None,
               load_balancer_name=None, network_security_group=None,
               private_ip_address=None, private_ip_address_version=None,
               public_ip_address=None, virtual_network_name=None, enable_accelerated_networking=None,
               application_security_groups=None, no_wait=False,
               app_gateway_backend_address_pools=None, edge_zone=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    (NetworkInterface, NetworkInterfaceDnsSettings, NetworkInterfaceIPConfiguration, NetworkSecurityGroup,
     PublicIPAddress, Subnet, SubResource) = cmd.get_models(
         'NetworkInterface', 'NetworkInterfaceDnsSettings', 'NetworkInterfaceIPConfiguration',
         'NetworkSecurityGroup', 'PublicIPAddress', 'Subnet', 'SubResource')

    dns_settings = NetworkInterfaceDnsSettings(internal_dns_name_label=internal_dns_name_label,
                                               dns_servers=dns_servers or [])

    nic = NetworkInterface(location=location, tags=tags, enable_ip_forwarding=enable_ip_forwarding,
                           dns_settings=dns_settings)

    if cmd.supported_api_version(min_api='2016-09-01'):
        nic.enable_accelerated_networking = enable_accelerated_networking

    if network_security_group:
        nic.network_security_group = NetworkSecurityGroup(id=network_security_group)
    ip_config_args = {
        'name': 'ipconfig1',
        'load_balancer_backend_address_pools': load_balancer_backend_address_pool_ids,
        'load_balancer_inbound_nat_rules': load_balancer_inbound_nat_rule_ids,
        'private_ip_allocation_method': 'Static' if private_ip_address else 'Dynamic',
        'private_ip_address': private_ip_address,
        'subnet': Subnet(id=subnet),
        'application_gateway_backend_address_pools':
            [SubResource(id=x) for x in app_gateway_backend_address_pools]
            if app_gateway_backend_address_pools else None
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        ip_config_args['private_ip_address_version'] = private_ip_address_version
    if cmd.supported_api_version(min_api='2017-09-01'):
        ip_config_args['application_security_groups'] = application_security_groups
    ip_config = NetworkInterfaceIPConfiguration(**ip_config_args)

    if public_ip_address:
        ip_config.public_ip_address = PublicIPAddress(id=public_ip_address)
    nic.ip_configurations = [ip_config]

    if edge_zone:
        nic.extended_location = _edge_zone_model(cmd, edge_zone)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, network_interface_name, nic)


def update_nic(cmd, instance, network_security_group=None, enable_ip_forwarding=None,
               internal_dns_name_label=None, dns_servers=None, enable_accelerated_networking=None):
    if enable_ip_forwarding is not None:
        instance.enable_ip_forwarding = enable_ip_forwarding

    if network_security_group == '':
        instance.network_security_group = None
    elif network_security_group is not None:
        NetworkSecurityGroup = cmd.get_models('NetworkSecurityGroup')
        instance.network_security_group = NetworkSecurityGroup(id=network_security_group)

    if internal_dns_name_label == '':
        instance.dns_settings.internal_dns_name_label = None
    elif internal_dns_name_label is not None:
        instance.dns_settings.internal_dns_name_label = internal_dns_name_label
    if dns_servers == ['']:
        instance.dns_settings.dns_servers = None
    elif dns_servers:
        instance.dns_settings.dns_servers = dns_servers

    if enable_accelerated_networking is not None:
        instance.enable_accelerated_networking = enable_accelerated_networking

    return instance


def create_nic_ip_config(cmd, resource_group_name, network_interface_name, ip_config_name, subnet=None,
                         virtual_network_name=None, public_ip_address=None, load_balancer_name=None,
                         load_balancer_backend_address_pool_ids=None,
                         load_balancer_inbound_nat_rule_ids=None,
                         private_ip_address=None,
                         private_ip_address_version=None,
                         make_primary=False,
                         application_security_groups=None,
                         app_gateway_backend_address_pools=None):
    NetworkInterfaceIPConfiguration, PublicIPAddress, Subnet, SubResource = cmd.get_models(
        'NetworkInterfaceIPConfiguration', 'PublicIPAddress', 'Subnet', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    nic = ncf.network_interfaces.get(resource_group_name, network_interface_name)

    if cmd.supported_api_version(min_api='2016-09-01'):
        IPVersion = cmd.get_models('IPVersion')
        private_ip_address_version = private_ip_address_version or IPVersion.I_PV4.value
        if private_ip_address_version == IPVersion.I_PV4.value and not subnet:
            primary_config = next(x for x in nic.ip_configurations if x.primary)
            subnet = primary_config.subnet.id
        if make_primary:
            for config in nic.ip_configurations:
                config.primary = False

    new_config_args = {
        'name': ip_config_name,
        'subnet': Subnet(id=subnet) if subnet else None,
        'public_ip_address': PublicIPAddress(id=public_ip_address) if public_ip_address else None,
        'load_balancer_backend_address_pools': load_balancer_backend_address_pool_ids,
        'load_balancer_inbound_nat_rules': load_balancer_inbound_nat_rule_ids,
        'private_ip_address': private_ip_address,
        'private_ip_allocation_method': 'Static' if private_ip_address else 'Dynamic'
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        new_config_args['private_ip_address_version'] = private_ip_address_version
        new_config_args['primary'] = make_primary
    if cmd.supported_api_version(min_api='2017-09-01'):
        new_config_args['application_security_groups'] = application_security_groups
    if cmd.supported_api_version(min_api='2018-08-01'):
        new_config_args['application_gateway_backend_address_pools'] = \
            [SubResource(id=x) for x in app_gateway_backend_address_pools] \
            if app_gateway_backend_address_pools else None

    new_config = NetworkInterfaceIPConfiguration(**new_config_args)

    upsert_to_collection(nic, 'ip_configurations', new_config, 'name')
    poller = ncf.network_interfaces.begin_create_or_update(
        resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def update_nic_ip_config_setter(cmd, resource_group_name, network_interface_name, parameters, gateway_lb):
    aux_subscriptions = []
    if is_valid_resource_id(gateway_lb):
        aux_subscriptions.append(parse_resource_id(gateway_lb)['subscription'])
    client = network_client_factory(cmd.cli_ctx, aux_subscriptions=aux_subscriptions).network_interfaces
    return client.begin_create_or_update(resource_group_name, network_interface_name, parameters)


def set_nic_ip_config(cmd, instance, parent, ip_config_name, subnet=None,
                      virtual_network_name=None, public_ip_address=None, load_balancer_name=None,
                      load_balancer_backend_address_pool_ids=None,
                      load_balancer_inbound_nat_rule_ids=None,
                      private_ip_address=None,
                      private_ip_address_version=None, make_primary=False,
                      application_security_groups=None,
                      app_gateway_backend_address_pools=None, gateway_lb=None):
    PublicIPAddress, Subnet, SubResource = cmd.get_models('PublicIPAddress', 'Subnet', 'SubResource')

    if make_primary:
        for config in parent.ip_configurations:
            config.primary = False
        instance.primary = True

    if private_ip_address == '':
        # switch private IP address allocation to Dynamic if empty string is used
        instance.private_ip_address = None
        instance.private_ip_allocation_method = 'dynamic'
        if cmd.supported_api_version(min_api='2016-09-01'):
            instance.private_ip_address_version = 'ipv4'
    elif private_ip_address is not None:
        # if specific address provided, allocation is static
        instance.private_ip_address = private_ip_address
        instance.private_ip_allocation_method = 'static'
        if private_ip_address_version is not None:
            instance.private_ip_address_version = private_ip_address_version

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(id=subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    if load_balancer_backend_address_pool_ids == '':
        instance.load_balancer_backend_address_pools = None
    elif load_balancer_backend_address_pool_ids is not None:
        instance.load_balancer_backend_address_pools = load_balancer_backend_address_pool_ids

    if load_balancer_inbound_nat_rule_ids == '':
        instance.load_balancer_inbound_nat_rules = None
    elif load_balancer_inbound_nat_rule_ids is not None:
        instance.load_balancer_inbound_nat_rules = load_balancer_inbound_nat_rule_ids

    if application_security_groups == ['']:
        instance.application_security_groups = None
    elif application_security_groups:
        instance.application_security_groups = application_security_groups

    if app_gateway_backend_address_pools == ['']:
        instance.application_gateway_backend_address_pools = None
    elif app_gateway_backend_address_pools:
        instance.application_gateway_backend_address_pools = \
            [SubResource(id=x) for x in app_gateway_backend_address_pools]
    if gateway_lb is not None:
        instance.gateway_load_balancer = None if gateway_lb == '' else SubResource(id=gateway_lb)
    return parent


def _get_nic_ip_config(nic, name):
    if nic.ip_configurations:
        ip_config = next(
            (x for x in nic.ip_configurations if x.name.lower() == name.lower()), None)
    else:
        ip_config = None
    if not ip_config:
        raise CLIError('IP configuration {} not found.'.format(name))
    return ip_config


def add_nic_ip_config_address_pool(
        cmd, resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None, application_gateway_name=None):
    BackendAddressPool = cmd.get_models('BackendAddressPool')
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    if load_balancer_name:
        upsert_to_collection(ip_config, 'load_balancer_backend_address_pools',
                             BackendAddressPool(id=backend_address_pool),
                             'id')
    elif application_gateway_name:
        upsert_to_collection(ip_config, 'application_gateway_backend_address_pools',
                             BackendAddressPool(id=backend_address_pool),
                             'id')
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def remove_nic_ip_config_address_pool(
        cmd, resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None, application_gateway_name=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    if load_balancer_name:
        keep_items = [x for x in ip_config.load_balancer_backend_address_pools or [] if x.id != backend_address_pool]
        ip_config.load_balancer_backend_address_pools = keep_items
    elif application_gateway_name:
        keep_items = [x for x in ip_config.application_gateway_backend_address_pools or [] if
                      x.id != backend_address_pool]
        ip_config.application_gateway_backend_address_pools = keep_items
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def add_nic_ip_config_inbound_nat_rule(
        cmd, resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None):
    InboundNatRule = cmd.get_models('InboundNatRule')
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    upsert_to_collection(ip_config, 'load_balancer_inbound_nat_rules',
                         InboundNatRule(id=inbound_nat_rule),
                         'id')
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def remove_nic_ip_config_inbound_nat_rule(
        cmd, resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    keep_items = \
        [x for x in ip_config.load_balancer_inbound_nat_rules or [] if x.id != inbound_nat_rule]
    ip_config.load_balancer_inbound_nat_rules = keep_items
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)
# endregion


# region NetworkWatchers
def _create_network_watchers(cmd, client, resource_group_name, locations, tags):
    if resource_group_name is None:
        raise CLIError("usage error: '--resource-group' required when enabling new regions")

    NetworkWatcher = cmd.get_models('NetworkWatcher')
    for location in locations:
        client.create_or_update(
            resource_group_name, '{}-watcher'.format(location),
            NetworkWatcher(location=location, tags=tags))


def _update_network_watchers(cmd, client, watchers, tags):
    NetworkWatcher = cmd.get_models('NetworkWatcher')
    for watcher in watchers:
        id_parts = parse_resource_id(watcher.id)
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        watcher_tags = watcher.tags if tags is None else tags
        client.create_or_update(
            watcher_rg, watcher_name,
            NetworkWatcher(location=watcher.location, tags=watcher_tags))


def _delete_network_watchers(cmd, client, watchers):
    for watcher in watchers:
        from azure.cli.core.commands import LongRunningOperation
        id_parts = parse_resource_id(watcher.id)
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        logger.warning(
            "Disabling Network Watcher for region '%s' by deleting resource '%s'",
            watcher.location, watcher.id)
        LongRunningOperation(cmd.cli_ctx)(client.begin_delete(watcher_rg, watcher_name))


def configure_network_watcher(cmd, client, locations, resource_group_name=None, enabled=None, tags=None):
    watcher_list = list(client.list_all())
    locations_list = [location.lower() for location in locations]
    existing_watchers = [w for w in watcher_list if w.location in locations_list]
    nonenabled_regions = list(set(locations) - set(watcher.location for watcher in existing_watchers))

    if enabled is None:
        if resource_group_name is not None:
            logger.warning(
                "Resource group '%s' is only used when enabling new regions and will be ignored.",
                resource_group_name)
        for location in nonenabled_regions:
            logger.warning(
                "Region '%s' is not enabled for Network Watcher and will be ignored.", location)
        _update_network_watchers(cmd, client, existing_watchers, tags)

    elif enabled:
        _create_network_watchers(cmd, client, resource_group_name, nonenabled_regions, tags)
        _update_network_watchers(cmd, client, existing_watchers, tags)

    else:
        if tags is not None:
            raise CLIError("usage error: '--tags' cannot be used when disabling regions")
        _delete_network_watchers(cmd, client, existing_watchers)

    return client.list_all()


def create_nw_connection_monitor(cmd,
                                 client,
                                 connection_monitor_name,
                                 watcher_rg,
                                 watcher_name,
                                 resource_group_name=None,
                                 location=None,
                                 tags=None,
                                 endpoint_source_name=None,
                                 endpoint_source_resource_id=None,
                                 endpoint_source_address=None,
                                 endpoint_source_type=None,
                                 endpoint_source_coverage_level=None,
                                 endpoint_dest_name=None,
                                 endpoint_dest_resource_id=None,
                                 endpoint_dest_address=None,
                                 endpoint_dest_type=None,
                                 endpoint_dest_coverage_level=None,
                                 test_config_name=None,
                                 test_config_frequency=None,
                                 test_config_protocol=None,
                                 test_config_preferred_ip_version=None,
                                 test_config_threshold_failed_percent=None,
                                 test_config_threshold_round_trip_time=None,
                                 test_config_tcp_disable_trace_route=None,
                                 test_config_tcp_port=None,
                                 test_config_tcp_port_behavior=None,
                                 test_config_icmp_disable_trace_route=None,
                                 test_config_http_port=None,
                                 test_config_http_method=None,
                                 test_config_http_path=None,
                                 test_config_http_valid_status_codes=None,
                                 test_config_http_prefer_https=None,
                                 test_group_name=None,
                                 test_group_disable=None,
                                 output_type=None,
                                 workspace_ids=None,
                                 notes=None):
    connection_monitor = _create_nw_connection_monitor_v2(cmd,
                                                          location,
                                                          tags,
                                                          endpoint_source_name,
                                                          endpoint_source_resource_id,
                                                          endpoint_source_address,
                                                          endpoint_source_type,
                                                          endpoint_source_coverage_level,
                                                          endpoint_dest_name,
                                                          endpoint_dest_resource_id,
                                                          endpoint_dest_address,
                                                          endpoint_dest_type,
                                                          endpoint_dest_coverage_level,
                                                          test_config_name,
                                                          test_config_frequency,
                                                          test_config_protocol,
                                                          test_config_preferred_ip_version,
                                                          test_config_threshold_failed_percent,
                                                          test_config_threshold_round_trip_time,
                                                          test_config_tcp_port,
                                                          test_config_tcp_port_behavior,
                                                          test_config_tcp_disable_trace_route,
                                                          test_config_icmp_disable_trace_route,
                                                          test_config_http_port,
                                                          test_config_http_method,
                                                          test_config_http_path,
                                                          test_config_http_valid_status_codes,
                                                          test_config_http_prefer_https,
                                                          test_group_name,
                                                          test_group_disable,
                                                          output_type,
                                                          workspace_ids,
                                                          notes)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def _create_nw_connection_monitor_v2(cmd,
                                     location=None,
                                     tags=None,
                                     endpoint_source_name=None,
                                     endpoint_source_resource_id=None,
                                     endpoint_source_address=None,
                                     endpoint_source_type=None,
                                     endpoint_source_coverage_level=None,
                                     endpoint_dest_name=None,
                                     endpoint_dest_resource_id=None,
                                     endpoint_dest_address=None,
                                     endpoint_dest_type=None,
                                     endpoint_dest_coverage_level=None,
                                     test_config_name=None,
                                     test_config_frequency=None,
                                     test_config_protocol=None,
                                     test_config_preferred_ip_version=None,
                                     test_config_threshold_failed_percent=None,
                                     test_config_threshold_round_trip_time=None,
                                     test_config_tcp_port=None,
                                     test_config_tcp_port_behavior=None,
                                     test_config_tcp_disable_trace_route=False,
                                     test_config_icmp_disable_trace_route=False,
                                     test_config_http_port=None,
                                     test_config_http_method=None,
                                     test_config_http_path=None,
                                     test_config_http_valid_status_codes=None,
                                     test_config_http_prefer_https=None,
                                     test_group_name=None,
                                     test_group_disable=False,
                                     output_type=None,
                                     workspace_ids=None,
                                     notes=None):
    src_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                             endpoint_source_name,
                                                             endpoint_resource_id=endpoint_source_resource_id,
                                                             address=endpoint_source_address,
                                                             endpoint_type=endpoint_source_type,
                                                             coverage_level=endpoint_source_coverage_level)
    dst_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                             endpoint_dest_name,
                                                             endpoint_resource_id=endpoint_dest_resource_id,
                                                             address=endpoint_dest_address,
                                                             endpoint_type=endpoint_dest_type,
                                                             coverage_level=endpoint_dest_coverage_level)
    test_config = _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                                      test_config_name,
                                                                      test_config_frequency,
                                                                      test_config_protocol,
                                                                      test_config_threshold_failed_percent,
                                                                      test_config_threshold_round_trip_time,
                                                                      test_config_preferred_ip_version,
                                                                      test_config_tcp_port,
                                                                      test_config_tcp_port_behavior,
                                                                      test_config_tcp_disable_trace_route,
                                                                      test_config_icmp_disable_trace_route,
                                                                      test_config_http_port,
                                                                      test_config_http_method,
                                                                      test_config_http_path,
                                                                      test_config_http_valid_status_codes,
                                                                      test_config_http_prefer_https)
    test_group = _create_nw_connection_monitor_v2_test_group(cmd,
                                                             test_group_name,
                                                             test_group_disable,
                                                             [test_config],
                                                             [src_endpoint],
                                                             [dst_endpoint])

    # If 'workspace_ids' option is specified but 'output_type' is not then still it should be implicit that 'output-type' is 'Workspace'
    # since only supported value for output_type is 'Workspace' currently.
    if workspace_ids and not output_type:
        output_type = 'Workspace'

    if output_type:
        outputs = []
        if workspace_ids:
            for workspace_id in workspace_ids:
                output = _create_nw_connection_monitor_v2_output(cmd, output_type, workspace_id)
                outputs.append(output)
    else:
        outputs = []

    ConnectionMonitor = cmd.get_models('ConnectionMonitor')
    cmv2 = ConnectionMonitor(location=location,
                             tags=tags,
                             auto_start=None,
                             monitoring_interval_in_seconds=None,
                             endpoints=[src_endpoint, dst_endpoint],
                             test_configurations=[test_config],
                             test_groups=[test_group],
                             outputs=outputs,
                             notes=notes)
    return cmv2


def _create_nw_connection_monitor_v2_endpoint(cmd,
                                              name,
                                              endpoint_resource_id=None,
                                              address=None,
                                              filter_type=None,
                                              filter_items=None,
                                              endpoint_type=None,
                                              coverage_level=None):
    if (filter_type and not filter_items) or (not filter_type and filter_items):
        raise CLIError('usage error: '
                       '--filter-type and --filter-item for endpoint filter must be present at the same time.')

    ConnectionMonitorEndpoint, ConnectionMonitorEndpointFilter = cmd.get_models(
        'ConnectionMonitorEndpoint', 'ConnectionMonitorEndpointFilter')

    endpoint = ConnectionMonitorEndpoint(name=name,
                                         resource_id=endpoint_resource_id,
                                         address=address,
                                         type=endpoint_type,
                                         coverage_level=coverage_level)

    if filter_type and filter_items:
        endpoint_filter = ConnectionMonitorEndpointFilter(type=filter_type, items=filter_items)
        endpoint.filter = endpoint_filter

    return endpoint


def _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                        name,
                                                        test_frequency,
                                                        protocol,
                                                        threshold_failed_percent,
                                                        threshold_round_trip_time,
                                                        preferred_ip_version,
                                                        tcp_port=None,
                                                        tcp_port_behavior=None,
                                                        tcp_disable_trace_route=None,
                                                        icmp_disable_trace_route=None,
                                                        http_port=None,
                                                        http_method=None,
                                                        http_path=None,
                                                        http_valid_status_codes=None,
                                                        http_prefer_https=None,
                                                        http_request_headers=None):
    (ConnectionMonitorTestConfigurationProtocol,
     ConnectionMonitorTestConfiguration, ConnectionMonitorSuccessThreshold) = cmd.get_models(
         'ConnectionMonitorTestConfigurationProtocol',
         'ConnectionMonitorTestConfiguration', 'ConnectionMonitorSuccessThreshold')

    test_config = ConnectionMonitorTestConfiguration(name=name,
                                                     test_frequency_sec=test_frequency,
                                                     protocol=protocol,
                                                     preferred_ip_version=preferred_ip_version)

    if threshold_failed_percent or threshold_round_trip_time:
        threshold = ConnectionMonitorSuccessThreshold(checks_failed_percent=threshold_failed_percent,
                                                      round_trip_time_ms=threshold_round_trip_time)
        test_config.success_threshold = threshold

    if protocol == ConnectionMonitorTestConfigurationProtocol.tcp:
        ConnectionMonitorTcpConfiguration = cmd.get_models('ConnectionMonitorTcpConfiguration')
        tcp_config = ConnectionMonitorTcpConfiguration(
            port=tcp_port,
            destination_port_behavior=tcp_port_behavior,
            disable_trace_route=tcp_disable_trace_route
        )
        test_config.tcp_configuration = tcp_config
    elif protocol == ConnectionMonitorTestConfigurationProtocol.icmp:
        ConnectionMonitorIcmpConfiguration = cmd.get_models('ConnectionMonitorIcmpConfiguration')
        icmp_config = ConnectionMonitorIcmpConfiguration(disable_trace_route=icmp_disable_trace_route)
        test_config.icmp_configuration = icmp_config
    elif protocol == ConnectionMonitorTestConfigurationProtocol.http:
        ConnectionMonitorHttpConfiguration = cmd.get_models('ConnectionMonitorHttpConfiguration')
        http_config = ConnectionMonitorHttpConfiguration(
            port=http_port,
            method=http_method,
            path=http_path,
            request_headers=http_request_headers,
            valid_status_code_ranges=http_valid_status_codes,
            prefer_https=http_prefer_https)
        test_config.http_configuration = http_config
    else:
        raise CLIError('Unsupported protocol: "{}" for test configuration'.format(protocol))

    return test_config


def _create_nw_connection_monitor_v2_test_group(cmd,
                                                name,
                                                disable,
                                                test_configurations,
                                                source_endpoints,
                                                destination_endpoints):
    ConnectionMonitorTestGroup = cmd.get_models('ConnectionMonitorTestGroup')

    test_group = ConnectionMonitorTestGroup(name=name,
                                            disable=disable,
                                            test_configurations=[tc.name for tc in test_configurations],
                                            sources=[e.name for e in source_endpoints],
                                            destinations=[e.name for e in destination_endpoints])
    return test_group


def _create_nw_connection_monitor_v2_output(cmd,
                                            output_type,
                                            workspace_id=None):
    ConnectionMonitorOutput, OutputType = cmd.get_models('ConnectionMonitorOutput', 'OutputType')
    output = ConnectionMonitorOutput(type=output_type)

    if output_type == OutputType.workspace:
        ConnectionMonitorWorkspaceSettings = cmd.get_models('ConnectionMonitorWorkspaceSettings')
        workspace = ConnectionMonitorWorkspaceSettings(workspace_resource_id=workspace_id)
        output.workspace_settings = workspace
    else:
        raise CLIError('Unsupported output type: "{}"'.format(output_type))

    return output


def add_nw_connection_monitor_v2_endpoint(cmd,
                                          client,
                                          watcher_rg,
                                          watcher_name,
                                          connection_monitor_name,
                                          location,
                                          name,
                                          coverage_level=None,
                                          endpoint_type=None,
                                          source_test_groups=None,
                                          dest_test_groups=None,
                                          endpoint_resource_id=None,
                                          address=None,
                                          filter_type=None,
                                          filter_items=None,
                                          address_include=None,
                                          address_exclude=None):
    (ConnectionMonitorEndpoint, ConnectionMonitorEndpointFilter,
     ConnectionMonitorEndpointScope, ConnectionMonitorEndpointScopeItem) = cmd.get_models(
         'ConnectionMonitorEndpoint', 'ConnectionMonitorEndpointFilter',
         'ConnectionMonitorEndpointScope', 'ConnectionMonitorEndpointScopeItem')

    endpoint_scope = ConnectionMonitorEndpointScope(include=[], exclude=[])
    for ip in address_include or []:
        include_item = ConnectionMonitorEndpointScopeItem(address=ip)
        endpoint_scope.include.append(include_item)
    for ip in address_exclude or []:
        exclude_item = ConnectionMonitorEndpointScopeItem(address=ip)
        endpoint_scope.exclude.append(exclude_item)

    endpoint = ConnectionMonitorEndpoint(name=name,
                                         resource_id=endpoint_resource_id,
                                         address=address,
                                         type=endpoint_type,
                                         coverage_level=coverage_level,
                                         scope=endpoint_scope if address_include or address_exclude else None)

    if filter_type and filter_items:
        endpoint_filter = ConnectionMonitorEndpointFilter(type=filter_type, items=filter_items)
        endpoint.filter = endpoint_filter

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    connection_monitor.endpoints.append(endpoint)

    src_test_groups, dst_test_groups = set(source_test_groups or []), set(dest_test_groups or [])
    for test_group in connection_monitor.test_groups:
        if test_group.name in src_test_groups:
            test_group.sources.append(endpoint.name)
        if test_group.name in dst_test_groups:
            test_group.destinations.append(endpoint.name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_endpoint(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location,
                                             name,
                                             test_groups=None):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    # refresh endpoints
    new_endpoints = [endpoint for endpoint in connection_monitor.endpoints if endpoint.name != name]
    connection_monitor.endpoints = new_endpoints

    # refresh test groups
    if test_groups is not None:
        temp_test_groups = [t for t in connection_monitor.test_groups if t.name in test_groups]
    else:
        temp_test_groups = connection_monitor.test_groups

    for test_group in temp_test_groups:
        if name in test_group.sources:
            test_group.sources.remove(name)
        if name in test_group.destinations:
            test_group.destinations.remove(name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_endpoint(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location,
                                           name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for endpoint in connection_monitor.endpoints:
        if endpoint.name == name:
            return endpoint

    raise CLIError('unknown endpoint: {}'.format(name))


def list_nw_connection_monitor_v2_endpoint(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.endpoints


def add_nw_connection_monitor_v2_test_configuration(cmd,
                                                    client,
                                                    watcher_rg,
                                                    watcher_name,
                                                    connection_monitor_name,
                                                    location,
                                                    name,
                                                    protocol,
                                                    test_groups,
                                                    frequency=None,
                                                    threshold_failed_percent=None,
                                                    threshold_round_trip_time=None,
                                                    preferred_ip_version=None,
                                                    tcp_port=None,
                                                    tcp_port_behavior=None,
                                                    tcp_disable_trace_route=None,
                                                    icmp_disable_trace_route=None,
                                                    http_port=None,
                                                    http_method=None,
                                                    http_path=None,
                                                    http_valid_status_codes=None,
                                                    http_prefer_https=None,
                                                    http_request_headers=None):
    new_test_config = _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                                          name,
                                                                          frequency,
                                                                          protocol,
                                                                          threshold_failed_percent,
                                                                          threshold_round_trip_time,
                                                                          preferred_ip_version,
                                                                          tcp_port,
                                                                          tcp_port_behavior,
                                                                          tcp_disable_trace_route,
                                                                          icmp_disable_trace_route,
                                                                          http_port,
                                                                          http_method,
                                                                          http_path,
                                                                          http_valid_status_codes,
                                                                          http_prefer_https,
                                                                          http_request_headers)

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    connection_monitor.test_configurations.append(new_test_config)

    for test_group in connection_monitor.test_groups:
        if test_group.name in test_groups:
            test_group.test_configurations.append(new_test_config.name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_test_configuration(client,
                                                       watcher_rg,
                                                       watcher_name,
                                                       connection_monitor_name,
                                                       location,
                                                       name,
                                                       test_groups=None):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    # refresh test configurations
    new_test_configurations = [t for t in connection_monitor.test_configurations if t.name != name]
    connection_monitor.test_configurations = new_test_configurations

    if test_groups is not None:
        temp_test_groups = [t for t in connection_monitor.test_groups if t.name in test_groups]
    else:
        temp_test_groups = connection_monitor.test_groups

    # refresh test groups
    for test_group in temp_test_groups:
        test_group.test_configurations.remove(name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_test_configuration(client,
                                                     watcher_rg,
                                                     watcher_name,
                                                     connection_monitor_name,
                                                     location,
                                                     name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for test_config in connection_monitor.test_configurations:
        if test_config.name == name:
            return test_config

    raise CLIError('unknown test configuration: {}'.format(name))


def list_nw_connection_monitor_v2_test_configuration(client,
                                                     watcher_rg,
                                                     watcher_name,
                                                     connection_monitor_name,
                                                     location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.test_configurations


def add_nw_connection_monitor_v2_test_group(cmd,
                                            client,
                                            connection_monitor_name,
                                            watcher_rg,
                                            watcher_name,
                                            location,
                                            name,
                                            endpoint_source_name,
                                            endpoint_dest_name,
                                            test_config_name,
                                            disable=False,
                                            endpoint_source_resource_id=None,
                                            endpoint_source_address=None,
                                            endpoint_dest_resource_id=None,
                                            endpoint_dest_address=None,
                                            test_config_frequency=None,
                                            test_config_protocol=None,
                                            test_config_preferred_ip_version=None,
                                            test_config_threshold_failed_percent=None,
                                            test_config_threshold_round_trip_time=None,
                                            test_config_tcp_disable_trace_route=None,
                                            test_config_tcp_port=None,
                                            test_config_icmp_disable_trace_route=None,
                                            test_config_http_port=None,
                                            test_config_http_method=None,
                                            test_config_http_path=None,
                                            test_config_http_valid_status_codes=None,
                                            test_config_http_prefer_https=None):
    new_test_configuration_creation_requirements = [
        test_config_protocol, test_config_preferred_ip_version,
        test_config_threshold_failed_percent, test_config_threshold_round_trip_time,
        test_config_tcp_disable_trace_route, test_config_tcp_port,
        test_config_icmp_disable_trace_route,
        test_config_http_port, test_config_http_method,
        test_config_http_path, test_config_http_valid_status_codes, test_config_http_prefer_https
    ]

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    new_test_group = _create_nw_connection_monitor_v2_test_group(cmd,
                                                                 name,
                                                                 disable,
                                                                 [], [], [])

    # deal with endpoint
    if any([endpoint_source_address, endpoint_source_resource_id]):
        src_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                                 endpoint_source_name,
                                                                 endpoint_source_resource_id,
                                                                 endpoint_source_address)
        connection_monitor.endpoints.append(src_endpoint)
    if any([endpoint_dest_address, endpoint_dest_resource_id]):
        dst_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                                 endpoint_dest_name,
                                                                 endpoint_dest_resource_id,
                                                                 endpoint_dest_address)
        connection_monitor.endpoints.append(dst_endpoint)

    new_test_group.sources.append(endpoint_source_name)
    new_test_group.destinations.append(endpoint_dest_name)

    # deal with test configuration
    if any(new_test_configuration_creation_requirements):
        test_config = _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                                          test_config_name,
                                                                          test_config_frequency,
                                                                          test_config_protocol,
                                                                          test_config_threshold_failed_percent,
                                                                          test_config_threshold_round_trip_time,
                                                                          test_config_preferred_ip_version,
                                                                          test_config_tcp_port,
                                                                          test_config_tcp_disable_trace_route,
                                                                          test_config_icmp_disable_trace_route,
                                                                          test_config_http_port,
                                                                          test_config_http_method,
                                                                          test_config_http_path,
                                                                          test_config_http_valid_status_codes,
                                                                          test_config_http_prefer_https)
        connection_monitor.test_configurations.append(test_config)
    new_test_group.test_configurations.append(test_config_name)

    connection_monitor.test_groups.append(new_test_group)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_test_group(client,
                                               watcher_rg,
                                               watcher_name,
                                               connection_monitor_name,
                                               location,
                                               name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    new_test_groups, removed_test_group = [], None
    for t in connection_monitor.test_groups:
        if t.name == name:
            removed_test_group = t
        else:
            new_test_groups.append(t)

    if removed_test_group is None:
        raise CLIError('test group: "{}" not exist'.format(name))
    connection_monitor.test_groups = new_test_groups

    # deal with endpoints which are only referenced by this removed test group
    removed_endpoints = []
    for e in removed_test_group.sources + removed_test_group.destinations:
        tmp = [t for t in connection_monitor.test_groups if (e in t.sources or e in t.destinations)]
        if not tmp:
            removed_endpoints.append(e)
    connection_monitor.endpoints = [e for e in connection_monitor.endpoints if e.name not in removed_endpoints]

    # deal with test configurations which are only referenced by this remove test group
    removed_test_configurations = []
    for c in removed_test_group.test_configurations:
        tmp = [t for t in connection_monitor.test_groups if c in t.test_configurations]
        if not tmp:
            removed_test_configurations.append(c)
    connection_monitor.test_configurations = [c for c in connection_monitor.test_configurations
                                              if c.name not in removed_test_configurations]

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_test_group(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location,
                                             name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for t in connection_monitor.test_groups:
        if t.name == name:
            return t

    raise CLIError('unknown test group: {}'.format(name))


def list_nw_connection_monitor_v2_test_group(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.test_groups


def add_nw_connection_monitor_v2_output(cmd,
                                        client,
                                        watcher_rg,
                                        watcher_name,
                                        connection_monitor_name,
                                        location,
                                        out_type,
                                        workspace_id=None):
    output = _create_nw_connection_monitor_v2_output(cmd, out_type, workspace_id)

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    if connection_monitor.outputs is None:
        connection_monitor.outputs = []

    connection_monitor.outputs.append(output)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_output(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    connection_monitor.outputs = []

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def list_nw_connection_monitor_v2_output(client,
                                         watcher_rg,
                                         watcher_name,
                                         connection_monitor_name,
                                         location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.outputs


def show_topology_watcher(cmd, client, resource_group_name, network_watcher_name, target_resource_group_name=None,
                          target_vnet=None, target_subnet=None):  # pylint: disable=unused-argument
    TopologyParameters = cmd.get_models('TopologyParameters')
    return client.get_topology(
        resource_group_name=resource_group_name,
        network_watcher_name=network_watcher_name,
        parameters=TopologyParameters(
            target_resource_group_name=target_resource_group_name,
            target_virtual_network=target_vnet,
            target_subnet=target_subnet
        ))


def check_nw_connectivity(cmd, client, watcher_rg, watcher_name, source_resource, source_port=None,
                          dest_resource=None, dest_port=None, dest_address=None,
                          resource_group_name=None, protocol=None, method=None, headers=None, valid_status_codes=None):
    ConnectivitySource, ConnectivityDestination, ConnectivityParameters, ProtocolConfiguration, HTTPConfiguration = \
        cmd.get_models(
            'ConnectivitySource', 'ConnectivityDestination', 'ConnectivityParameters', 'ProtocolConfiguration',
            'HTTPConfiguration')
    params = ConnectivityParameters(
        source=ConnectivitySource(resource_id=source_resource, port=source_port),
        destination=ConnectivityDestination(resource_id=dest_resource, address=dest_address, port=dest_port),
        protocol=protocol
    )
    if any([method, headers, valid_status_codes]):
        params.protocol_configuration = ProtocolConfiguration(http_configuration=HTTPConfiguration(
            method=method,
            headers=headers,
            valid_status_codes=valid_status_codes
        ))
    return client.begin_check_connectivity(watcher_rg, watcher_name, params)


def check_nw_ip_flow(cmd, client, vm, watcher_rg, watcher_name, direction, protocol, local, remote,
                     resource_group_name=None, nic=None, location=None):
    VerificationIPFlowParameters = cmd.get_models('VerificationIPFlowParameters')

    try:
        local_ip_address, local_port = local.split(':')
        remote_ip_address, remote_port = remote.split(':')
    except:
        raise CLIError("usage error: the format of the '--local' and '--remote' should be like x.x.x.x:port")

    if not is_valid_resource_id(vm):
        if not resource_group_name:
            raise CLIError("usage error: --vm NAME --resource-group NAME | --vm ID")

        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    if nic and not is_valid_resource_id(nic):
        if not resource_group_name:
            raise CLIError("usage error: --nic NAME --resource-group NAME | --nic ID")

        nic = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Network', type='networkInterfaces', name=nic)

    return client.begin_verify_ip_flow(
        watcher_rg, watcher_name,
        VerificationIPFlowParameters(
            target_resource_id=vm, direction=direction, protocol=protocol, local_port=local_port,
            remote_port=remote_port, local_ip_address=local_ip_address,
            remote_ip_address=remote_ip_address, target_nic_resource_id=nic))


def show_nw_next_hop(cmd, client, resource_group_name, vm, watcher_rg, watcher_name,
                     source_ip, dest_ip, nic=None, location=None):
    NextHopParameters = cmd.get_models('NextHopParameters')

    if not is_valid_resource_id(vm):
        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    if nic and not is_valid_resource_id(nic):
        nic = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Network', type='networkInterfaces', name=nic)

    return client.begin_get_next_hop(
        watcher_rg, watcher_name, NextHopParameters(target_resource_id=vm,
                                                    source_ip_address=source_ip,
                                                    destination_ip_address=dest_ip,
                                                    target_nic_resource_id=nic))


def show_nw_security_view(cmd, client, resource_group_name, vm, watcher_rg, watcher_name, location=None):
    if not is_valid_resource_id(vm):
        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    security_group_view_parameters = cmd.get_models('SecurityGroupViewParameters')(target_resource_id=vm)
    return client.begin_get_vm_security_rules(watcher_rg, watcher_name, security_group_view_parameters)


def create_nw_packet_capture(cmd, client, resource_group_name, capture_name,
                             watcher_rg, watcher_name, vm=None, location=None,
                             storage_account=None, storage_path=None, file_path=None,
                             capture_size=None, capture_limit=None, time_limit=None, filters=None,
                             target_type=None, target=None, include=None, exclude=None):
    PacketCapture, PacketCaptureStorageLocation = cmd.get_models('PacketCapture', 'PacketCaptureStorageLocation')
    PacketCaptureMachineScope = cmd.get_models('PacketCaptureMachineScope')
    # Set the appropriate fields if target is VM
    pcap_scope = None
    if not target_type or target_type.lower() != "azurevmss":
        target = vm
    else:
        pcap_scope = PacketCaptureMachineScope(include=include, exclude=exclude)

    storage_settings = PacketCaptureStorageLocation(storage_id=storage_account,
                                                    storage_path=storage_path, file_path=file_path)
    capture_params = PacketCapture(target=target, storage_location=storage_settings,
                                   bytes_to_capture_per_packet=capture_size,
                                   total_bytes_per_session=capture_limit, time_limit_in_seconds=time_limit,
                                   filters=filters, target_type=target_type, scope=pcap_scope)
    return client.begin_create(watcher_rg, watcher_name, capture_name, capture_params)


def set_nsg_flow_logging(cmd, client, watcher_rg, watcher_name, nsg, storage_account=None,
                         resource_group_name=None, enabled=None, retention=0, log_format=None, log_version=None,
                         traffic_analytics_workspace=None, traffic_analytics_interval=None,
                         traffic_analytics_enabled=None):
    from azure.cli.core.commands import LongRunningOperation
    flowlog_status_parameters = cmd.get_models('FlowLogStatusParameters')(target_resource_id=nsg)
    config = LongRunningOperation(cmd.cli_ctx)(client.begin_get_flow_log_status(watcher_rg,
                                                                                watcher_name,
                                                                                flowlog_status_parameters))
    try:
        if not config.flow_analytics_configuration.network_watcher_flow_analytics_configuration.workspace_id:
            config.flow_analytics_configuration = None
    except AttributeError:
        config.flow_analytics_configuration = None

    with cmd.update_context(config) as c:
        c.set_param('enabled', enabled if enabled is not None else config.enabled)
        c.set_param('storage_id', storage_account or config.storage_id)
    if retention is not None:
        config.retention_policy = {
            'days': retention,
            'enabled': int(retention) > 0
        }
    if cmd.supported_api_version(min_api='2018-10-01') and (log_format or log_version):
        config.format = {
            'type': log_format,
            'version': log_version
        }

    if cmd.supported_api_version(min_api='2018-10-01') and \
            any([traffic_analytics_workspace is not None, traffic_analytics_enabled is not None]):
        workspace = None

        if traffic_analytics_workspace:
            from azure.cli.core.commands.arm import get_arm_resource_by_id
            workspace = get_arm_resource_by_id(cmd.cli_ctx, traffic_analytics_workspace)

        if not config.flow_analytics_configuration:
            # must create whole object
            if not workspace:
                raise CLIError('usage error (analytics not already configured): --workspace NAME_OR_ID '
                               '[--enabled {true|false}]')
            if traffic_analytics_enabled is None:
                traffic_analytics_enabled = True
            config.flow_analytics_configuration = {
                'network_watcher_flow_analytics_configuration': {
                    'enabled': traffic_analytics_enabled,
                    'workspace_id': workspace.properties['customerId'],
                    'workspace_region': workspace.location,
                    'workspace_resource_id': traffic_analytics_workspace,
                    'traffic_analytics_interval': traffic_analytics_interval
                }
            }
        else:
            # pylint: disable=line-too-long
            with cmd.update_context(config.flow_analytics_configuration.network_watcher_flow_analytics_configuration) as c:
                # update object
                c.set_param('enabled', traffic_analytics_enabled)
                if traffic_analytics_workspace == "":
                    config.flow_analytics_configuration = None
                elif workspace:
                    c.set_param('workspace_id', workspace.properties['customerId'])
                    c.set_param('workspace_region', workspace.location)
                    c.set_param('workspace_resource_id', traffic_analytics_workspace)
                    c.set_param('traffic_analytics_interval', traffic_analytics_interval)

    return client.begin_set_flow_log_configuration(watcher_rg, watcher_name, config)


# combination of resource_group_name and nsg is for old output
# combination of location and flow_log_name is for new output
def show_nw_flow_logging(cmd, client, watcher_rg, watcher_name, location=None, resource_group_name=None, nsg=None,
                         flow_log_name=None):
    # deprecated approach to show flow log
    if nsg is not None:
        flowlog_status_parameters = cmd.get_models('FlowLogStatusParameters')(target_resource_id=nsg)
        return client.begin_get_flow_log_status(watcher_rg, watcher_name, flowlog_status_parameters)

    # new approach to show flow log
    from ._client_factory import cf_flow_logs
    client = cf_flow_logs(cmd.cli_ctx, None)
    return client.get(watcher_rg, watcher_name, flow_log_name)


def create_nw_flow_log(cmd,
                       client,
                       location,
                       watcher_rg,
                       watcher_name,
                       flow_log_name,
                       nsg=None,
                       vnet=None,
                       subnet=None,
                       nic=None,
                       storage_account=None,
                       resource_group_name=None,
                       enabled=None,
                       retention=0,
                       log_format=None,
                       log_version=None,
                       traffic_analytics_workspace=None,
                       traffic_analytics_interval=60,
                       traffic_analytics_enabled=None,
                       tags=None):
    FlowLog = cmd.get_models('FlowLog')

    if sum(map(bool, [vnet, subnet, nic, nsg])) == 0:
        raise RequiredArgumentMissingError("Please enter atleast one target resource ID.")
    if sum(map(bool, [vnet, nic, nsg])) > 1:
        raise MutuallyExclusiveArgumentError("Please enter only one target resource ID.")

    if subnet is not None:
        flow_log = FlowLog(location=location, target_resource_id=subnet, storage_id=storage_account, enabled=enabled, tags=tags)
    elif vnet is not None and subnet is None:
        flow_log = FlowLog(location=location, target_resource_id=vnet, storage_id=storage_account, enabled=enabled, tags=tags)
    elif nic is not None:
        flow_log = FlowLog(location=location, target_resource_id=nic, storage_id=storage_account, enabled=enabled, tags=tags)
    elif nsg is not None:
        flow_log = FlowLog(location=location, target_resource_id=nsg, storage_id=storage_account, enabled=enabled, tags=tags)

    if retention > 0:
        RetentionPolicyParameters = cmd.get_models('RetentionPolicyParameters')
        retention_policy = RetentionPolicyParameters(days=retention, enabled=(retention > 0))
        flow_log.retention_policy = retention_policy

    if log_format is not None or log_version is not None:
        FlowLogFormatParameters = cmd.get_models('FlowLogFormatParameters')
        format_config = FlowLogFormatParameters(type=log_format, version=log_version)
        flow_log.format = format_config

    if traffic_analytics_workspace is not None:
        TrafficAnalyticsProperties, TrafficAnalyticsConfigurationProperties = \
            cmd.get_models('TrafficAnalyticsProperties', 'TrafficAnalyticsConfigurationProperties')

        from azure.cli.core.commands.arm import get_arm_resource_by_id
        workspace = get_arm_resource_by_id(cmd.cli_ctx, traffic_analytics_workspace)
        if not workspace:
            raise CLIError('Name or ID of workspace is invalid')

        traffic_analytics_config = TrafficAnalyticsConfigurationProperties(
            enabled=traffic_analytics_enabled,
            workspace_id=workspace.properties['customerId'],
            workspace_region=workspace.location,
            workspace_resource_id=workspace.id,
            traffic_analytics_interval=traffic_analytics_interval
        )
        traffic_analytics = TrafficAnalyticsProperties(
            network_watcher_flow_analytics_configuration=traffic_analytics_config
        )

        flow_log.flow_analytics_configuration = traffic_analytics

    return client.begin_create_or_update(watcher_rg, watcher_name, flow_log_name, flow_log)


def update_nw_flow_log_getter(client, watcher_rg, watcher_name, flow_log_name):
    return client.get(watcher_rg, watcher_name, flow_log_name)


def update_nw_flow_log_setter(client, watcher_rg, watcher_name, flow_log_name, parameters):
    return client.begin_create_or_update(watcher_rg, watcher_name, flow_log_name, parameters)


def update_nw_flow_log(cmd,
                       instance,
                       location,
                       resource_group_name=None,    # dummy parameter to let it appear in command
                       enabled=None,
                       nsg=None,
                       vnet=None,
                       subnet=None,
                       nic=None,
                       storage_account=None,
                       retention=0,
                       log_format=None,
                       log_version=None,
                       traffic_analytics_workspace=None,
                       traffic_analytics_interval=60,
                       traffic_analytics_enabled=None,
                       tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('enabled', enabled)
        c.set_param('tags', tags)
        c.set_param('storage_id', storage_account)

    if sum(map(bool, [vnet, nic, nsg])) > 1:
        raise MutuallyExclusiveArgumentError("Please enter only one target resource ID.")

    if subnet is not None:
        c.set_param('target_resource_id', subnet)
    elif vnet is not None and subnet is None:
        c.set_param('target_resource_id', vnet)
    elif nic is not None:
        c.set_param('target_resource_id', nic)
    else:
        c.set_param('target_resource_id', nsg)

    with cmd.update_context(instance.retention_policy) as c:
        c.set_param('days', retention)
        c.set_param('enabled', retention > 0)

    with cmd.update_context(instance.format) as c:
        c.set_param('type', log_format)
        c.set_param('version', log_version)

    if traffic_analytics_workspace is not None:
        from azure.cli.core.commands.arm import get_arm_resource_by_id
        workspace = get_arm_resource_by_id(cmd.cli_ctx, traffic_analytics_workspace)
        if not workspace:
            raise CLIError('Name or ID of workspace is invalid')

        if instance.flow_analytics_configuration.network_watcher_flow_analytics_configuration is None:
            analytics_conf = cmd.get_models('TrafficAnalyticsConfigurationProperties')
            instance.flow_analytics_configuration.network_watcher_flow_analytics_configuration = analytics_conf()

        with cmd.update_context(
                instance.flow_analytics_configuration.network_watcher_flow_analytics_configuration) as c:
            c.set_param('enabled', traffic_analytics_enabled)
            c.set_param('workspace_id', workspace.properties['customerId'])
            c.set_param('workspace_region', workspace.location)
            c.set_param('workspace_resource_id', workspace.id)
            c.set_param('traffic_analytics_interval', traffic_analytics_interval)

    return instance


def list_nw_flow_log(client, watcher_rg, watcher_name, location):
    return client.list(watcher_rg, watcher_name)


def delete_nw_flow_log(client, watcher_rg, watcher_name, location, flow_log_name):
    return client.begin_delete(watcher_rg, watcher_name, flow_log_name)


def start_nw_troubleshooting(cmd, client, watcher_name, watcher_rg, resource, storage_account,
                             storage_path, resource_type=None, resource_group_name=None,
                             no_wait=False):
    TroubleshootingParameters = cmd.get_models('TroubleshootingParameters')
    params = TroubleshootingParameters(target_resource_id=resource, storage_id=storage_account,
                                       storage_path=storage_path)
    return sdk_no_wait(no_wait, client.begin_get_troubleshooting, watcher_rg, watcher_name, params)


def show_nw_troubleshooting_result(cmd, client, watcher_name, watcher_rg, resource, resource_type=None,
                                   resource_group_name=None):
    query_troubleshooting_parameters = cmd.get_models('QueryTroubleshootingParameters')(target_resource_id=resource)
    return client.begin_get_troubleshooting_result(watcher_rg, watcher_name, query_troubleshooting_parameters)


def run_network_configuration_diagnostic(cmd, client, watcher_rg, watcher_name, resource,
                                         direction=None, protocol=None, source=None, destination=None,
                                         destination_port=None, queries=None,
                                         resource_group_name=None, resource_type=None, parent=None):
    NetworkConfigurationDiagnosticParameters, NetworkConfigurationDiagnosticProfile = \
        cmd.get_models('NetworkConfigurationDiagnosticParameters', 'NetworkConfigurationDiagnosticProfile')

    if not queries:
        queries = [NetworkConfigurationDiagnosticProfile(
            direction=direction,
            protocol=protocol,
            source=source,
            destination=destination,
            destination_port=destination_port
        )]
    params = NetworkConfigurationDiagnosticParameters(target_resource_id=resource, profiles=queries)
    return client.begin_get_network_configuration_diagnostic(watcher_rg, watcher_name, params)
# endregion


# region CustomIpPrefix
def create_custom_ip_prefix(cmd, client, resource_group_name, custom_ip_prefix_name, location=None,
                            cidr=None, tags=None, zone=None, signed_message=None, authorization_message=None,
                            custom_ip_prefix_parent=None, no_wait=False):

    CustomIpPrefix = cmd.get_models('CustomIpPrefix')
    prefix = CustomIpPrefix(
        location=location,
        cidr=cidr,
        zones=zone,
        tags=tags,
        signed_message=signed_message,
        authorization_message=authorization_message
    )

    if custom_ip_prefix_parent:
        try:
            prefix.custom_ip_prefix_parent = client.get(resource_group_name, custom_ip_prefix_name)
        except ResourceNotFoundError:
            raise ResourceNotFoundError("Custom ip prefix parent {} doesn't exist".format(custom_ip_prefix_name))

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, custom_ip_prefix_name, prefix)


def update_custom_ip_prefix(instance,
                            signed_message=None,
                            authorization_message=None,
                            tags=None,
                            commissioned_state=None):
    if tags is not None:
        instance.tags = tags
    if signed_message is not None:
        instance.signed_message = signed_message
    if authorization_message is not None:
        instance.authorization_message = authorization_message
    if commissioned_state is not None:
        instance.commissioned_state = commissioned_state[0].upper() + commissioned_state[1:] + 'ing'
    return instance
# endregion


# region TrafficManagers
def create_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   routing_method, unique_dns_name, monitor_path=None,
                                   monitor_port=80, monitor_protocol="HTTP",
                                   profile_status="Enabled",
                                   ttl=30, tags=None, interval=None, timeout=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.profile import Create
    Create_Profile = Create(cmd.loader)

    if monitor_path is None and monitor_protocol == 'HTTP':
        monitor_path = '/'
    args = {
        "name": traffic_manager_profile_name,
        "location": "global",
        "resource_group": resource_group_name,
        "unique_dns_name": unique_dns_name,
        "ttl": ttl,
        "max_return": max_return,
        "status": profile_status,
        "routing_method": routing_method,
        "tags": tags,
        "custom_headers": monitor_custom_headers,
        "status_code_ranges": status_code_ranges,
        "interval": interval,
        "path": monitor_path,
        "port": monitor_port,
        "protocol": monitor_protocol,
        "timeout": timeout,
        "max_failures": max_failures
    }

    return Create_Profile(args)


def update_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   profile_status=None, routing_method=None, tags=None,
                                   monitor_protocol=None, monitor_port=None, monitor_path=None,
                                   ttl=None, timeout=None, interval=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.profile import Update
    Update_Profile = Update(cmd.loader)

    args = {
        "name": traffic_manager_profile_name,
        "resource_group": resource_group_name
    }
    if ttl is not None:
        args["ttl"] = ttl
    if max_return is not None:
        args["max_return"] = max_return
    if profile_status is not None:
        args["status"] = profile_status
    if routing_method is not None:
        args["routing_method"] = routing_method
    if tags is not None:
        args["tags"] = tags
    if monitor_custom_headers is not None:
        args["custom_headers"] = monitor_custom_headers
    if status_code_ranges is not None:
        args["status_code_ranges"] = status_code_ranges
    if interval is not None:
        args["interval"] = interval
    if monitor_path is not None:
        args["path"] = monitor_path
    if monitor_port is not None:
        args["port"] = monitor_port
    if monitor_protocol is not None:
        args["protocol"] = monitor_protocol
    if timeout is not None:
        args["timeout"] = timeout
    if max_failures is not None:
        args["max_failures"] = max_failures

    return Update_Profile(args)


def create_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_type, endpoint_name,
                                    target_resource_id=None, target=None,
                                    endpoint_status=None, weight=None, priority=None,
                                    endpoint_location=None, endpoint_monitor_status=None,
                                    min_child_endpoints=None, min_child_ipv4=None, min_child_ipv6=None,
                                    geo_mapping=None, monitor_custom_headers=None, subnets=None):
    from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.endpoint import Create
    Create_Endpoint = Create(cmd.loader)

    args = {
        "name": endpoint_name,
        "type": endpoint_type,
        "profile_name": profile_name,
        "resource_group": resource_group_name,
        "custom_headers": monitor_custom_headers,
        "endpoint_location": endpoint_location,
        "endpoint_monitor_status": endpoint_monitor_status,
        "endpoint_status": endpoint_status,
        "geo_mapping": geo_mapping,
        "min_child_endpoints": min_child_endpoints,
        "min_child_ipv4": min_child_ipv4,
        "min_child_ipv6": min_child_ipv6,
        "priority": priority,
        "subnets": subnets,
        "target": target,
        "target_resource_id": target_resource_id,
        "weight": weight
    }

    return Create_Endpoint(args)


def update_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_name,
                                    endpoint_type, endpoint_location=None,
                                    endpoint_status=None, endpoint_monitor_status=None,
                                    priority=None, target=None, target_resource_id=None,
                                    weight=None, min_child_endpoints=None, min_child_ipv4=None,
                                    min_child_ipv6=None, geo_mapping=None,
                                    subnets=None, monitor_custom_headers=None):
    from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.endpoint import Update
    Update_Endpoint = Update(cmd.loader)

    args = {
        "name": endpoint_name,
        "type": endpoint_type,
        "profile_name": profile_name,
        "resource_group": resource_group_name
    }
    if monitor_custom_headers is not None:
        args["custom_headers"] = monitor_custom_headers
    if endpoint_location is not None:
        args["endpoint_location"] = endpoint_location
    if endpoint_monitor_status is not None:
        args["endpoint_monitor_status"] = endpoint_monitor_status
    if endpoint_status is not None:
        args["endpoint_status"] = endpoint_status
    if geo_mapping is not None:
        args["geo_mapping"] = geo_mapping
    if min_child_endpoints is not None:
        args["min_child_endpoints"] = min_child_endpoints
    if min_child_ipv4 is not None:
        args["min_child_ipv4"] = min_child_ipv4
    if min_child_ipv6 is not None:
        args["min_child_ipv6"] = min_child_ipv6
    if priority is not None:
        args["priority"] = priority
    if subnets is not None:
        args["subnets"] = subnets
    if target is not None:
        args["target"] = target
    if target_resource_id is not None:
        args["target_resource_id"] = target_resource_id
    if weight is not None:
        args["weight"] = weight

    return Update_Endpoint(args)


def list_traffic_manager_endpoints(cmd, resource_group_name, profile_name, endpoint_type=None):
    from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.profile import Show
    Show_Profile = Show(cmd.loader)

    args = {
        "resource_group": resource_group_name,
        "profile_name": profile_name
    }
    profile = Show_Profile(args)

    return [e for e in profile['endpoints'] if not endpoint_type or e['type'].endswith(endpoint_type)]
# endregion


# region VirtualNetworks
# pylint: disable=too-many-locals
def create_vnet(cmd, resource_group_name, vnet_name, vnet_prefixes='10.0.0.0/16',
                subnet_name=None, subnet_prefix=None, dns_servers=None,
                location=None, tags=None, vm_protection=None, ddos_protection=None, bgp_community=None,
                ddos_protection_plan=None, network_security_group=None, edge_zone=None, flowtimeout=None,
                enable_encryption=None, encryption_enforcement_policy=None):
    AddressSpace, DhcpOptions, Subnet, VirtualNetwork, SubResource, NetworkSecurityGroup = \
        cmd.get_models('AddressSpace', 'DhcpOptions', 'Subnet', 'VirtualNetwork',
                       'SubResource', 'NetworkSecurityGroup')
    client = network_client_factory(cmd.cli_ctx).virtual_networks
    tags = tags or {}

    vnet = VirtualNetwork(
        location=location, tags=tags,
        dhcp_options=DhcpOptions(dns_servers=dns_servers),
        address_space=AddressSpace(address_prefixes=(vnet_prefixes if isinstance(vnet_prefixes, list) else [vnet_prefixes])))  # pylint: disable=line-too-long
    if subnet_name:
        if cmd.supported_api_version(min_api='2018-08-01'):
            vnet.subnets = [Subnet(name=subnet_name,
                                   address_prefix=subnet_prefix[0] if len(subnet_prefix) == 1 else None,
                                   address_prefixes=subnet_prefix if len(subnet_prefix) > 1 else None,
                                   private_endpoint_network_policies='Disabled',
                                   network_security_group=NetworkSecurityGroup(id=network_security_group)
                                   if network_security_group else None)]
        else:
            vnet.subnets = [Subnet(name=subnet_name, address_prefix=subnet_prefix)]
    if cmd.supported_api_version(min_api='2017-09-01'):
        vnet.enable_ddos_protection = ddos_protection
        vnet.enable_vm_protection = vm_protection
    if cmd.supported_api_version(min_api='2018-02-01'):
        vnet.ddos_protection_plan = SubResource(id=ddos_protection_plan) if ddos_protection_plan else None
    if edge_zone:
        vnet.extended_location = _edge_zone_model(cmd, edge_zone)
    if flowtimeout is not None:
        vnet.flow_timeout_in_minutes = flowtimeout
    if bgp_community is not None and cmd.supported_api_version(min_api='2020-06-01'):
        VirtualNetworkBgpCommunities = cmd.get_models('VirtualNetworkBgpCommunities')
        vnet.bgp_communities = VirtualNetworkBgpCommunities(virtual_network_community=bgp_community)
    if enable_encryption is not None:
        if not vnet.encryption:
            vnet.encryption = {}
        vnet.encryption["enabled"] = enable_encryption
    if encryption_enforcement_policy is not None:
        if not vnet.encryption:
            raise ArgumentUsageError('usage error: --encryption--enforcement--policy is only configurable when '
                                     '--enable-encryption is specified.')
        vnet.encryption["enforcement"] = encryption_enforcement_policy
    return cached_put(cmd, client.begin_create_or_update, vnet, resource_group_name, vnet_name)


def update_vnet(cmd, instance, vnet_prefixes=None, dns_servers=None, ddos_protection=None, vm_protection=None,
                ddos_protection_plan=None, flowtimeout=None, bgp_community=None, enable_encryption=None,
                encryption_enforcement_policy=None):
    # server side validation reports pretty good error message on invalid CIDR,
    # so we don't validate at client side
    AddressSpace, DhcpOptions, SubResource = cmd.get_models('AddressSpace', 'DhcpOptions', 'SubResource')
    if vnet_prefixes and instance.address_space:
        instance.address_space.address_prefixes = vnet_prefixes
    elif vnet_prefixes:
        instance.address_space = AddressSpace(address_prefixes=vnet_prefixes)

    if dns_servers == ['']:
        instance.dhcp_options.dns_servers = None
    elif dns_servers and instance.dhcp_options:
        instance.dhcp_options.dns_servers = dns_servers
    elif dns_servers:
        instance.dhcp_options = DhcpOptions(dns_servers=dns_servers)

    if ddos_protection is not None:
        instance.enable_ddos_protection = ddos_protection
    if vm_protection is not None:
        instance.enable_vm_protection = vm_protection
    if ddos_protection_plan == '':
        instance.ddos_protection_plan = None
    elif ddos_protection_plan is not None:
        instance.ddos_protection_plan = SubResource(id=ddos_protection_plan)
    if flowtimeout is not None:
        instance.flow_timeout_in_minutes = flowtimeout
    if bgp_community is not None and cmd.supported_api_version(min_api='2020-06-01'):
        VirtualNetworkBgpCommunities = cmd.get_models('VirtualNetworkBgpCommunities')
        instance.bgp_communities = VirtualNetworkBgpCommunities(virtual_network_community=bgp_community)
    if enable_encryption is not None:
        if not instance.encryption:
            VirtualNetworkEncryption = cmd.get_models('VirtualNetworkEncryption')
            instance.encryption = VirtualNetworkEncryption(enabled=enable_encryption)
        instance.encryption.enabled = enable_encryption
    if encryption_enforcement_policy is not None:
        if not instance.encryption:
            raise ArgumentUsageError('usage error: --encryption--enforcement--policy is only configurable when '
                                     '--enable-encryption is specified.')
        instance.encryption.enforcement = encryption_enforcement_policy
    return instance


def _set_route_table(ncf, resource_group_name, route_table, subnet):
    if route_table:
        is_id = is_valid_resource_id(route_table)
        rt = None
        if is_id:
            res_id = parse_resource_id(route_table)
            rt = ncf.route_tables.get(res_id['resource_group'], res_id['name'])
        else:
            rt = ncf.route_tables.get(resource_group_name, route_table)
        subnet.route_table = rt
    elif route_table == '':
        subnet.route_table = None


def create_subnet(cmd, resource_group_name, virtual_network_name, subnet_name,
                  address_prefix, network_security_group=None,
                  route_table=None, service_endpoints=None, service_endpoint_policy=None,
                  delegations=None, nat_gateway=None,
                  disable_private_endpoint_network_policies=None,
                  disable_private_link_service_network_policies=None):
    NetworkSecurityGroup, ServiceEndpoint, Subnet, SubResource = cmd.get_models(
        'NetworkSecurityGroup', 'ServiceEndpointPropertiesFormat', 'Subnet', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)

    if cmd.supported_api_version(min_api='2018-08-01'):
        subnet = Subnet(
            name=subnet_name,
            address_prefixes=address_prefix if len(address_prefix) > 1 else None,
            address_prefix=address_prefix[0] if len(address_prefix) == 1 else None
        )
        if cmd.supported_api_version(min_api='2019-02-01') and nat_gateway:
            subnet.nat_gateway = SubResource(id=nat_gateway)
    else:
        subnet = Subnet(name=subnet_name, address_prefix=address_prefix)

    if network_security_group:
        subnet.network_security_group = NetworkSecurityGroup(id=network_security_group)
    _set_route_table(ncf, resource_group_name, route_table, subnet)
    if service_endpoints:
        subnet.service_endpoints = []
        for service in service_endpoints:
            subnet.service_endpoints.append(ServiceEndpoint(service=service))
    if service_endpoint_policy:
        subnet.service_endpoint_policies = []
        for policy in service_endpoint_policy:
            subnet.service_endpoint_policies.append(SubResource(id=policy))
    if delegations:
        subnet.delegations = delegations

    if disable_private_endpoint_network_policies is None or disable_private_endpoint_network_policies is True:
        subnet.private_endpoint_network_policies = "Disabled"
    if disable_private_endpoint_network_policies is False:
        subnet.private_endpoint_network_policies = "Enabled"

    if disable_private_link_service_network_policies is True:
        subnet.private_link_service_network_policies = "Disabled"
    if disable_private_link_service_network_policies is False:
        subnet.private_link_service_network_policies = "Enabled"

    vnet = cached_get(cmd, ncf.virtual_networks.get, resource_group_name, virtual_network_name)
    upsert_to_collection(vnet, 'subnets', subnet, 'name')
    vnet = cached_put(
        cmd, ncf.virtual_networks.begin_create_or_update, vnet, resource_group_name, virtual_network_name).result()
    return get_property(vnet.subnets, subnet_name)


def update_subnet(cmd, instance, resource_group_name, address_prefix=None, network_security_group=None,
                  route_table=None, service_endpoints=None, delegations=None, nat_gateway=None,
                  service_endpoint_policy=None, disable_private_endpoint_network_policies=None,
                  disable_private_link_service_network_policies=None):
    NetworkSecurityGroup, ServiceEndpoint, SubResource = cmd.get_models(
        'NetworkSecurityGroup', 'ServiceEndpointPropertiesFormat', 'SubResource')

    if address_prefix:
        if cmd.supported_api_version(min_api='2018-08-01'):
            instance.address_prefixes = address_prefix if len(address_prefix) > 1 else None
            instance.address_prefix = address_prefix[0] if len(address_prefix) == 1 else None
        else:
            instance.address_prefix = address_prefix

    if cmd.supported_api_version(min_api='2019-02-01') and nat_gateway:
        instance.nat_gateway = SubResource(id=nat_gateway)
    elif nat_gateway == '':
        instance.nat_gateway = None

    if network_security_group:
        instance.network_security_group = NetworkSecurityGroup(id=network_security_group)
    elif network_security_group == '':  # clear it
        instance.network_security_group = None

    _set_route_table(network_client_factory(cmd.cli_ctx), resource_group_name, route_table, instance)

    if service_endpoints == ['']:
        instance.service_endpoints = None
    elif service_endpoints:
        instance.service_endpoints = []
        for service in service_endpoints:
            instance.service_endpoints.append(ServiceEndpoint(service=service))

    if service_endpoint_policy == '':
        instance.service_endpoint_policies = None
    elif service_endpoint_policy:
        instance.service_endpoint_policies = []
        for policy in service_endpoint_policy:
            instance.service_endpoint_policies.append(SubResource(id=policy))

    if delegations:
        instance.delegations = delegations

    if disable_private_endpoint_network_policies:
        instance.private_endpoint_network_policies = "Disabled"
    elif disable_private_endpoint_network_policies is not None:
        instance.private_endpoint_network_policies = "Enabled"

    if disable_private_link_service_network_policies:
        instance.private_link_service_network_policies = "Disabled"
    elif disable_private_link_service_network_policies is not None:
        instance.private_link_service_network_policies = "Enabled"

    return instance


def list_avail_subnet_delegations(cmd, resource_group_name=None, location=None):
    client = network_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.available_resource_group_delegations.list(location, resource_group_name)
    return client.available_delegations.list(location)


def create_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name,
                        remote_virtual_network, allow_virtual_network_access=False,
                        allow_forwarded_traffic=False, allow_gateway_transit=False,
                        use_remote_gateways=False):
    if not is_valid_resource_id(remote_virtual_network):
        remote_virtual_network = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=remote_virtual_network
        )
    SubResource, VirtualNetworkPeering = cmd.get_models('SubResource', 'VirtualNetworkPeering')
    peering = VirtualNetworkPeering(
        id=resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=virtual_network_name),
        name=virtual_network_peering_name,
        remote_virtual_network=SubResource(id=remote_virtual_network),
        allow_virtual_network_access=allow_virtual_network_access,
        allow_gateway_transit=allow_gateway_transit,
        allow_forwarded_traffic=allow_forwarded_traffic,
        use_remote_gateways=use_remote_gateways)
    aux_subscription = parse_resource_id(remote_virtual_network)['subscription']
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[aux_subscription])
    return ncf.virtual_network_peerings.begin_create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)


def sync_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name):
    subscription_id = get_subscription_id(cmd.cli_ctx)
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[subscription_id])

    try:
        peering = ncf.virtual_network_peerings.get(resource_group_name, virtual_network_name, virtual_network_peering_name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError('Virtual network peering {} doesn\'t exist.'.format(virtual_network_peering_name))

    return ncf.virtual_network_peerings.begin_create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering, sync_remote_address_space=True)


def update_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name, **kwargs):
    peering = kwargs['parameters']
    aux_subscription = parse_resource_id(peering.remote_virtual_network.id)['subscription']
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[aux_subscription])
    return ncf.virtual_network_peerings.begin_create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)


def list_available_ips(cmd, resource_group_name, virtual_network_name):
    client = network_client_factory(cmd.cli_ctx).virtual_networks
    vnet = client.get(resource_group_name=resource_group_name,
                      virtual_network_name=virtual_network_name)
    start_ip = vnet.address_space.address_prefixes[0].split('/')[0]
    available_ips = client.check_ip_address_availability(resource_group_name=resource_group_name,
                                                         virtual_network_name=virtual_network_name,
                                                         ip_address=start_ip)
    return available_ips.available_ip_addresses


def subnet_list_available_ips(cmd, resource_group_name, virtual_network_name, subnet_name):
    client = network_client_factory(cmd.cli_ctx)
    subnet = client.subnets.get(resource_group_name=resource_group_name,
                                virtual_network_name=virtual_network_name,
                                subnet_name=subnet_name)
    if subnet.address_prefix is not None:
        start_ip = subnet.address_prefix.split('/')[0]
    available_ips = client.virtual_networks.check_ip_address_availability(resource_group_name=resource_group_name,
                                                                          virtual_network_name=virtual_network_name,
                                                                          ip_address=start_ip)
    return available_ips.available_ip_addresses
# endregion


# region VirtualNetworkGateways
def create_vnet_gateway_root_cert(cmd, resource_group_name, gateway_name, public_cert_data, cert_name):
    VpnClientRootCertificate = cmd.get_models('VpnClientRootCertificate')
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    if not gateway.vpn_client_configuration:
        raise CLIError("Must add address prefixes to gateway '{}' prior to adding a root cert."
                       .format(gateway_name))
    config = gateway.vpn_client_configuration

    if config.vpn_client_root_certificates is None:
        config.vpn_client_root_certificates = []

    cert = VpnClientRootCertificate(name=cert_name, public_cert_data=public_cert_data)
    upsert_to_collection(config, 'vpn_client_root_certificates', cert, 'name')
    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def delete_vnet_gateway_root_cert(cmd, resource_group_name, gateway_name, cert_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_root_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_root_certificates.remove(cert)

    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def create_vnet_gateway_revoked_cert(cmd, resource_group_name, gateway_name, thumbprint, cert_name):
    VpnClientRevokedCertificate = cmd.get_models('VpnClientRevokedCertificate')
    config, gateway, ncf = _prep_cert_create(cmd, gateway_name, resource_group_name)

    cert = VpnClientRevokedCertificate(name=cert_name, thumbprint=thumbprint)
    upsert_to_collection(config, 'vpn_client_revoked_certificates', cert, 'name')
    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def delete_vnet_gateway_revoked_cert(cmd, resource_group_name, gateway_name, cert_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_revoked_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_revoked_certificates.remove(cert)

    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def _prep_cert_create(cmd, gateway_name, resource_group_name):
    VpnClientConfiguration = cmd.get_models('VpnClientConfiguration')
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    if not gateway.vpn_client_configuration:
        gateway.vpn_client_configuration = VpnClientConfiguration()
    config = gateway.vpn_client_configuration

    if not config.vpn_client_address_pool or not config.vpn_client_address_pool.address_prefixes:
        raise CLIError('Address prefixes must be set on VPN gateways before adding'
                       ' certificates.  Please use "update" with --address-prefixes first.')

    if config.vpn_client_revoked_certificates is None:
        config.vpn_client_revoked_certificates = []
    if config.vpn_client_root_certificates is None:
        config.vpn_client_root_certificates = []

    return config, gateway, ncf


def create_vnet_gateway(cmd, resource_group_name, virtual_network_gateway_name, public_ip_address,
                        virtual_network, location=None, tags=None,
                        no_wait=False, gateway_type=None, sku=None, vpn_type=None, vpn_gateway_generation=None,
                        asn=None, bgp_peering_address=None, peer_weight=None,
                        address_prefixes=None, radius_server=None, radius_secret=None, client_protocol=None,
                        gateway_default_site=None, custom_routes=None, aad_tenant=None, aad_audience=None,
                        aad_issuer=None, root_cert_data=None, root_cert_name=None, vpn_auth_type=None, edge_zone=None,
                        nat_rule=None):
    (VirtualNetworkGateway, BgpSettings, SubResource, VirtualNetworkGatewayIPConfiguration, VirtualNetworkGatewaySku,
     VpnClientConfiguration, AddressSpace, VpnClientRootCertificate, VirtualNetworkGatewayNatRule,
     VpnNatRuleMapping) = cmd.get_models(
         'VirtualNetworkGateway', 'BgpSettings', 'SubResource', 'VirtualNetworkGatewayIPConfiguration',
         'VirtualNetworkGatewaySku', 'VpnClientConfiguration', 'AddressSpace', 'VpnClientRootCertificate',
         'VirtualNetworkGatewayNatRule', 'VpnNatRuleMapping')

    client = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    subnet = virtual_network + '/subnets/GatewaySubnet'
    active = len(public_ip_address) == 2
    vnet_gateway = VirtualNetworkGateway(
        gateway_type=gateway_type, vpn_type=vpn_type, vpn_gateway_generation=vpn_gateway_generation, location=location,
        tags=tags, sku=VirtualNetworkGatewaySku(name=sku, tier=sku), active=active, ip_configurations=[],
        gateway_default_site=SubResource(id=gateway_default_site) if gateway_default_site else None)
    for i, public_ip in enumerate(public_ip_address):
        ip_configuration = VirtualNetworkGatewayIPConfiguration(
            subnet=SubResource(id=subnet),
            public_ip_address=SubResource(id=public_ip),
            private_ip_allocation_method='Dynamic',
            name='vnetGatewayConfig{}'.format(i)
        )
        vnet_gateway.ip_configurations.append(ip_configuration)
    if asn or bgp_peering_address or peer_weight:
        vnet_gateway.enable_bgp = True
        vnet_gateway.bgp_settings = BgpSettings(asn=asn, bgp_peering_address=bgp_peering_address,
                                                peer_weight=peer_weight)

    if any((address_prefixes, client_protocol)):
        vnet_gateway.vpn_client_configuration = VpnClientConfiguration()
        vnet_gateway.vpn_client_configuration.vpn_client_address_pool = AddressSpace()
        vnet_gateway.vpn_client_configuration.vpn_client_address_pool.address_prefixes = address_prefixes
        vnet_gateway.vpn_client_configuration.vpn_client_protocols = client_protocol
        if any((radius_secret, radius_server)) and cmd.supported_api_version(min_api='2017-06-01'):
            vnet_gateway.vpn_client_configuration.radius_server_address = radius_server
            vnet_gateway.vpn_client_configuration.radius_server_secret = radius_secret

        # multi authentication
        if cmd.supported_api_version(min_api='2020-11-01'):
            vnet_gateway.vpn_client_configuration.vpn_authentication_types = vpn_auth_type
            vnet_gateway.vpn_client_configuration.aad_tenant = aad_tenant
            vnet_gateway.vpn_client_configuration.aad_issuer = aad_issuer
            vnet_gateway.vpn_client_configuration.aad_audience = aad_audience
            vnet_gateway.vpn_client_configuration.vpn_client_root_certificates = [
                VpnClientRootCertificate(name=root_cert_name,
                                         public_cert_data=root_cert_data)] if root_cert_data else None

    if custom_routes and cmd.supported_api_version(min_api='2019-02-01'):
        vnet_gateway.custom_routes = AddressSpace()
        vnet_gateway.custom_routes.address_prefixes = custom_routes

    if edge_zone:
        vnet_gateway.extended_location = _edge_zone_model(cmd, edge_zone)
    if nat_rule:
        vnet_gateway.nat_rules = [
            VirtualNetworkGatewayNatRule(type_properties_type=rule.get('type'), mode=rule.get('mode'), name=rule.get('name'),
                                         internal_mappings=[VpnNatRuleMapping(address_space=i_map) for i_map in rule.get('internal_mappings')] if rule.get('internal_mappings') else None,
                                         external_mappings=[VpnNatRuleMapping(address_space=i_map) for i_map in rule.get('external_mappings')] if rule.get('external_mappings') else None,
                                         ip_configuration_id=rule.get('ip_config_id')) for rule in nat_rule]

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name, virtual_network_gateway_name, vnet_gateway)


def update_vnet_gateway(cmd, instance, sku=None, vpn_type=None, tags=None,
                        public_ip_address=None, gateway_type=None, enable_bgp=None,
                        asn=None, bgp_peering_address=None, peer_weight=None, virtual_network=None,
                        address_prefixes=None, radius_server=None, radius_secret=None, client_protocol=None,
                        gateway_default_site=None, custom_routes=None, aad_tenant=None, aad_audience=None,
                        aad_issuer=None, root_cert_data=None, root_cert_name=None, vpn_auth_type=None):
    (AddressSpace, SubResource, VirtualNetworkGatewayIPConfiguration, VpnClientConfiguration,
     VpnClientRootCertificate) = cmd.get_models('AddressSpace', 'SubResource', 'VirtualNetworkGatewayIPConfiguration',
                                                'VpnClientConfiguration', 'VpnClientRootCertificate')

    if any((address_prefixes, radius_server, radius_secret, client_protocol)) and not instance.vpn_client_configuration:
        instance.vpn_client_configuration = VpnClientConfiguration()

    if address_prefixes is not None:
        if not instance.vpn_client_configuration.vpn_client_address_pool:
            instance.vpn_client_configuration.vpn_client_address_pool = AddressSpace()
        if not instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes:
            instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes = []
        instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes = address_prefixes

    with cmd.update_context(instance.vpn_client_configuration) as c:
        c.set_param('vpn_client_protocols', client_protocol)
        c.set_param('radius_server_address', radius_server)
        c.set_param('radius_server_secret', radius_secret)
        if cmd.supported_api_version(min_api='2020-11-01'):
            c.set_param('aad_tenant', aad_tenant)
            c.set_param('aad_audience', aad_audience)
            c.set_param('aad_issuer', aad_issuer)
            c.set_param('vpn_authentication_types', vpn_auth_type)

    if root_cert_data and cmd.supported_api_version(min_api='2020-11-01'):
        upsert_to_collection(instance.vpn_client_configuration, 'vpn_client_root_certificates',
                             VpnClientRootCertificate(name=root_cert_name, public_cert_data=root_cert_data), 'name')

    with cmd.update_context(instance.sku) as c:
        c.set_param('name', sku)
        c.set_param('tier', sku)

    with cmd.update_context(instance) as c:
        c.set_param('gateway_default_site', SubResource(id=gateway_default_site) if gateway_default_site else None)
        c.set_param('vpn_type', vpn_type)
        c.set_param('tags', tags)

    subnet_id = '{}/subnets/GatewaySubnet'.format(virtual_network) if virtual_network else \
        instance.ip_configurations[0].subnet.id
    if virtual_network is not None:
        for config in instance.ip_configurations:
            config.subnet.id = subnet_id

    if public_ip_address is not None:
        instance.ip_configurations = []
        for i, public_ip in enumerate(public_ip_address):
            ip_configuration = VirtualNetworkGatewayIPConfiguration(
                subnet=SubResource(id=subnet_id),
                public_ip_address=SubResource(id=public_ip),
                private_ip_allocation_method='Dynamic', name='vnetGatewayConfig{}'.format(i))
            instance.ip_configurations.append(ip_configuration)

        # Update active-active/active-standby status
        active = len(public_ip_address) == 2
        if instance.active and not active:
            logger.info('Placing gateway in active-standby mode.')
        elif not instance.active and active:
            logger.info('Placing gateway in active-active mode.')
        instance.active = active

    if gateway_type is not None:
        instance.gateway_type = gateway_type

    if enable_bgp is not None:
        instance.enable_bgp = enable_bgp.lower() == 'true'

    if custom_routes and cmd.supported_api_version(min_api='2019-02-01'):
        if not instance.custom_routes:
            instance.custom_routes = AddressSpace()
        instance.custom_routes.address_prefixes = custom_routes

    _validate_bgp_peering(cmd, instance, asn, bgp_peering_address, peer_weight)

    return instance


def start_vnet_gateway_package_capture(cmd, client, resource_group_name, virtual_network_gateway_name,
                                       filter_data=None, no_wait=False):
    VpnPacketCaptureStartParameters = cmd.get_models('VpnPacketCaptureStartParameters')
    parameters = VpnPacketCaptureStartParameters(filter_data=filter_data)
    return sdk_no_wait(no_wait, client.begin_start_packet_capture, resource_group_name,
                       virtual_network_gateway_name, parameters=parameters)


def stop_vnet_gateway_package_capture(cmd, client, resource_group_name, virtual_network_gateway_name,
                                      sas_url, no_wait=False):
    VpnPacketCaptureStopParameters = cmd.get_models('VpnPacketCaptureStopParameters')
    parameters = VpnPacketCaptureStopParameters(sas_url=sas_url)
    return sdk_no_wait(no_wait, client.begin_stop_packet_capture, resource_group_name,
                       virtual_network_gateway_name, parameters=parameters)


def generate_vpn_client(cmd, client, resource_group_name, virtual_network_gateway_name, processor_architecture=None,
                        authentication_method=None, radius_server_auth_certificate=None, client_root_certificates=None,
                        use_legacy=False):
    params = cmd.get_models('VpnClientParameters')(
        processor_architecture=processor_architecture
    )

    if cmd.supported_api_version(min_api='2017-06-01') and not use_legacy:
        params.authentication_method = authentication_method
        params.radius_server_auth_certificate = radius_server_auth_certificate
        params.client_root_certificates = client_root_certificates
        return client.begin_generate_vpn_profile(resource_group_name, virtual_network_gateway_name, params)
    # legacy implementation
    return client.begin_generatevpnclientpackage(resource_group_name, virtual_network_gateway_name, params)


def set_vpn_client_ipsec_policy(cmd, client, resource_group_name, virtual_network_gateway_name,
                                sa_life_time_seconds, sa_data_size_kilobytes,
                                ipsec_encryption, ipsec_integrity,
                                ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    VpnClientIPsecParameters = cmd.get_models('VpnClientIPsecParameters')
    vpnclient_ipsec_params = VpnClientIPsecParameters(sa_life_time_seconds=sa_life_time_seconds,
                                                      sa_data_size_kilobytes=sa_data_size_kilobytes,
                                                      ipsec_encryption=ipsec_encryption,
                                                      ipsec_integrity=ipsec_integrity,
                                                      ike_encryption=ike_encryption,
                                                      ike_integrity=ike_integrity,
                                                      dh_group=dh_group,
                                                      pfs_group=pfs_group)
    return sdk_no_wait(no_wait, client.begin_set_vpnclient_ipsec_parameters, resource_group_name,
                       virtual_network_gateway_name, vpnclient_ipsec_params)


def disconnect_vnet_gateway_vpn_connections(cmd, client, resource_group_name, virtual_network_gateway_name,
                                            vpn_connection_ids, no_wait=False):
    P2SVpnConnectionRequest = cmd.get_models('P2SVpnConnectionRequest')
    request = P2SVpnConnectionRequest(vpn_connection_ids=vpn_connection_ids)
    return sdk_no_wait(no_wait, client.begin_disconnect_virtual_network_gateway_vpn_connections,
                       resource_group_name, virtual_network_gateway_name, request)

# endregion


# region VirtualNetworkGatewayConnections
# pylint: disable=too-many-locals
def create_vpn_connection(cmd, resource_group_name, connection_name, vnet_gateway1,
                          location=None, tags=None, no_wait=False, validate=False,
                          vnet_gateway2=None, express_route_circuit2=None, local_gateway2=None,
                          authorization_key=None, enable_bgp=False, routing_weight=10,
                          connection_type=None, shared_key=None,
                          use_policy_based_traffic_selectors=False,
                          express_route_gateway_bypass=None, ingress_nat_rule=None, egress_nat_rule=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network.azure_stack._template_builder import build_vpn_connection_resource

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    tags = tags or {}

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    vpn_connection_resource = build_vpn_connection_resource(
        cmd, connection_name, location, tags, vnet_gateway1,
        vnet_gateway2 or local_gateway2 or express_route_circuit2,
        connection_type, authorization_key, enable_bgp, routing_weight, shared_key,
        use_policy_based_traffic_selectors, express_route_gateway_bypass, ingress_nat_rule, egress_nat_rule)
    master_template.add_resource(vpn_connection_resource)
    master_template.add_output('resource', connection_name, output_type='object')
    if shared_key:
        master_template.add_secure_parameter('sharedKey', shared_key)
    if authorization_key:
        master_template.add_secure_parameter('authorizationKey', authorization_key)

    template = master_template.build()
    parameters = master_template.build_parameters()

    # deploy ARM template
    deployment_name = 'vpn_connection_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def list_vpn_connections(cmd, resource_group_name, virtual_network_gateway_name=None):
    if virtual_network_gateway_name:
        client = network_client_factory(cmd.cli_ctx).virtual_network_gateways
        return client.list_connections(resource_group_name, virtual_network_gateway_name)
    client = network_client_factory(cmd.cli_ctx).virtual_network_gateway_connections
    return client.list(resource_group_name)


def start_vpn_conn_package_capture(cmd, client, resource_group_name, virtual_network_gateway_connection_name,
                                   filter_data=None, no_wait=False):
    VpnPacketCaptureStartParameters = cmd.get_models('VpnPacketCaptureStartParameters')
    parameters = VpnPacketCaptureStartParameters(filter_data=filter_data)
    return sdk_no_wait(no_wait, client.begin_start_packet_capture, resource_group_name,
                       virtual_network_gateway_connection_name, parameters=parameters)


def stop_vpn_conn_package_capture(cmd, client, resource_group_name, virtual_network_gateway_connection_name,
                                  sas_url, no_wait=False):
    VpnPacketCaptureStopParameters = cmd.get_models('VpnPacketCaptureStopParameters')
    parameters = VpnPacketCaptureStopParameters(sas_url=sas_url)
    return sdk_no_wait(no_wait, client.begin_stop_packet_capture, resource_group_name,
                       virtual_network_gateway_connection_name, parameters=parameters)


def show_vpn_connection_device_config_script(cmd, client, resource_group_name, virtual_network_gateway_connection_name,
                                             vendor, device_family, firmware_version):
    VpnDeviceScriptParameters = cmd.get_models('VpnDeviceScriptParameters')
    parameters = VpnDeviceScriptParameters(
        vendor=vendor,
        device_family=device_family,
        firmware_version=firmware_version
    )
    return client.vpn_device_configuration_script(resource_group_name, virtual_network_gateway_connection_name,
                                                  parameters=parameters)
# endregion


# region IPSec Policy Commands
def add_vnet_gateway_ipsec_policy(cmd, resource_group_name, gateway_name,
                                  sa_life_time_seconds, sa_data_size_kilobytes,
                                  ipsec_encryption, ipsec_integrity,
                                  ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    IpsecPolicy = cmd.get_models('IpsecPolicy')
    new_policy = IpsecPolicy(sa_life_time_seconds=sa_life_time_seconds,
                             sa_data_size_kilobytes=sa_data_size_kilobytes,
                             ipsec_encryption=ipsec_encryption,
                             ipsec_integrity=ipsec_integrity,
                             ike_encryption=ike_encryption,
                             ike_integrity=ike_integrity,
                             dh_group=dh_group,
                             pfs_group=pfs_group)

    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    try:
        if gateway.vpn_client_configuration.vpn_client_ipsec_policies:
            gateway.vpn_client_configuration.vpn_client_ipsec_policies.append(new_policy)
        else:
            gateway.vpn_client_configuration.vpn_client_ipsec_policies = [new_policy]
    except AttributeError:
        raise CLIError('VPN client configuration must first be set through `az network vnet-gateway create/update`.')
    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def clear_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    try:
        gateway.vpn_client_configuration.vpn_client_ipsec_policies = None
    except AttributeError:
        raise CLIError('VPN client configuration must first be set through `az network vnet-gateway create/update`.')
    if no_wait:
        return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)

    from azure.cli.core.commands import LongRunningOperation
    poller = sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)
    return LongRunningOperation(cmd.cli_ctx)(poller).vpn_client_configuration.vpn_client_ipsec_policies


def list_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    try:
        return ncf.get(resource_group_name, gateway_name).vpn_client_configuration.vpn_client_ipsec_policies
    except AttributeError:
        raise CLIError('VPN client configuration must first be set through `az network vnet-gateway create/update`.')


def add_vpn_conn_ipsec_policy(cmd, client, resource_group_name, connection_name,
                              sa_life_time_seconds, sa_data_size_kilobytes,
                              ipsec_encryption, ipsec_integrity,
                              ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    IpsecPolicy = cmd.get_models('IpsecPolicy')
    new_policy = IpsecPolicy(sa_life_time_seconds=sa_life_time_seconds,
                             sa_data_size_kilobytes=sa_data_size_kilobytes,
                             ipsec_encryption=ipsec_encryption,
                             ipsec_integrity=ipsec_integrity,
                             ike_encryption=ike_encryption,
                             ike_integrity=ike_integrity,
                             dh_group=dh_group,
                             pfs_group=pfs_group)

    conn = client.get(resource_group_name, connection_name)
    if conn.ipsec_policies:
        conn.ipsec_policies.append(new_policy)
    else:
        conn.ipsec_policies = [new_policy]
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, connection_name, conn)


def assign_vnet_gateway_aad(cmd, resource_group_name, gateway_name,
                            aad_tenant, aad_audience, aad_issuer, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    if gateway.vpn_client_configuration is None:
        raise CLIError('VPN client configuration must be set first through `az network vnet-gateway create/update`.')

    gateway.vpn_client_configuration.aad_tenant = aad_tenant
    gateway.vpn_client_configuration.aad_audience = aad_audience
    gateway.vpn_client_configuration.aad_issuer = aad_issuer

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def show_vnet_gateway_aad(cmd, resource_group_name, gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    if gateway.vpn_client_configuration is None:
        raise CLIError('VPN client configuration must be set first through `az network vnet-gateway create/update`.')

    return gateway.vpn_client_configuration


def remove_vnet_gateway_aad(cmd, resource_group_name, gateway_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    if gateway.vpn_client_configuration is None:
        raise CLIError('VPN client configuration must be set first through `az network vnet-gateway create/update`.')

    gateway.vpn_client_configuration.aad_tenant = None
    gateway.vpn_client_configuration.aad_audience = None
    gateway.vpn_client_configuration.aad_issuer = None
    if cmd.supported_api_version(min_api='2020-11-01'):
        gateway.vpn_client_configuration.vpn_authentication_types = None

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def add_vnet_gateway_nat_rule(cmd, resource_group_name, gateway_name, name, internal_mappings, external_mappings,
                              rule_type=None, mode=None, ip_config_id=None, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    VirtualNetworkGatewayNatRule, VpnNatRuleMapping = cmd.get_models('VirtualNetworkGatewayNatRule',
                                                                     'VpnNatRuleMapping')
    gateway.nat_rules.append(
        VirtualNetworkGatewayNatRule(type_properties_type=rule_type, mode=mode, name=name,
                                     internal_mappings=[VpnNatRuleMapping(address_space=i_map) for i_map in internal_mappings] if internal_mappings else None,
                                     external_mappings=[VpnNatRuleMapping(address_space=e_map) for e_map in external_mappings] if external_mappings else None,
                                     ip_configuration_id=ip_config_id))

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def show_vnet_gateway_nat_rule(cmd, resource_group_name, gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    return gateway.nat_rules


def remove_vnet_gateway_nat_rule(cmd, resource_group_name, gateway_name, name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    for rule in gateway.nat_rules:
        if name == rule.name:
            gateway.nat_rules.remove(rule)
            return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)

    raise UnrecognizedArgumentError(f'Do not find nat_rules named {name}!!!')
# endregion


# region VirtualHub
def create_virtual_hub(cmd, client,
                       resource_group_name,
                       virtual_hub_name,
                       hosted_subnet,
                       public_ip_address,
                       location=None,
                       tags=None):
    from azure.core.exceptions import HttpResponseError
    from azure.cli.core.commands import LongRunningOperation

    try:
        client.get(resource_group_name, virtual_hub_name)
        raise CLIError('The VirtualHub "{}" under resource group "{}" exists'.format(
            virtual_hub_name, resource_group_name))
    except HttpResponseError:
        pass

    SubResource = cmd.get_models('SubResource')

    VirtualHub, HubIpConfiguration, PublicIPAddress = cmd.get_models('VirtualHub', 'HubIpConfiguration',
                                                                     'PublicIPAddress')

    hub = VirtualHub(tags=tags, location=location,
                     virtual_wan=None,
                     sku='Standard')
    vhub_poller = client.begin_create_or_update(resource_group_name, virtual_hub_name, hub)
    LongRunningOperation(cmd.cli_ctx)(vhub_poller)

    ip_config = HubIpConfiguration(
        subnet=SubResource(id=hosted_subnet),
        public_ip_address=PublicIPAddress(id=public_ip_address)
    )
    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration
    try:
        vhub_ip_poller = vhub_ip_config_client.begin_create_or_update(
            resource_group_name, virtual_hub_name, 'Default', ip_config)
        LongRunningOperation(cmd.cli_ctx)(vhub_ip_poller)
    except Exception as ex:
        logger.error(ex)
        try:
            vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, 'Default')
        except HttpResponseError:
            pass
        client.begin_delete(resource_group_name, virtual_hub_name)
        raise ex

    return client.get(resource_group_name, virtual_hub_name)


def delete_virtual_hub(cmd, client, resource_group_name, virtual_hub_name, no_wait=False):
    from azure.cli.core.commands import LongRunningOperation
    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration
    ip_configs = list(vhub_ip_config_client.list(resource_group_name, virtual_hub_name))
    if ip_configs:
        ip_config = ip_configs[0]   # There will always be only 1
        poller = vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, ip_config.name)
        LongRunningOperation(cmd.cli_ctx)(poller)
    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, virtual_hub_name)
# endregion


# region VirtualRouter
def create_virtual_router(cmd,
                          resource_group_name,
                          virtual_router_name,
                          hosted_gateway=None,
                          hosted_subnet=None,
                          location=None,
                          tags=None):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs

    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        pass

    virtual_hub_name = virtual_router_name
    try:
        vhub_client.get(resource_group_name, virtual_hub_name)
        raise CLIError('The VirtualRouter "{}" under resource group "{}" exists'.format(virtual_hub_name,
                                                                                        resource_group_name))
    except HttpResponseError:
        pass

    SubResource = cmd.get_models('SubResource')

    # for old VirtualRouter
    if hosted_gateway is not None:
        VirtualRouter = cmd.get_models('VirtualRouter')
        virtual_router = VirtualRouter(virtual_router_asn=None,
                                       virtual_router_ips=[],
                                       hosted_subnet=None,
                                       hosted_gateway=SubResource(id=hosted_gateway),
                                       location=location,
                                       tags=tags)
        return vrouter_client.begin_create_or_update(resource_group_name, virtual_router_name, virtual_router)

    # for VirtualHub
    VirtualHub, HubIpConfiguration = cmd.get_models('VirtualHub', 'HubIpConfiguration')

    hub = VirtualHub(tags=tags, location=location, virtual_wan=None, sku='Standard')
    ip_config = HubIpConfiguration(subnet=SubResource(id=hosted_subnet))

    from azure.cli.core.commands import LongRunningOperation

    vhub_poller = vhub_client.begin_create_or_update(resource_group_name, virtual_hub_name, hub)
    LongRunningOperation(cmd.cli_ctx)(vhub_poller)

    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration
    try:
        vhub_ip_poller = vhub_ip_config_client.begin_create_or_update(resource_group_name,
                                                                      virtual_hub_name,
                                                                      'Default',
                                                                      ip_config)
        LongRunningOperation(cmd.cli_ctx)(vhub_ip_poller)
    except Exception as ex:
        logger.error(ex)
        vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, 'Default')
        vhub_client.begin_delete(resource_group_name, virtual_hub_name)
        raise ex

    return vhub_client.get(resource_group_name, virtual_hub_name)


def virtual_router_update_getter(cmd, resource_group_name, virtual_router_name):
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        return vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:  # 404
        pass

    virtual_hub_name = virtual_router_name
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
    return vhub_client.get(resource_group_name, virtual_hub_name)


def virtual_router_update_setter(cmd, resource_group_name, virtual_router_name, parameters):
    if parameters.type == 'Microsoft.Network/virtualHubs':
        client = network_client_factory(cmd.cli_ctx).virtual_hubs
    else:
        client = network_client_factory(cmd.cli_ctx).virtual_routers

    # If the client is virtual_hubs,
    # the virtual_router_name represents virtual_hub_name and
    # the parameters represents VirtualHub
    return client.begin_create_or_update(resource_group_name, virtual_router_name, parameters)


def update_virtual_router(cmd, instance, tags=None):
    # both VirtualHub and VirtualRouter own those properties
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance


def list_virtual_router(cmd, resource_group_name=None):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs

    if resource_group_name is not None:
        vrouters = vrouter_client.list_by_resource_group(resource_group_name)
        vhubs = vhub_client.list_by_resource_group(resource_group_name)
    else:
        vrouters = vrouter_client.list()
        vhubs = vhub_client.list()

    return list(vrouters) + list(vhubs)


def show_virtual_router(cmd, resource_group_name, virtual_router_name):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs

    from azure.core.exceptions import HttpResponseError
    try:
        item = vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        virtual_hub_name = virtual_router_name
        item = vhub_client.get(resource_group_name, virtual_hub_name)

    return item


def delete_virtual_router(cmd, resource_group_name, virtual_router_name):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration

    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client.get(resource_group_name, virtual_router_name)
        item = vrouter_client.begin_delete(resource_group_name, virtual_router_name)
    except HttpResponseError:
        from azure.cli.core.commands import LongRunningOperation

        virtual_hub_name = virtual_router_name
        poller = vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, 'Default')
        LongRunningOperation(cmd.cli_ctx)(poller)

        item = vhub_client.begin_delete(resource_group_name, virtual_hub_name)

    return item


def create_virtual_router_peering(cmd, resource_group_name, virtual_router_name, peering_name, peer_asn, peer_ip):

    # try VirtualRouter first
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        pass
    else:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        VirtualRouterPeering = cmd.get_models('VirtualRouterPeering')
        virtual_router_peering = VirtualRouterPeering(peer_asn=peer_asn, peer_ip=peer_ip)
        return vrouter_peering_client.begin_create_or_update(resource_group_name,
                                                             virtual_router_name,
                                                             peering_name,
                                                             virtual_router_peering)

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    # try VirtualHub then if the virtual router doesn't exist
    try:
        vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
        vhub_client.get(resource_group_name, virtual_hub_name)
    except HttpResponseError:
        msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                      resource_group_name)
        raise CLIError(msg)

    BgpConnection = cmd.get_models('BgpConnection')
    vhub_bgp_conn = BgpConnection(name=peering_name, peer_asn=peer_asn, peer_ip=peer_ip)

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.begin_create_or_update(resource_group_name, virtual_hub_name,
                                                       bgp_conn_name, vhub_bgp_conn)


def virtual_router_peering_update_getter(cmd, resource_group_name, virtual_router_name, peering_name):
    vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings

    from azure.core.exceptions import HttpResponseError
    try:
        return vrouter_peering_client.get(resource_group_name, virtual_router_name, peering_name)
    except HttpResponseError:  # 404
        pass

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.get(resource_group_name, virtual_hub_name, bgp_conn_name)


def virtual_router_peering_update_setter(cmd, resource_group_name, virtual_router_name, peering_name, parameters):
    if parameters.type == 'Microsoft.Network/virtualHubs/bgpConnections':
        client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    else:
        client = network_client_factory(cmd.cli_ctx).virtual_router_peerings

    # if the client is virtual_hub_bgp_connection,
    # the virtual_router_name represents virtual_hub_name and
    # the peering_name represents bgp_connection_name and
    # the parameters represents BgpConnection
    return client.begin_create_or_update(resource_group_name, virtual_router_name, peering_name, parameters)


def update_virtual_router_peering(cmd, instance, peer_asn=None, peer_ip=None):
    # both VirtualHub and VirtualRouter own those properties
    with cmd.update_context(instance) as c:
        c.set_param('peer_asn', peer_asn)
        c.set_param('peer_ip', peer_ip)
    return instance


def list_virtual_router_peering(cmd, resource_group_name, virtual_router_name):
    virtual_hub_name = virtual_router_name

    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        try:
            vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
            vhub_client.get(resource_group_name, virtual_hub_name)
        except HttpResponseError:
            msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                          resource_group_name)
            raise CLIError(msg)

    try:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        vrouter_peerings = list(vrouter_peering_client.list(resource_group_name, virtual_router_name))
    except HttpResponseError:
        vrouter_peerings = []

    virtual_hub_name = virtual_router_name
    try:
        vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connections
        vhub_bgp_connections = list(vhub_bgp_conn_client.list(resource_group_name, virtual_hub_name))
    except HttpResponseError:
        vhub_bgp_connections = []

    return list(vrouter_peerings) + list(vhub_bgp_connections)


def show_virtual_router_peering(cmd, resource_group_name, virtual_router_name, peering_name):
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        pass
    else:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        return vrouter_peering_client.get(resource_group_name, virtual_router_name, peering_name)

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    # try VirtualHub then if the virtual router doesn't exist
    try:
        vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
        vhub_client.get(resource_group_name, virtual_hub_name)
    except HttpResponseError:
        msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                      resource_group_name)
        raise CLIError(msg)

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.get(resource_group_name, virtual_hub_name, bgp_conn_name)


def delete_virtual_router_peering(cmd, resource_group_name, virtual_router_name, peering_name):
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except:  # pylint: disable=bare-except
        pass
    else:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        return vrouter_peering_client.begin_delete(resource_group_name, virtual_router_name, peering_name)

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    # try VirtualHub then if the virtual router doesn't exist
    try:
        vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
        vhub_client.get(resource_group_name, virtual_hub_name)
    except HttpResponseError:
        msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                      resource_group_name)
        raise CLIError(msg)

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.begin_delete(resource_group_name, virtual_hub_name, bgp_conn_name)
# endregion


# region network gateway connection
def reset_shared_key(cmd, client, virtual_network_gateway_connection_name, key_length, resource_group_name=None):
    ConnectionResetSharedKey = cmd.get_models('ConnectionResetSharedKey')
    shared_key = ConnectionResetSharedKey(key_length=key_length)
    return client.begin_reset_shared_key(resource_group_name=resource_group_name,
                                         virtual_network_gateway_connection_name=virtual_network_gateway_connection_name,  # pylint: disable=line-too-long
                                         parameters=shared_key)


def update_shared_key(cmd, instance, value):
    with cmd.update_context(instance) as c:
        c.set_param('value', value)
    return instance
# endregion
