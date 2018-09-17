# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from enum import Enum

from azure.cli.core.util import b64encode
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.arm import ArmTemplateBuilder

from azure.cli.command_modules.vm._vm_utils import get_target_network_api


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


def build_storage_account_resource(_, name, location, tags, sku):
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


def build_public_ip_resource(cmd, name, location, tags, address_allocation, dns_name, sku, zone):
    public_ip_properties = {'publicIPAllocationMethod': address_allocation}

    if dns_name:
        public_ip_properties['dnsSettings'] = {'domainNameLabel': dns_name}

    public_ip = {
        'apiVersion': get_target_network_api(cmd.cli_ctx),
        'type': 'Microsoft.Network/publicIPAddresses',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': public_ip_properties
    }

    # when multiple zones are provided(through a x-zone scale set), we don't propagate to PIP becasue it doesn't
    # support x-zone; rather we will rely on the Standard LB to work with such scale sets
    if zone and len(zone) == 1:
        public_ip['zones'] = zone

    if sku and cmd.supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-08-01'):
        public_ip['sku'] = {'name': sku}
    return public_ip


def build_nic_resource(_, name, location, tags, vm_name, subnet_id, private_ip_address=None,
                       nsg_id=None, public_ip_id=None, application_security_groups=None, accelerated_networking=None):

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

    api_version = '2015-06-15'
    if application_security_groups:
        asg_ids = [{'id': x.id} for x in application_security_groups]
        nic_properties['ipConfigurations'][0]['properties']['applicationSecurityGroups'] = asg_ids
        api_version = '2017-09-01'

    if accelerated_networking is not None:
        nic_properties['enableAcceleratedNetworking'] = accelerated_networking
        api_version = '2016-09-01' if api_version < '2016-09-01' else api_version

    nic = {
        'apiVersion': api_version,
        'type': 'Microsoft.Network/networkInterfaces',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': nic_properties
    }
    return nic


def build_nsg_resource(_, name, location, tags, nsg_rule_type):

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


