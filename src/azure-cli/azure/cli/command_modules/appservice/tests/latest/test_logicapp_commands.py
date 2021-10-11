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
WINDOWS_ASP_LOCATION_LOGICAPP = 'francecentral'
LINUX_ASP_LOCATION_LOGICAPP = 'ukwest'
DEFAULT_LOCATION = "westus"

class LogicappBasicE2ETest(ScenarioTest):
    
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_logicapp_e2e(self, resource_group):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        storage = 'logicpplanstorage1'
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan)).get_output_in_json()['id']
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
            JMESPathCheck('kind', 'functionapp,workflowapp'),
            JMESPathCheck('state', 'Running') # app should be running on creation
        ])

        self.cmd('logicapp list -g {}'.format(resource_group),
        checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', logicapp_name)
        ])

        #restarting a running app
        self.cmd('logicapp restart -g {} -n {}'.format(resource_group, logicapp_name))
        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', logicapp_name)
        ])

        #stopping a running app
        self.cmd('logicapp stop -g {} -n {}'.format(resource_group, logicapp_name))
        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', logicapp_name)
        ])

        #stopping a stopped app
        self.cmd('logicapp stop -g {} -n {}'.format(resource_group, logicapp_name))
        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', logicapp_name)
        ])

        #restarting a stopped app
        self.cmd('logicapp restart -g {} -n {}'.format(resource_group, logicapp_name))
        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', logicapp_name)
        ])

        #starting a stopped app
        self.cmd('logicapp start -g {} -n {}'.format(resource_group, logicapp_name))
        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', logicapp_name)
        ])

        #starting a running app
        self.cmd('logicapp start -g {} -n {}'.format(resource_group, logicapp_name))
        self.cmd('logicapp show -g {} -n {}'.format(resource_group, logicapp_name), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', logicapp_name)
        ])

        self.cmd('logicapp delete -g {} -n {} -y'.format(resource_group, logicapp_name))

        self.cmd('logicapp list -g {}'.format(resource_group),
        checks=[
            JMESPathCheck('length([])', 0)
        ])


class LogicAppOnWindows(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_LOGICAPP)
    @StorageAccountPreparer()
    def test_logicapp_windows(self, resource_group, storage_account):
        logicapp_name = self.create_random_name(
            'logicappwindowsruntime', 40)

        self.cmd('logicapp create -g {} -n {} -c {} -s {} --os-type Windows'
                 .format(resource_group, logicapp_name, WINDOWS_ASP_LOCATION_LOGICAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', logicapp_name),
                     JMESPathCheck('kind', 'functionapp,workflowapp'),
                     JMESPathCheck('hostNames[0]', logicapp_name + '.azurewebsites.net')])
        self.cmd('logicapp delete -g {} -n {} -y'.format(resource_group, logicapp_name))


class LogicAppOnLinux(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_LOGICAPP)
    @StorageAccountPreparer()
    def test_logicapp_on_linux(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        logicapp_name = self.create_random_name(
            prefix='logicapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('logicapp create -g {} -n {} --plan {} -s {}'.format(resource_group, logicapp_name, plan, storage_account), checks=[
            JMESPathCheck('name', logicapp_name)
        ])
        self.cmd('logicapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', logicapp_name),
            JMESPathCheck('[0].kind', 'functionapp,linux,workflowapp')
        ]).get_output_in_json()
        # self.assertTrue('functionapp,workflowapp,linux' in result[0]['kind'])

        
        self.cmd('logicapp delete -g {} -n {} -y'.format(resource_group, logicapp_name))



if __name__ == '__main__':
    unittest.main()
