# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
from enum import Enum
import json
import os

PATH = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', 'templates', '{}'))

class ArmTemplateBuilder(object):

    def __init__(self):
        template = OrderedDict()
        template['$schema'] = 'https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#'
        template['contentVersion'] = '1.0.0.0'
        template['parameters'] = {}
        template['variables'] = {}
        template['resources'] = []
        template['outputs'] = {}
        self.template = template

    def add_resource(self, resource):
        self.template['resources'].append(resource)

    def add_id_output(self, key, provider, property_type, property_name):
        new_output = {
            key: {
                'type': 'string',
                'value': "[resourceId('{}/{}', '{}')]".format(provider, property_type, property_name)
            }
        }
        self.template['outputs'].update(new_output)

    def add_variable_output(self, key, property_key, property_name, output_type='string', path=None):
        value = "[reference(variables('{}'))".format(property_key)
        value = '{}.{}]'.format(value, path) if path else '{}]'.format(value)
        new_output = {
            key: {
                'type': output_type,
                'value': value
            }
        }
        self.template['outputs'].update(new_output)
        new_variable = {
            property_key: property_name
        }
        self.template['variables'].update(new_variable)

    def add_output(self, key, property_name, provider=None, property_type=None, output_type='string', path=None):

        if provider and property_type:
            value = "[reference(resourceId('{provider}/{type}', '{property}'),providers('{provider}', '{type}').apiVersions[0])".format(
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

        # dump template to file temporarily...
        test_path = PATH.format('test.json')
        try:
            os.remove(test_path)
        except:
            pass
        test_file = open(test_path, 'w')
        test_file.write(json.dumps(self.template))
        test_file.close()

        return json.loads(json.dumps(self.template))

class StorageProfile(Enum):
    SAPirImage = 1
    SACustomImage = 2
    MDPirImage = 3
    MDCustomImage = 4
    MDAttachExisting = 5

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

def build_output_deployment_resource(key, property_name, property_provider, property_type, parent_name=None, output_type='object', path=None):
    from azure.cli.command_modules.vm._vm_utils import random_string
    output_tb = ArmTemplateBuilder()
    output_tb.add_output(key, property_name, property_provider, property_type, output_type=output_type, path=path)
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
    deployment['dependsOn'] = [] if not parent_name else ['Microsoft.Resources/deployments/{}'.format(parent_name)]

    return deployment

def build_storage_account_resource(name, location, tags, sku):
    storage_account = {
        "type": "Microsoft.Storage/storageAccounts",
        "name": name,
        "apiVersion": "2015-06-15",
        "location": location,
        "tags": tags,
        "dependsOn": [ ],
        "properties": {
            "accountType": sku
        }
    }
    return storage_account

def build_public_ip_resource(name, location, tags, address_allocation, dns_name=None):

    public_ip_properties = {
        "publicIPAllocationMethod": address_allocation
    }

    if dns_name:
        public_ip_properties['dnsSettings'] = {
            "domainNameLabel": dns_name
        }

    public_ip = {
        "apiVersion": "2015-06-15",
        "type": "Microsoft.Network/publicIPAddresses",
        "name": name,
        "location": location,
        "tags": tags,
        "dependsOn": [ ],
        "properties": public_ip_properties
    }
    return public_ip

def build_nic_resource(name, location, tags, vm_name, subnet_id, private_ip_address=None, nsg_id=None, public_ip_id=None):

    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'
    ip_config_properties = {
        'privateIPAllocationMethod': private_ip_allocation,
        'subnet': { 'id': subnet_id }
    }

    if private_ip_address:
        ip_config_properties['privateIPAddress'] = private_ip_address

    if public_ip_id:
        ip_config_properties['publicIPAddress'] = { 'id': public_ip_id }

    nic_properties = {
        'ipConfigurations': [
            {
                'name': 'ipconfig{}'.format(vm_name),
                'properties': ip_config_properties 
            }
        ]
    }

    if nsg_id:
        nic_properties['networkSecurityGroup'] = { 'id': nsg_id }

    nic = {
        "apiVersion": "2015-06-15",
        "type": "Microsoft.Network/networkInterfaces",
        "name": name,
        "location": location,
        "tags": tags,
        "dependsOn": [ ],
        "properties": nic_properties
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
        "type": "Microsoft.Network/networkSecurityGroups",
        "name": name,
        "apiVersion": "2015-06-15",
        "location": location,
        "tags": tags,
        "dependsOn": [ ],
        "properties": nsg_properties
    }
    return nsg

def build_vnet_resource(name, location, tags, vnet_prefix='10.0.0.0/16', subnet=None, subnet_prefix='10.0.0.0/24', dns_servers=None):
    vnet = {
      'name': name,
      'type': 'Microsoft.Network/virtualNetworks',
      'location': location,
      'apiVersion': '2015-06-15',
      'dependsOn': [ ],
      'tags': tags,
      'properties': {
        'addressSpace': {
          'addressPrefixes': [vnet_prefix]
        },
      }
    }
    if dns_servers:
        vnet['properties']['dhcpOptions'] = {
          'dnsServers': dns_servers
        }
    if subnet:
        vnet['properties']['subnets'] = [
          {
            'name': subnet,
            'properties': {
              'addressPrefix': subnet_prefix
            }
          }
        ]
    return vnet

def build_vm_resource(
    name, location, tags, size, storage_profile, nics, admin_username, availability_set_id=None,
    admin_password=None, ssh_key_value=None, ssh_key_path=None, image_reference=None,
    os_disk_name=None, custom_image_os_type=None, storage_caching=None, storage_sku=None,
    os_publisher=None, os_offer=None, os_sku=None, os_version=None, os_vhd_uri=None):

    def _build_os_profile():

        os_profile = {
            "computerName": name,
            "adminUsername": admin_username,
        }

        if admin_password:
            os_profile['adminPassword'] = admin_password

        if ssh_key_value and ssh_key_path:
            os_profile['linuxConfiguration'] = {
                "disablePasswordAuthentication": True,
                "ssh": {
                    "publicKeys": [
                        {
                            "keyData": ssh_key_value,
                            "path": ssh_key_path
                        }
                    ]
                }
            }

        return os_profile

    def _build_storage_profile():
        
        storage_profiles = {
            "SACustomImage": {
                "osDisk": {
                    "createOption": "fromImage",
                    "name": os_disk_name,
                    "caching": storage_caching,
                    "osType": custom_image_os_type,
                    "image": {
                        "uri": image_reference
                    },
                    "vhd": {
                        "uri": os_vhd_uri
                    }
                }
            },
            "SAPirImage": {
                "osDisk": {
                    "createOption": "fromImage",
                    "name": os_disk_name,
                    "caching": storage_caching,
                    "vhd": {
                        "uri": os_vhd_uri
                    }
                },
                "imageReference": {
                    "publisher": os_publisher,
                    "offer": os_offer,
                    "sku": os_sku,
                    "version": os_version
                }
            },
            "MDCustomImage": {
                "osDisk": {
                    "createOption": "fromImage",
                    "name": os_disk_name,
                },
                "imageReference": {
                    "id": image_reference
                }
            },
            "MDPirImage": {
                "osDisk": {
                    "createOption": "fromImage",
                    "name": os_disk_name,
                },
                "imageReference": {
                    "publisher": os_publisher,
                    "offer": os_offer,
                    "sku": os_sku,
                    "version": os_version
                }
            },
            "MDAttachExisting": {
                "osDisk": {
                    "createOption": "attach",
                    "osType": custom_image_os_type,
                    "managedDisk": {
                        "id": image_reference
                    }
                }
            }
        }
        return storage_profiles[storage_profile.name]

    vm_properties = {
        "hardwareProfile": {
            "vmSize": size
        },
        "networkProfile": {
            "networkInterfaces": nics
        }
    }

    vm_properties['storageProfile'] = _build_storage_profile()

    if availability_set_id:
        vm_properties['availabilitySet'] = {
            'id': availability_set_id
        }

    if storage_profile is not StorageProfile.MDAttachExisting:
        vm_properties['osProfile'] = _build_os_profile()

    vm = {
        "apiVersion": "2015-06-15",
        "type": "Microsoft.Compute/virtualMachines",
        "name": name,
        "location": location,
        "tags": tags,
        "dependsOn": [ ],
        "properties": vm_properties,
    }
    return vm

def build_lb_resource():
    raise Exception('TODO: this!')
    lb_properties = {
        "backendAddressPools": [
            {
                "name": "[parameters('backendPoolName')]"
            }
        ],
        "inboundNatPools": [
            {
                "name": "[parameters('natPoolName')]",
                "properties": {
                    "frontendIPConfiguration": {
                        "id": "[variables('frontEndIPConfigID')]"
                    },
                    "protocol": "tcp",
                    "frontendPortRangeStart": "50000",
                    "frontendPortRangeEnd": "50119",
                    "backendPort": "[parameters('backendPort')]"
                }
            }
        ],
        "frontendIPConfigurations": "[variables('frontendConfig')[parameters('publicIpAddressType')]]"
    }
    lb = {
        "type": "Microsoft.Network/loadBalancers",
        "name": "[parameters('loadBalancerName')]",
        "location": "[parameters('location')]",
        "tags": "[parameters('tags')]",
        "apiVersion": "2015-06-15",
        "dependsOn": [
            "[concat('Microsoft.Resources/deployments/', variables('ipDeploymentName'))]",
            "[concat('Microsoft.Resources/deployments/', variables('subnetDeploymentName'))]"
        ],
        "properties": lb_properties
    }
    return lb

def build_vmss_resource():
    raise Exception('TODO: this!')
    vmss_properties = {
        "overprovision": "[parameters('overprovision')]",
        "upgradePolicy": {
          "mode": "[parameters('upgradePolicyMode')]"
        },
        "virtualMachineProfile": {
          "storageProfile": "[variables('storageProfilesCustomImage')[parameters('osDiskType')]]",
          "osProfile": "[variables('osProfileReference')]",
          "networkProfile": {
            "networkInterfaceConfigurations": [
              {
                "name": "[variables('nicName')]",
                "properties": {
                  "primary": "true",
                  "ipConfigurations": "[variables('ipConfigurations')[parameters('loadBalancerType')]]"
                }
              }
            ]
          }
        }
    }
    vmss = {
        "type": "Microsoft.Compute/virtualMachineScaleSets",
        "name": "[parameters('name')]",
        "location": "[variables('resourceLocation')]",
        "tags": "[parameters('tags')]",
        "apiVersion": "[variables('vmssApiVersion')]",
        "dependsOn": [
            "storageLoop",
            "[concat('Microsoft.Resources/deployments/', variables('lbDeploymentName'))]",
            "[concat('Microsoft.Resources/deployments/', variables('vnetDeploymentName'))]"
        ],
        "sku": {
            "name": "[parameters('vmSku')]",
            "tier": "Standard",
            "capacity": "[variables('instanceCount')]"
        },
        "properties": vmss_properties
    }
    return vmss
