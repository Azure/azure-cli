# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.vm._template_builder import (StorageProfile, build_av_set_resource,
                                                            build_load_balancer_resource, build_vm_resource,
                                                            build_vmss_resource)


class TestTemplateBuilder(unittest.TestCase):

    def test_build_scheduled_events_policy(self):
        disk_info = {'os': {'caching': 'ReadWrite', 'storageAccountType': 'Standard_LRS'}}
        vm_resource = build_vm_resource(
            name='vm1', location='westus', tags={}, size='Standard_D2s_v5',
            storage_profile=StorageProfile.ManagedPirImage, nics=[], admin_username='azureuser',
            custom_image_os_type='linux', os_publisher='Canonical', os_offer='UbuntuServer', os_sku='18.04-LTS',
            os_version='latest', disk_info=disk_info, additional_scheduled_events=True,
            enable_user_reboot_scheduled_events=True, enable_user_redeploy_scheduled_events=True,
            enable_all_instance_down=True, scheduled_events_api_version='2020-07-01')

        expected_policy = {
            'scheduledEventsAdditionalPublishingTargets': {
                'eventGridAndResourceGraph': {
                    'enable': True,
                    'scheduledEventsApiVersion': '2020-07-01'
                }
            },
            'allInstancesDown': {
                'automaticallyApprove': True
            },
            'userInitiatedRedeploy': {
                'automaticallyApprove': True
            },
            'userInitiatedReboot': {
                'automaticallyApprove': True
            }
        }
        self.assertEqual(vm_resource['properties']['scheduledEventsPolicy'], expected_policy)

        cmd_mock = mock.MagicMock()
        cmd_mock.supported_api_version.return_value = False
        vmss_resource = build_vmss_resource(
            cmd=cmd_mock, name='vmss1', computer_name_prefix='vmss', location='westus', tags={}, overprovision=True,
            upgrade_policy_mode='Manual', vm_sku='Standard_D2s_v5', instance_count=2, ip_config_name='ipconfig',
            nic_name='nic', subnet_id=None, public_ip_per_vm=False, vm_domain_name=None, dns_servers=None, nsg=None,
            accelerated_networking=None, admin_username='azureuser', authentication_type='ssh',
            storage_profile=StorageProfile.ManagedPirImage, os_disk_name=None, disk_info=disk_info, os_type='linux',
            os_publisher='Canonical', os_offer='UbuntuServer', os_sku='18.04-LTS', os_version='latest',
            additional_scheduled_events=False, enable_all_instance_down=False,
            scheduled_events_api_version='2020-07-01')
        self.assertEqual(vmss_resource['properties']['scheduledEventsPolicy'], {
            'scheduledEventsAdditionalPublishingTargets': {
                'eventGridAndResourceGraph': {
                    'enable': False,
                    'scheduledEventsApiVersion': '2020-07-01'
                }
            },
            'allInstancesDown': {
                'automaticallyApprove': False
            }
        })

        cmd_mock.get_api_version.return_value = '2025-04-01'
        av_set_resource = build_av_set_resource(
            cmd_mock, 'avset1', 'westus', {}, platform_update_domain_count=1, platform_fault_domain_count=1,
            unmanaged=False, enable_all_instance_down=True, scheduled_events_api_version='2020-07-01')
        self.assertEqual(av_set_resource['properties']['scheduledEventsPolicy'], {
            'scheduledEventsAdditionalPublishingTargets': {
                'eventGridAndResourceGraph': {
                    'scheduledEventsApiVersion': '2020-07-01'
                }
            },
            'allInstancesDown': {
                'automaticallyApprove': True
            }
        })

    @mock.patch('azure.cli.command_modules.vm._template_builder.get_target_network_api', autospec=True)
    def test_build_load_balancer_resource(self, mock_get_api):
        mock_get_api.returtn_value = '1970-01-01'
        cmd_mock = mock.MagicMock()
        cmd_mock.supported_api_version.return_value = False

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=1, disable_overprovision=False)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50119')

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=80, disable_overprovision=False)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50159')

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=80, disable_overprovision=True)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50119')

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=140, disable_overprovision=True)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50139')
