# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime, timedelta
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, JMESPathCheckExists, NoneCheck, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk.decorators import serial_test
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageADLSUploadLiveTests(LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2', hns=True)
    def test_storage_file_upload_2G_file(self, resource_group, storage_account):
        file_size_kb = 2 * 1024 * 1024
        file_system = self.create_random_name(prefix='cont', length=24)
        local_file = self.create_temp_file(file_size_kb, full_random=True)
        file_name = self.create_random_name(prefix='adls', length=24)
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                               .format(storage_account, resource_group)).output

        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)

        self.cmd('storage fs create -n {}'.format(file_system))

        self.cmd('storage fs file exists -p {} -f {}'.format(file_name, file_system),
                 checks=JMESPathCheck('exists', False))

        self.cmd('storage fs file upload -f {} -s "{}" -p {} '.format(file_system, local_file, file_name))

        self.cmd('storage fs file exists -f {} -p {}'.format(file_system, file_name),
                 checks=JMESPathCheck('exists', True))

        self.cmd('storage fs file show -p {} -f {}'.format(file_name, file_system),
                 checks=[JMESPathCheck('size', file_size_kb * 1024)])
