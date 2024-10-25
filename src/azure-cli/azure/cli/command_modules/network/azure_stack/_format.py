# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict


def transform_dns_record_set_output(result):
    from azure.mgmt.dns.models import RecordSetListResult

    def _strip_null_records(item):
        for prop in [x for x in dir(item) if 'record' in x]:
            if not getattr(item, prop):
                delattr(item, prop)

    if isinstance(result, RecordSetListResult):
        result = list(result)
        for item in result:
            _strip_null_records(item)
    else:
        _strip_null_records(result)

    return result


def transform_dns_record_set_table_output(result):
    table_output = []

    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item['name']
        table_row['ResourceGroup'] = item['resourceGroup']
        table_row['Ttl'] = item['ttl']
        table_row['Type'] = item['type'].rsplit('/', 1)[1]
        metadata = item['metadata']
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
        item['DDOSProtection'] = result['enableDdosProtection']
        item['VMProtection'] = result['enableVmProtection']
        return item
    if isinstance(result, list):
        return [_transform(r) for r in result]
    return _transform(result)


def transform_public_ip_create_output(result):
    return {'publicIp': result.result()}


def transform_nsg_rule_table_output(result):
    item = OrderedDict()
    item['Name'] = result['name']
    item['ResourceGroup'] = result['resourceGroup']
    item['Priority'] = result['priority']
    item['Access'] = result['access']
    item['Protocol'] = result['protocol']
    item['Direction'] = result['direction']
    if 'SourcePortRanges' in result:
        item['SourcePortRanges'] = result.get('sourcePortRange', ' '.join(result['sourcePortRanges']))
    if 'SourceAddressPrefixes' in result:
        item['SourceAddressPrefixes'] = result.get('sourceAddressPrefix', ' '.join(result['sourceAddressPrefixes']))
    if 'SourceASG' in result:
        item['SourceASG'] = result.get('sourceApplicationSecurityGroups', 'None')
    if 'DestinationPortRanges' in result:
        item['DestinationPortRanges'] = result.get('destinationPortRange', ' '.join(result['destinationPortRanges']))
    if 'DestinationAddressPrefixes' in result:
        item['DestinationAddressPrefixes'] = result.get('destinationAddressPrefix',
                                                        ' '.join(result['destinationAddressPrefixes']))
    if 'DestinationASG' in result:
        item['DestinationASG'] = result.get('destinationApplicationSecurityGroups', 'None')
    return item


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
            ('Address Prefix', ' '.join(item['addressPrefix'] or [])),
            ('Next Hop Type', item['nextHopType']),
            ('Next Hop IP', ' '.join(item['nextHopIpAddress'] or []))
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
