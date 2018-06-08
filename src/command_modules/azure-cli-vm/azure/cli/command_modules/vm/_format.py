# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def transform_ip_addresses(result):
    from collections import OrderedDict
    transformed = []
    for r in result:
        network = r['virtualMachine']['network']
        public = network.get('publicIpAddresses')
        public_ip_addresses = ','.join([p['ipAddress'] for p in public if p['ipAddress']]) if public else None
        private = network.get('privateIpAddresses')
        private_ip_addresses = ','.join(private) if private else None
        entry = OrderedDict([('virtualMachine', r['virtualMachine']['name']),
                             ('publicIPAddresses', public_ip_addresses),
                             ('privateIPAddresses', private_ip_addresses)])
        transformed.append(entry)

    return transformed


def transform_vm(vm):
    from collections import OrderedDict
    result = OrderedDict([('name', vm['name']),
                          ('resourceGroup', vm['resourceGroup']),
                          ('powerState', vm.get('powerState')),
                          ('publicIps', vm.get('publicIps')),
                          ('fqdns', vm.get('fqdns')),
                          ('location', vm['location'])])
    if 'zones' in vm:
        result['zones'] = ','.join(vm['zones']) if vm['zones'] else ''
    return result


def transform_vm_create_output(result):
    from msrestazure.tools import parse_resource_id
    from collections import OrderedDict
    try:
        resource_group = getattr(result, 'resource_group', None) or parse_resource_id(result.id)['resource_group']
        output = OrderedDict([('id', result.id),
                              ('resourceGroup', resource_group),
                              ('powerState', result.power_state),
                              ('publicIpAddress', result.public_ips),
                              ('fqdns', result.fqdns),
                              ('privateIpAddress', result.private_ips),
                              ('macAddress', result.mac_addresses),
                              ('location', result.location)])
        if getattr(result, 'identity', None):
            output['identity'] = result.identity
        if hasattr(result, 'zones'):  # output 'zones' column even the property value is None
            output['zones'] = result.zones[0] if result.zones else ''
        return output
    except AttributeError:
        from msrest.pipeline import ClientRawResponse
        return None if isinstance(result, ClientRawResponse) else result


def transform_vm_usage_list(result):
    result = list(result)
    for item in result:
        item.current_value = str(item.current_value)
        item.limit = str(item.limit)
        item.local_name = item.name.localized_value
    return result


def transform_vm_list(vm_list):
    return [transform_vm(v) for v in vm_list]


# flattern out important fields (single member arrays) to be displayed in the table output
def transform_sku_for_table_output(skus):
    from collections import OrderedDict
    result = []
    for k in skus:
        order_dict = OrderedDict()
        order_dict['resourceType'] = k['resourceType']
        order_dict['locations'] = str(k['locations']) if len(k['locations']) > 1 else k['locations'][0]
        order_dict['name'] = k['name']
        if k.get('locationInfo'):
            order_dict['zones'] = ','.join(sorted(k['locationInfo'][0].get('zones', [])))
        order_dict['tier'] = k['tier']
        order_dict['size'] = k['size']
        if k['capabilities']:
            temp = ['{}={}'.format(pair['name'], pair['value']) for pair in k['capabilities']]
            order_dict['capabilities'] = str(temp) if len(temp) > 1 else temp[0]
        else:
            order_dict['capabilities'] = None
        if k['restrictions']:
            reasons = [x['reasonCode'] for x in k['restrictions']]
            order_dict['restrictions'] = str(reasons) if len(reasons) > 1 else reasons[0]
        else:
            order_dict['restrictions'] = None
        result.append(order_dict)
    return result


transform_extension_show_table_output = '{Name:name, ProvisioningState:provisioningState, Publisher:publisher, ' \
                                        'Version:typeHandlerVersion, AutoUpgradeMinorVersion:autoUpgradeMinorVersion}'


transform_disk_show_table_output = '{Name:name, ResourceGroup:resourceGroup, Location:location, Zones: ' \
                                   '(!zones && \' \') || join(` `, zones), Sku:sku.name, OsType:osType, ' \
                                   'SizeGb:diskSizeGb, ProvisioningState:provisioningState}'


def get_vmss_table_output_transformer(loader, for_list=True):
    transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Capacity:sku.capacity, ' \
                'Overprovision:overprovision, UpgradePolicy:upgradePolicy.mode}'
    transform = transform.replace('$zone$', 'Zones: (!zones && \' \') || join(\' \', zones), '
                                  if loader.supported_api_version(min_api='2017-03-30') else ' ')
    return transform if not for_list else '[].' + transform
