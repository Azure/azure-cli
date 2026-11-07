# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import logger as error_logger
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest
from azure.cli.testsdk.patches import patch_main_exception_handler


class VMCreateErrorsScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep the real CLI error renderer: the default harness patch only raises an exception.
        self.recording_patches.remove(patch_main_exception_handler)
        self.replay_patches.remove(patch_main_exception_handler)

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_success_', location='eastus')
    def test_vm_create_windows_standard_ssd_no_public_ip(self, resource_group):
        self.kwargs.update({
            'vm': 'windowsvm',
            'admin_username': 'clitestuser',
            'admin_password': 'TestPassword1234!',
        })

        # Exercise failure reporting before the successful VM consumes regional quota.
        self._assert_vm_create_disk_error('invaliddiskvm')

        result = self.cmd(
            'vm create -g {rg} -n {vm} --location eastus '
            '--image Win2022Datacenter --size Standard_D2s_v4 '
            '--storage-sku StandardSSD_LRS --public-ip-address "" '
            '--admin-username {admin_username} --admin-password {admin_password}',
            checks=[
                self.exists('id'),
                self.check('resourceGroup', '{rg}'),
                self.check('location', 'eastus'),
                self.check('powerState', 'VM running'),
                self.check('publicIpAddress', ''),
                self.exists('privateIpAddress'),
            ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip())
        created_vm = result.get_output_in_json()

        vm = self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('id', created_vm['id']),
            self.check('provisioningState', 'Succeeded'),
            self.check('hardwareProfile.vmSize', 'Standard_D2s_v4'),
            self.check('storageProfile.imageReference.publisher', 'MicrosoftWindowsServer'),
            self.check('storageProfile.imageReference.offer', 'WindowsServer'),
            self.check('storageProfile.imageReference.sku', '2022-datacenter-g2'),
            self.exists('storageProfile.imageReference.version'),
            self.check('storageProfile.osDisk.osType', 'Windows'),
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'StandardSSD_LRS'),
        ]).get_output_in_json()

        self.cmd('vm get-instance-view -g {rg} -n {vm}', checks=[
            self.check("instanceView.statuses[?code=='ProvisioningState/succeeded'] | length(@)", 1),
            self.check("instanceView.statuses[?code=='PowerState/running'] | length(@)", 1),
        ])

        nics = vm['networkProfile']['networkInterfaces']
        self.assertTrue(nics)
        for nic in nics:
            self.kwargs['nic_id'] = nic['id']
            attached_nic = self.cmd('network nic show --ids {nic_id}').get_output_in_json()
            ip_configurations = attached_nic['ipConfigurations']
            self.assertTrue(ip_configurations)
            for ip_configuration in ip_configurations:
                self.assertFalse(ip_configuration.get('publicIpAddress'))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_disk_error_', location='eastus')
    def test_vm_create_windows_os_disk_too_small(self, resource_group):
        self.kwargs.update({
            'vm': 'invaliddiskvm',
            'admin_username': 'clitestuser',
            'admin_password': 'TestPassword1234!',
        })

        self._assert_vm_create_disk_error(self.kwargs['vm'])

    def _assert_vm_create_disk_error(self, vm_name):
        self.kwargs['invalid_vm'] = vm_name
        # This size is passed into the deployment template; Compute rejects shrinking the image disk.
        with self.assertLogs(error_logger, level='WARNING') as logs:
            result = self.cmd(
                'vm create -g {rg} -n {invalid_vm} --location eastus '
                '--image Win2022Datacenter --size Standard_D2s_v4 '
                '--storage-sku StandardSSD_LRS --public-ip-address "" '
                '--admin-username {admin_username} --admin-password {admin_password} '
                '--os-disk-size-gb 1',
                expect_failure=True)

        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), '')
        self.assertIsNone(self.cli_ctx.result.result)
        self.assertIsNotNone(self.cli_ctx.result.error)
        errors = '\n'.join(logs.output)
        self.assertIn('OperationNotAllowed', errors)
        self.assertRegex(errors.lower(), r'disk size\s+1\b')
        self.assertIn('smaller than', errors.lower())
        self.assertIn('image', errors.lower())
        for internal_error in ('Traceback', 'RuntimeError', 'already consumed', 'NoneType'):
            self.assertNotIn(internal_error, errors)
            self.assertNotIn(internal_error, str(self.cli_ctx.result.error))