def build_vnet_resource(_, name, location, tags, vnet_prefix=None, subnet=None,
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


def build_msi_role_assignment(vm_vmss_name, vm_vmss_resource_id, role_definition_id,
                              role_assignment_guid, identity_scope, is_vm=True):
    from msrestazure.tools import parse_resource_id
    result = parse_resource_id(identity_scope)
    if result.get('type'):  # is a resource id?
        name = '{}/Microsoft.Authorization/{}'.format(result['name'], role_assignment_guid)
        assignment_type = '{}/{}/providers/roleAssignments'.format(result['namespace'], result['type'])
    else:
        name = role_assignment_guid
        assignment_type = 'Microsoft.Authorization/roleAssignments'

    # pylint: disable=line-too-long
    msi_rp_api_version = '2015-08-31-PREVIEW'
    return {
        'name': name,
        'type': assignment_type,
        'apiVersion': '2015-07-01',  # the minimum api-version to create the assignment
        'dependsOn': [
            'Microsoft.Compute/{}/{}'.format('virtualMachines' if is_vm else 'virtualMachineScaleSets', vm_vmss_name)
        ],
        'properties': {
            'roleDefinitionId': role_definition_id,
            'principalId': "[reference('{}/providers/Microsoft.ManagedIdentity/Identities/default', '{}').principalId]".format(
                vm_vmss_resource_id, msi_rp_api_version),
            'scope': identity_scope
        }
    }


def build_vm_resource(  # pylint: disable=too-many-locals
        cmd, name, location, tags, size, storage_profile, nics, admin_username,
        availability_set_id=None, admin_password=None, ssh_key_value=None, ssh_key_path=None,
        image_reference=None, os_disk_name=None, custom_image_os_type=None,
        storage_sku=None, os_publisher=None, os_offer=None, os_sku=None, os_version=None, os_vhd_uri=None,
        attach_os_disk=None, os_disk_size_gb=None, custom_data=None, secrets=None, license_type=None, zone=None,
        disk_info=None, boot_diagnostics_storage_uri=None, ultra_ssd_enabled=None):

    os_caching = disk_info['os'].get('caching')
    # TODO: split out the storage_sku for os disk(can't be ultra-ssd) and individual data disks
    os_storage_sku = None if storage_sku == 'UltraSSD_LRS' else storage_sku

    def _build_os_profile():

        os_profile = {
            'computerName': name,
            'adminUsername': admin_username
        }

        if admin_password:
            os_profile['adminPassword'] = "[parameters('adminPassword')]"

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
                    'managedDisk': {'storageAccountType': os_storage_sku}
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
        if os_disk_size_gb:
            profile['osDisk']['diskSizeGb'] = os_disk_size_gb
        if disk_info['os'].get('writeAcceleratorEnabled') is not None:
            profile['osDisk']['writeAcceleratorEnabled'] = disk_info['os']['writeAcceleratorEnabled']
        data_disks = [v for k, v in disk_info.items() if k != 'os']
        if data_disks:
            profile['dataDisks'] = data_disks

        return profile

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

    if boot_diagnostics_storage_uri:
        vm_properties['diagnosticsProfile'] = {
            'bootDiagnostics': {
                "enabled": True,
                "storageUri": boot_diagnostics_storage_uri
            }
        }

    if ultra_ssd_enabled is not None:
        vm_properties['additionalCapabilities'] = {'ultraSSDEnabled': ultra_ssd_enabled}

    vm = {
        'apiVersion': cmd.get_api_version(ResourceType.MGMT_COMPUTE, operation_group='virtual_machines'),
        'type': 'Microsoft.Compute/virtualMachines',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': vm_properties,
    }
    if zone:
        vm['zones'] = zone
    return vm


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


def build_application_gateway_resource(_, name, location, tags, backend_pool_name, backend_port, frontend_ip_name,
                                       public_ip_id, subnet_id, gateway_subnet_id,
                                       private_ip_address, private_ip_allocation, sku, capacity):
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
            'name': sku,
            'tier': sku.split('_')[0],
            'capacity': capacity
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


def build_load_balancer_resource(cmd, name, location, tags, backend_pool_name, nat_pool_name,
                                 backend_port, frontend_ip_name, public_ip_id, subnet_id,
                                 private_ip_address, private_ip_allocation, sku):
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
        'apiVersion': get_target_network_api(cmd.cli_ctx),
        'dependsOn': [],
        'properties': lb_properties
    }
    if sku and cmd.supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-08-01'):
        lb['sku'] = {'name': sku}
        # LB rule is the way to enable SNAT so outbound connections are possible
        if sku.lower() == 'standard':
            lb_properties['loadBalancingRules'] = [{
                "name": "LBRule",
                "properties": {
                    "frontendIPConfiguration": {
                        'id': "[concat({}, '/frontendIPConfigurations/', '{}')]".format(lb_id, frontend_ip_name)
                    },
                    "backendAddressPool": {
                        "id": "[concat({}, '/backendAddressPools/', '{}')]".format(lb_id, backend_pool_name)
                    },
                    "protocol": "tcp",
                    "frontendPort": 80,
                    "backendPort": 80,
                    "enableFloatingIP": False,
                    "idleTimeoutInMinutes": 5,
                }
            }]
    return lb


