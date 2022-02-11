# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.DATA_STORAGE, min_api='2017-11-09')
class StorageOauthTests(StorageScenarioMixin, ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_storage_oauth')
    @StorageAccountPreparer()
    def test_storage_blob_oauth(self, resource_group, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'account': storage_account,
            'container': self.create_random_name(prefix='container', length=20),
            'local_dir': self.create_temp_dir(),
            'local_file': self.create_temp_file(1),
            'blob': self.create_random_name(prefix='blob', length=20)
        })

        self.oauth_cmd('storage container create -n {container} --account-name {account} --public-access off', checks=[
            JMESPathCheck('created', True)])

        # # upload a blob
        self.oauth_cmd('storage blob upload -c {container} -f "{local_file}" -n {blob} --type block '
                       '--account-name {account}')
        self.oauth_cmd('storage blob exists -n {blob} -c {container} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])
        self.oauth_cmd('storage blob list -c {container} --account-name {account}', checks=[
            JMESPathCheck('length(@)', 1)])
        self.oauth_cmd('storage blob show -c {container} --account-name {account} -n {blob}', checks=[
            JMESPathCheck('name', self.kwargs['blob'])])

        # download the blob
        self.kwargs['download_path'] = os.path.join(self.kwargs.get('local_dir'), 'test.file')
        self.oauth_cmd('storage blob download -n {blob} -c {container} --file "{download_path}"'
                       ' --account-name {account}')

    @ResourceGroupPreparer(name_prefix='cli_test_storage_oauth')
    @StorageAccountPreparer()
    def test_storage_queue_oauth(self, resource_group, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'account': storage_account,
            'queue': self.create_random_name(prefix='queue', length=20)
        })

        self.oauth_cmd('storage queue create -n {queue} --account-name {account} --fail-on-exist --metadata a=b c=d',
                       checks=[JMESPathCheck('created', True)])
        self.oauth_cmd('storage queue exists -n {queue} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage queue metadata show -n {queue} --account-name {account}', checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])

        self.oauth_cmd('storage queue metadata update -n {queue} --account-name {account} --metadata e=f g=h')
        self.oauth_cmd('storage queue metadata show -n {queue} --account-name {account}', checks=[
            JMESPathCheck('e', 'f'),
            JMESPathCheck('g', 'h')
        ])
