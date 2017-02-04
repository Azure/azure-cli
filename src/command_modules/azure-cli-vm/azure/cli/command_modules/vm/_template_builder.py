# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-arguments

from collections import OrderedDict
import json

from enum import Enum


class ArmTemplateBuilder(object):

    def __init__(self):
        template = OrderedDict()
        template['$schema'] = \
            'https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#'
        template['contentVersion'] = '1.0.0.0'
        template['parameters'] = {}
        template['variables'] = {}
        template['resources'] = []
        template['outputs'] = {}
        self.template = template

    def add_resource(self, resource):
        self.template['resources'].append(resource)

    def add_variable(self, key, value):
        self.template['variables'][key] = value

    def add_parameter(self, key, value):
        self.template['parameters'][key] = value

    def add_id_output(self, key, provider, property_type, property_name):
        new_output = {
            key: {
                'type': 'string',
                'value': "[resourceId('{}/{}', '{}')]".format(
                    provider, property_type, property_name)
            }
        }
        self.template['outputs'].update(new_output)

    def add_output(self, key, property_name, provider=None, property_type=None,
                   output_type='string', path=None):

        if provider and property_type:
            value = "[reference(resourceId('{provider}/{type}', '{property}'),providers('{provider}', '{type}').apiVersions[0])".format(  # pylint: disable=line-too-long
                provider=provider, type=property_type, property=property_name)
        else:
            value = "[reference('{}')".format(property_name)
        value = '{}.{}]'.format(value, path) if path else '{}]'.format(value)
        new_output = {
            key: {
                'type': output_type,
                'value': value
            }
        }
        self.template['outputs'].update(new_output)

    def build(self):
        return json.loads(json.dumps(self.template))


# pylint: disable=too-few-public-methods
class StorageProfile(Enum):
    SAPirImage = 1
    SACustomImage = 2
    ManagedPirImage = 3  # this would be the main scenarios
    ManagedCustomImage = 4
    ManagedSpecializedOSDisk = 5


def build_deployment_resource(name, template, dependencies=None):
    from azure.cli.command_modules.vm._vm_utils import random_string
    dependencies = dependencies or []
    deployment = {
        'name': name,
        'type': 'Microsoft.Resources/deployments',
        'apiVersion': '2015-01-01',
        'dependsOn': dependencies,
        'properties': {
            'mode': 'Incremental',
            'template': template,
        }
    }
    return deployment


def build_output_deployment_resource(key, property_name, property_provider, property_type,
                                     parent_name=None, output_type='object', path=None):
    from azure.cli.command_modules.vm._vm_utils import random_string
    output_tb = ArmTemplateBuilder()
    output_tb.add_output(key, property_name, property_provider, property_type,
                         output_type=output_type, path=path)
    output_template = output_tb.build()

    deployment_name = '{}_{}'.format(property_name, random_string(16))
    deployment = {
        'name': deployment_name,
        'type': 'Microsoft.Resources/deployments',
        'apiVersion': '2015-01-01',
        'properties': {
            'mode': 'Incremental',
            'template': output_template,
        }
    }
    deployment['dependsOn'] = [] if not parent_name \
        else ['Microsoft.Resources/deployments/{}'.format(parent_name)]

    return deployment


def build_storage_account_resource(name, location, tags, sku):
    storage_account = {
        'type': 'Microsoft.Storage/storageAccounts',
        'name': name,
        'apiVersion': '2015-06-15',
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': {'accountType': sku}
    }
    return storage_account


def build_public_ip_resource(name, location, tags, address_allocation, dns_name=None):

    public_ip_properties = {'publicIPAllocationMethod': address_allocation}

    if dns_name:
        public_ip_properties['dnsSettings'] = {'domainNameLabel': dns_name}

    public_ip = {
        'apiVersion': '2015-06-15',
        'type': 'Microsoft.Network/publicIPAddresses',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': public_ip_properties
    }
    return public_ip


