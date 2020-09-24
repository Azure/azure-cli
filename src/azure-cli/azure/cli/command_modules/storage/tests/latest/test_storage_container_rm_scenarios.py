# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import ScenarioTest, api_version_constraint, ResourceGroupPreparer, StorageAccountPreparer
from azure_devtools.scenario_tests import AllowLargeResponse


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
class StorageContainerRmScenarios(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_container_using_rm_main_scenario(self):
        # 1. Test create command.

        # Create container with specified public access and metadata.
        cname = self.create_random_name('container', 24)
        self.kwargs.update({
            'cname': cname,
        })
        result = self.cmd('storage container-rm create --account-name {sa} -g {rg} '
                          '-n {cname} --public-access blob --metadata key1=value1').get_output_in_json()
        self.assertEqual(result['name'], cname)
        self.assertEqual(result['publicAccess'], 'Blob')
        self.assertEqual(result['metadata']['key1'], 'value1')

        # Create container using existing name while setting fail-on-exist true
        from azure.cli.core.azclierror import AzCLIError
        with self.assertRaisesRegexp(AzCLIError, 'The specified container already exists.'):
            self.cmd(
                'storage container-rm create --account-name {sa} -g {rg} -n {cname} --fail-on-exist').get_output_in_json()

        # 2. Test exists command (the container exists).
        result = self.cmd('storage container-rm exists --account-name {sa} -g {rg} -n {cname}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # 3. Test show command (the container exists).
        result = self.cmd('storage container-rm show --account-name {sa} -g {rg} -n {cname}').get_output_in_json()
        self.assertEqual(result['name'], cname)
        self.assertEqual(result['publicAccess'], 'Blob')
        self.assertEqual(result['metadata']['key1'], 'value1')

        # 4. Test update command
        result = self.cmd('storage container-rm update --account-name {sa} -g {rg} -n {cname} '
                          '--metadata key2=value2 --deny-encryption-scope-override true').get_output_in_json()
        self.assertEqual(result['denyEncryptionScopeOverride'], True)
        self.assertEqual(result['metadata']['key2'], 'value2')
        self.assertNotIn('key1', result['metadata'])

        # 5. Test list command
        self.assertIn(cname,
                      self.cmd('storage container-rm list --account-name {sa} --query "[].name"').get_output_in_json())

        # 6. Test delete command
        self.cmd('storage container-rm delete --account-name {sa} -g {rg} -n {cname} -y')

        # 7. Test show command (the container doesn't exist).
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('storage container-rm show --account-name {sa} -g {rg} -n {cname}')

        # 8. Test exists command (the container doesn't exist).
        result = self.cmd('storage container-rm exists --account-name {sa} -g {rg} -n {cname}').get_output_in_json()
        self.assertEqual(result['exists'], False)
