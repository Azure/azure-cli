# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, JMESPathCheckExists, NoneCheck, live_only)
from ..storage_test_util import StorageScenarioMixin
from knack.util import CLIError
from datetime import datetime, timedelta

class StorageSASScenario(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_container_access_policy_scenario(self, resource_group, storage_account):
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        account_info = self.get_account_info(resource_group, storage_account)
        container = self.create_container(account_info)
        local_file = self.create_temp_file(128, full_random=False)
        blob_name = self.create_random_name('blob', 16)
        policy = self.create_random_name('policy', 16)

        self.storage_cmd('storage container policy create -c {} -n {} --expiry {} --permissions racwdxyltfmei',
                         account_info,
                         container, policy, expiry)
        self.storage_cmd('storage container policy list -c {} ', account_info, container) \
            .assert_with_checks(JMESPathCheckExists('{}.expiry'.format(policy)),
                                JMESPathCheck('{}.permission'.format(policy), 'racwdxyltmei'))
        self.storage_cmd('storage container policy show -c {} -n {} ', account_info, container, policy, expiry) \
            .assert_with_checks(JMESPathCheckExists('expiry'),
                                JMESPathCheck('permission', 'racwdxyltmei'))

        sas = self.storage_cmd('storage blob generate-sas -n {} -c {} --policy-name {} -otsv ', account_info, blob_name,
                               container, policy).output.strip()

        self.storage_cmd('storage blob upload -n {} -c {} -f "{}" --sas-token "{}" ', account_info, blob_name,
                         container,
                         local_file, sas)

        new_start = (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        new_expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        self.storage_cmd('storage container policy update -c {} -n {} --permissions rwdxl --start {} --expiry {}',
                         account_info, container,
                         policy, new_start, new_expiry)
        self.storage_cmd('storage container policy show -c {} -n {} ', account_info, container, policy) \
            .assert_with_checks(JMESPathCheckExists('expiry'),
                                JMESPathCheck('permission', 'rwdxl'))
        self.storage_cmd('storage container policy delete -c {} -n {} ', account_info, container, policy)
        self.storage_cmd('storage container policy list -c {} ', account_info, container) \
            .assert_with_checks(NoneCheck())