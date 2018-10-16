# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only


class AcrCommandsTests(ScenarioTest):

    def _core_registry_scenario(self, registry_name, resource_group, location,
                                storage_account_for_update=None):
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

        # test acr storage account update
        if storage_account_for_update is not None:
            self.cmd('acr update -n {} -g {} --storage-account-name {}'.format(
                registry_name, resource_group, storage_account_for_update),
                checks=[self.check('name', registry_name),
                        self.check('location', location)])

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
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_acr_create_with_new_storage(self, resource_group, resource_group_location,
                                         storage_account_for_update):
        registry_name = self.create_random_name('clireg', 20)

        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': resource_group_location,
            'sku': 'Classic',
            'deployment_name': 'Microsoft.ContainerRegistry'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku} --deployment-name {deployment_name}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Classic'),
                         self.check('sku.tier', 'Classic'),
                         self.check('provisioningState', 'Succeeded')])
        self._core_registry_scenario(registry_name, resource_group, resource_group_location,
                                     storage_account_for_update)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_acr_create_with_existing_storage(self, resource_group, resource_group_location,
                                              storage_account_for_update,
                                              storage_account_for_create):
        registry_name = self.create_random_name('clireg', 20)

        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': resource_group_location,
            'sku': 'Classic',
            'sa_for_create': storage_account_for_create,
            'deployment_name': 'Microsoft.ContainerRegistry'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku} --storage-account-name {sa_for_create} --deployment-name {deployment_name}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Classic'),
                         self.check('sku.tier', 'Classic'),
                         self.check('provisioningState', 'Succeeded')])

        self._core_registry_scenario(registry_name, resource_group, resource_group_location,
                                     storage_account_for_update)

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
    def test_acr_create_build_task(self, resource_group, resource_group_location):
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'build_task_name1': 'cliregbuildtask1',
            'build_task_name2': 'cliregbuildtask2',
            'rg_loc': 'eastus',
            'sku': 'Standard',
            # This token requires 'admin:repo_hook' access. Recycle the token after recording tests.
            'git_access_token': 'b67dce55c2d8a654a4c823751a58aac1e59d9641',
            'context': 'https://github.com/xiadu94/BuildTest',
            'image1': 'repo1:tag1',
            'image2': 'repo2:tag2',
            'build_arg': 'key1=value1',
            'secret_build_arg': 'key2=value2',
            'non_default_os_type': 'Windows',
            'non_default_status': 'Disabled',
            'non_default_timeout': '10000',
            'non_default_commit_trigger_enabled': 'false',
            'non_default_base_image_trigger': 'None',
            'non_default_branch': 'dev',
            'non_default_docker_file_path': 'Dockerfile_dev',
            'non_default_no_push': 'true',
            'non_default_no_cache': 'true'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # Create a build task using the minimum required parameters
        self.cmd('acr build-task create -n {build_task_name1} -r {registry_name} --git-access-token {git_access_token} --context {context} --image {image1}',
                 checks=[self.check('name', '{build_task_name1}'),
                         self.check('location', '{rg_loc}'),
                         self.check('alias', '{build_task_name1}'),
                         self.check('platform.osType', 'Linux'),
                         self.check('platform.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('sourceRepository.repositoryUrl', '{context}'),
                         self.check('sourceRepository.sourceControlType', 'GitHub'),
                         self.check('sourceRepository.isCommitTriggerEnabled', True),
                         self.check('properties.baseImageTrigger', 'Runtime'),
                         self.check('properties.branch', 'master'),
                         self.check('properties.dockerFilePath', 'Dockerfile'),
                         self.check('properties.imageNames', ['repo1:tag1']),
                         self.check('properties.buildArguments', []),
                         self.check('properties.isPushEnabled', True),
                         self.check('properties.noCache', False),
                         self.check('properties.provisioningState', 'Succeeded')])

        # Create a build task using all parameters
        self.cmd('acr build-task create -n {build_task_name2} -r {registry_name} --git-access-token {git_access_token} --context {context} --image {image1}'
                 ' --os {non_default_os_type} --status {non_default_status} --timeout {non_default_timeout} --commit-trigger-enabled {non_default_commit_trigger_enabled}'
                 ' --base-image-trigger {non_default_base_image_trigger} --branch {non_default_branch} --file {non_default_docker_file_path} --image {image2}'
                 ' --build-arg {build_arg} --secret-build-arg {secret_build_arg} --no-push {non_default_no_push} --no-cache {non_default_no_cache}',
                 checks=[self.check('name', '{build_task_name2}'),
                         self.check('location', '{rg_loc}'),
                         self.check('alias', '{build_task_name2}'),
                         self.check('platform.osType', '{non_default_os_type}'),
                         self.check('platform.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', '{non_default_status}'),
                         self.check('timeout', '{non_default_timeout}'),
                         self.check('sourceRepository.repositoryUrl', '{context}'),
                         self.check('sourceRepository.sourceControlType', 'GitHub'),
                         self.check('sourceRepository.isCommitTriggerEnabled', False),
                         self.check('properties.baseImageTrigger', '{non_default_base_image_trigger}'),
                         self.check('properties.branch', '{non_default_branch}'),
                         self.check('properties.dockerFilePath', '{non_default_docker_file_path}'),
                         self.check('properties.imageNames', ['repo1:tag1', 'repo2:tag2']),
                         self.check('properties.buildArguments[0].name', 'key1'),
                         self.check('properties.buildArguments[0].value', 'value1'),
                         self.check('properties.isPushEnabled', False),
                         self.check('properties.noCache', True),
                         self.check('properties.provisioningState', 'Succeeded')])

        self.cmd('acr build-task list -r {registry_name}',
                 checks=[self.check('[0].name', '{build_task_name1}'),
                         self.check('[1].name', '{build_task_name2}')])

        # trigger a build from the build task
        response = self.cmd('acr build-task run -n {build_task_name1} -r {registry_name} --no-logs',
                            checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/builds'),
                                    self.check('status', 'Succeeded')]).get_output_in_json()

        self.kwargs.update({
            'build_id': response['buildId']
        })

        # list all builds from the build task
        self.cmd('acr build-task list-builds -n {build_task_name1} -r {registry_name}',
                 checks=[self.check('[0].type', 'Microsoft.ContainerRegistry/registries/builds'),
                         self.check('[0].buildId', '{build_id}'),
                         self.check('[0].isArchiveEnabled', False)])

        self.cmd('acr build-task show -n {build_task_name1} -r {registry_name}',
                 checks=[self.check('name', '{build_task_name1}')])
        self.cmd('acr build-task show -n {build_task_name2} -r {registry_name}',
                 checks=[self.check('name', '{build_task_name2}')])

        self.cmd('acr build-task show -n {build_task_name2} -r {registry_name} --with-secure-properties',
                 checks=[self.check('name', '{build_task_name2}'),
                         self.check('location', '{rg_loc}'),
                         self.check('alias', '{build_task_name2}'),
                         self.check('platform.osType', '{non_default_os_type}'),
                         self.check('platform.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', '{non_default_status}'),
                         self.check('timeout', '{non_default_timeout}'),
                         self.check('sourceRepository.repositoryUrl', '{context}'),
                         self.check('sourceRepository.sourceControlType', 'GitHub'),
                         self.check('sourceRepository.isCommitTriggerEnabled', False),
                         self.check('sourceRepository.sourceControlAuthProperties.token', '{git_access_token}'),
                         self.check('sourceRepository.sourceControlAuthProperties.tokenType', 'PAT'),
                         self.check('sourceRepository.sourceControlAuthProperties.scope', 'repo'),
                         self.check('properties.baseImageTrigger', '{non_default_base_image_trigger}'),
                         self.check('properties.branch', '{non_default_branch}'),
                         self.check('properties.dockerFilePath', '{non_default_docker_file_path}'),
                         self.check('properties.imageNames', ['repo1:tag1', 'repo2:tag2']),
                         self.check('properties.buildArguments[0].name', 'key1'),
                         self.check('properties.buildArguments[0].value', 'value1'),
                         self.check('properties.buildArguments[0].isSecret', False),
                         self.check('properties.buildArguments[1].name', 'key2'),
                         self.check('properties.buildArguments[1].value', 'value2'),
                         self.check('properties.buildArguments[1].isSecret', True),
                         self.check('properties.isPushEnabled', False),
                         self.check('properties.noCache', True),
                         self.check('properties.provisioningState', 'Succeeded')])

        # update the first build task using non-default parameter values
        self.cmd('acr build-task update -n {build_task_name1} -r {registry_name} --git-access-token {git_access_token} --context {context} --image {image1}'
                 ' --os {non_default_os_type} --status {non_default_status} --timeout {non_default_timeout} --commit-trigger-enabled {non_default_commit_trigger_enabled}'
                 ' --base-image-trigger {non_default_base_image_trigger} --branch {non_default_branch} --file {non_default_docker_file_path} --image {image2}'
                 ' --build-arg {build_arg} --secret-build-arg {secret_build_arg} --no-push {non_default_no_push} --no-cache {non_default_no_cache}',
                 checks=[self.check('name', '{build_task_name1}'),
                         self.check('location', '{rg_loc}'),
                         self.check('alias', '{build_task_name1}'),
                         self.check('platform.osType', '{non_default_os_type}'),
                         self.check('platform.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', '{non_default_status}'),
                         self.check('timeout', '{non_default_timeout}'),
                         self.check('sourceRepository.repositoryUrl', '{context}'),
                         self.check('sourceRepository.sourceControlType', 'GitHub'),
                         self.check('sourceRepository.isCommitTriggerEnabled', False),
                         self.check('properties.baseImageTrigger', '{non_default_base_image_trigger}'),
                         self.check('properties.branch', '{non_default_branch}'),
                         self.check('properties.dockerFilePath', '{non_default_docker_file_path}'),
                         self.check('properties.imageNames', ['repo1:tag1', 'repo2:tag2']),
                         self.check('properties.buildArguments[0].name', 'key1'),
                         self.check('properties.buildArguments[0].value', 'value1'),
                         self.check('properties.isPushEnabled', False),
                         self.check('properties.noCache', True),
                         self.check('properties.provisioningState', 'Succeeded')])

        # update a build of the first task
        self.cmd('acr build-task update-build -r {registry_name} --build-id {build_id} --no-archive false',
                 checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/builds'),
                         self.check('buildId', '{build_id}'),
                         self.check('isArchiveEnabled', True),
                         self.check('provisioningState', 'Succeeded')])

        # test build task delete
        self.cmd('acr build-task delete -n {build_task_name1} -r {registry_name}')
        self.cmd('acr build-task delete -n {build_task_name2} -r {registry_name}')

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg}')

    @ResourceGroupPreparer()
    @record_only()
    def test_acr_image_import(self, resource_group):
        '''There are six test cases in the function.
        Case 1: Import image from a regsitry in a different subscription from the current one
        Case 2: Import image from one regsitry to another where both registries belong to the same subscription
        Case 3: Import image to the target regsitry and keep the repository:tag the same as that in the source
        Case 4: Import image to enable multiple tags in the target registry
        Case 5: Import image within the same registry
        Case 6: Import image by manifest digest
        '''

        registry_name = self.create_random_name("targetregsitry", 20)

        '''
        To be able to run the tests, we are assuming the following resources before the test:
        Current active cloud account and subscription.
        Two source registries, one in the subscription other than the current one and another in the subscription the same as the current one.
        Two source images each of which stays in a different source registries mentioned above.
        '''
        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': 'eastus',
            'sku': 'Standard',
            'resource_id': '/subscriptions/a7ee80a4-3d5e-45c2-9378-36e8d98f4d13/resourceGroups/resourcegroupdiffsub/providers/Microsoft.ContainerRegistry/registries/sourceregistrydiffsub',
            'source_image_diff_sub': 'builder:latest',
            'source_image_same_sub': 'sourceregistrysamesub.azurecr.io/builder:latest',
            'source_image_same_registry': '{}.azurecr.io/builder:latest'.format(registry_name),
            'source_image_by_digest': 'sourceregistrysamesub.azurecr.io/builder@sha256:bc3842ba36fcc182317c07a8643daa4a8e4e7aed45958b1f7e2a2b30c2f5a64f',
            'tag_diff_sub': 'repository_diff_sub:tag_diff_sub',
            'tag_same_sub': 'repository_same_sub:tag_same_sub',
            'tag_multitag1': 'repository_multi1:tag_multi1',
            'tag_multitag2': 'repository_multi2:tag_multi2',
            'tag_same_registry': 'repository_same_registry:tag_same_registry',
            'tag_by_digest': 'repository_by_digest:tag_by_digest'
        })

        # create a target registry to hold the imported images
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # Case 1: Import image from a regsitry in a different subscription from the current one
        self.cmd('acr import -n {registry_name} -r {resource_id} --source {source_image_diff_sub} -t {tag_diff_sub}')

        # Case 2: Import image from one regsitry to another where both registries belong to the same subscription
        self.cmd('acr import -n {registry_name} --source {source_image_same_sub} -t {tag_same_sub}')

        # Case 3: Import image to the target regsitry and keep the repository:tag the same as that in the source
        self.cmd('acr import -n {registry_name} --source {source_image_same_sub}')

        # Case 4: Import image to enable multiple tags in the target registry
        self.cmd('acr import -n {registry_name} --source {source_image_same_sub} -t {tag_multitag1} -t {tag_multitag2}')

        # Case 5: Import image within the same registry
        self.cmd('acr import -n {registry_name} --source {source_image_same_registry} -t {tag_same_registry}')

        # Case 6: Import image by manifest digest
        self.cmd('acr import -n {registry_name} --source {source_image_by_digest} -t {tag_by_digest}')
