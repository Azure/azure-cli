# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict
import json

from enum import Enum

from azure.cli.core.util import b64encode
from azure.cli.core.profiles import get_api_version, supported_api_version, ResourceType


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
    SASpecializedOSDisk = 3
    ManagedPirImage = 4  # this would be the main scenarios
    ManagedCustomImage = 5
    ManagedSpecializedOSDisk = 6


def build_deployment_resource(name, template, dependencies=None):
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
    from azure.cli.core.util import random_string
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
        os_caching=None, data_caching=None, storage_sku=None,
        os_publisher=None, os_offer=None, os_sku=None, os_version=None, os_vhd_uri=None,
        attach_os_disk=None, attach_data_disks=None, data_disk_sizes_gb=None, image_data_disks=None,
        custom_data=None, secrets=None, license_type=None):

    def _build_os_profile():

        os_profile = {
            'computerName': name,
            'adminUsername': admin_username
        }

        if admin_password:
            os_profile['adminPassword'] = admin_password

        if custom_data:
            os_profile['customData'] = b64encode(custom_data)

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

        if secrets:
            os_profile['secrets'] = secrets

        return os_profile

    def _build_storage_profile():

        storage_profiles = {
            'SACustomImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': os_caching,
                    'osType': custom_image_os_type,
                    'image': {'uri': image_reference},
                    'vhd': {'uri': os_vhd_uri}
                }
            },
            'SAPirImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': os_caching,
                    'vhd': {'uri': os_vhd_uri}
                },
                'imageReference': {
                    'publisher': os_publisher,
                    'offer': os_offer,
                    'sku': os_sku,
                    'version': os_version
                }
            },
            'SASpecializedOSDisk': {
                'osDisk': {
                    'createOption': 'attach',
                    'osType': custom_image_os_type,
                    'name': os_disk_name,
                    'vhd': {'uri': attach_os_disk}
                }
            },
            'ManagedPirImage': {
                'osDisk': {
                    'createOption': 'fromImage',
                    'name': os_disk_name,
                    'caching': os_caching,
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
                    'caching': os_caching,
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
                        'id': attach_os_disk
                    }
                }
            }
        }
        profile = storage_profiles[storage_profile.name]
        return _build_data_disks(profile, data_disk_sizes_gb, image_data_disks,
                                 data_caching, storage_sku, attach_data_disks=attach_data_disks)

    vm_properties = {
        'hardwareProfile': {'vmSize': size},
        'networkProfile': {'networkInterfaces': nics}
    }

    vm_properties['storageProfile'] = _build_storage_profile()

    if availability_set_id:
        vm_properties['availabilitySet'] = {'id': availability_set_id}

    if not attach_os_disk:
        vm_properties['osProfile'] = _build_os_profile()

    if license_type:
        vm_properties['licenseType'] = license_type

    vm_api_version = get_api_version(ResourceType.MGMT_COMPUTE)
    vm = {
        'apiVersion': vm_api_version,
        'type': 'Microsoft.Compute/virtualMachines',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': vm_properties,
    }
    return vm


def _build_data_disks(profile, data_disk_sizes_gb, image_data_disks,
                      data_caching, storage_sku, attach_data_disks=None):
    lun = 0
    profile['dataDisks'] = []
    if data_disk_sizes_gb is not None:
        for image_data_disk in image_data_disks or []:
            profile['dataDisks'].append({
                'lun': image_data_disk.lun,
                'createOption': "fromImage",
                'caching': data_caching
            })
        lun = max([d.lun for d in image_data_disks]) + 1 if image_data_disks else 0
        for size in data_disk_sizes_gb:
            profile['dataDisks'].append({
                'lun': lun,
                'createOption': "empty",
                'diskSizeGB': int(size),
                'caching': data_caching,
                'managedDisk': {'storageAccountType': storage_sku}
            })
            lun = lun + 1

    if attach_data_disks:
        from azure.cli.core.commands.arm import is_valid_resource_id
        for d in attach_data_disks:
            disk_entry = {
                'lun': lun,
                'createOption': 'attach',
                'caching': data_caching,
            }
            if is_valid_resource_id(d):
                disk_entry['managedDisk'] = {'id': d}
            else:
                disk_entry['vhd'] = {'uri': d}
                disk_entry['name'] = d.split('/')[-1].split('.')[0]
            profile['dataDisks'].append(disk_entry)
            lun += 1

    return profile


