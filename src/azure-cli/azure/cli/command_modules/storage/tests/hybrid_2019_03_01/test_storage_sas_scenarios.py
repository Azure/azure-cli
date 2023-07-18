# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, live_only)
from ..storage_test_util import StorageScenarioMixin


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

        # test sas-token for a fileshare
        sas = self.cmd('storage share generate-sas -n {share} --account-name {account} --https-only '
                       '--permissions dlrw --expiry {expiry} -otsv').output.strip()
        self.kwargs['share_sas'] = sas
        self.cmd('storage file upload --share-name {share} --source "{local_file}" -p {file} '
                 '--account-name {account} --sas-token "{share_sas}"')

        # test sas-token for a file
        sas = self.cmd('storage file generate-sas -s {share} -p {file} --account-name {account} --https-only '
                       '--permissions cdrw --expiry {expiry} -otsv').output.strip()
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

        # test sas-token for a container
        sas = self.cmd('storage container generate-sas -n {container} --account-name {account} --https-only '
                       '--permissions dlrw --expiry {expiry} -otsv').output.strip()
        self.kwargs['container_sas'] = sas
        self.cmd('storage blob upload -c {container} -f "{local_file}" -n {blob} '
                 '--account-name {account} --sas-token "{container_sas}"')

        # test sas-token for a file
        sas = self.cmd('storage blob generate-sas -c {container} -n {blob} --account-name {account} --https-only '
                       '--permissions acdrw --expiry {expiry} -otsv').output.strip()
        self.kwargs['blob_sas'] = sas
        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}') \
            .assert_with_checks(JMESPathCheck('name', blob_name))
