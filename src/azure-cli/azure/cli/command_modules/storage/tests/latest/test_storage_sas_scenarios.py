# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, live_only)
from ..storage_test_util import StorageScenarioMixin
from knack.util import CLIError

class StorageSASScenario(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_file_sas_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        account_info = self.get_account_info(resource_group, storage_account)
        share = self.create_share(account_info)
        local_file = self.create_temp_file(128, full_random=False)
        file_name = self.create_random_name('file', 16) + '.txt'

        self.kwargs.update({
            'expiry': expiry,
            'account': storage_account,
            'share': share,
            'local_file': local_file,
            'file': file_name
        })

        # test sas-token for a fileshare with account key
        sas = self.storage_cmd('storage share generate-sas -n {} --https-only --permissions dlrw --expiry {} -otsv',
                               account_info, share, expiry).output.strip()
        self.kwargs['share_sas'] = sas
        self.cmd('storage file upload --share-name {share} --source "{local_file}" -p {file} '
                 '--account-name {account} --sas-token "{share_sas}"')

        # test sas-token for a file with account key
        sas = self.storage_cmd(
            'storage file generate-sas -s {} -p {} --https-only --permissions cdrw --expiry {} -otsv',
            account_info, share, file_name, expiry).output.strip()
        self.kwargs['file_sas'] = sas
        self.cmd('storage file show -s {share} -p {file} --account-name {account} --sas-token {file_sas}') \
            .assert_with_checks(JMESPathCheck('name', file_name))

        # connection string
        connection_str = self.cmd('storage account show-connection-string -n {account}  --query connectionString '
                                  '-otsv').output.strip()
        self.kwargs['con_str'] = connection_str
        # test sas-token for a fileshare with connection string
        sas = self.cmd('storage share generate-sas -n {share} --https-only --permissions dlrw --expiry {expiry} '
                       '--connection-string "{con_str}" -otsv').output.strip()
        self.kwargs['share_sas'] = sas
        self.cmd('storage file upload --share-name {share} --source "{local_file}" -p {file} '
                 '--account-name {account} --sas-token "{share_sas}"')

        # test sas-token for a file with connection string
        sas = self.cmd(
            'storage file generate-sas -s {share} -p {file} --https-only --permissions cdrw --expiry {expiry} '
            '--connection-string {con_str} -otsv').output.strip()
        self.kwargs['file_sas'] = sas
        self.cmd('storage file show -s {share} -p {file} --account-name {account} --sas-token {file_sas}') \
            .assert_with_checks(JMESPathCheck('name', file_name))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_sas_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        account_info = self.get_account_info(resource_group, storage_account)
        container = self.create_container(account_info)
        local_file = self.create_temp_file(128, full_random=False)
        blob_name = self.create_random_name('blob', 16)

        self.kwargs.update({
            'expiry': expiry,
            'account': storage_account,
            'container': container,
            'local_file': local_file,
            'blob': blob_name
        })

        # account key
        # test sas-token for a container
        sas = self.storage_cmd('storage container generate-sas -n {} --https-only --permissions dlrw --expiry {} -otsv',
                               account_info, container, expiry).output.strip()
        self.kwargs['container_sas'] = sas
        self.cmd('storage blob upload -c {container} -f "{local_file}" -n {blob} '
                 '--account-name {account} --sas-token "{container_sas}"')

        # test sas-token for a file
        sas = self.storage_cmd('storage blob generate-sas -c {} -n {} --https-only --permissions acdrw --expiry {} '
                               '-otsv', account_info, container, blob_name, expiry).output.strip()
        self.kwargs['blob_sas'] = sas
        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}') \
            .assert_with_checks(JMESPathCheck('name', blob_name))

        # connection string
        connection_str = self.cmd('storage account show-connection-string -n {account}  --query connectionString '
                                  '-otsv').output.strip()
        self.kwargs['con_str'] = connection_str
        # test sas-token for a container
        sas = self.cmd('storage container generate-sas -n {container} --https-only --permissions racwdxyltfmei '
                       '--connection-string {con_str} --expiry {expiry} -otsv').output.strip()
        self.kwargs['container_sas'] = sas
        self.assertIn('sig=', sas, 'SAS token {} does not contain sig segment'.format(sas))
        self.assertIn('se=', sas, 'SAS token {} does not contain se(expiry) segment'.format(sas))
        self.assertIn('sp=racwdxyltfmei', sas, 'SAS token {} does not contain permission segment'.format(sas))
        self.assertIn('spr=https', sas, 'SAS token {} does not contain https segment'.format(sas))
        self.cmd('storage blob upload -c {container} -f "{local_file}" -n {blob} '
                 '--account-name {account} --sas-token "{container_sas}" --overwrite')

        # test sas-token for a blob
        sas = self.cmd('storage blob generate-sas -c {container} -n {blob} --account-name {account} --https-only '
                       '--permissions racwdxytmei --expiry {expiry} -otsv').output.strip()
        self.kwargs['blob_sas'] = sas
        self.assertIn('sig=', sas, 'SAS token {} does not contain sig segment'.format(sas))
        self.assertIn('se=', sas, 'SAS token {} does not contain se(expiry) segment'.format(sas))
        self.assertIn('sp=racwdxytmei', sas, 'SAS token {} does not contain permission segment'.format(sas))
        self.assertIn('spr=https', sas, 'SAS token {} does not contain https segment'.format(sas))
        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}') \
            .assert_with_checks(JMESPathCheck('name', blob_name))

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='queuesas', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_queue_sas_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        account_info = self.get_account_info(resource_group, storage_account)
        queue = self.create_random_name('queue', 24)

        self.storage_cmd('storage queue create -n {} --fail-on-exist --metadata a=b c=d', account_info, queue)\
            .assert_with_checks(JMESPathCheck('created', True))

        sas = self.storage_cmd('storage queue generate-sas -n {} --permissions r --expiry {}',
                               account_info, queue, expiry).output
        self.assertIn('sig', sas, 'The sig segment is not in the sas {}'.format(sas))

        self.cmd('storage queue exists -n {} --account-name {} --sas-token {}'.format(queue, storage_account, sas),
                 checks=JMESPathCheck('exists', True))
        self.storage_cmd('storage queue policy create -n testqp -q {} --permissions r --expiry {}',
                         account_info, queue, expiry)

        sas2 = self.storage_cmd('storage queue generate-sas -n {} --policy-name testqp', account_info, queue).output
        self.assertIn('sig', sas2, 'The sig segment is not in the sas {}'.format(sas2))

        self.cmd('storage queue exists -n {} --account-name {} --sas-token {}'.format(queue, storage_account, sas2),
                 checks=JMESPathCheck('exists', True))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_account_sas_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        connection_str = self.cmd('storage account show-connection-string -n {} -otsv'.format(storage_account)).output
        sas = self.cmd('storage account generate-sas --resource-types co --services b '
                       '--expiry {} --permissions r --https-only --connection-string {}'
                       .format(expiry, connection_str)).output.strip()
        self.assertIn('sig=', sas, 'SAS token {} does not contain sig segment'.format(sas))
        self.assertIn('se=', sas, 'SAS token {} does not contain se segment'.format(sas))

        account_info = self.get_account_info(resource_group, storage_account)
        container = self.create_container(account_info)
        blob_name = self.create_random_name('blob', 16)
        self.cmd('storage blob exists -c {} -n {} --account-name {} --sas-token {}'
                 .format(container, blob_name, storage_account, sas),
                 checks=JMESPathCheck('exists', False))

        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaises(CLIError):
            self.cmd('storage account generate-sas --resource-types o --services b --expiry 2000-01-01 '
                     '--permissions r --account-name ""')

        invalid_connection_string = "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;"
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('storage account generate-sas --resource-types o --services b --expiry 2000-01-01 '
                     '--permissions r --connection-string {}'.format(invalid_connection_string))

        sas = self.storage_cmd('storage account generate-sas --resource-types sco --services bqtf '
                               '--expiry 2046-12-31T08:23Z --permissions rwdxylacupfti --https-only ',
                               account_info).output
        self.assertIn('sig=', sas, 'SAS token {} does not contain sig segment'.format(sas))
        self.assertIn('se=', sas, 'SAS token {} does not contain se(expiry) segment'.format(sas))
        self.assertIn('sp=rwdxylacupfti', sas, 'SAS token {} does not contain permission segment'.format(sas))
        self.assertIn('spr=https', sas, 'SAS token {} does not contain https segment'.format(sas))
        self.assertRegex(sas, '.*ss=[bqtf]{4}.*', 'SAS token {} does not contain services segment'.format(sas))
        self.assertRegex(sas, '.*srt=[sco]{3}.*', 'SAS token {} does not contain resource type segment'.format(sas))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(hns=True, kind='StorageV2')
    def test_storage_fs_sas_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        account_info = self.get_account_info(resource_group, storage_account)
        file_system = self.create_file_system(account_info)

        self.kwargs.update({
            'expiry': expiry,
            'account': storage_account,
            'fs': file_system,
            'local_file': self.create_temp_file(128, full_random=False),
            'file': self.create_random_name('file', 16),
            'directory': self.create_random_name('dir', 16)
        })

        # ----account key----
        # test sas-token for a file system
        fs_sas = self.storage_cmd('storage fs generate-sas -n {} --https-only --permissions dlrwopm --expiry {} -otsv',
                                  account_info, file_system, expiry).output.strip()
        self.kwargs['fs_sas'] = fs_sas

        self.cmd('storage fs directory list -f {fs} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 0)
        ])
        self.cmd('storage fs directory create -f {fs} -n {directory} --account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs directory list -f {fs} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('storage fs file list -f {fs} --path {directory} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 0)
        ])
        self.cmd('storage fs file upload -f {fs} -s "{local_file}" -p {directory}/{file} '
                 '--account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs file list -f {fs} --path {directory} --account-name {account} --sas-token "{fs_sas}"',
                 checks=[self.check('length(@)', 1)])

        self.cmd('storage fs file move -f {fs} --new-path {fs}/{file} -p {directory}/{file} '
                 '--account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs file list -f {fs} --path {directory} --exclude-dir --account-name {account} '
                 '--sas-token "{fs_sas}"', checks=[self.check('length(@)', 0)])

        self.cmd('storage fs file list -f {fs} --exclude-dir --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 1)])

        # ----connection string----
        # test sas-token for a file system
        connection_str = self.cmd('storage account show-connection-string -n {account}  --query connectionString '
                                  '-otsv').output.strip()
        self.kwargs['con_str'] = connection_str

        sas = self.cmd('storage fs generate-sas -n {fs} --https-only --permissions dlrwop '
                       '--connection-string {con_str} --expiry {expiry} -otsv').output.strip()
        self.kwargs['fs_sas'] = sas

        self.kwargs['new_dir'] = self.create_random_name('ndir', 16)
        self.kwargs['new_file'] = self.create_random_name('nfile', 16)

        self.cmd('storage fs directory list -f {fs} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('storage fs directory create -f {fs} -n {new_dir} --account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs directory list -f {fs} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('storage fs file list -f {fs} --exclude-dir --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('storage fs file upload -f {fs} -s "{local_file}" -p {new_file} '
                 '--account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs file list -f {fs} --exclude-dir --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 2)
        ])

        # ----stored access policy----
        # test sas-token for a file system
        self.kwargs['policy'] = self.create_random_name(prefix='policy', length=16)
        self.cmd('storage container policy create -n {policy} -c {fs} --permissions dlrw '
                 '--connection-string {con_str} --expiry {expiry} -otsv')

        sas = self.cmd('storage fs generate-sas -n {fs} --https-only --policy-name {policy} '
                       '--connection-string {con_str} -otsv').output.strip()
        self.kwargs['fs_sas'] = sas

        self.kwargs['new_dir1'] = self.create_random_name('ndir1', 16)
        self.kwargs['new_file1'] = self.create_random_name('nfile1', 16)

        self.cmd('storage fs directory list -f {fs} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 2)
        ])
        self.cmd('storage fs directory create -f {fs} -n {new_dir1} --account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs directory list -f {fs} --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 3)
        ])

        self.cmd('storage fs file list -f {fs} --exclude-dir --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 2)
        ])
        self.cmd('storage fs file upload -f {fs} -s "{local_file}" -p {new_file1} '
                 '--account-name {account} --sas-token "{fs_sas}"')
        self.cmd('storage fs file list -f {fs} --exclude-dir --account-name {account} --sas-token "{fs_sas}"', checks=[
            self.check('length(@)', 3)
        ])