def build_nic_resource(name, location, tags, vm_name, subnet_id, private_ip_address=None,
                       nsg_id=None, public_ip_id=None):

    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'
    ip_config_properties = {
        'privateIPAllocationMethod': private_ip_allocation,
        'subnet': {'id': subnet_id}
    }

    if private_ip_address:
        ip_config_properties['privateIPAddress'] = private_ip_address

    if public_ip_id:
        ip_config_properties['publicIPAddress'] = {'id': public_ip_id}

    nic_properties = {
        'ipConfigurations': [
            {
                'name': 'ipconfig{}'.format(vm_name),
                'properties': ip_config_properties
            }
        ]
    }

    if nsg_id:
        nic_properties['networkSecurityGroup'] = {'id': nsg_id}

    nic = {
        'apiVersion': '2015-06-15',
        'type': 'Microsoft.Network/networkInterfaces',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': nic_properties
    }
    return nic


def build_nsg_resource(name, location, tags, nsg_rule_type):

    rule_name = 'rdp' if nsg_rule_type == 'rdp' else 'default-allow-ssh'
    rule_dest_port = '3389' if nsg_rule_type == 'rdp' else '22'

    nsg_properties = {
        'securityRules': [
            {
                'name': rule_name,
                'properties': {
                    'protocol': 'Tcp',
                    'sourcePortRange': '*',
                    'destinationPortRange': rule_dest_port,
                    'sourceAddressPrefix': '*',
                    'destinationAddressPrefix': '*',
                    'access': 'Allow',
                    'priority': 1000,
                    'direction': 'Inbound'
                }
            }
        ]
    }

    nsg = {
        'type': 'Microsoft.Network/networkSecurityGroups',
        'name': name,
        'apiVersion': '2015-06-15',
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': nsg_properties
    }
    return nsg


def build_vnet_resource(name, location, tags, vnet_prefix=None, subnet=None,
                        subnet_prefix=None, dns_servers=None):
    vnet = {
        'name': name,
        'type': 'Microsoft.Network/virtualNetworks',
        'location': location,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'tags': tags,
        'properties': {
            'addressSpace': {'addressPrefixes': [vnet_prefix]},
        }
    }
    if dns_servers:
        vnet['properties']['dhcpOptions'] = {
            'dnsServers': dns_servers
        }
    if subnet:
        vnet['properties']['subnets'] = [{
            'name': subnet,
            'properties': {
                'addressPrefix': subnet_prefix
            }
        }]
    return vnet


def build_vm_resource(  # pylint: disable=too-many-locals
        name, location, tags, size, storage_profile, nics, admin_username,
        availability_set_id=None, admin_password=None, ssh_key_value=None, ssh_key_path=None,
        image_reference=None, os_disk_name=None, custom_image_os_type=None,
        storage_caching=None, storage_sku=None,
        os_publisher=None, os_offer=None, os_sku=None, os_version=None,
        os_vhd_uri=None, managed_os_disk=None, data_disk_sizes_gb=None, image_data_disks=None):

    def _build_os_profile():

        os_profile = {
            'computerName': name,
            'adminUsername': admin_username,
        }

        if admin_password:
            os_profile['adminPassword'] = admin_password

        if ssh_key_value and ssh_key_path:
            os_profile['linuxConfiguration'] = {
                'disablePasswordAuthentication': True,
                'ssh': {
                    'publicKeys': [
                        {
                            'keyData': ssh_key_value,
                            'path': ssh_key_path
                        }
                    ]
                }
            }

        return os_profile

    def _build_storage_profile():

        storage_profiles = {
            'SACustomImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': storage_caching,
                    'osType': custom_image_os_type,
                    'image': {'uri': image_reference},
                    'vhd': {'uri': os_vhd_uri}
                }
            },
            'SAPirImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': storage_caching,
                    'vhd': {'uri': os_vhd_uri}
                },
                'imageReference': {
                    'publisher': os_publisher,
                    'offer': os_offer,
                    'sku': os_sku,
                    'version': os_version
                }
            },
            'ManagedPirImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': storage_caching,
                    'managedDisk': {'storageAccountType': storage_sku}
                },
                'imageReference': {
                    'publisher': os_publisher,
                    'offer': os_offer,
                    'sku': os_sku,
                    'version': os_version
                }
            },
            'ManagedCustomImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': storage_caching,
                    'managedDisk': {'storageAccountType': storage_sku}
                },
                "imageReference": {
                    'id': image_reference
                }
            },
            'ManagedSpecializedOSDisk': {
                'osDisk': {
                    'createOption': 'attach',
                    'osType': custom_image_os_type,
                    'managedDisk': {
                        "id": managed_os_disk
                    }
                }
            }
        }
        profile = storage_profiles[storage_profile.name]
        return _build_data_disks(profile, data_disk_sizes_gb, image_data_disks,
                                 storage_caching, storage_sku)

    vm_properties = {
        'hardwareProfile': {'vmSize': size},
        'networkProfile': {'networkInterfaces': nics}
    }

    vm_properties['storageProfile'] = _build_storage_profile()

    if availability_set_id:
        vm_properties['availabilitySet'] = {'id': availability_set_id}

    if not managed_os_disk:
        vm_properties['osProfile'] = _build_os_profile()

    vm = {
        'apiVersion': '2016-04-30-preview',
        'type': 'Microsoft.Compute/virtualMachines',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': vm_properties,
    }
    return vm


