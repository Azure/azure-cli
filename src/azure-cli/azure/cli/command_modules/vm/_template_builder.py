# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from enum import Enum

from knack.util import CLIError

from azure.cli.core.azclierror import ValidationError
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


def build_public_ip_resource(cmd, name, location, tags, address_allocation, dns_name, sku, zone, count=None):
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

    if count:
        public_ip['name'] = "[concat('{}', copyIndex())]".format(name)
        public_ip['copy'] = {
            'name': 'publicipcopy',
            'mode': 'parallel',
            'count': count
        }

    # when multiple zones are provided(through a x-zone scale set), we don't propagate to PIP becasue it doesn't
    # support x-zone; rather we will rely on the Standard LB to work with such scale sets
    if zone and len(zone) == 1:
        public_ip['zones'] = zone

    if sku and cmd.supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-08-01'):
        public_ip['sku'] = {'name': sku}
    return public_ip


def build_nic_resource(_, name, location, tags, vm_name, subnet_id, private_ip_address=None,
                       nsg_id=None, public_ip_id=None, application_security_groups=None, accelerated_networking=None,
                       count=None):
    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'
    ip_config_properties = {
        'privateIPAllocationMethod': private_ip_allocation,
        'subnet': {'id': subnet_id}
    }

    if private_ip_address:
        ip_config_properties['privateIPAddress'] = private_ip_address

    if public_ip_id:
        ip_config_properties['publicIPAddress'] = {'id': public_ip_id}
        if count:
            ip_config_properties['publicIPAddress']['id'] = "[concat('{}', copyIndex())]".format(public_ip_id)

    ipconfig_name = 'ipconfig{}'.format(vm_name)
    nic_properties = {
        'ipConfigurations': [
            {
                'name': ipconfig_name,
                'properties': ip_config_properties
            }
        ]
    }
    if count:
        nic_properties['ipConfigurations'][0]['name'] = "[concat('{}', copyIndex())]".format(ipconfig_name)

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

    if count:
        nic['name'] = "[concat('{}', copyIndex())]".format(name)
        nic['copy'] = {
            'name': 'niccopy',
            'mode': 'parallel',
            'count': count
        }

    return nic


def build_nsg_resource(_, name, location, tags, nsg_rule):
    nsg = {
        'type': 'Microsoft.Network/networkSecurityGroups',
        'name': name,
        'apiVersion': '2015-06-15',
        'location': location,
        'tags': tags,
        'dependsOn': []
    }

    if nsg_rule != 'NONE':
        rule_name = 'rdp' if nsg_rule == 'RDP' else 'default-allow-ssh'
        rule_dest_port = '3389' if nsg_rule == 'RDP' else '22'

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

        nsg['properties'] = nsg_properties

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
    msi_rp_api_version = '2019-07-01'
    return {
        'name': name,
        'type': assignment_type,
        'apiVersion': '2015-07-01',  # the minimum api-version to create the assignment
        'dependsOn': [
            'Microsoft.Compute/{}/{}'.format('virtualMachines' if is_vm else 'virtualMachineScaleSets', vm_vmss_name)
        ],
        'properties': {
            'roleDefinitionId': role_definition_id,
            'principalId': "[reference('{}', '{}', 'Full').identity.principalId]".format(
                vm_vmss_resource_id, msi_rp_api_version),
            'scope': identity_scope
        }
    }


