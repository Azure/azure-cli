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
    @StorageAccountPreparer()
    def test_storage_blob_lease_oauth(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        local_file = self.create_temp_file(128)
        c = self.create_container(account_info)
        b = self.create_random_name('blob', 24)
        proposed_lease_id = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
        new_lease_id = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
        date = '2016-04-01t12:00z'

        self.oauth_cmd('storage blob upload -c {} -n {} -f "{}"', account_info, c, b, local_file)

        # test lease operations
        self.oauth_cmd('storage blob lease acquire --lease-duration 60 -b {} -c {} '
                       '--if-modified-since {} --proposed-lease-id {}', account_info, b, c, date,
                        proposed_lease_id)
        self.oauth_cmd('storage blob show -n {} -c {}', account_info, b, c) \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', 'fixed'),
                                JMESPathCheck('properties.lease.state', 'leased'),
                                JMESPathCheck('properties.lease.status', 'locked'))
        self.oauth_cmd('storage blob lease change -b {} -c {} --lease-id {} '
                         '--proposed-lease-id {}', account_info, b, c, proposed_lease_id,
                         new_lease_id)
        self.oauth_cmd('storage blob lease renew -b {} -c {} --lease-id {}', account_info, b, c,
                         new_lease_id)
        self.oauth_cmd('storage blob show -n {} -c {}', account_info, b, c) \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', 'fixed'),
                                JMESPathCheck('properties.lease.state', 'leased'),
                                JMESPathCheck('properties.lease.status', 'locked'))
        self.oauth_cmd('storage blob lease break -b {} -c {} --lease-break-period 30',
                         account_info, b, c)
        self.oauth_cmd('storage blob show -n {} -c {}', account_info, b, c) \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', None),
                                JMESPathCheck('properties.lease.state', 'breaking'),
                                JMESPathCheck('properties.lease.status', 'locked'))
        self.oauth_cmd('storage blob lease release -b {} -c {} --lease-id {}', account_info, b, c,
                         new_lease_id)
        self.oauth_cmd('storage blob show -n {} -c {}', account_info, b, c) \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', None),
                                JMESPathCheck('properties.lease.state', 'available'),
                                JMESPathCheck('properties.lease.status', 'unlocked'))