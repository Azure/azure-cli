# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


class StorageOauthTests(StorageScenarioMixin, ScenarioTest):
    def oauth_cmd(self, cmd, *args, **kwargs):
        return self.cmd(cmd + ' --auth-mode login', *args, **kwargs)

    @api_version_constraint(ResourceType.DATA_STORAGE_FILEDATALAKE, min_api='2018-11-09')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_oauth')
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_storage_filedatalake_oauth(self, resource_group, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'account': storage_account,
            'filesystem': self.create_random_name(prefix='filesystem', length=20),
            'directory': self.create_random_name(prefix='directory', length=20),
            'local_dir': self.create_temp_dir(),
            'local_file': self.create_temp_file(1),
            'file': self.create_random_name(prefix='file', length=20)
        })

        self.oauth_cmd('storage fs create -n {filesystem} --account-name {account}')

        self.oauth_cmd('storage fs exists -n {filesystem} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage fs show --n {filesystem} --account-name {account}', checks=[
            JMESPathCheck('name', self.kwargs['filesystem'])])

        self.oauth_cmd('storage fs list --account-name {account}', checks=[
            JMESPathCheck('length(@)', 1)])

        # Create directory
        self.oauth_cmd('storage fs directory create -n {directory} -f {filesystem} --account-name {account}')

        self.oauth_cmd('storage fs directory exists -n {directory} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage fs directory show --n {directory} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('name', self.kwargs['directory'])])

        self.oauth_cmd('storage fs directory list -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('length(@)', 1)])

        # Create file
        self.oauth_cmd('storage fs file create -p {file} -f {filesystem} --account-name {account}')

        # Upload a file
        self.oauth_cmd('storage fs file upload -f {filesystem} -s "{local_file}" -p {file} '
                       '--account-name {account}')

        self.oauth_cmd('storage fs file exists -p {file} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage fs file list -f {filesystem} --account-name {account} ', checks=[
            JMESPathCheck('length(@)', 2)])
        self.oauth_cmd('storage fs file list -f {filesystem} --account-name {account} --exclude-dir', checks=[
            JMESPathCheck('length(@)', 1)])

        self.oauth_cmd('storage fs file show -p {file} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('name', self.kwargs['file'])])

        # download the file
        self.kwargs['download_path'] = os.path.join(self.kwargs.get('local_dir'), 'test.file')
        self.oauth_cmd('storage fs file download -p {file} -f {filesystem} -d "{download_path}"'
                       ' --account-name {account}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2', name_prefix='blob')
    def test_storage_blob_service_properties_oauth(self):
        # service properties will need Owner/Contributor role
        self.oauth_cmd('storage blob service-properties show --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', False),
                                JMESPathCheck('hourMetrics.enabled', True),
                                JMESPathCheck('minuteMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.includeApis', None),
                                JMESPathCheck('logging.delete', False))

        self.oauth_cmd('storage blob service-properties update --static-website --index-document index.html '
                       '--404-document error.html --account-name {sa}')\
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', True),
                                JMESPathCheck('staticWebsite.errorDocument_404Path', 'error.html'),
                                JMESPathCheck('staticWebsite.indexDocument', 'index.html'),
                                JMESPathCheck('minuteMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.includeApis', None),
                                JMESPathCheck('logging.delete', False))

        self.oauth_cmd('storage blob service-properties update --delete-retention --delete-retention-period 1 '
                       '--account-name {sa}') \
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', True),
                                JMESPathCheck('staticWebsite.errorDocument_404Path', 'error.html'),
                                JMESPathCheck('staticWebsite.indexDocument', 'index.html'),
                                JMESPathCheck('deleteRetentionPolicy.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.days', 1),
                                JMESPathCheck('minuteMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.includeApis', None),
                                JMESPathCheck('logging.delete', False))

        self.oauth_cmd('storage blob service-properties update --set hourMetrics.enabled=false --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', True),
                                JMESPathCheck('staticWebsite.errorDocument_404Path', 'error.html'),
                                JMESPathCheck('staticWebsite.indexDocument', 'index.html'),
                                JMESPathCheck('deleteRetentionPolicy.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.days', 1),
                                JMESPathCheck('hourMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.includeApis', None),
                                JMESPathCheck('logging.delete', False))

        self.oauth_cmd('storage blob service-properties update --set minuteMetrics.enabled=true '
                       'minuteMetrics.includeApis=true --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', True),
                                JMESPathCheck('staticWebsite.errorDocument_404Path', 'error.html'),
                                JMESPathCheck('staticWebsite.indexDocument', 'index.html'),
                                JMESPathCheck('deleteRetentionPolicy.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.days', 1),
                                JMESPathCheck('hourMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.enabled', True),
                                JMESPathCheck('minuteMetrics.includeApis', True),
                                JMESPathCheck('logging.delete', False))

        self.oauth_cmd('storage blob service-properties update --set logging.delete=true --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', True),
                                JMESPathCheck('staticWebsite.errorDocument_404Path', 'error.html'),
                                JMESPathCheck('staticWebsite.indexDocument', 'index.html'),
                                JMESPathCheck('deleteRetentionPolicy.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.days', 1),
                                JMESPathCheck('hourMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.enabled', True),
                                JMESPathCheck('minuteMetrics.includeApis', True),
                                JMESPathCheck('logging.delete', True))

        self.oauth_cmd('storage blob service-properties show --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('staticWebsite.enabled', True),
                                JMESPathCheck('staticWebsite.errorDocument_404Path', 'error.html'),
                                JMESPathCheck('staticWebsite.indexDocument', 'index.html'),
                                JMESPathCheck('deleteRetentionPolicy.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.days', 1),
                                JMESPathCheck('hourMetrics.enabled', False),
                                JMESPathCheck('minuteMetrics.enabled', True),
                                JMESPathCheck('minuteMetrics.includeApis', True),
                                JMESPathCheck('logging.delete', True))