def _build_data_disks(profile, data_disk_sizes_gb, image_data_disks,
                      storage_caching, storage_sku):
    if data_disk_sizes_gb is not None:
        profile['dataDisks'] = []
        for image_data_disk in image_data_disks or []:
            profile['dataDisks'].append({
                'lun': image_data_disk.lun,
                'createOption': "fromImage",
            })
        lun = max([d.lun for d in image_data_disks]) + 1 if image_data_disks else 1
        for size in data_disk_sizes_gb:
            profile['dataDisks'].append({
                'lun': lun,
                'createOption': "empty",
                'diskSizeGB': int(size),
                'caching': storage_caching,
                'managedDisk': {'storageAccountType': storage_sku}
            })
            lun = lun + 1
    return profile


def build_load_balancer_resource(name, location, tags, backend_pool_name, nat_pool_name,
                                 backend_port, frontend_ip_name, public_ip_id, subnet_id,
                                 private_ip_address='', private_ip_allocation='dynamic'):
    lb_id = "resourceId('Microsoft.Network/loadBalancers', '{}')".format(name)

    frontend_ip_config = {
        'name': frontend_ip_name
    }

    if public_ip_id:
        frontend_ip_config.update({
            'properties': {
                'publicIPAddress': {
                    'id': public_ip_id
                }
            }
        })
    else:
        frontend_ip_config.update({
            'properties': {
                'privateIPAllocationMethod': private_ip_allocation,
                'privateIPAddress': private_ip_address,
                'subnet': {
                    'id': subnet_id
                }
            }
        })

    lb_properties = {
        'backendAddressPools': [
            {
                'name': backend_pool_name
            }
        ],
        'inboundNatPools': [
            {
                'name': nat_pool_name,
                'properties': {
                    'frontendIPConfiguration': {
                        'id': "[concat({}, '/frontendIPConfigurations/', '{}')]".format(
                            lb_id, frontend_ip_name)
                    },
                    'protocol': 'tcp',
                    'frontendPortRangeStart': '50000',
                    'frontendPortRangeEnd': '50119',
                    'backendPort': backend_port
                }
            }
        ],
        'frontendIPConfigurations': [frontend_ip_config]
    }

    lb = {
        "type": "Microsoft.Network/loadBalancers",
        "name": name,
        "location": location,
        "tags": tags,
        "apiVersion": "2015-06-15",
        "dependsOn": [],
        "properties": lb_properties
    }
    return lb


def build_vmss_storage_account_pool_resource(loop_name, location, tags, storage_sku):

    storage_resource = {
        'type': 'Microsoft.Storage/storageAccounts',
        'name': "[variables('storageAccountNames')[copyIndex()]]",
        'location': location,
        'tags': tags,
        'apiVersion': '2015-06-15',
        'copy': {
            'name': loop_name,
            'count': 5
        },
        'properties': {
            'accountType': storage_sku
        }
    }
    return storage_resource


