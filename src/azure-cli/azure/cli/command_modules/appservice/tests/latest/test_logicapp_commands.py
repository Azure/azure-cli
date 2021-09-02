# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import unittest
from unittest import mock
import os
import time
import tempfile
import requests
import datetime

from azure_devtools.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               StorageAccountPreparer, JMESPathCheck, live_only)
from azure.cli.testsdk.checkers import JMESPathPatternCheck

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long
# In the future, for any reasons the repository get removed, the source code is under "sample-repo-for-deployment-test"
# you can use to rebuild the repository
TEST_REPO_URL = 'https://github.com/yugangw-msft/azure-site-test.git'
WINDOWS_ASP_LOCATION_WEBAPP = 'japanwest'
WINDOWS_ASP_LOCATION_FUNCTIONAPP = 'francecentral'
LINUX_ASP_LOCATION_WEBAPP = 'eastus2'
LINUX_ASP_LOCATION_FUNCTIONAPP = 'ukwest'
WINDOWS_ASP_LOCATION_CHINACLOUD_WEBAPP = 'chinaeast'
DEFAULT_LOCATION = "westus"

class LogicappBasicE2ETest(ScenarioTest):
    
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_logicapp_e2e(self, resource_group):
        logicapp_name = self.create_random_name('logic-e2e', 24)
        plan = self.create_random_name('logic-e2e-plan', 24)
        storage = 'logicappplanstorage'
        plan_id = self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('appservice plan list -g {}'.format(resource_group))
        self.cmd('storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(storage, resource_group, DEFAULT_LOCATION))

        self.cmd('logicapp create -g {} -n {} -p {} -s {}'.format(resource_group, logicapp_name, plan, storage), 
                 checks=[
                         JMESPathCheck('state', 'Running'),
                         JMESPathCheck('name', logicapp_name),
                         JMESPathCheck('hostNames[0]', logicapp_name + '.azurewebsites.net')
                 ]
        )

        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name),
        checks=[
            JMESPathCheck('name', logicapp_name),
            JMESPathCheck('kind', 'functionapp,workflowapp')
        ])

        self.cmd('logicapp list -g {}'.format(resource_group),
        checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', logicapp_name)
        ])

        self.cmd('logicapp delete -g {} -n {}'.format(resource_group, logicapp_name))

        self.cmd('logicapp list -g {}'.format(resource_group),
        checks=[
            JMESPathCheck('length([])', 0)
        ])


if __name__ == '__main__':
    unittest.main()
