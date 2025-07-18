# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
#
# pylint: disable=line-too-long
from collections import OrderedDict


def transform_dns_record_set_output(result):
    for prop in [x for x in dir(result) if 'record' in x]:
        if not getattr(result, prop):
            delattr(result, prop)

    return result


def transform_dns_record_set_table_output(result):
    table_output = []

    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item['name']
        table_row['ResourceGroup'] = item['resourceGroup']
        table_row['Ttl'] = item.get('ttl') or item.get('TTL')
        table_row['Type'] = item['type'].rsplit('/', 1)[1]
        metadata = item.get('metadata')
        if metadata:
            table_row['Metadata'] = ' '.join(['{}="{}"'.format(x, metadata[x]) for x in sorted(metadata)])
        else:
            table_row['Metadata'] = ' '
        table_output.append(table_row)
    return table_output


def transform_dns_zone_table_output(result):
    is_list = isinstance(result, list)

    if not is_list:
        result = [result]

    final_result = []
    for item in result:
        new_item = OrderedDict([
            ('ZoneName', item['name']),
            ('ResourceGroup', item['resourceGroup']),
            ('RecordSets', item['numberOfRecordSets']),
            ('MaxRecordSets', item['maxNumberOfRecordSets'])
        ])
        final_result.append(new_item)

    return final_result if is_list else final_result[0]


def transform_local_gateway_table_output(result):
    final_result = []
    for item in result:
        new_item = OrderedDict([
            ('Name', item['name']), ('Location', item['location']),
            ('ResourceGroup', item['resourceGroup']),
            ('ProvisioningState', item['provisioningState']),
            ('GatewayIpAddress', item['gatewayIpAddress'])
        ])
        try:
            local_prefixes = item['localNetworkAddressSpace']['addressPrefixes'] or [' ']
        except TypeError:
            local_prefixes = [' ']
        prefix_val = '{}{}'.format(local_prefixes[0], ', ...' if len(local_prefixes) > 1 else '')
        new_item['AddressPrefixes'] = prefix_val
        final_result.append(new_item)
    return final_result


def transform_vnet_table_output(result):

    def _transform(result):
        item = OrderedDict()
        item['Name'] = result['name']
        item['ResourceGroup'] = result['resourceGroup']
        item['Location'] = result['location']
        item['NumSubnets'] = len(result.get('subnets', []))
        item['Prefixes'] = ', '.join(result['addressSpace']['addressPrefixes']) or ' '
        item['DnsServers'] = ', '.join((result.get('dhcpOptions') or {}).get('dnsServers', [])) or ' '
        item["DDOSProtection"] = result.get("enableDdosProtection", " ")
        item["VMProtection"] = result.get("enableVmProtection", " ")
        return item
    if isinstance(result, list):
        return [_transform(r) for r in result]
    return _transform(result)


def transform_public_ip_create_output(result):
    return {'publicIp': result.result()}


def transform_traffic_manager_create_output(result):
    return {'TrafficManagerProfile': result}


def transform_nsg_rule_table_output(result):
    item = OrderedDict()
    item['Name'] = result['name']
    item['ResourceGroup'] = result['resourceGroup']
    item['Priority'] = result['priority']
    item['SourcePortRanges'] = result.get('sourcePortRange', None) or ' '.join(result['sourcePortRanges'])
    item['SourceAddressPrefixes'] = result.get('sourceAddressPrefix', None) or ' '.join(result['sourceAddressPrefixes'])
    item['SourceASG'] = result.get('sourceApplicationSecurityGroups', None) or 'None'
    item['Access'] = result['access']
    item['Protocol'] = result['protocol']
    item['Direction'] = result['direction']
    item['DestinationPortRanges'] = result.get('destinationPortRange', None) or ' '.join(result['destinationPortRanges'])
    item['DestinationAddressPrefixes'] = result.get('destinationAddressPrefix', None) or ' '.join(result['destinationAddressPrefixes'])
    item['DestinationASG'] = result.get('destinationApplicationSecurityGroups', None) or 'None'
    return item