def build_vm_resource(  # pylint: disable=too-many-locals, too-many-statements
        cmd, name, location, tags, size, storage_profile, nics, admin_username,
        availability_set_id=None, admin_password=None, ssh_key_values=None, ssh_key_path=None,
        image_reference=None, os_disk_name=None, custom_image_os_type=None, authentication_type=None,
        os_publisher=None, os_offer=None, os_sku=None, os_version=None, os_vhd_uri=None,
        attach_os_disk=None, os_disk_size_gb=None, custom_data=None, secrets=None, license_type=None, zone=None,
        disk_info=None, boot_diagnostics_storage_uri=None, ultra_ssd_enabled=None, proximity_placement_group=None,
        computer_name=None, dedicated_host=None, priority=None, max_price=None, eviction_policy=None,
        enable_agent=None, vmss=None, os_disk_encryption_set=None, data_disk_encryption_sets=None, specialized=None,
        encryption_at_host=None, dedicated_host_group=None, enable_auto_update=None, patch_mode=None,
        enable_hotpatching=None, platform_fault_domain=None, security_type=None, enable_secure_boot=None,
        enable_vtpm=None, count=None):

    os_caching = disk_info['os'].get('caching')

    def _build_os_profile():

        special_chars = '`~!@#$%^&*()=+_[]{}\\|;:\'\",<>/?'

        # _computer_name is used to avoid shadow names
        _computer_name = computer_name or ''.join(filter(lambda x: x not in special_chars, name))

        os_profile = {
            # Use name as computer_name if it's not provided. Remove special characters from name.
            'computerName': _computer_name,
            'adminUsername': admin_username
        }

        if count:
            os_profile['computerName'] = "[concat('{}', copyIndex())]".format(_computer_name)

        if admin_password:
            os_profile['adminPassword'] = "[parameters('adminPassword')]"

        if custom_data:
            os_profile['customData'] = b64encode(custom_data)

        if ssh_key_values and ssh_key_path:
            os_profile['linuxConfiguration'] = {
                'disablePasswordAuthentication': authentication_type == 'ssh',
                'ssh': {
                    'publicKeys': [
                        {
                            'keyData': ssh_key_value,
                            'path': ssh_key_path
                        } for ssh_key_value in ssh_key_values
                    ]
                }
            }

        if enable_agent is not None:
            if custom_image_os_type.lower() == 'linux':
                if 'linuxConfiguration' not in os_profile:
                    os_profile['linuxConfiguration'] = {}
                os_profile['linuxConfiguration']['provisionVMAgent'] = enable_agent
            elif custom_image_os_type.lower() == 'windows':
                if 'windowsConfiguration' not in os_profile:
                    os_profile['windowsConfiguration'] = {}
                os_profile['windowsConfiguration']['provisionVMAgent'] = enable_agent

        if secrets:
            os_profile['secrets'] = secrets

        if enable_auto_update is not None and custom_image_os_type.lower() == 'windows':
            os_profile['windowsConfiguration']['enableAutomaticUpdates'] = enable_auto_update

        # Windows patch settings
        if patch_mode is not None and custom_image_os_type.lower() == 'windows':
            if patch_mode.lower() not in ['automaticbyos', 'automaticbyplatform', 'manual']:
                raise ValidationError(
                    'Invalid value of --patch-mode for Windows VM. Valid values are AutomaticByOS, '
                    'AutomaticByPlatform, Manual.')
            os_profile['windowsConfiguration']['patchSettings'] = {
                'patchMode': patch_mode,
                'enableHotpatching': enable_hotpatching
            }

        # Linux patch settings
        if patch_mode is not None and custom_image_os_type.lower() == 'linux':
            if patch_mode.lower() not in ['automaticbyplatform', 'imagedefault']:
                raise ValidationError(
                    'Invalid value of --patch-mode for Linux VM. Valid values are AutomaticByPlatform, ImageDefault.')
            os_profile['linuxConfiguration']['patchSettings'] = {
                'patchMode': patch_mode
            }

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
                    'managedDisk': {
                        'storageAccountType': disk_info['os'].get('storageAccountType'),
                    }
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
                    'managedDisk': {
                        'storageAccountType': disk_info['os'].get('storageAccountType'),
                    }
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
        if os_disk_encryption_set is not None:
            storage_profiles['ManagedPirImage']['osDisk']['managedDisk']['diskEncryptionSet'] = {
                'id': os_disk_encryption_set,
            }
            storage_profiles['ManagedCustomImage']['osDisk']['managedDisk']['diskEncryptionSet'] = {
                'id': os_disk_encryption_set,
            }
        profile = storage_profiles[storage_profile.name]
        if os_disk_size_gb:
            profile['osDisk']['diskSizeGb'] = os_disk_size_gb
        if disk_info['os'].get('writeAcceleratorEnabled') is not None:
            profile['osDisk']['writeAcceleratorEnabled'] = disk_info['os']['writeAcceleratorEnabled']
        data_disks = [v for k, v in disk_info.items() if k != 'os']
        if data_disk_encryption_sets:
            if len(data_disk_encryption_sets) != len(data_disks):
                raise CLIError(
                    'usage error: Number of --data-disk-encryption-sets mismatches with number of data disks.')
            for i, data_disk in enumerate(data_disks):
                data_disk['managedDisk']['diskEncryptionSet'] = {'id': data_disk_encryption_sets[i]}
        if data_disks:
            profile['dataDisks'] = data_disks

        if disk_info['os'].get('diffDiskSettings'):
            profile['osDisk']['diffDiskSettings'] = disk_info['os']['diffDiskSettings']

        return profile

    vm_properties = {'hardwareProfile': {'vmSize': size}, 'networkProfile': {'networkInterfaces': nics},
                     'storageProfile': _build_storage_profile()}

    if availability_set_id:
        vm_properties['availabilitySet'] = {'id': availability_set_id}

    # vmss is ID
    if vmss is not None:
        vm_properties['virtualMachineScaleSet'] = {'id': vmss}

    if not attach_os_disk and not specialized:
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

    if proximity_placement_group:
        vm_properties['proximityPlacementGroup'] = {'id': proximity_placement_group}

    if dedicated_host:
        vm_properties['host'] = {'id': dedicated_host}

    if dedicated_host_group:
        vm_properties['hostGroup'] = {'id': dedicated_host_group}

    if priority is not None:
        vm_properties['priority'] = priority

    if eviction_policy is not None:
        vm_properties['evictionPolicy'] = eviction_policy

    if max_price is not None:
        vm_properties['billingProfile'] = {'maxPrice': max_price}

    vm_properties['securityProfile'] = {}

    if encryption_at_host is not None:
        vm_properties['securityProfile']['encryptionAtHost'] = encryption_at_host

    if security_type is not None:
        vm_properties['securityProfile']['securityType'] = security_type

    if enable_secure_boot is not None or enable_vtpm is not None:
        vm_properties['securityProfile']['uefiSettings'] = {
            'secureBootEnabled': enable_secure_boot,
            'vTpmEnabled': enable_vtpm
        }

    if platform_fault_domain is not None:
        vm_properties['platformFaultDomain'] = platform_fault_domain

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
    if count:
        vm['copy'] = {
            'name': 'vmcopy',
            'mode': 'parallel',
            'count': count
        }
        vm['name'] = "[concat('{}', copyIndex())]".format(name)
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
                                 backend_port, frontend_ip_name, public_ip_id, subnet_id, private_ip_address,
                                 private_ip_allocation, sku, instance_count, disable_overprovision):
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
                    # keep 50119 as minimum for backward compat, and ensure over-provision is taken care of
                    'frontendPortRangeEnd': str(max(50119,
                                                    49999 + instance_count * (1 if disable_overprovision else 2))),
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


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, too-many-lines
def build_vmss_resource(cmd, name, naming_prefix, location, tags, overprovision, upgrade_policy_mode,
                        vm_sku, instance_count, ip_config_name, nic_name, subnet_id,
                        public_ip_per_vm, vm_domain_name, dns_servers, nsg, accelerated_networking,
                        admin_username, authentication_type, storage_profile, os_disk_name, disk_info,
                        os_type, image=None, admin_password=None, ssh_key_values=None,
                        ssh_key_path=None, os_publisher=None, os_offer=None, os_sku=None, os_version=None,
                        backend_address_pool_id=None, inbound_nat_pool_id=None, health_probe=None,
                        single_placement_group=None, platform_fault_domain_count=None, custom_data=None,
                        secrets=None, license_type=None, zones=None, priority=None, eviction_policy=None,
                        application_security_groups=None, ultra_ssd_enabled=None, proximity_placement_group=None,
                        terminate_notification_time=None, max_price=None, scale_in_policy=None,
                        os_disk_encryption_set=None, data_disk_encryption_sets=None,
                        data_disk_iops=None, data_disk_mbps=None, automatic_repairs_grace_period=None,
                        specialized=None, os_disk_size_gb=None, encryption_at_host=None, host_group=None,
                        max_batch_instance_percent=None, max_unhealthy_instance_percent=None,
                        max_unhealthy_upgraded_instance_percent=None, pause_time_between_batches=None,
                        enable_cross_zone_upgrade=None, prioritize_unhealthy_instances=None):

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

        if os_disk_size_gb is not None:
            storage_properties['osDisk']['diskSizeGB'] = os_disk_size_gb
    elif storage_profile in [StorageProfile.ManagedPirImage, StorageProfile.ManagedCustomImage]:
        storage_properties['osDisk'] = {
            'createOption': 'FromImage',
            'caching': os_caching,
            'managedDisk': {'storageAccountType': disk_info['os'].get('storageAccountType')}
        }
        if os_disk_encryption_set is not None:
            storage_properties['osDisk']['managedDisk']['diskEncryptionSet'] = {
                'id': os_disk_encryption_set
            }
        if disk_info['os'].get('diffDiskSettings'):
            storage_properties['osDisk']['diffDiskSettings'] = disk_info['os']['diffDiskSettings']

        if os_disk_size_gb is not None:
            storage_properties['osDisk']['diskSizeGB'] = os_disk_size_gb

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
    if data_disk_encryption_sets:
        if len(data_disk_encryption_sets) != len(data_disks):
            raise CLIError(
                'usage error: Number of --data-disk-encryption-sets mismatches with number of data disks.')
        for i, data_disk in enumerate(data_disks):
            data_disk['managedDisk']['diskEncryptionSet'] = {'id': data_disk_encryption_sets[i]}
    if data_disk_iops:
        if len(data_disk_iops) != len(data_disks):
            raise CLIError('usage error: Number of --data-disk-iops mismatches with number of data disks.')
        for i, data_disk in enumerate(data_disks):
            data_disk['diskIOPSReadWrite'] = data_disk_iops[i]
    if data_disk_mbps:
        if len(data_disk_mbps) != len(data_disks):
            raise CLIError('usage error: Number of --data-disk-mbps mismatches with number of data disks.')
        for i, data_disk in enumerate(data_disks):
            data_disk['diskMBpsReadWrite'] = data_disk_mbps[i]
    if data_disks:
        storage_properties['dataDisks'] = data_disks

    # Build OS Profile
    os_profile = {
        'computerNamePrefix': naming_prefix,
        'adminUsername': admin_username
    }

    if admin_password:
        os_profile['adminPassword'] = "[parameters('adminPassword')]"

    if ssh_key_values and ssh_key_path:
        os_profile['linuxConfiguration'] = {
            'disablePasswordAuthentication': authentication_type == 'ssh',
            'ssh': {
                'publicKeys': [
                    {
                        'path': ssh_key_path,
                        'keyData': ssh_key_value
                    } for ssh_key_value in ssh_key_values
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
            'mode': upgrade_policy_mode,
            'rollingUpgradePolicy': {
                'maxBatchInstancePercent': max_batch_instance_percent,
                'maxUnhealthyInstancePercent': max_unhealthy_instance_percent,
                'maxUnhealthyUpgradedInstancePercent': max_unhealthy_upgraded_instance_percent,
                'pauseTimeBetweenBatches': pause_time_between_batches,
                'enableCrossZoneUpgrade': enable_cross_zone_upgrade,
                'prioritizeUnhealthyInstances': prioritize_unhealthy_instances
            }
        },
        'virtualMachineProfile': {
            'storageProfile': storage_properties,
            'networkProfile': {
                'networkInterfaceConfigurations': [nic_config]
            }
        }
    }

    if not specialized:
        vmss_properties['virtualMachineProfile']['osProfile'] = os_profile

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

    if max_price is not None and cmd.supported_api_version(
            min_api='2019-03-01', operation_group='virtual_machine_scale_sets'):
        vmss_properties['virtualMachineProfile']['billingProfile'] = {'maxPrice': max_price}

    if platform_fault_domain_count is not None and cmd.supported_api_version(
            min_api='2017-12-01', operation_group='virtual_machine_scale_sets'):
        vmss_properties['platformFaultDomainCount'] = platform_fault_domain_count

    if ultra_ssd_enabled is not None:
        if cmd.supported_api_version(min_api='2019-03-01', operation_group='virtual_machine_scale_sets'):
            vmss_properties['additionalCapabilities'] = {'ultraSSDEnabled': ultra_ssd_enabled}
        else:
            vmss_properties['virtualMachineProfile']['additionalCapabilities'] = {'ultraSSDEnabled': ultra_ssd_enabled}

    if proximity_placement_group:
        vmss_properties['proximityPlacementGroup'] = {'id': proximity_placement_group}

    if terminate_notification_time is not None:
        scheduled_events_profile = {
            'terminateNotificationProfile': {
                'notBeforeTimeout': terminate_notification_time,
                'enable': 'true'
            }
        }
        vmss_properties['virtualMachineProfile']['scheduledEventsProfile'] = scheduled_events_profile

    if automatic_repairs_grace_period is not None:
        automatic_repairs_policy = {
            'enabled': 'true',
            'gracePeriod': automatic_repairs_grace_period
        }
        vmss_properties['automaticRepairsPolicy'] = automatic_repairs_policy

    if scale_in_policy:
        vmss_properties['scaleInPolicy'] = {'rules': scale_in_policy}

    if encryption_at_host:
        vmss_properties['virtualMachineProfile']['securityProfile'] = {'encryptionAtHost': encryption_at_host}

    if host_group:
        vmss_properties['hostGroup'] = {'id': host_group}

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


def build_av_set_resource(cmd, name, location, tags, platform_update_domain_count,
                          platform_fault_domain_count, unmanaged, proximity_placement_group=None):
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

    if proximity_placement_group:
        av_set['properties']['proximityPlacementGroup'] = {'id': proximity_placement_group}

    return av_set


def build_vm_linux_log_analytics_workspace_agent(_, vm_name, location):
    '''
    This is used for log analytics workspace
    '''
    mmaExtension_resource = {
        'type': 'Microsoft.Compute/virtualMachines/extensions',
        'apiVersion': '2018-10-01',
        'properties': {
            'publisher': 'Microsoft.EnterpriseCloud.Monitoring',
            'type': 'OmsAgentForLinux',
            'typeHandlerVersion': '1.0',
            'autoUpgradeMinorVersion': 'true',
            'settings': {
                'workspaceId': "[reference(parameters('workspaceId'), '2015-11-01-preview').customerId]",
                'stopOnMultipleConnections': 'true'
            },
            'protectedSettings': {
                'workspaceKey': "[listKeys(parameters('workspaceId'), '2015-11-01-preview').primarySharedKey]"
            }
        }
    }

    mmaExtension_resource['name'] = vm_name + '/OmsAgentForLinux'
    mmaExtension_resource['location'] = location
    mmaExtension_resource['dependsOn'] = ['Microsoft.Compute/virtualMachines/' + vm_name]
    return mmaExtension_resource


def build_vm_windows_log_analytics_workspace_agent(_, vm_name, location):
    '''
    This function is used for log analytics workspace.
    '''
    mmaExtension_resource = {
        'type': 'Microsoft.Compute/virtualMachines/extensions',
        'apiVersion': '2018-10-01',
        'properties': {
            'publisher': 'Microsoft.EnterpriseCloud.Monitoring',
            'type': 'MicrosoftMonitoringAgent',
            'typeHandlerVersion': '1.0',
            'autoUpgradeMinorVersion': 'true',
            'settings': {
                'workspaceId': "[reference(parameters('workspaceId'), '2015-11-01-preview').customerId]",
                'stopOnMultipleConnections': 'true'
            },
            'protectedSettings': {
                'workspaceKey': "[listKeys(parameters('workspaceId'), '2015-11-01-preview').primarySharedKey]"
            }
        }
    }

    mmaExtension_resource['name'] = vm_name + '/MicrosoftMonitoringAgent'
    mmaExtension_resource['location'] = location
    mmaExtension_resource['dependsOn'] = ['Microsoft.Compute/virtualMachines/' + vm_name]
    return mmaExtension_resource
