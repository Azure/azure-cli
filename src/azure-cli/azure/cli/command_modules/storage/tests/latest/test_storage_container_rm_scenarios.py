# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import (ScenarioTest, api_version_constraint,
                               ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
class StorageContainerRmScenarios(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix="cli", location="eastus")
    @StorageAccountPreparer(name_prefix="containerrm", location="eastus")
    def test_storage_container_using_rm_main_scenario(self):
        # 1. Test create command.

        # Create container with storage account name and resource group.
        container_name = self.create_random_name('container', 24)
        self.kwargs.update({
            'container_name': container_name,
            'encryption': self.create_random_name(prefix="encryption", length=24),
        })
        result = self.cmd('storage container-rm create --storage-account {sa} -g {rg} '
                          '-n {container_name} --public-access blob --metadata key1=value1 '
                          '-d {encryption} --deny-override false').get_output_in_json()
        self.assertEqual(result['name'], container_name)
        self.assertEqual(result['publicAccess'], 'Blob')
        self.assertEqual(result['metadata']['key1'], 'value1')
        self.assertEqual(result['defaultEncryptionScope'], self.kwargs['encryption'])
        self.assertEqual(result['denyEncryptionScopeOverride'], False)

        container_id = result['id']
        self.kwargs.update({'container_id': container_id})

        # Create container using existing name while setting fail-on-exist true
        from knack.util import CLIError
        with self.assertRaisesRegex(CLIError, 'The specified container already exists.'):
            self.cmd(
                'storage container-rm create --storage-account {sa} -g {rg} -n {container_name} --fail-on-exist').get_output_in_json()

        # Create container with storage account id.
        container_name_2 = self.create_random_name('container', 24)
        storage_account = self.cmd('storage account show -n {sa}').get_output_in_json()
        storage_account_id = storage_account['id']
        self.kwargs.update({
            'container_name_2': container_name_2,
            'storage_account_id': storage_account_id
        })
        result = self.cmd('storage container-rm create --storage-account {storage_account_id} '
                          '-n {container_name_2} --public-access off').get_output_in_json()
        self.assertEqual(result['name'], container_name_2)
        self.assertEqual(result['publicAccess'], None)
        self.assertEqual(result['metadata'], None)
        self.assertEqual(result['defaultEncryptionScope'], None)
        self.assertEqual(result['denyEncryptionScopeOverride'], None)

        # 2. Test exists command (the container exists).

        # Check existence with storage account name and resource group.
        result = self.cmd('storage container-rm exists --storage-account {sa} -g {rg} -n {container_name}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # Check existence with storage account id.
        result = self.cmd('storage container-rm exists --storage-account {storage_account_id} -n {container_name}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # Check existence by container resource id.
        result = self.cmd('storage container-rm exists --ids {container_id}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # 3. Test show command (the container exists).

        # Show properties of a container with storage account name and resource group.
        result = self.cmd('storage container-rm show --storage-account {sa} -g {rg} -n {container_name}').get_output_in_json()
        self.assertEqual(result['name'], container_name)

        # Show properties of a container with storage account id.
        result = self.cmd('storage container-rm show --storage-account {storage_account_id} -n {container_name}').get_output_in_json()
        self.assertEqual(result['name'], container_name)

        # Show properties of a container by container resource id.
        result = self.cmd('storage container-rm show --ids {container_id}').get_output_in_json()
        self.assertEqual(result['name'], container_name)

        # 4. Test update command

        # Update container with storage account name and resource group.
        result = self.cmd('storage container-rm update --storage-account {sa} -g {rg} '
                          '-n {container_name} --metadata key2=value2').get_output_in_json()
        self.assertEqual(result['name'], container_name)
        self.assertEqual(result['metadata']['key2'], 'value2')
        self.assertNotIn('key1', result['metadata'])

        # Update container with storage account id.
        result = self.cmd('storage container-rm update --storage-account {storage_account_id} '
                          '-n {container_name} --public-access container').get_output_in_json()
        self.assertEqual(result['name'], container_name)
        self.assertEqual(result['publicAccess'], 'Container')

        # Update container by container resource id.
        result = self.cmd('storage container-rm update --ids {container_id} '
                          '--deny-encryption-scope-override true').get_output_in_json()
        self.assertEqual(result['denyEncryptionScopeOverride'], True)

        # 5. Test list command(with storage account name and resource group)
        result = self.cmd('storage container-rm list --storage-account {sa} --query "[].name"').get_output_in_json()
        self.assertIn(container_name, result)
        self.assertEqual(len(result), 2)

        # 6. Test delete command(with storage account name and resource group)
        self.cmd('storage container-rm delete --storage-account {sa} -g {rg} -n {container_name_2} -y')

        # 7. Test list command(with storage account id)
        result = self.cmd('storage container-rm list --storage-account {storage_account_id} --query "[].name"').get_output_in_json()
        self.assertNotIn(container_name_2, result)
        self.assertIn(container_name, result)
        self.assertEqual(len(result), 1)

        # 8. Test delete command(with storage account id)
        self.cmd('storage container-rm delete --ids {container_id} -y')
        self.assertEqual(self.cmd('storage container-rm list --storage-account {storage_account_id}').get_output_in_json(), [])

        # 7. Test show command (the container doesn't exist).
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('storage container-rm show --storage-account {sa} -g {rg} -n {container_name}')

        # 8. Test exists command (the container doesn't exist).
        result = self.cmd('storage container-rm exists --storage-account {sa} -g {rg} -n {container_name}').get_output_in_json()
        self.assertEqual(result['exists'], False)

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix="cli", location="eastus")
    def test_storage_container_squash_scenario(self, resource_group):
        self.kwargs.update({
            'sa': self.create_random_name(prefix='account', length=24),
            'cont': self.create_random_name(prefix='container', length=24),
            'vnet': self.create_random_name(prefix='vnet', length=10),
            'subnet': self.create_random_name(prefix='subnet', length=10)
        })
        result = self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}').get_output_in_json()
        self.kwargs['subnet_id'] = result['newVNet']['subnets'][0]['id']
        self.cmd(
            'network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints Microsoft.Storage')
        self.cmd('storage account create -n {sa} -g {rg} --subnet {subnet_id} '
                 '--default-action Deny --hns --sku Standard_LRS --enable-nfs-v3 true',
                 checks=[JMESPathCheck('enableNfsV3', True)])

        self.cmd('storage container-rm create -n {cont} --storage-account {sa} --root-squash RootSquash',
                 checks=[JMESPathCheck('enableNfsV3AllSquash', False),
                         JMESPathCheck('enableNfsV3RootSquash', True)])

        self.cmd('storage container-rm update -n {cont} --storage-account {sa} --root-squash AllSquash',
                 checks=[JMESPathCheck('enableNfsV3AllSquash', True),
                         JMESPathCheck('enableNfsV3RootSquash', True)])

        self.cmd('storage container-rm update -n {cont} --storage-account {sa} --root-squash NoRootSquash',
                 checks=[JMESPathCheck('enableNfsV3AllSquash', False),
                         JMESPathCheck('enableNfsV3RootSquash', False)])
