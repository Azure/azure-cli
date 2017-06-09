# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict


def transform_dns_record_set_output(result):
    from azure.mgmt.dns.models import RecordSetPaged

    def _strip_null_records(item):
        for prop in [x for x in dir(item) if 'record' in x]:
            if not getattr(item, prop):
                delattr(item, prop)

    if isinstance(result, RecordSetPaged):
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


def transform_vpn_connection_list(result):
    return [transform_vpn_connection(v) for v in result]


def transform_vpn_connection(result):
    if result:
        properties_to_strip = \
            ['virtual_network_gateway1', 'virtual_network_gateway2', 'local_network_gateway2', 'peer']
        for prop in properties_to_strip:
            prop_val = getattr(result, prop, None)
            if not prop_val:
                delattr(result, prop)
            else:
                null_props = [key for key in prop_val.__dict__ if not prop_val.__dict__[key]]
                for null_prop in null_props:
                    delattr(prop_val, null_prop)
    return result


def transform_vpn_connection_create_output(result):
    from azure.cli.core.commands import DeploymentOutputLongRunningOperation
    from msrest.pipeline import ClientRawResponse
    from msrestazure.azure_operation import AzureOperationPoller
    if isinstance(result, AzureOperationPoller):
        # normally returns a LRO poller
        result = DeploymentOutputLongRunningOperation('Starting network vpn-connection create')(result)
        return result['resource']
    elif isinstance(result, ClientRawResponse):
        # returns a raw response if --no-wait used
        return

    # returns a plain response (not a poller) if --validate used
    return result


def transform_vnet_create_output(result):
    return {'newVNet': result.result()}


def transform_public_ip_create_output(result):
    return {'publicIp': result.result()}


def transform_traffic_manager_create_output(result):
    return {'TrafficManagerProfile': result}


def transform_nic_create_output(result):
    return {'NewNIC': result.result()}


def transform_nsg_create_output(result):
    return {'NewNSG': result.result()}


def transform_vnet_gateway_create_output(result):
    return {'vnetGateway': result.result()}


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


def transform_network_usage_list(result):
    result = list(result)
    for item in result:
        item.current_value = str(item.current_value)
        item.limit = str(item.limit)
        item.local_name = item.name.localized_value
    return result


def transform_network_usage_table(result):
    transformed = []
    for item in result:
        transformed.append(OrderedDict([
            ('Name', item['localName']),
            ('CurrentValue', item['currentValue']),
            ('Limit', item['limit'])
        ]))
    return transformed
