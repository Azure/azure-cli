# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, record_only


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

        if registry['sku']['name'] == 'Standard':
            self.cmd('acr show-usage -n {} -g {}'.format(registry_name, resource_group))

        # enable admin user
        self.cmd('acr update -n {} -g {} --tags foo=bar cat --admin-enabled true'.format(registry_name, resource_group),
                 checks=[self.check('name', registry_name),
                         self.check('location', location),
                         self.check('tags', {'cat': '', 'foo': 'bar'}),
                         self.check('adminUserEnabled', True),
                         self.check('provisioningState', 'Succeeded')])

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
        self.cmd('acr delete -n {} -g {}'.format(registry_name, resource_group))

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
            'sku': 'Standard'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
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
        self.cmd('acr delete -n {registry_name} -g {rg}')

    @ResourceGroupPreparer()
    def test_acr_create_replication(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)
        # replication location should be different from registry location
        replication_location = 'southcentralus'
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
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('acr replication list -r {registry_name}',
                 checks=[self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[1].provisioningState', 'Succeeded')])
        self.cmd('acr replication show -n {replication_name} -r {registry_name}',
                 checks=[self.check('name', '{replication_name}'),
                         self.check('provisioningState', 'Succeeded')])

        # update replication
        self.cmd('acr replication update -n {replication_name} -r {registry_name} --tags {tags}',
                 checks=[self.check('name', '{replication_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('tags', {'key': 'value'})])

        # test replication delete
        self.cmd('acr replication delete -n {replication_name} -r {registry_name}')
        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg}')

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
        service_principal_username = self.cmd('keyvault secret show --id https://imageimport.vault.azure.net/secrets/SPusername').get_output_in_json()['value']
        service_principal_password = self.cmd('keyvault secret show --id https://imageimport.vault.azure.net/secrets/SPpassword').get_output_in_json()['value']

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
