# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageCorsTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account')
    def test_storage_cors_scenario(self, resource_group, account):
        connection_string = self.cmd('storage account show-connection-string -n {} -g {} -otsv'
                                     .format(account, resource_group)).output

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string),
                 checks=JMESPathCheck('length(@)', 0))

        self.cmd('storage cors add --method POST --origins http://example.com --services bfq '
                 '--max-age 60 --connection-string "{}"'.format(connection_string))

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string),
                 checks=JMESPathCheck('length(@)', 3))

        self.cmd('storage cors clear --services bf --connection-string "{}"'
                 .format(connection_string))

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string),
                 checks=JMESPathCheck('length(@)', 1))

        self.cmd('storage cors clear --services bfq --connection-string "{}"'
                 .format(connection_string))

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string),
                 checks=JMESPathCheck('length(@)', 0))
