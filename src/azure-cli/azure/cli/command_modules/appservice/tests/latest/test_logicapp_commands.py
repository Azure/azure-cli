# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from email import message
import json
import unittest
from unittest import mock
import os
import time
import tempfile
import requests
import datetime

from azure.cli.testsdk.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               StorageAccountPreparer, JMESPathCheck, live_only)
from azure.cli.testsdk.checkers import JMESPathPatternCheck
from azure.mgmt.core.tools import resource_id, parse_resource_id

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
        storage = self.create_random_name(prefix='logicstorage', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku WS1'.format(resource_group, plan)).get_output_in_json()['id']
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


    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer(location=DEFAULT_LOCATION)
    def test_logicapp_e2etest_logicapp_versions_e2e(self, resource_group, storage_account):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        runtime_version = '~16'
        functions_version = '4'
        self.cmd('appservice plan create -g {} -n {} --sku WS1'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('appservice plan list -g {}'.format(resource_group))
        self.cmd('logicapp create -g {} -n {} -p {} -s {} --runtime-version {} --functions-version {}'.format(
            resource_group,
            logicapp_name,
            plan,
            storage_account,
            runtime_version,
            functions_version
            ),
        checks=[
                JMESPathCheck('state', 'Running'),
                JMESPathCheck('name', logicapp_name),
                JMESPathCheck('hostNames[0]', logicapp_name + '.azurewebsites.net')
        ])

        # show
        result = self.cmd('logicapp config appsettings list -g {} -n {}'.format(
            resource_group, logicapp_name)).get_output_in_json()
        appsetting_runtime_version = next((x for x in result if x['name'] == 'WEBSITE_NODE_DEFAULT_VERSION'))
        self.assertEqual(appsetting_runtime_version['name'], 'WEBSITE_NODE_DEFAULT_VERSION')
        self.assertEqual(appsetting_runtime_version['value'], '~16')
        appsetting_functions_version = next((x for x in result if x['name'] == 'FUNCTIONS_EXTENSION_VERSION'))
        self.assertEqual(appsetting_functions_version['name'], 'FUNCTIONS_EXTENSION_VERSION')
        self.assertEqual(appsetting_functions_version['value'], '~4')


    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_logicapp_https_only(self, resource_group, storage_account):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku WS1').get_output_in_json()['id']

        self.cmd(f'logicapp create -g {resource_group} -n {logicapp_name} -p {plan} -s {storage_account} --https-only', checks=[JMESPathCheck('httpsOnly', True)])
        self.cmd('logicapp create -g {} -n {} -p {} -s {}'.format(resource_group, logicapp_name, plan, storage_account), checks=[JMESPathCheck('httpsOnly', False)])

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_logicapp_config_appsettings_e2e(self, resource_group):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        storage = self.create_random_name(prefix='logicstorage', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku WS1'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('appservice plan list -g {}'.format(resource_group))
        self.cmd('storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(storage, resource_group, DEFAULT_LOCATION))

        self.cmd('logicapp create -g {} -n {} -p {} -s {}'.format(resource_group, logicapp_name, plan, storage),
                 checks=[
                         JMESPathCheck('state', 'Running'),
                         JMESPathCheck('name', logicapp_name),
                         JMESPathCheck('hostNames[0]', logicapp_name + '.azurewebsites.net')
                 ]
        )

        # update through key value pairs
        self.cmd('logicapp config appsettings set -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(resource_group, logicapp_name)).assert_with_checks([
            JMESPathCheck("[?name=='s1']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])

        # show
        result = self.cmd('logicapp config appsettings list -g {} -n {}'.format(
            resource_group, logicapp_name)).get_output_in_json()
        s2 = next((x for x in result if x['name'] == 's2'))
        self.assertEqual(s2['name'], 's2')
        self.assertEqual(s2['slotSetting'], False)
        self.assertEqual(s2['value'], 'bar')
        # delete
        self.cmd('logicapp config appsettings delete -g {} -n {} --setting-names s1 s2'.format(resource_group, logicapp_name)).assert_with_checks([
            JMESPathCheck("[?name=='s3']|[0].value", None),
            JMESPathCheck("[?name=='WEBSITE_NODE_DEFAULT_VERSION']|[0].value", None)
        ])
        # show
        self.cmd('logicapp config appsettings list -g {} -n {}'.format(
            resource_group, logicapp_name)).assert_with_checks([
                JMESPathCheck("length([?name=='s3'])", 1),
                JMESPathCheck("length([?name=='s1'])", 0),
                JMESPathCheck("length([?name=='s2'])", 0)])

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_logicapp_scale_e2e(self, resource_group):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        storage = self.create_random_name(prefix='logicstorage', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku WS1'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('appservice plan update -g {} -n {} --m 5 --elastic-scale'.format(resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(resource_group))
        self.cmd('storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(storage, resource_group, DEFAULT_LOCATION))

        self.cmd('logicapp create -g {} -n {} -p {} -s {}'.format(resource_group, logicapp_name, plan, storage),
                 checks=[
                         JMESPathCheck('state', 'Running'),
                         JMESPathCheck('name', logicapp_name),
                         JMESPathCheck('hostNames[0]', logicapp_name + '.azurewebsites.net')
                 ]
        )

        # update through key value pairs
        self.cmd('logicapp scale -g {} -n {} --min-instances 2 --max-instances 4'.format(resource_group, logicapp_name)).assert_with_checks([
            JMESPathCheck("functionAppScaleLimit", 4),
            JMESPathCheck("minimumElasticInstanceCount", 2),
        ])


class LogicappCommandsTest(ScenarioTest):
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_logicapp_update(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='logicappplan', length=24)
        logicapp = self.create_random_name(prefix='logicapp-slot', length=24)
        slotname = self.create_random_name(prefix='slotname', length=24)

        self.cmd('appservice plan create -g {} -n {} --sku WS1'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'WS1'),
        ])
        self.cmd('logicapp create -g {} -n {} --plan {} -s {}'.format(resource_group, logicapp, plan,
                                                                                        storage_account), checks=[
            JMESPathCheck('name', logicapp)
        ])
        self.cmd('logicapp update -g {} -n {} --set siteConfig.healthCheckPath=/api/HealthCheck'.format(resource_group, logicapp, slotname), checks=[
            JMESPathCheck('name', logicapp),
        ])
        self.cmd('logicapp show -g {} -n {} '.format(resource_group, logicapp), checks=[
            JMESPathCheck('siteConfig.healthCheckPath', '/api/HealthCheck')
        ])


class LogicAppDeployTest(LiveScenarioTest):
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_logicapp_zip_deploy_e2e(self, resource_group):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        zip_file = os.path.join(TEST_DIR, 'logicapp.zip')
        storage = self.create_random_name(prefix='logic', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku WS1'.format(resource_group, plan))
        self.cmd('storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(storage, resource_group, DEFAULT_LOCATION))
        self.cmd('logicapp create -g {} -n {} -p {} -s {}'.format(resource_group, logicapp_name, plan, storage))

        self.cmd('logicapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, logicapp_name, zip_file), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('site_name', logicapp_name),
        ])

    @unittest.skip("Falky test fails with read time out, need invesigation")
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_LOGICAPP)
    def test_linux_logicapp_zip_deploy_e2e(self, resource_group):
        logicapp_name = self.create_random_name(prefix='logic-e2e', length=24)
        plan = self.create_random_name(prefix='logic-e2e-plan', length=24)
        zip_file = os.path.join(TEST_DIR, 'logicapp.zip')
        storage = self.create_random_name(prefix='logic', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku WS1 --is-linux'.format(resource_group, plan))
        self.cmd('storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(storage, resource_group, DEFAULT_LOCATION))
        self.cmd('logicapp create -g {} -n {} -p {} -s {}'.format(resource_group, logicapp_name, plan, storage))

        self.cmd('logicapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, logicapp_name, zip_file), checks=[
            JMESPathCheck('status', 4),
            JMESPathCheck('complete', True),
        ])


class LogicAppPlanTest(ScenarioTest):
    def _create_app_service_plan(self, sku, resource_group, plan_name=None, expect_failure=False):
        if plan_name == None:
            plan = self.create_random_name('plan', 24)
        else:
            plan = plan_name
        self.cmd('appservice plan create -g {} -n {} --sku {}'.format(resource_group, plan, sku), expect_failure=expect_failure)
        return plan


    def _create_logic_app(self, plan, resource_group, storage_account):
        name = self.create_random_name('logicapp', 24)
        self.cmd('logicapp create -g {} -n {} --plan {} --storage-account {}'.format(resource_group, name, plan, storage_account))
        return name

    def _validate_ws_plan(self, plan, resource_group, sku):
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('properties.provisioningState', 'Succeeded'),
            JMESPathCheck('properties.status', 'Ready'),
            JMESPathCheck('sku.tier', 'WorkflowStandard'),
            JMESPathCheck('kind', 'elastic'),
            JMESPathCheck('sku.name', sku),
            JMESPathCheck('sku.size', sku),
        ])

    def _validate_logicapp_create(self, name, resource_group, plan):
        plan_id = resource_id(subscription=self.get_subscription_id(),
                              resource_group=resource_group,
                              namespace='Microsoft.Web',
                              type='serverfarms',
                              name=plan)

        self.cmd('logicapp show -g {} -n {}'.format(resource_group, name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('resourceGroup', resource_group),
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('enabled', True),
            JMESPathCheck('appServicePlanId', plan_id),
            JMESPathCheck('kind', 'functionapp,workflowapp'),
        ])

    def _run_sku_test(self, sku, resource_group, storage_account):
        plan = self._create_app_service_plan(sku, resource_group)
        self._validate_ws_plan(plan, resource_group, sku)
        name = self._create_logic_app(plan, resource_group, storage_account)
        self._validate_logicapp_create(name, resource_group, plan)

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_asp_ws1_create(self, resource_group, storage_account):
        self._run_sku_test("WS1", resource_group, storage_account)

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_asp_ws2_create(self, resource_group, storage_account):
        self._run_sku_test("WS2", resource_group, storage_account)

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_asp_ws3_create(self, resource_group, storage_account):
        self._run_sku_test("WS3", resource_group, storage_account)

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_autocreate_asp_for_logicapp(self, resource_group, storage_account):
        name = self.create_random_name('logicapp', 24)
        self.cmd('logicapp create -g {} -n {} --storage-account {}'.format(resource_group, name, storage_account))
        show = self.cmd('logicapp show -g {} -n {}'.format(resource_group, name))
        plan = parse_resource_id(show.get_output_in_json()["appServicePlanId"])
        sku = "WS1"
        self._validate_logicapp_create(name, resource_group, plan["name"])
        self._validate_ws_plan(plan["name"], resource_group, sku)

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_update_asp_to_logicapp_sku_fails(self, resource_group):
        plan_name = self._create_app_service_plan("F1", resource_group)
        self._create_app_service_plan("WS1", resource_group, plan_name, expect_failure=True)
        self._create_app_service_plan("WS2", resource_group, plan_name, expect_failure=True)
        self._create_app_service_plan("WS3", resource_group, plan_name, expect_failure=True)

    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_update_logicapp_asp_sku(self, resource_group):
        plan_name = self._create_app_service_plan("WS1", resource_group)
        self._create_app_service_plan("WS2", resource_group, plan_name)
        self._create_app_service_plan("WS3", resource_group, plan_name)


class LogicAppOnLinux(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_LOGICAPP)
    @StorageAccountPreparer()
    def test_logicapp_on_linux(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        logicapp_name = self.create_random_name(
            prefix='logicapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku WS1 --is-linux' .format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'WS1'),
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
