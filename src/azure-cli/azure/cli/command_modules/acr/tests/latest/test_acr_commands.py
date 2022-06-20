# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer, record_only
from azure.cli.command_modules.acr.custom import DEF_DIAG_SETTINGS_NAME_TEMPLATE


class AcrCommandsTests(ScenarioTest):

    def _core_registry_scenario(self, registry_name, resource_group, location):
        self.cmd('acr check-name -n {}'.format(registry_name),
                 checks=[self.check('nameAvailable', False),
                         self.check('reason', 'AlreadyExists')])
        self.cmd('acr list -g {}'.format(resource_group),
                 checks=[self.check('[0].name', registry_name),
                         self.check('[0].location', location),
                         self.check('[0].adminUserEnabled', False)])
        registry = self.cmd('acr show -n {} -g {}'.format(registry_name, resource_group),
                            checks=[self.check('name', registry_name),
                                    self.check('location', location),
                                    self.check('adminUserEnabled', False)]).get_output_in_json()

        if registry['sku']['name'] == 'Premium':
            self.cmd('acr show-usage -n {} -g {}'.format(registry_name, resource_group))

        # enable admin user
        self.cmd('acr update -n {} -g {} --tags foo=bar cat --admin-enabled true'.format(registry_name, resource_group),
                 checks=[self.check('name', registry_name),
                         self.check('location', location),
                         self.check('tags', {'cat': '', 'foo': 'bar'}),
                         self.check('adminUserEnabled', True),
                         self.check('provisioningState', 'Succeeded')])

        # test retention
        self.cmd('acr config retention update -r {} --status enabled --days 30 --type UntaggedManifests'.format(registry_name),
                 checks=[self.check('status', "enabled"),
                         self.check('days', 30)])

        self.cmd('acr config retention show -r {}'.format(registry_name),
                 checks=[self.check('status', "enabled"),
                         self.check('days', 30)])

        # test content-trust
        self.cmd('acr config content-trust update -n {} --status enabled'.format(registry_name),
                 checks=[self.check('status', "enabled")])

        self.cmd('acr config content-trust show -n {}'.format(registry_name),
                 checks=[self.check('status', "enabled")])

        # test soft-delete
        self.cmd('acr config soft-delete update -r {} --status enabled --days 30 --yes'.format(registry_name),
                checks=[self.check('status', 'enabled'),
                        self.check('retentionDays', 30)])

        self.cmd('acr config soft-delete show -r {}'.format(registry_name),
                checks=[self.check('status', 'enabled'),
                        self.check('retentionDays', 30)])

        # test credential module
        credential = self.cmd(
            'acr credential show -n {} -g {}'.format(registry_name, resource_group)).get_output_in_json()
        username = credential['username']
        password = credential['passwords'][0]['value']
        password2 = credential['passwords'][1]['value']
        assert username and password and password2

        # renew password
        credential = self.cmd('acr credential renew -n {} -g {} --password-name {}'.format(
            registry_name, resource_group, 'password')).get_output_in_json()
        renewed_username = credential['username']
        renewed_password = credential['passwords'][0]['value']
        renewed_password2 = credential['passwords'][1]['value']
        assert renewed_username and renewed_password and renewed_password2
        assert username == renewed_username
        assert password != renewed_password
        assert password2 == renewed_password2

        # renew password2
        credential = self.cmd('acr credential renew -n {} -g {} --password-name {}'.format(
            registry_name, resource_group, 'password2')).get_output_in_json()
        renewed_username = credential['username']
        renewed_password = credential['passwords'][0]['value']
        renewed_password2 = credential['passwords'][1]['value']
        assert renewed_username and renewed_password and renewed_password2
        assert username == renewed_username
        assert password != renewed_password
        assert password2 != renewed_password2

        # test acr delete
        self.cmd('acr delete -n {} -g {} -y'.format(registry_name, resource_group))

    def test_check_name_availability(self):
        # the chance of this randomly generated name has a duplication is rare
        name = self.create_random_name('clireg', 20)
        self.kwargs.update({
            'name': name
        })

        self.cmd('acr check-name -n {name}', checks=[
            self.check('nameAvailable', True)
        ])

    @ResourceGroupPreparer()
    def test_acr_create_with_managed_registry(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)

        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': resource_group_location,
            'sku': 'Premium'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Premium'),
                         self.check('sku.tier', 'Premium'),
                         self.check('provisioningState', 'Succeeded')])

        self._core_registry_scenario(registry_name, resource_group, resource_group_location)

    @ResourceGroupPreparer()
    def test_acr_create_webhook(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)
        webhook_name = 'cliregwebhook'

        self.kwargs.update({
            'registry_name': registry_name,
            'webhook_name': webhook_name,
            'rg_loc': resource_group_location,
            'headers': 'key=value',
            'webhook_scope': 'hello-world',
            'uri': 'http://www.microsoft.com',
            'actions': 'push',
            'sku': 'Standard'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('acr webhook create -n {webhook_name} -r {registry_name} --uri {uri} --actions {actions}',
                 checks=[self.check('name', '{webhook_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('status', 'enabled'),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('acr webhook list -r {registry_name}',
                 checks=[self.check('[0].name', '{webhook_name}'),
                         self.check('[0].status', 'enabled'),
                         self.check('[0].provisioningState', 'Succeeded')])
        self.cmd('acr webhook show -n {webhook_name} -r {registry_name}',
                 checks=[self.check('name', '{webhook_name}'),
                         self.check('status', 'enabled'),
                         self.check('provisioningState', 'Succeeded')])

        # update webhook
        self.cmd('acr webhook update -n {webhook_name} -r {registry_name} --headers {headers} --scope {webhook_scope}',
                 checks=[self.check('name', '{webhook_name}'),
                         self.check('status', 'enabled'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('scope', '{webhook_scope}')])

        # get webhook config
        self.cmd('acr webhook get-config -n {webhook_name} -r {registry_name}',
                 checks=[self.check('serviceUri', '{uri}'),
                         self.check('customHeaders', {'key': 'value'})])
        # ping
        self.cmd('acr webhook ping -n {webhook_name} -r {registry_name}', checks=[self.exists('id')])
        # list webhook events
        self.cmd('acr webhook list-events -n {webhook_name} -r {registry_name}')

        # get registry usage
        self.cmd('acr show-usage -n {registry_name} -g {rg}',
                 checks=[self.check('value[?name==`Size`]|[0].currentValue', 0),
                         self.greater_than('value[?name==`Size`]|[0].limit', 0),
                         self.check('value[?name==`Webhooks`]|[0].currentValue', 1),
                         self.greater_than('value[?name==`Webhooks`]|[0].limit', 0)])

        # test webhook delete
        self.cmd('acr webhook delete -n {webhook_name} -r {registry_name}')
        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_acr_create_replication(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)
        # replication location should be different from registry location
        replication_location = 'centralus'
        replication_name = replication_location

        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': resource_group_location,
            'replication_name': replication_name,
            'replication_loc': replication_location,
            'sku': 'Premium',
            'tags': 'key=value'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Premium'),
                         self.check('sku.tier', 'Premium'),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('acr replication create -n {replication_name} -r {registry_name} -l {replication_loc}',
                 checks=[self.check('name', '{replication_name}'),
                         self.check('location', '{replication_loc}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('regionEndpointEnabled', True)])

        self.cmd('acr replication list -r {registry_name}',
                 checks=[self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[1].provisioningState', 'Succeeded')])

        self.cmd('acr replication show -n {replication_name} -r {registry_name}',
                 checks=[self.check('name', '{replication_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('regionEndpointEnabled', True)
                         ])

        # update replication
        self.cmd('acr replication update -n {replication_name} -r {registry_name} --tags {tags} --region-endpoint-enabled false',
                 checks=[self.check('name', '{replication_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('regionEndpointEnabled', False),
                         self.check('tags', {'key': 'value'})])

        # test replication delete
        self.cmd('acr replication delete -n {replication_name} -r {registry_name}')

        # test create replication disable on home region
        self.cmd('acr replication create -n {replication_name} -r {registry_name} -l {replication_loc} --region-endpoint-enabled false',
                 checks=[self.check('name', '{replication_name}'),
                         self.check('location', '{replication_loc}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('regionEndpointEnabled', False)])

        # test replication delete
        self.cmd('acr replication delete -n {replication_name} -r {registry_name}')

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')

    @ResourceGroupPreparer()
    def test_acr_import_no_wait(self, resource_group):
        source_registry_name = self.create_random_name("sourceregistrysamesub", 40)

        self.kwargs.update({
            'resource_id': '/subscriptions/dfb63c8c-7c89-4ef8-af13-75c1d873c895/resourcegroups/resourcegroupdiffsub/providers/Microsoft.ContainerRegistry/registries/sourceregistrydiffsub',
            'source_registry_rg': 'resourcegroupsamesub',
            'source_loc': 'westus',
            'source_registry_name': source_registry_name,
            'sku': 'Standard',
            'source_image': 'microsoft:azure-cli',
        })

        # create a resource group for the source registry
        self.cmd('group create -n {source_registry_rg} -l {source_loc}')

        # create a source registry
        self.cmd('acr create -n {source_registry_name} -g {source_registry_rg} -l {source_loc} --sku {sku}',
                 checks=[self.check('name', '{source_registry_name}'),
                         self.check('location', '{source_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # import image using no-wait
        self.cmd('acr import -n {source_registry_name} -r {resource_id} --source {source_image} --no-wait')

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @record_only()
    def test_acr_image_import(self, resource_group):
        '''There are nine test cases.
        Case 1: Import image from a registry in a different subscription from the current one
        Case 2: Import image from one registry to another where both registries belong to the same subscription
        Case 3: Import image to the target registry and keep the repository:tag the same as that in the source
        Case 4: Import image to enable multiple tags in the target registry
        Case 5: Import image within the same registry
        Case 6: Import image by manifest digest
        Case 7: Import image from a registry in Docker Hub
        Case 8: Import image from an Azure Container Registry with Service Principal's credentials
        Case 9: Import image from an Azure Container Registry with personal access token
        '''

        source_registry_name = self.create_random_name("sourceregistrysamesub", 40)
        registry_name = self.create_random_name("targetregistry", 20)
        token = self.cmd('account get-access-token').get_output_in_json()['accessToken']

        # service principal creds to support import from resource_imageV1
        service_principal_username = self.cmd('keyvault secret show --id https://cliimportkv73021.vault.azure.net/secrets/SPusername').get_output_in_json()['value']
        service_principal_password = self.cmd('keyvault secret show --id https://cliimportkv73021.vault.azure.net/secrets/SPpassword').get_output_in_json()['value']

        self.kwargs.update({
            'resource_id': '/subscriptions/dfb63c8c-7c89-4ef8-af13-75c1d873c895/resourcegroups/resourcegroupdiffsub/providers/Microsoft.ContainerRegistry/registries/sourceregistrydiffsub',
            'resource_imageV1': 'sourceregistrydiffsub.azurecr.io/microsoft:azure-cli-1',
            'resource_imageV2': 'sourceregistrydiffsub.azurecr.io/microsoft:azure-cli-2',
            'source_registry_rg': 'resourcegroupsamesub',
            'source_loc': 'westus',
            'source_registry_name': source_registry_name,
            'registry_name': registry_name,
            'sku': 'Standard',
            'rg_loc': 'eastus',
            'source_image': 'microsoft:azure-cli',
            'source_image_same_registry': '{}.azurecr.io/microsoft:azure-cli'.format(registry_name),
            'source_image_by_digest': '{}.azurecr.io/azure-cli@sha256:622731d3e3a16b11a1f318b1c5018d0c44996b4c096b864fe2eac5b8beab535a'.format(source_registry_name),
            'tag_same_sub': 'repository_same_sub:tag_same_sub',
            'tag_multitag1': 'repository_multi1:tag_multi1',
            'tag_multitag2': 'repository_multi2:tag_multi2',
            'tag_same_registry': 'repository_same_registry:tag_same_registry',
            'tag_by_digest': 'repository_by_digest:tag_by_digest',
            'source_image_public_registry_dockerhub': 'registry.hub.docker.com/library/hello-world',
            'application_ID': service_principal_username,
            'service_principal_password': service_principal_password,
            'token': token
        })

        # create a resource group for the source registry
        self.cmd('group create -n {source_registry_rg} -l {source_loc}')

        # create a source registry which stays in the same subscription as the target registry does
        self.cmd('acr create -n {source_registry_name} -g {source_registry_rg} -l {source_loc} --sku {sku}',
                 checks=[self.check('name', '{source_registry_name}'),
                         self.check('location', '{source_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # Case 1: Import image from a registry in a different subscription from the current one
        self.cmd('acr import -n {source_registry_name} -r {resource_id} --source {source_image}')

        # create a target registry to hold the imported images
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # Case 2: Import image from one registry to another where both registries belong to the same subscription
        self.cmd('acr import -n {registry_name} --source {source_image} -r {source_registry_name} -t {tag_same_sub}')

        # Case 3: Import image to the target registry and keep the repository:tag the same as that in the source
        self.cmd('acr import -n {registry_name} --source {source_image} -r {source_registry_name}')

        # Case 4: Import image to enable multiple tags in the target registry
        self.cmd('acr import -n {registry_name} --source {source_image} -r {source_registry_name} -t {tag_multitag1} -t {tag_multitag2}')

        # Case 5: Import image within the same registry
        self.cmd('acr import -n {registry_name} --source {source_image_same_registry} -t {tag_same_registry}')

        # Case 6: Import image by manifest digest
        self.cmd('acr import -n {registry_name} --source {source_image_by_digest} -t {tag_by_digest}')

        # Case 7: Import image from a public registry in dockerhub
        self.cmd('acr import -n {registry_name} --source {source_image_public_registry_dockerhub}')

        # Case 8: Import image from an Azure Container Registry with Service Principal's credentials
        self.cmd('acr import -n {registry_name} --source {resource_imageV1} -u {application_ID} -p {service_principal_password}')

        # Case 9: Import image from an Azure Container Registry with personal access token
        self.cmd('acr import -n {registry_name} --source {resource_imageV2} -p {token}')


    @ResourceGroupPreparer()
    def test_acr_export_policy(self, resource_group):
        registry_1 = self.create_random_name('clireg', 20)
        registry_2 = self.create_random_name('clireg', 20)

        self.kwargs.update({
            'registry_1': registry_1,
            'registry_2': registry_2,
            'sku': 'Premium',
        })

        self.cmd('acr create -n {registry_1} -g {rg} --sku {sku} --public-network-enabled false --allow-exports',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'Enabled')])  # case insensitive check

        self.cmd('acr create -n {registry_1} -g {rg} --sku {sku} --public-network-enabled false --allow-exports true',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'enabled')])

        # for export policy to be disabled, we need to disable public network access
        self.cmd('acr create -n {registry_1} -g {rg} --sku {sku} --public-network-enabled false --allow-exports false',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'Disabled')])

        # create/PUT should default to enabling export policy
        self.cmd('acr create -n {registry_1} -g {rg} --sku {sku} --public-network-enabled false',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'Enabled')])

        self.cmd('acr update -n {registry_1} -g {rg} --sku {sku} --allow-exports true',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'enabled')])

        self.cmd('acr update -n {registry_1} -g {rg} --sku {sku} --allow-exports false',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'disabled')])

        self.cmd('acr update -n {registry_1} -g {rg} --sku {sku}',
                 checks=[self.check('name', '{registry_1}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check_pattern('policies.exportPolicy.status', 'Disabled')])

    @ResourceGroupPreparer()
    def test_acr_create_with_audits(self, resource_group):
        registry_name = self.create_random_name('clireg', 20)
        workspace_name = self.create_random_name('wprkspace', 20)
        self.kwargs.update({
            'registry_name': registry_name,
            'sku': 'basic',
            'workspace': workspace_name,
            'diagnostic-settings': DEF_DIAG_SETTINGS_NAME_TEMPLATE.format(registry_name)
        })

        self.cmd('monitor log-analytics workspace create -g {rg} -n {workspace}')

        result = self.cmd('acr create -n {registry_name} -g {rg} --sku {sku} --workspace {workspace}')
        self.kwargs['registry_id'] = result.get_output_in_json()['id']
        self.cmd('monitor diagnostic-settings show -g {rg} --resource {registry_id} -n {diagnostic-settings}', checks=[
            self.check('logs[0].category', 'ContainerRegistryRepositoryEvents'),
            self.check('logs[1].category', 'ContainerRegistryLoginEvents'),
            self.check('metrics[0].category', 'AllMetrics'),
        ])

    @ResourceGroupPreparer()
    @KeyVaultPreparer()
    def test_acr_encryption_with_cmk(self, key_vault, resource_group):
        self.kwargs.update({
            'key_vault': key_vault,
            'key_name': self.create_random_name('testkey', 20),
            'rotate_key_name': self.create_random_name('rotatekey', 20),
            'identity_name': self.create_random_name('testidentity', 20),
            'identity_permissions': "get unwrapkey wrapkey",
            'registry_name': self.create_random_name('testreg', 20),
        })

        # update kv key protection settings and create a new key
        self.cmd('keyvault update --name {key_vault} --enable-soft-delete --enable-purge-protection')
        result = self.cmd('keyvault key create --name {key_name} --vault-name {key_vault}')
        self.kwargs['key_id'] = result.get_output_in_json()['key']['kid']

        # create a user-assigned identity and give it access to the key
        result = self.cmd('identity create --name {identity_name} -g {rg}')
        self.kwargs['principal_id'] = result.get_output_in_json()['principalId']
        self.kwargs['identity_id'] = result.get_output_in_json()['id']
        self.kwargs['client_id'] = result.get_output_in_json()['clientId']

        self.cmd('keyvault set-policy --object-id {principal_id} --name {key_vault} --key-permissions {identity_permissions}')

        # create the registry with CMK encryption enabled using the user-assigned identity
        result = self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium --identity {identity_id} --key-encryption-key {key_id}', checks=[
            self.check('identity.type', 'userAssigned'),
            self.check('encryption.status', 'enabled'),
            self.check('encryption.keyVaultProperties.identity', '{client_id}'),
            self.check('encryption.keyVaultProperties.keyIdentifier', '{key_id}')
        ])

        self.assertTrue(bool(result.get_output_in_json()['identity']['userAssignedIdentities']))

        # rotate key and show encryption
        result = self.cmd('keyvault key create --name {rotate_key_name} --vault-name {key_vault}')
        self.kwargs['rotate_key_id'] = result.get_output_in_json()['key']['kid']
        self.cmd('acr encryption rotate-key --name {registry_name} --identity {identity_id} --key-encryption-key {rotate_key_id} -g {rg}',
                 self.check('encryption.keyVaultProperties.keyIdentifier', '{rotate_key_id}'))

        # show encryption
        self.cmd('acr encryption show --name {registry_name} -g {rg}', self.check('keyVaultProperties.keyIdentifier', '{rotate_key_id}'))

    @ResourceGroupPreparer()
    def test_acr_identity(self, resource_group):
        self.kwargs.update({
            'identity_name': self.create_random_name('testidentity', 30),
            'second_identity_name': self.create_random_name('testidentity2', 30),
            'registry_name': self.create_random_name('testreg', 25),
            'system_identity': '[system]'
        })

        # create registry
        self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium')

        # create user-assigned identities
        result = self.cmd('identity create --name {identity_name} -g {rg}')
        self.kwargs['identity_id'] = result.get_output_in_json()['id']

        result = self.cmd('identity create --name {second_identity_name} -g {rg}')
        self.kwargs['second_identity_id'] = result.get_output_in_json()['id']

        # add identities
        self.cmd('acr identity assign --name {registry_name} --identities "{system_identity}" "{identity_id}"')

        # show identity
        result = self.cmd('acr identity show --name {registry_name}').get_output_in_json()
        self.assertTrue('systemAssigned' in result['type'])
        self.assertTrue('userAssigned' in result['type'])
        self.assertTrue(len(result['userAssignedIdentities']) == 1)
        self.assertEquals(list(result['userAssignedIdentities'].keys())[0].lower(), self.kwargs['identity_id'].lower())

        # remove identities
        import time
        time.sleep(10)
        self.cmd('acr identity remove --name {registry_name} --identities "{system_identity}" "{identity_id}"', self.check('identity', None))

        # try different combinations of adds and deletes
        # system
        self.cmd('acr identity assign --name {registry_name} --identities {system_identity}', self.check('identity.type', 'systemAssigned'))
        time.sleep(10)
        self.cmd('acr identity remove --name {registry_name} --identities {system_identity}', self.check('identity', None))
        # user
        self.cmd('acr identity assign --name {registry_name} --identities {identity_id}', self.check('identity.type', 'userAssigned'))
        time.sleep(10)
        self.cmd('acr identity remove --name {registry_name} --identities {identity_id}', self.check('identity', None))

        # add multiple identities
        result = self.cmd('acr identity assign --name {registry_name} --identities "{system_identity}" "{identity_id}"',
                          self.check('identity.type', 'systemAssigned, userAssigned')).get_output_in_json()
        self.assertUserIdentitiesExpected([self.kwargs['identity_id'].lower()], result['identity'])
        # add another user identity to existing
        time.sleep(10)
        result = self.cmd('acr identity assign --name {registry_name} --identities {second_identity_id}',
                          self.check('identity.type', 'systemAssigned, userAssigned')).get_output_in_json()
        self.assertUserIdentitiesExpected([self.kwargs['identity_id'].lower(), self.kwargs['second_identity_id'].lower()], result['identity'])

        # remove identities and validate result
        time.sleep(10)
        self.cmd('acr identity remove --name {registry_name} --identities {second_identity_id}', self.check('identity.type', 'systemAssigned, userAssigned'))

        self.cmd('acr identity remove --name {registry_name} --identities {identity_id}', self.check('identity.type', 'systemAssigned'))
        self.cmd('acr identity remove --name {registry_name} --identities {system_identity}', self.check('identity', None))

    @ResourceGroupPreparer()
    def test_acr_with_dedicated_data_endpoints(self, resource_group, resource_group_location):
        self.kwargs.update({
            'registry_name': self.create_random_name('testreg', 20),
            'rg_loc': resource_group_location,
            'replication_loc': 'southcentralus'
        })
        login_server = self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium').get_output_in_json()['loginServer']
        self.cmd('acr show-endpoints --name {registry_name} --resource-group {rg}', checks=[
            self.check('length(dataEndpoints)', 1),
            self.check('dataEndpoints[0].endpoint', '*.blob.core.windows.net'),
            self.check('dataEndpoints[0].region', resource_group_location),
            self.check('loginServer', login_server)
        ])
        suffix = login_server.split('.', 1)[1]
        self.cmd('acr update --name {registry_name} --resource-group {rg} --data-endpoint-enabled')
        self.cmd('acr show-endpoints --name {registry_name} --resource-group {rg}', checks=[
            self.check('dataEndpoints[0].endpoint', '{}.{}.data.{}'.format(self.kwargs['registry_name'], self.kwargs['rg_loc'], suffix)),
        ])
        self.cmd('acr replication create -r {registry_name} -l {replication_loc}')
        self.cmd('acr show-endpoints --name {registry_name} --resource-group {rg}', checks=[
            self.check('length(dataEndpoints)', 2),
            self.check('dataEndpoints[0].endpoint', '{}.{}.data.{}'.format(self.kwargs['registry_name'], self.kwargs['replication_loc'], suffix)),
            self.check('dataEndpoints[1].endpoint', '{}.{}.data.{}'.format(self.kwargs['registry_name'], self.kwargs['rg_loc'], suffix)),
        ])
        self.cmd('acr update --name {registry_name} --resource-group {rg} --data-endpoint-enabled false')
        self.cmd('acr show-endpoints --name {registry_name} --resource-group {rg}', checks=[
            self.check('length(dataEndpoints)', 2),
            self.check('dataEndpoints[0].endpoint', '*.blob.core.windows.net'),
            self.check('dataEndpoints[1].endpoint', '*.blob.core.windows.net'),
        ])

    @ResourceGroupPreparer()
    def test_acr_with_public_network_access(self, resource_group, resource_group_location):
        self.kwargs.update({
            'registry_name': self.create_random_name('testreg', 20),
            'registry_2_name': self.create_random_name('testreg2', 20)
        })

        # test defaults
        self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium',
                 checks=[self.check('publicNetworkAccess', 'Enabled'),
                         self.check('networkRuleBypassOptions', 'AzureServices')])

        self.cmd('acr update --name {registry_name} --resource-group {rg} --public-network-enabled false --allow-trusted-services false',
                 checks=[self.check('publicNetworkAccess', 'Disabled'),
                         self.check('networkRuleBypassOptions', 'None')])

        self.cmd('acr update --name {registry_name} --resource-group {rg} --allow-trusted-services true',
                 checks=[self.check('publicNetworkAccess', 'Disabled'),
                         self.check('networkRuleBypassOptions', 'AzureServices')])

        self.cmd('acr create --name {registry_2_name} --resource-group {rg} --sku premium --public-network-enabled false --allow-trusted-services false',
                 checks=[self.check('publicNetworkAccess', 'Disabled'),
                         self.check('networkRuleBypassOptions', 'None')])

    @ResourceGroupPreparer()
    def test_acr_with_anonymous_pull(self, resource_group, resource_group_location):
        self.kwargs.update({
            'registry_name': self.create_random_name('testreg', 20)
        })
        self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium -l eastus',
                 checks=[self.check('anonymousPullEnabled', False)])
        self.cmd('acr update --name {registry_name} --resource-group {rg} --anonymous-pull-enabled true',
                 checks=[self.check('anonymousPullEnabled', True)])
        self.cmd('acr update --name {registry_name} --resource-group {rg} --anonymous-pull-enabled false',
                 checks=[self.check('anonymousPullEnabled', False)])

    @ResourceGroupPreparer(location='eastus2')
    def test_acr_with_private_endpoint(self, resource_group):
        self.kwargs.update({
            'registry_name': self.create_random_name('testreg', 20),
            'vnet_name': self.create_random_name('testvnet', 20),
            'subnet_name': self.create_random_name('testsubnet', 20),
            'endpoint_name': self.create_random_name('priv_endpoint', 25),
            'endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'second_endpoint_name': self.create_random_name('priv_endpoint', 25),
            'second_endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'description_msg': 'somedescription'
        })

        # create subnet with disabled endpoint network policies
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        result = self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium').get_output_in_json()
        self.kwargs['registry_id'] = result['id']

        # add an endpoint and approve it
        result = self.cmd('network private-endpoint create -n {endpoint_name} -g {rg} --subnet {subnet_name} --vnet-name {vnet_name}  '
                          '--private-connection-resource-id {registry_id} --group-ids registry --connection-name {endpoint_conn_name} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd('acr private-endpoint-connection list -g {rg} --registry-name {registry_name}').get_output_in_json()
        self.kwargs['endpoint_request'] = result[0]['name']

        self.cmd('acr private-endpoint-connection approve -g {rg} --registry-name {registry_name} -n {endpoint_request} --description {description_msg}', checks=[
            self.check('privateLinkServiceConnectionState.status', 'Approved'),
            self.check('privateLinkServiceConnectionState.description', '{description_msg}')
        ])

        # add an endpoint and then reject it
        self.cmd('network private-endpoint create -n {second_endpoint_name} -g {rg} --subnet {subnet_name} --vnet-name {vnet_name} --private-connection-resource-id {registry_id} --group-ids registry --connection-name {second_endpoint_conn_name} --manual-request')
        result = self.cmd('az acr private-endpoint-connection list -g {rg} -r {registry_name}').get_output_in_json()

        # the connection request name starts with the registry / resource name
        self.kwargs['second_endpoint_request'] = [conn['name'] for conn in result if self.kwargs['second_endpoint_name'].lower() in conn['privateEndpoint']['id'].lower()][0]

        self.cmd('acr private-endpoint-connection reject -g {rg} -r {registry_name} -n {second_endpoint_request} --description {description_msg}', checks=[
            self.check('privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('privateLinkServiceConnectionState.description', '{description_msg}')
        ])

        # list endpoints
        self.cmd('acr private-endpoint-connection list -g {rg} -r {registry_name}', checks=[
            self.check('length(@)', '2'),
        ])

        # remove endpoints
        self.cmd('acr private-endpoint-connection delete -g {rg} --registry-name {registry_name} -n {second_endpoint_request}')
        self.cmd('acr private-endpoint-connection show -g {rg} -r {registry_name} -n {endpoint_request}', checks=[
            self.check('privateLinkServiceConnectionState.status', 'Approved'),
            self.check('privateLinkServiceConnectionState.description', '{description_msg}'),
            self.check('name', '{endpoint_request}')
        ])

        self.cmd('acr private-endpoint-connection delete -g {rg} --registry-name {registry_name} -n {endpoint_request}')
        result = self.cmd('acr private-endpoint-connection list -g {rg} -r {registry_name}').get_output_in_json()
        self.assertFalse(result)

    @ResourceGroupPreparer(location="eastus")
    def test_acr_with_zone_redundancy(self, resource_group, resource_group_location):
        self.kwargs.update({
            'registry_1': self.create_random_name('testreg', 20),
            'registry_2': self.create_random_name('testreg2', 20),
            'location_2': 'eastus2',
            'location_3': 'westus2'
        })

        # test defaults
        self.cmd('acr create --name {registry_1} --resource-group {rg} --sku premium',
                 checks=[self.check('zoneRedundancy', 'Disabled')])

        result = self.cmd('acr create --name {registry_2} --resource-group {rg} --sku premium --zone-redundancy Enabled',
                          checks=[self.check('zoneRedundancy', 'Enabled')]).get_output_in_json()

        self.kwargs["home_location"] = result["location"]

        self.cmd('acr replication show --name {home_location} --registry {registry_2} --resource-group {rg}',
                 checks=[self.check('zoneRedundancy', 'Enabled')])

        self.cmd('acr replication create --registry {registry_1}  -g {rg} --location {location_2} --zone-redundancy Enabled',
                 checks=[self.check('zoneRedundancy', 'Enabled')])

        self.cmd('acr replication create --registry {registry_2}  -g {rg} --location {location_2}',
                 checks=[self.check('zoneRedundancy', 'Disabled')])

        self.cmd('acr replication create --registry {registry_2}  -g {rg} --location {location_3} --zone-redundancy Disabled',
                 checks=[self.check('zoneRedundancy', 'Disabled')])

    def assertUserIdentitiesExpected(self, query_identities, result):
        result_identities = [identity.lower() for identity in result['userAssignedIdentities'].keys()]
        self.assertEqual(len(result['userAssignedIdentities']), len(query_identities))
        self.assertEqual(sorted(result_identities), sorted(query_identities))