def build_vmss_storage_account_pool_resource(_, loop_name, location, tags, storage_sku):

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


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def build_vmss_resource(cmd, name, naming_prefix, location, tags, overprovision, upgrade_policy_mode,
                        vm_sku, instance_count, ip_config_name, nic_name, subnet_id,
                        public_ip_per_vm, vm_domain_name, dns_servers, nsg, accelerated_networking,
                        admin_username, authentication_type, storage_profile, os_disk_name, disk_info,
                        storage_sku, os_type, image=None, admin_password=None, ssh_key_value=None, ssh_key_path=None,
                        os_publisher=None, os_offer=None, os_sku=None, os_version=None,
                        backend_address_pool_id=None, inbound_nat_pool_id=None, health_probe=None,
                        single_placement_group=None, platform_fault_domain_count=None, custom_data=None,
                        secrets=None, license_type=None, zones=None, priority=None, eviction_policy=None,
                        application_security_groups=None, ultra_ssd_enabled=None):

    # Build IP configuration
    ip_configuration = {
        'name': ip_config_name,
        'properties': {
            'subnet': {'id': subnet_id}
        }
    }

    if public_ip_per_vm:
        ip_configuration['properties']['publicipaddressconfiguration'] = {
            'name': 'instancepublicip',
            'properties': {
                'idleTimeoutInMinutes': 10,
            }
        }
        if vm_domain_name:
            ip_configuration['properties']['publicipaddressconfiguration']['properties']['dnsSettings'] = {
                'domainNameLabel': vm_domain_name
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

    if application_security_groups and cmd.supported_api_version(min_api='2018-06-01',
                                                                 operation_group='virtual_machine_scale_sets'):
        ip_configuration['properties']['applicationSecurityGroups'] = [{'id': x.id}
                                                                       for x in application_security_groups]
    # Build storage profile
    storage_properties = {}
    os_caching = disk_info['os'].get('caching')
    # TODO: split out the storage_sku for os disk(can't be ultra-ssd) and individual data disks
    os_storage_sku = None if storage_sku == 'UltraSSD_LRS' else storage_sku

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
            'managedDisk': {'storageAccountType': os_storage_sku}
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
    data_disks = [v for k, v in disk_info.items() if k != 'os']
    if data_disks:
        storage_properties['dataDisks'] = data_disks

    # Build OS Profile
    os_profile = {
        'computerNamePrefix': naming_prefix,
        'adminUsername': admin_username
    }
    if authentication_type == 'password' and admin_password:
        os_profile['adminPassword'] = "[parameters('adminPassword')]"
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

    # Build VMSS
    nic_config = {
        'name': nic_name,
        'properties': {
            'primary': 'true',
            'ipConfigurations': [ip_configuration]
        }
    }

    if cmd.supported_api_version(min_api='2017-03-30', operation_group='virtual_machine_scale_sets'):
        if dns_servers:
            nic_config['properties']['dnsSettings'] = {'dnsServers': dns_servers}

        if accelerated_networking:
            nic_config['properties']['enableAcceleratedNetworking'] = True

    if nsg:
        nic_config['properties']['networkSecurityGroup'] = {'id': nsg}

    vmss_properties = {
        'overprovision': overprovision,
        'upgradePolicy': {
            'mode': upgrade_policy_mode
        },
        'virtualMachineProfile': {
            'storageProfile': storage_properties,
            'osProfile': os_profile,
            'networkProfile': {
                'networkInterfaceConfigurations': [nic_config]
            }
        }
    }

    if license_type:
        vmss_properties['virtualMachineProfile']['licenseType'] = license_type

    if health_probe and cmd.supported_api_version(min_api='2017-03-30', operation_group='virtual_machine_scale_sets'):
        vmss_properties['virtualMachineProfile']['networkProfile']['healthProbe'] = {'id': health_probe}

    if cmd.supported_api_version(min_api='2016-04-30-preview', operation_group='virtual_machine_scale_sets'):
        vmss_properties['singlePlacementGroup'] = single_placement_group

    if priority and cmd.supported_api_version(min_api='2017-12-01', operation_group='virtual_machine_scale_sets'):
        vmss_properties['virtualMachineProfile']['priority'] = priority

    if eviction_policy and cmd.supported_api_version(min_api='2017-12-01',
                                                     operation_group='virtual_machine_scale_sets'):
        vmss_properties['virtualMachineProfile']['evictionPolicy'] = eviction_policy

    if platform_fault_domain_count is not None and cmd.supported_api_version(
            min_api='2017-12-01', operation_group='virtual_machine_scale_sets'):
        vmss_properties['platformFaultDomainCount'] = platform_fault_domain_count

    if ultra_ssd_enabled is not None:
        vmss_properties['virtualMachineProfile']['additionalCapabilities'] = {'ultraSSDEnabled': ultra_ssd_enabled}

    vmss = {
        'type': 'Microsoft.Compute/virtualMachineScaleSets',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': cmd.get_api_version(ResourceType.MGMT_COMPUTE, operation_group='virtual_machine_scale_sets'),
        'dependsOn': [],
        'sku': {
            'name': vm_sku,
            'capacity': instance_count
        },
        'properties': vmss_properties
    }
    if zones:
        vmss['zones'] = zones
    return vmss


def build_av_set_resource(cmd, name, location, tags,
                          platform_update_domain_count, platform_fault_domain_count, unmanaged):
    av_set = {
        'type': 'Microsoft.Compute/availabilitySets',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': cmd.get_api_version(ResourceType.MGMT_COMPUTE, operation_group='availability_sets'),
        "properties": {
            'platformFaultDomainCount': platform_fault_domain_count,
        }
    }

    if cmd.supported_api_version(min_api='2016-04-30-preview', operation_group='availability_sets'):
        av_set['sku'] = {
            'name': 'Classic' if unmanaged else 'Aligned'
        }

    # server defaults the UD to 5 unless set otherwise
    if platform_update_domain_count is not None:
        av_set['properties']['platformUpdateDomainCount'] = platform_update_domain_count

    return av_set
