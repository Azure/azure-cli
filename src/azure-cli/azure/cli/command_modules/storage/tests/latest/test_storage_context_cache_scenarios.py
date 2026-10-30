# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest


class StorageContextCacheTests(ScenarioTest):

    @ResourceGroupPreparer(location='eastus', name_prefix='cli_context_cache')
    def test_storage_context_cache_lifecycle(self, resource_group, resource_group_location):
        self.kwargs.update({
            'cache': self.create_random_name('cache', 24),
            'container': self.create_random_name('container', 24),
            'location': resource_group_location
        })
        self.cmd('storage context-cache check-name --name {cache}', checks=self.check('nameAvailable', True))
        self.cmd('storage context-cache create -g {rg} -n {cache} -l {location} '
                 '--account-kind Regional --description original --tags purpose=cli-test --no-wait')
        self.cmd('storage context-cache wait -g {rg} -n {cache} --created')
        self.cmd('storage context-cache show -g {rg} -n {cache}', checks=[
            self.check('properties.accountKind', 'Regional'),
            self.check('properties.description', 'original'),
            self.check('tags.purpose', 'cli-test')
        ])
        self.cmd('storage context-cache check-name --name {cache}', checks=self.check('nameAvailable', False))
        self.cmd('storage context-cache list -g {rg}',
                 checks=self.check("contains([].name, '{cache}')", True))
        self.cmd('storage context-cache list',
                 checks=self.check("contains([].name, '{cache}')", True))
        self.cmd('storage context-cache update -g {rg} -n {cache} --description updated', checks=[
            self.check('properties.description', 'updated'),
            self.check('properties.accountKind', 'Regional'),
            self.check('tags.purpose', 'cli-test')
        ])

        self.cmd('storage context-cache container create -g {rg} --context-cache-name {cache} -n {container} '
                 '--model-name gpt-4o --provider OpenAI --time-to-live 1 --description original', checks=[
                     self.check('properties.timeToLive', 1),
                     self.check('properties.modelName', 'gpt-4o'),
                     self.check('properties.provider', 'OpenAI')
                 ])
        self.cmd('storage context-cache container update -g {rg} --context-cache-name {cache} -n {container} '
                 '--time-to-live 30 --description updated', checks=[
                     self.check('properties.timeToLive', 30),
                     self.check('properties.description', 'updated')
                 ])
        self.cmd('storage context-cache container show -g {rg} --context-cache-name {cache} -n {container}', checks=[
            self.check('properties.timeToLive', 30),
            self.check('properties.description', 'updated'),
            self.check('properties.modelName', 'gpt-4o'),
            self.check('properties.provider', 'OpenAI')
        ])
        self.cmd('storage context-cache container list -g {rg} --context-cache-name {cache}',
                 checks=self.check("contains([].name, '{container}')", True))
        self.cmd('storage context-cache container delete -g {rg} --context-cache-name {cache} -n {container} --yes')
        self.cmd('storage context-cache container list -g {rg} --context-cache-name {cache}',
                 checks=self.check("contains([].name, '{container}')", False))
        self.cmd('storage context-cache delete -g {rg} -n {cache} --yes')
        self.cmd('storage context-cache list -g {rg}',
                 checks=self.check("contains([].name, '{cache}')", False))

    @ResourceGroupPreparer(location='eastus', name_prefix='cli_context_cache_identity')
    def test_storage_context_cache_managed_identities(self, resource_group, resource_group_location):
        self.kwargs.update({
            'cache': self.create_random_name('cache', 24),
            'location': resource_group_location,
            'identity1': self.create_random_name('identity', 24)
        })
        self.kwargs['identity1_id'] = self.cmd(
            'identity create -g {rg} -n {identity1} -l {location}').get_output_in_json()['id']
        self.cmd('storage context-cache create -g {rg} -n {cache} -l {location} '
                 '--account-kind Regional --description original --identity type=SystemAssigned')
        self.cmd('storage context-cache identity assign -g {rg} -n {cache} '
                 '--user-assigned {identity1_id}', checks=[
                     self.check('type', 'SystemAssigned, UserAssigned'),
                     self.check('length(userAssignedIdentities)', 1)
                 ])
        self.cmd('storage context-cache identity remove -g {rg} -n {cache} --system-assigned', checks=[
            self.check('type', 'UserAssigned'),
            self.check('length(userAssignedIdentities)', 1),
            self.check("contains(keys(userAssignedIdentities), '{identity1_id}')", True)
        ])
        self.cmd('storage context-cache update -g {rg} -n {cache} --description updated', checks=[
            self.check('identity.type', 'UserAssigned'),
            self.check('length(identity.userAssignedIdentities)', 1)
        ])
        self.cmd('storage context-cache identity show -g {rg} -n {cache}', checks=[
            self.check('type', 'UserAssigned'),
            self.check("contains(keys(userAssignedIdentities), '{identity1_id}')", True)
        ])
        self.cmd('storage context-cache identity assign -g {rg} -n {cache} --system-assigned', checks=[
            self.check('type', 'SystemAssigned, UserAssigned'),
            self.check("contains(keys(userAssignedIdentities), '{identity1_id}')", True)
        ])
        self.cmd('storage context-cache identity remove -g {rg} -n {cache} --user-assigned', checks=[
            self.check('type', 'SystemAssigned')
        ])
        self.cmd('storage context-cache identity remove -g {rg} -n {cache} --system-assigned')
        self.cmd('storage context-cache show -g {rg} -n {cache}', checks=[
            self.check("identity == null || identity.type == 'None'", True),
            self.check('properties.description', 'updated'),
            self.check('properties.accountKind', 'Regional')
        ])
        self.cmd('storage context-cache delete -g {rg} -n {cache} --yes')
