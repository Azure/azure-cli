# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck)


class StorageQueueScenarioTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(sku='Standard_RAGRS')
    def test_storage_queue_stats(self, storage_account):
        self.cmd('storage queue stats --account-name {}'.format(storage_account),
                 checks=JMESPathCheck('geoReplication.status', 'live'))