def _build_frontend_ip_config(name, public_ip_id=None, private_ip_address=None,
                              private_ip_allocation=None, subnet_id=None):
    frontend_ip_config = {
        'name': name
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
    return frontend_ip_config


def build_application_gateway_resource(name, location, tags, backend_pool_name, backend_port,
                                       frontend_ip_name, public_ip_id,
                                       subnet_id, gateway_subnet_id,
                                       private_ip_address, private_ip_allocation):
    frontend_ip_config = _build_frontend_ip_config(frontend_ip_name, public_ip_id,
                                                   private_ip_address, private_ip_allocation,
                                                   subnet_id)

    def _ag_subresource_id(_type, name):
        return "[concat(variables('appGwID'), '/{}/{}')]".format(_type, name)

    frontend_ip_config_id = _ag_subresource_id('frontendIPConfigurations', frontend_ip_name)
    frontend_port_id = _ag_subresource_id('frontendPorts', 'appGwFrontendPort')
    http_listener_id = _ag_subresource_id('httpListeners', 'appGwHttpListener')
    backend_address_pool_id = _ag_subresource_id('backendAddressPools', backend_pool_name)
    backend_http_settings_id = _ag_subresource_id(
        'backendHttpSettingsCollection', 'appGwBackendHttpSettings')

    ag_properties = {
        'backendAddressPools': [
            {
                'name': backend_pool_name
            }
        ],
        'backendHttpSettingsCollection': [
            {
                'name': 'appGwBackendHttpSettings',
                'properties': {
                    'Port': backend_port,
                    'Protocol': 'Http',
                    'CookieBasedAffinity': 'Disabled'
                }
            }
        ],
        'frontendIPConfigurations': [frontend_ip_config],
        'frontendPorts': [
            {
                'name': 'appGwFrontendPort',
                'properties': {
                    'Port': 80
                }
            }
        ],
        'gatewayIPConfigurations': [
            {
                'name': 'appGwIpConfig',
                'properties': {
                    'subnet': {'id': gateway_subnet_id}
                }
            }
        ],
        'httpListeners': [
            {
                'name': 'appGwHttpListener',
                'properties': {
                    'FrontendIPConfiguration': {'Id': frontend_ip_config_id},
                    'FrontendPort': {'Id': frontend_port_id},
                    'Protocol': 'Http',
                    'SslCertificate': None
                }
            }
        ],
        'sku': {
            'name': 'Standard_Large',
            'tier': 'Standard',
            'capacity': '10'
        },
        'requestRoutingRules': [
            {
                'Name': 'rule1',
                'properties': {
                    'RuleType': 'Basic',
                    'httpListener': {'id': http_listener_id},
                    'backendAddressPool': {'id': backend_address_pool_id},
                    'backendHttpSettings': {'id': backend_http_settings_id}
                }
            }
        ]
    }

    ag = {
        'type': 'Microsoft.Network/applicationGateways',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'properties': ag_properties
    }
    return ag


def build_load_balancer_resource(name, location, tags, backend_pool_name, nat_pool_name,
                                 backend_port, frontend_ip_name, public_ip_id, subnet_id,
                                 private_ip_address, private_ip_allocation):
    lb_id = "resourceId('Microsoft.Network/loadBalancers', '{}')".format(name)

    frontend_ip_config = _build_frontend_ip_config(frontend_ip_name, public_ip_id,
                                                   private_ip_address, private_ip_allocation,
                                                   subnet_id)

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
        'type': 'Microsoft.Network/loadBalancers',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'properties': lb_properties
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
                        os_caching, data_caching, storage_sku, data_disk_sizes_gb,
                        image_data_disks, os_type,
                        image=None, admin_password=None, ssh_key_value=None, ssh_key_path=None,
                        os_publisher=None, os_offer=None, os_sku=None, os_version=None,
                        backend_address_pool_id=None, inbound_nat_pool_id=None,
                        single_placement_group=None, custom_data=None, secrets=None):

    # Build IP configuration
    ip_configuration = {
        'name': ip_config_name,
        'properties': {
            'subnet': {'id': subnet_id}
        }
    }

    if backend_address_pool_id:
        key = 'loadBalancerBackendAddressPools' if 'loadBalancers' in backend_address_pool_id \
            else 'ApplicationGatewayBackendAddressPools'
        ip_configuration['properties'][key] = [
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
            'caching': os_caching,
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
    elif storage_profile in [StorageProfile.ManagedPirImage, StorageProfile.ManagedCustomImage]:
        storage_properties['osDisk'] = {
            'createOption': 'FromImage',
            'caching': os_caching,
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
                                        image_data_disks, data_caching,
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

    if custom_data:
        os_profile['customData'] = b64encode(custom_data)

    if secrets:
        os_profile['secrets'] = secrets

    if single_placement_group is None:  # this should never happen, but just in case
        raise ValueError('single_placement_group was not set by validators')
    # Build VMSS
    vmss_properties = {
        'overprovision': overprovision,
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

    if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2016-04-30-preview'):
        vmss_properties['singlePlacementGroup'] = single_placement_group

    vmss_api_version = get_api_version(ResourceType.MGMT_COMPUTE)
    vmss = {
        'type': 'Microsoft.Compute/virtualMachineScaleSets',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': vmss_api_version,
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
    av_set_api_version = get_api_version(ResourceType.MGMT_COMPUTE)
    av_set = {
        'type': 'Microsoft.Compute/availabilitySets',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': av_set_api_version,
        'sku': {
            'name': 'Classic' if unmanaged else 'Aligned'
        },
        "properties": {
            'platformFaultDomainCount': platform_fault_domain_count,
        }
    }

    # server defaults the UD to 5 unless set otherwise
    if platform_update_domain_count is not None:
        av_set['properties']['platformUpdateDomainCount'] = platform_update_domain_count

    return av_set