def transform_geographic_hierachy_table_output(result):
    transformed = []

    def _extract_values(obj):
        obj = obj if isinstance(obj, list) else [obj]
        for item in obj:
            item_obj = OrderedDict()
            item_obj['code'] = item['code']
            item_obj['name'] = item['name']
            transformed.append(item_obj)
            _extract_values(item['regions'])

    _extract_values(result['geographicHierarchy'])
    return transformed


def transform_service_community_table_output(result):
    transformed = []
    for item in result:
        service_name = item['serviceName']
        for community in item['bgpCommunities']:
            item_obj = OrderedDict()
            item_obj['serviceName'] = service_name
            item_obj['communityValue'] = community['communityValue']
            item_obj['supportedRegion'] = community['serviceSupportedRegion']
            transformed.append(item_obj)
    return transformed


def transform_waf_rule_sets_table_output(result):
    transformed = []
    for item in result:
        rule_set_name = item['name']
        for group in item['ruleGroups']:
            rule_group_name = group['ruleGroupName']
            if group['rules']:
                for rule in group['rules']:
                    item_obj = OrderedDict()
                    item_obj['ruleSet'] = rule_set_name
                    item_obj['ruleGroup'] = rule_group_name
                    item_obj['ruleId'] = rule['ruleId']
                    item_obj['description'] = rule['description']
                    transformed.append(item_obj)
            else:
                item_obj = OrderedDict()
                item_obj['ruleSet'] = rule_set_name
                item_obj['ruleGroup'] = rule_group_name
                transformed.append(item_obj)
    return transformed


def transform_network_usage_table(result):
    transformed = []
    for item in result:
        transformed.append(OrderedDict([
            ('Name', item['localName']),
            ('CurrentValue', item['currentValue']),
            ('Limit', item['limit'])
        ]))
    return transformed


def transform_effective_route_table(result):
    transformed = []
    for item in result['value']:
        transformed.append(OrderedDict([
            ('Source', item['source']),
            ('State', item['state']),
            ('Address Prefix', ' '.join(item.get('addressPrefix', []))),
            ('Next Hop Type', item['nextHopType']),
            ('Next Hop IP', ' '.join(item.get('nextHopIpAddress', []))),
        ]))
    return transformed


def transform_effective_nsg(result):
    from azure.mgmt.core.tools import parse_resource_id
    transformed = []
    for item in result['value']:
        association = item['association']
        try:
            nic = parse_resource_id(association['networkInterface']['id'])['name']
        except TypeError:
            nic = '-'
        try:
            subnet = parse_resource_id(association['subnet']['id'])['name']
        except TypeError:
            subnet = '-'
        nsg = parse_resource_id(item['networkSecurityGroup']['id'])['name']
        print_names = True
        for rule in item['effectiveSecurityRules']:
            transformed.append(OrderedDict([
                ('NIC', nic if print_names else ' '),
                ('Subnet', subnet if print_names else ' '),
                ('NSG', nsg if print_names else ' '),
                ('Rule Name', rule.get('name', '')),
                ('Protocol', rule.get('protocol', '')),
                ('Direction', rule.get('direction', '')),
                ('Access', rule.get('access', ''))
            ]))
            print_names = False
    return transformed


def transform_vnet_gateway_routes_table(result):
    transformed = []
    for item in result.get('value', []):
        transformed.append(OrderedDict([
            ('Network', item.get('network', '')),
            ('NextHop', item.get('nextHop', '')),
            ('Origin', item.get('origin', '')),
            ('SourcePeer', item.get('sourcePeer', '')),
            ('AsPath', item.get('asPath', '')),
            ('Weight', item.get('weight', ''))
        ]))
    return transformed


def transform_vnet_gateway_bgp_peer_table(result):
    transformed = []
    for item in result.get('value', []):
        transformed.append(OrderedDict([
            ('Neighbor', item.get('neighbor', '')),
            ('ASN', item.get('asn', '')),
            ('State', item.get('state', '')),
            ('ConnectedDuration', item.get('connectedDuration', '')),
            ('RoutesReceived', item.get('routesReceived', '')),
            ('MessagesSent', item.get('messagesSent', '')),
            ('MessagesReceived', item.get('messagesReceived', ''))
        ]))
    return transformed