# pylint: disable=too-many-locals
def build_vmss_resource(name, naming_prefix, location, tags, overprovision, upgrade_policy_mode,
                        vm_sku, instance_count, ip_config_name, nic_name, subnet_id,
                        admin_username, authentication_type,
                        storage_profile, os_disk_name,
                        storage_caching, storage_sku, data_disk_sizes_gb, image_data_disks, os_type,
                        image=None, admin_password=None, ssh_key_value=None, ssh_key_path=None,
                        os_publisher=None, os_offer=None, os_sku=None, os_version=None,
                        backend_address_pool_id=None, inbound_nat_pool_id=None,
                        single_placement_group=None):

    # Build IP configuration
    ip_configuration = {
        'name': ip_config_name,
        'properties': {
            'subnet': {'id': subnet_id}
        }
    }
    if backend_address_pool_id:
        ip_configuration['properties']['loadBalancerBackendAddressPools'] = [
            {'id': backend_address_pool_id}
        ]

    if inbound_nat_pool_id:
        ip_configuration['properties']['loadBalancerInboundNatPools'] = [
            {'id': inbound_nat_pool_id}
        ]

    # Build storage profile
    storage_properties = {}
    if storage_profile in [StorageProfile.SACustomImage, StorageProfile.SAPirImage]:
        storage_properties['osDisk'] = {
            'name': os_disk_name,
            'caching': storage_caching,
            'createOption': 'FromImage',
        }

        if storage_profile == StorageProfile.SACustomImage:
            storage_properties['osDisk'].update({
                'osType': os_type,
                'image': {
                    'uri': image
                }
            })
        else:
            storage_properties['osDisk']['vhdContainers'] = "[variables('vhdContainers')]"
    elif storage_profile in [StorageProfile.ManagedPirImage, StorageProfile.ManagedPirImage]:
        storage_properties['osDisk'] = {
            'createOption': 'FromImage',
            'caching': storage_caching,
            'managedDisk': {'storageAccountType': storage_sku}
        }

    if storage_profile in [StorageProfile.SAPirImage, StorageProfile.ManagedPirImage]:
        storage_properties['imageReference'] = {
            'publisher': os_publisher,
            'offer': os_offer,
            'sku': os_sku,
            'version': os_version
        }
    if storage_profile == StorageProfile.ManagedCustomImage:
        storage_properties['imageReference'] = {
            'id': image
        }

    storage_profile = _build_data_disks(storage_properties, data_disk_sizes_gb,
                                        image_data_disks, storage_caching,
                                        storage_sku)

    # Build OS Profile
    os_profile = {
        'computerNamePrefix': naming_prefix,
        'adminUsername': admin_username
    }
    if authentication_type == 'password':
        os_profile['adminPassword'] = admin_password
    else:
        os_profile['linuxConfiguration'] = {
            'disablePasswordAuthentication': True,
            'ssh': {
                'publicKeys': [
                    {
                        'path': ssh_key_path,
                        'keyData': ssh_key_value
                    }
                ]
            }
        }

    if single_placement_group is None:  # this should never happen, but just in case
        raise ValueError('single_placement_group was not set by validators')
    # Build VMSS
    vmss_properties = {
        'overprovision': overprovision,
        'singlePlacementGroup': single_placement_group,
        'upgradePolicy': {
            'mode': upgrade_policy_mode
        },
        'virtualMachineProfile': {
            'storageProfile': storage_properties,
            'osProfile': os_profile,
            'networkProfile': {
                'networkInterfaceConfigurations': [{
                    'name': nic_name,
                    'properties': {
                        'primary': 'true',
                        'ipConfigurations': [ip_configuration]
                    }
                }]
            }
        }
    }
    vmss = {
        'type': 'Microsoft.Compute/virtualMachineScaleSets',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2016-04-30-preview',
        'dependsOn': [],
        'sku': {
            'name': vm_sku,
            'tier': 'Standard',
            'capacity': instance_count
        },
        'properties': vmss_properties
    }
    return vmss


def build_av_set_resource(name, location, tags,
                          platform_update_domain_count, platform_fault_domain_count, unmanaged):
    av_set = {
        'type': 'Microsoft.Compute/availabilitySets',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2016-04-30-preview',
        'sku': {
            'name': 'Classic' if unmanaged else 'Aligned'
        },
        "properties": {
            'platformUpdateDomainCount': platform_update_domain_count,
            'platformFaultDomainCount': platform_fault_domain_count,
        }
    }
    return av_set
