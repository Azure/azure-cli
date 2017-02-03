# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=line-too-long

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
