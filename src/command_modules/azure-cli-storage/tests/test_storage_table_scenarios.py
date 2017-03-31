# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck)


class StorageTableScenarioTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(sku='Standard_RAGRS')
    def test_storage_table_stats(self, storage_account):
        self.cmd('storage table stats --account-name {}'.format(storage_account),
                 checks=JMESPathCheck('geoReplication.status', 'live'))
