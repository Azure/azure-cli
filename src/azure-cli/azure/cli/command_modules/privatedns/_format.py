# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict


def transform_privatedns_zone_table_output(result):
    is_list = isinstance(result, list)

    if not is_list:
        result = [result]

    final_result = []
    for item in result:
        new_item = OrderedDict([
            ('ZoneName', item['name']),
            ('ResourceGroup', item['resourceGroup']),
            ('RecordSets', item['numberOfRecordSets']),
            ('MaxRecordSets', item['maxNumberOfRecordSets']),
            ('VirtualNetworkLinks', item['numberOfVirtualNetworkLinks']),
            ('MaxVirtualNetworkLinks', item['maxNumberOfVirtualNetworkLinks']),
            ('VirtualNetworkLinksWithRegistration', item['numberOfVirtualNetworkLinksWithRegistration']),
            ('MaxVirtualNetworkLinksWithRegistration', item['maxNumberOfVirtualNetworkLinksWithRegistration']),
            ('ProvisioningState', item['provisioningState'])
        ])
        final_result.append(new_item)

    return final_result if is_list else final_result[0]


def transform_privatedns_link_table_output(result):
    is_list = isinstance(result, list)

    if not is_list:
        result = [result]

    final_result = []
    for item in result:
        new_item = OrderedDict([
            ('LinkName', item['name']),
            ('ResourceGroup', item['resourceGroup']),
            ('RegistrationEnabled', item['registrationEnabled']),
            ('VirtualNetwork', item['virtualNetwork']['id']),
            ('LinkState', item['virtualNetworkLinkState']),
            ('ProvisioningState', item['provisioningState'])
        ])
        final_result.append(new_item)

    return final_result if is_list else final_result[0]


def transform_privatedns_record_set_output(result):
    from azure.mgmt.privatedns.models import RecordSetListResult

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


def transform_privatedns_record_set_table_output(result):
    table_output = []

    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item['name']
        table_row['ResourceGroup'] = item['resourceGroup']
        table_row['Ttl'] = item['ttl']
        table_row['Type'] = item['type'].rsplit('/', 1)[1]
        table_row['AutoRegistered'] = item['isAutoRegistered']
        metadata = item['metadata']
        if metadata:
            table_row['Metadata'] = ' '.join(['{}="{}"'.format(x, metadata[x]) for x in sorted(metadata)])
        else:
            table_row['Metadata'] = ' '
        table_output.append(table_row)
    return table_output
