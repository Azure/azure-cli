# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import unittest
import mock
import os
import time
import tempfile
import requests
import datetime

from azure_devtools.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               StorageAccountPreparer, JMESPathCheck, live_only)

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


class FunctionappACRScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer()
    @AllowLargeResponse()
    def test_acr_integration_function_app(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='acrtestplanfunction', length=24)
        functionapp = self.create_random_name(
            prefix='functionappacrtest', length=24)
        runtime = 'node'
        acr_registry_name = functionapp
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(
            resource_group, acr_registry_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('functionapp create -g {} -n {} -s {} --plan {} --runtime {}'.format(
            resource_group, functionapp, storage_account, plan, runtime))
        creds = self.cmd('acr credential show -n {} -g {}'.format(
            acr_registry_name, resource_group)).get_output_in_json()
        self.cmd('functionapp config container set -g {0} -n {1} --docker-custom-image-name {2}.azurecr.io/image-name:latest --docker-registry-server-url https://{2}.azurecr.io'.format(
            resource_group, functionapp, acr_registry_name), checks=[
                JMESPathCheck(
                    "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username'])
        ])
        self.cmd('functionapp config container show -g {} -n {} '.format(resource_group, functionapp), checks=[
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username']),
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_URL']|[0].name", 'DOCKER_REGISTRY_SERVER_URL')
        ])
        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck(
                "[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'node'),
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME'].value|[0]", creds['username'])
        ])
        self.cmd(
            'functionapp config container delete -g {} -n {} '.format(resource_group, functionapp))
        json_result = self.cmd('functionapp config appsettings list -g {} -n {}'.format(
            resource_group, functionapp)).get_output_in_json()
        all_settings = [setting['name'] for setting in json_result]
        # Make sure the related settings are deleted
        self.assertNotIn('DOCKER_REGISTRY_SERVER_USERNAME', all_settings)
        self.assertNotIn('DOCKER_REGISTRY_SERVER_URL', all_settings)
        self.assertNotIn('DOCKER_REGISTRY_SERVER_PASSWORD', all_settings)
        self.assertIn('FUNCTIONS_WORKER_RUNTIME', all_settings)

        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp))


class FunctionAppCreateUsingACR(ScenarioTest):
    @ResourceGroupPreparer(location='brazilsouth')
    @StorageAccountPreparer(name_prefix='clitestacr')
    @AllowLargeResponse()
    def test_acr_create_function_app(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='acrtestplanfunction', length=24)
        functionapp = self.create_random_name(
            prefix='functionappacrtest', length=24)
        runtime = 'node'
        acr_registry_name = functionapp
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(
            resource_group, acr_registry_name))
        acr_creds = self.cmd('acr credential show -n {} -g {}'.format(
            acr_registry_name, resource_group)).get_output_in_json()
        username = acr_creds['username']
        password = acr_creds['passwords'][0]['value']
        self.cmd(
            'functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan))
        self.cmd('functionapp create -g {} -n {} -s {} --plan {} --runtime {}'
                 ' --deployment-container-image-name {}.azurecr.io/image-name:latest --docker-registry-server-user {}'
                 ' --docker-registry-server-password {}'.format(resource_group, functionapp, storage_account, plan, runtime,
                                                                acr_registry_name, username, password))

        self.cmd('functionapp config container show -g {} -n {} '.format(resource_group, functionapp), checks=[
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", username),
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_URL']|[0].name", 'DOCKER_REGISTRY_SERVER_URL')
        ])
        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck(
                "[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", None),
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME'].value|[0]", username)
        ])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'DOCKER|{}.azurecr.io/image-name:latest'.format(acr_registry_name))])

        self.cmd(
            'functionapp config container delete -g {} -n {} '.format(resource_group, functionapp))
        json_result = self.cmd(
            'functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp)).get_output_in_json()
        all_settings = [setting['name'] for setting in json_result]
        # Make sure the related settings are deleted
        self.assertNotIn('DOCKER_REGISTRY_SERVER_USERNAME', all_settings)
        self.assertNotIn('DOCKER_REGISTRY_SERVER_URL', all_settings)
        self.assertNotIn('DOCKER_REGISTRY_SERVER_PASSWORD', all_settings)
        self.assertNotIn('FUNCTIONS_WORKER_RUNTIME', all_settings)


class FunctionappACRDeploymentScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='brazilsouth')
    @StorageAccountPreparer(name_prefix='clitestacrdeploy')
    def test_acr_deployment_function_app(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='acrtestplanfunction', length=24)
        functionapp = self.create_random_name(
            prefix='functionappacrtest', length=24)
        runtime = 'node'
        acr_registry_name = functionapp
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(
            resource_group, acr_registry_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('functionapp create -g {} -n {} -s {} --plan {} --runtime {}'.format(
            resource_group, functionapp, storage_account, plan, runtime))
        creds = self.cmd('acr credential show -g {} -n {}'.format(
            resource_group, acr_registry_name)).get_output_in_json()
        self.cmd('functionapp config container set -g {0} -n {1} --docker-custom-image-name {2}.azurecr.io/image-name:latest --docker-registry-server-url https://{2}.azurecr.io'.format(
            resource_group, functionapp, acr_registry_name), checks=[
                JMESPathCheck(
                    "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username'])
        ])
        result = self.cmd('functionapp deployment container config -g {} -n {} --enable-cd true'.format(resource_group,
                                                                                                        functionapp)).get_output_in_json()
        self.assertTrue(result['CI_CD_URL'].startswith('https://'))
        self.assertTrue(result['CI_CD_URL'].endswith(
            '.scm.azurewebsites.net/docker/hook'))
        # verify that show-cd-url works the same way
        show_result = self.cmd('functionapp deployment container show-cd-url -g {} -n {}'.format(resource_group,
                                                                                                 functionapp)).get_output_in_json()
        self.assertTrue(show_result['CI_CD_URL'].startswith('https://'))
        self.assertTrue(show_result['CI_CD_URL'].endswith(
            '.scm.azurewebsites.net/docker/hook'))

        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp))


class FunctionAppReservedInstanceTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_reserved_instance(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwithreservedinstance', 40)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])
        self.cmd('functionapp config set -g {} -n {} --prewarmed-instance-count 4'
                 .format(resource_group, functionapp_name)).assert_with_checks([
                     JMESPathCheck('preWarmedInstanceCount', 4)])
        self.cmd(
            'functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppWithPlanE2ETest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @ResourceGroupPreparer(parameter_name='resource_group2', location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    def test_functionapp_e2e(self, resource_group, resource_group2):
        functionapp_name, functionapp_name2 = self.create_random_name(
            'func-e2e', 24), self.create_random_name('func-e2e', 24)
        plan = self.create_random_name('func-e2e-plan', 24)
        storage, storage2 = 'functionappplanstorage', 'functionappplanstorage2'
        plan_id = self.cmd('appservice plan create -g {} -n {}'.format(
            resource_group, plan)).get_output_in_json()['id']
        self.cmd('appservice plan list -g {}'.format(resource_group))
        self.cmd(
            'storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(storage, resource_group, WINDOWS_ASP_LOCATION_FUNCTIONAPP))
        storage_account_id2 = self.cmd('storage account create --name {} -g {} -l {} --sku Standard_LRS'.format(
            storage2, resource_group2, WINDOWS_ASP_LOCATION_FUNCTIONAPP)).get_output_in_json()['id']

        self.cmd('functionapp create -g {} -n {} -p {} -s {}'.format(resource_group, functionapp_name, plan, storage), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', functionapp_name),
            JMESPathCheck('hostNames[0]',
                          functionapp_name + '.azurewebsites.net')
        ])
        self.cmd('functionapp create -g {} -n {} -p {} -s {}'.format(resource_group2,
                                                                     functionapp_name2, plan_id, storage_account_id2))
        self.cmd(
            'functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_app_service_java(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime java --functions-version 3'
                 .format(resource_group, functionapp, plan, storage_account),
                 checks=[
                     JMESPathCheck('name', functionapp)
                 ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Java|8')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_app_service_java_with_runtime_version(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime java --runtime-version 11 --functions-version 3'
                 .format(resource_group, functionapp, plan, storage_account),
                 checks=[
                     JMESPathCheck('name', functionapp)
                 ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Java|11')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_app_service_powershell(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime powershell --functions-version 3'
                 .format(resource_group, functionapp, plan, storage_account),
                 checks=[
                     JMESPathCheck('name', functionapp)
                 ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'PowerShell|7')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_app_service_powershell_with_runtime_version(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime powershell --runtime-version 7.0 --functions-version 3'
                 .format(resource_group, functionapp, plan, storage_account),
                 checks=[
                     JMESPathCheck('name', functionapp)
                 ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'PowerShell|7')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_app_service_dotnet_isolated(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet-isolated --functions-version 3'
                 .format(resource_group, functionapp, plan, storage_account),
                 checks=[
                     JMESPathCheck('name', functionapp)
                 ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'dotnet-isolated')])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'dotnet-isolated|5.0')])


class FunctionUpdatePlan(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_move_plan_to_elastic(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappelastic', 40)
        ep_plan_name = self.create_random_name('somerandomplan', 40)
        second_plan_name = self.create_random_name('secondplan', 40)
        s1_plan_name = self.create_random_name('ab1planname', 40)

        plan_result = self.cmd('functionapp plan create -g {} -n {} --sku EP1'.format(resource_group, ep_plan_name), checks=[
            JMESPathCheck('sku.name', 'EP1')
        ]).get_output_in_json()

        self.cmd('functionapp plan create -g {} -n {} --sku EP1'.format(resource_group, second_plan_name), checks=[
            JMESPathCheck('sku.name', 'EP1')
        ]).get_output_in_json()

        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, s1_plan_name), checks=[
            JMESPathCheck('sku.name', 'S1')
        ])

        self.cmd('functionapp create -g {} -n {} --plan {} -s {}'
                 .format(resource_group, functionapp_name, second_plan_name, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp update -g {} -n {} --plan {}'
                 .format(resource_group, functionapp_name, ep_plan_name)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('serverFarmId', plan_result['id']),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        # Moving to and from an App Service plan (not Elastic Premium) is not allowed right now
        self.cmd('functionapp update -g {} -n {} --plan {}'
                 .format(resource_group, functionapp_name, s1_plan_name), expect_failure=True)


class FunctionAppWithConsumptionPlanE2ETest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-c-e2e', location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_consumption_e2e(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {}'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net'),
                     JMESPathCheck('clientCertMode', 'Required')])

        self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].kind', 'functionapp'),
            JMESPathCheck('[0].name', functionapp_name)
        ])
        self.cmd('functionapp show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('kind', 'functionapp'),
            JMESPathCheck('name', functionapp_name)
        ])
        self.cmd('functionapp update -g {} -n {} --set clientCertMode=Optional'.format(resource_group, functionapp_name),
                 checks=[self.check('clientCertMode', 'Optional')]
                 )

        self.cmd(
            'functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))

    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-c-e2e-ragrs', location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer(sku='Standard_RAGRS')
    def test_functionapp_consumption_ragrs_storage_e2e(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {}'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('kind', 'functionapp'),
            JMESPathCheck('name', functionapp_name)
        ])


class FunctionAppWithLinuxConsumptionPlanTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-linux', location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_consumption_linux(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionapplinuxconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Linux --runtime node'
                 .format(resource_group, functionapp_name, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('reserved', True),
                     JMESPathCheck('kind', 'functionapp,linux'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'node')])

    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-linux', location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_consumption_linux_java(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionapplinuxconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Linux --runtime java --functions-version 3'
                 .format(resource_group, functionapp_name, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('reserved', True),
                     JMESPathCheck('kind', 'functionapp,linux'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'java')])

    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-linux', location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_consumption_linux_powershell(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionapplinuxconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Linux --runtime powershell --functions-version 3'
                 .format(resource_group, functionapp_name, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('reserved', True),
                     JMESPathCheck('kind', 'functionapp,linux'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'powershell')])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('linuxFxVersion', 'PowerShell|7')])

    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-linux', location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_consumption_linux_dotnet_isolated(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionapplinuxconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Linux --runtime dotnet-isolated --functions-version 3'
                 .format(resource_group, functionapp_name, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('reserved', True),
                     JMESPathCheck('kind', 'functionapp,linux'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'dotnet-isolated')])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('linuxFxVersion', '')])


class FunctionAppOnWindowsWithRuntime(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows --runtime node'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'node')])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_java(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows --runtime java'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'java')])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('javaVersion', '1.8')])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_powershell(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows --runtime powershell'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'powershell')])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('powerShellVersion', '~6')])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_version(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows --runtime node --runtime-version 8'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
                 JMESPathCheck(
                     "[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'node'),
                 JMESPathCheck("[?name=='WEBSITE_NODE_DEFAULT_VERSION'].value|[0]", '~8')])

        self.cmd(
            'functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_dotnet_isolated(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows --runtime dotnet-isolated --functions-version 3'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'dotnet-isolated')])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('netFrameworkVersion', 'v5.0')])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_version_invalid(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} '
                 '--os-type Windows --runtime node --runtime-version 8.2'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account), expect_failure=True)

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_functions_version(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --functions-version 3 --os-type Windows --runtime node'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
                 JMESPathCheck(
                     "[?name=='FUNCTIONS_EXTENSION_VERSION'].value|[0]", '~3'),
                 JMESPathCheck("[?name=='WEBSITE_NODE_DEFAULT_VERSION'].value|[0]", '~14')])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_runtime_custom_handler(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowsruntime', 40)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --functions-version 3 --os-type Windows --runtime custom'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
                 JMESPathCheck("[?name=='FUNCTIONS_EXTENSION_VERSION'].value|[0]", '~3'),
                 JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'custom')])


class FunctionAppOnWindowsWithoutRuntime(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_windows_without_runtime(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwindowswithoutruntime', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd(
            'functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppWithAppInsightsKey(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_with_app_insights_key(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwithappinsights', 40)
        app_insights_key = '00000000-0000-0000-0000-123456789123'

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows'
                 ' --app-insights-key {}'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account, app_insights_key)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp_name)).assert_with_checks([
            JMESPathCheck(
                "[?name=='APPINSIGHTS_INSTRUMENTATIONKEY'].value|[0]", app_insights_key)
        ])

        self.cmd(
            'functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppWithAppInsightsDefault(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_with_default_app_insights(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwithappinsights', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        app_set = self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group,
                                                                                    functionapp_name)).get_output_in_json()
        self.assertTrue('APPINSIGHTS_INSTRUMENTATIONKEY' in [
                        kp['name'] for kp in app_set])
        self.assertTrue('AzureWebJobsDashboard' not in [
                        kp['name'] for kp in app_set])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_with_no_default_app_insights(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(
            'functionappwithappinsights', 40)

        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type Windows --disable-app-insights'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        app_set = self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group,
                                                                                    functionapp_name)).get_output_in_json()
        self.assertTrue('APPINSIGHTS_INSTRUMENTATIONKEY' not in [
                        kp['name'] for kp in app_set])
        self.assertTrue('AzureWebJobsDashboard' in [
                        kp['name'] for kp in app_set])


class FunctionAppOnLinux(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime node'.format(resource_group, functionapp, plan, storage_account), checks=[
            JMESPathCheck('name', functionapp)
        ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Node|10')])

        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp))

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_version(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime node --runtime-version 10'
                 .format(resource_group, functionapp, plan, storage_account),
                 checks=[
                     JMESPathCheck('name', functionapp)
                 ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Node|10')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_version_consumption(self, resource_group, storage_account):
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type linux --runtime python --runtime-version 3.7'
                 .format(resource_group, functionapp, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account), checks=[
                     JMESPathCheck('name', functionapp)
                 ])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Python|3.7')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_version_error(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan), checks=[
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])

        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime python --runtime-version 3.8'
                 .format(resource_group, functionapp, plan, storage_account), expect_failure=True)

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_consumption_python_39(self, resource_group, storage_account):
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --os-type linux --runtime python --functions-version 3 --runtime-version 3.9'
                 .format(resource_group, functionapp, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account), checks=[
                     JMESPathCheck('name', functionapp)
                 ])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Python|3.9')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_functions_version(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1')
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --functions-version 3 --runtime node'
                 .format(resource_group, functionapp, plan, storage_account), checks=[
                     JMESPathCheck('name', functionapp)
                 ])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Node|14')
        ])
        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp)).assert_with_checks([
            JMESPathCheck(
                "[?name=='FUNCTIONS_EXTENSION_VERSION'].value|[0]", '~3')
        ])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_custom_handler(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1')
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --functions-version 3 --runtime custom'
                 .format(resource_group, functionapp, plan, storage_account), checks=[
                     JMESPathCheck('name', functionapp)
                 ])

        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp)).assert_with_checks([
            JMESPathCheck("[?name=='FUNCTIONS_WORKER_RUNTIME'].value|[0]", 'custom')])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_functions_version_consumption(self, resource_group, storage_account):
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --functions-version 3 --runtime node --os-type linux'
                 .format(resource_group, functionapp, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account), checks=[
                     JMESPathCheck('name', functionapp)
                 ])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'Node|14')
        ])
        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp)).assert_with_checks([
            JMESPathCheck(
                "[?name=='FUNCTIONS_EXTENSION_VERSION'].value|[0]", '~3')
        ])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_on_linux_dotnet_consumption(self, resource_group, storage_account):
        functionapp = self.create_random_name(
            prefix='functionapp-linux', length=24)
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --functions-version 3 --runtime dotnet --os-type linux'
                 .format(resource_group, functionapp, LINUX_ASP_LOCATION_FUNCTIONAPP, storage_account), checks=[
                     JMESPathCheck('name', functionapp)
                 ])

        self.cmd('functionapp config show -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck('linuxFxVersion', 'dotnet|3.1')
        ])
        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp)).assert_with_checks([
            JMESPathCheck(
                "[?name=='FUNCTIONS_EXTENSION_VERSION'].value|[0]", '~3')
        ])


class FunctionAppServicePlan(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    def test_functionapp_app_service_plan(self, resource_group):
        plan = self.create_random_name(prefix='funcappplan', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1' .format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S1')
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    def test_functionapp_elastic_plan(self, resource_group):
        plan = self.create_random_name(prefix='funcappplan', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku EP1 --min-instances 4 --max-burst 12' .format(resource_group, plan), checks=[
            JMESPathCheck('maximumElasticWorkerCount', 12),
            JMESPathCheck('sku.name', 'EP1'),
            JMESPathCheck('sku.capacity', 4)
        ])
        self.cmd('functionapp plan update -g {} -n {} --min-instances 5 --max-burst 11' .format(resource_group, plan), checks=[
            JMESPathCheck('maximumElasticWorkerCount', 11),
            JMESPathCheck('sku.name', 'EP1'),
            JMESPathCheck('sku.capacity', 1)
        ])
        self.cmd('functionapp plan show -g {} -n {} '.format(resource_group, plan), checks=[
            JMESPathCheck('maximumElasticWorkerCount', 11),
            JMESPathCheck('sku.name', 'EP1'),
            JMESPathCheck('sku.capacity', 1)
        ])
        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, plan))


class FunctionAppServicePlanLinux(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_FUNCTIONAPP)
    def test_functionapp_app_service_plan_linux(self, resource_group):
        plan = self.create_random_name(prefix='funcappplan', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S1'),
            JMESPathCheck('kind', 'linux')
        ])


class FunctionAppSlotTests(ScenarioTest):
    @unittest.skip("Function app slot shouldn't use webapp")
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_slot_appsetting_update(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcappplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-slot', length=24)
        slotname = self.create_random_name(prefix='slotname', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime node'.format(resource_group, functionapp, plan,
                                                                                        storage_account), checks=[
            JMESPathCheck('name', functionapp)
        ])
        self.cmd('functionapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, functionapp, slotname), checks=[
            JMESPathCheck('name', slotname)
        ])
        self.cmd('functionapp config appsettings set -g {} -n {} --slot {} --slot-settings FOO=BAR'.format(resource_group, functionapp,
                                                                                                           slotname), checks=[
            JMESPathCheck("[?name=='FOO'].value|[0]", 'BAR'),
            JMESPathCheck("[?name=='FOO'].slotSetting|[0]", True)
        ])
        self.cmd('functionapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, functionapp, slotname), checks=[
            JMESPathCheck("[?name=='FOO'].value|[0]", 'BAR'),
            JMESPathCheck("[?name=='FOO'].slotSetting|[0]", True)
        ])
        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp))

    @unittest.skip("Function app slot shouldn't use webapp")
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_slot_swap(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcappplan', length=24)
        functionapp = self.create_random_name(
            prefix='functionapp-slot', length=24)
        slotname = self.create_random_name(prefix='slotname', length=24)
        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime node'.format(resource_group, functionapp,
                                                                                        plan,
                                                                                        storage_account), checks=[
            JMESPathCheck('name', functionapp)
        ])
        self.cmd('functionapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, functionapp,
                                                                                   slotname), checks=[
            JMESPathCheck('name', slotname)
        ])
        self.cmd('functionapp config appsettings set -g {} -n {} --slot {} --settings FOO=BAR'.format(resource_group, functionapp,
                                                                                                      slotname), checks=[
            JMESPathCheck("[?name=='FOO'].value|[0]", 'BAR')
        ])
        self.cmd('functionapp deployment slot swap -g {} -n {} --slot {} --action swap'.format(
            resource_group, functionapp, slotname))
        self.cmd('functionapp config appsettings list -g {} -n {}'.format(resource_group, functionapp), checks=[
            JMESPathCheck("[?name=='FOO'].value|[0]", 'BAR')
        ])
        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp))


class FunctionAppKeysTests(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_keys_set(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappkeys', 40)
        key_name = "keyname1"
        key_value = "keyvalue1"
        key_type = "functionKeys"
        self.cmd('functionapp create -g {} -n {} -c {} -s {} --functions-version 3'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp keys set -g {} -n {} --key-name {} --key-value {} --key-type {}'
                 .format(resource_group, functionapp_name, key_name, key_value, key_type)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value),
                     JMESPathCheck('type', 'Microsoft.Web/sites/host/functionKeys')])

        key_value = "keyvalue1_changed"
        self.cmd('functionapp keys set -g {} -n {} --key-name {} --key-value {} --key-type {}'
                 .format(resource_group, functionapp_name, key_name, key_value, key_type)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value),
                     JMESPathCheck('type', 'Microsoft.Web/sites/host/functionKeys')])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_keys_list(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappkeys', 40)
        key_name = "keyname1"
        key_value = "keyvalue1"
        key_type = "functionKeys"
        self.cmd('functionapp create -g {} -n {} -c {} -s {}'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp keys set -g {} -n {} --key-name {} --key-value {} --key-type {}'
                 .format(resource_group, functionapp_name, key_name, key_value, key_type)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value),
                     JMESPathCheck('type', 'Microsoft.Web/sites/host/functionKeys')])

        self.cmd('functionapp keys list -g {} -n {}'
                 .format(resource_group, functionapp_name)).assert_with_checks([
                     JMESPathCheck('functionKeys.{}'.format(key_name), key_value)])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_keys_delete(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappkeys', 40)
        key_name = "keyname1"
        key_value = "keyvalue1"
        key_type = "functionKeys"
        self.cmd('functionapp create -g {} -n {} -c {} -s {}'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp keys set -g {} -n {} --key-name {} --key-value {} --key-type {}'
                 .format(resource_group, functionapp_name, key_name, key_value, key_type)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value),
                     JMESPathCheck('type', 'Microsoft.Web/sites/host/functionKeys')])

        self.cmd('functionapp keys delete -g {} -n {} --key-name {} --key-type {}'
                 .format(resource_group, functionapp_name, key_name, key_type))

        self.cmd('functionapp keys list -g {} -n {}'
                 .format(resource_group, functionapp_name)).assert_with_checks([
                     JMESPathCheck('functionKeys.{}'.format(key_name), None)])

    @unittest.skip("Function app slot shouldn't use webapp")
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_keys_set_slot(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappkeys', 40)
        slot_name = self.create_random_name(prefix='slotname', length=24)
        key_name = "keyname1"
        key_value = "keyvalue1"
        key_type = "functionKeys"
        self.cmd('functionapp create -g {} -n {} -c {} -s {}'
                 .format(resource_group, functionapp_name, WINDOWS_ASP_LOCATION_FUNCTIONAPP, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('kind', 'functionapp'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp deployment slot create -g {} -n {} --slot {}'
                 .format(resource_group, functionapp_name, slot_name)).assert_with_checks([
                     JMESPathCheck('name', slot_name),
                     JMESPathCheck('type', 'Microsoft.Web/sites/slots')])

        self.cmd('functionapp keys set -g {} -n {} -s {} --key-name {} --key-value {} --key-type {}'
                 .format(resource_group, functionapp_name, slot_name, key_name, key_value, key_type)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value),
                     JMESPathCheck('type', 'Microsoft.Web/sites/host/functionKeys')])

        key_value = "keyvalue1_changed"
        self.cmd('functionapp keys set -g {} -n {} -s {} --key-name {} --key-value {} --key-type {}'
                 .format(resource_group, functionapp_name, slot_name, key_name, key_value, key_type)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value),
                     JMESPathCheck('type', 'Microsoft.Web/sites/host/functionKeys')])


class FunctionAppFunctionKeysTests(LiveScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_function_keys_set(self, resource_group, storage_account):
        zip_file = os.path.join(TEST_DIR, 'sample_csx_function_httptrigger/sample_csx_function_httptrigger.zip')
        functionapp_name = self.create_random_name('functionappkeys', 40)
        plan_name = self.create_random_name(prefix='functionappkeysplan', length=40)
        function_name = "HttpTrigger"
        key_name = "keyname1"
        key_value = "keyvalue1"

        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)])

        # ping function so you know it's ready
        requests.get('http://{}.azurewebsites.net/api/{}'.format(functionapp_name, function_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp function keys set -g {} -n {} --function-name {} --key-name {} --key-value {}'
                 .format(resource_group, functionapp_name, function_name, key_name, key_value)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value)])

        key_value = "keyvalue1_changed"
        self.cmd('functionapp function keys set -g {} -n {} --function-name {} --key-name {} --key-value {}'
                 .format(resource_group, functionapp_name, function_name, key_name, key_value)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value)])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_function_keys_list(self, resource_group, storage_account):
        zip_file = os.path.join(TEST_DIR, 'sample_csx_function_httptrigger/sample_csx_function_httptrigger.zip')
        functionapp_name = self.create_random_name('functionappkeys', 40)
        plan_name = self.create_random_name(prefix='functionappkeysplan', length=40)
        function_name = "HttpTrigger"
        key_name = "keyname1"
        key_value = "keyvalue1"

        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)])

        # ping function so you know it's ready
        requests.get('http://{}.azurewebsites.net/api/{}'.format(functionapp_name, function_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp function keys set -g {} -n {} --function-name {} --key-name {} --key-value {}'
                 .format(resource_group, functionapp_name, function_name, key_name, key_value)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value)])

        self.cmd('functionapp function keys list -g {} -n {} --function-name {}'
                 .format(resource_group, functionapp_name, function_name)).assert_with_checks([
                     JMESPathCheck('{}'.format(key_name), key_value)])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_function_keys_delete(self, resource_group, storage_account):
        zip_file = os.path.join(TEST_DIR, 'sample_csx_function_httptrigger/sample_csx_function_httptrigger.zip')
        functionapp_name = self.create_random_name('functionappkeys', 40)
        plan_name = self.create_random_name(prefix='functionappkeysplan', length=40)
        function_name = "HttpTrigger"
        key_name = "keyname1"
        key_value = "keyvalue1"

        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)])

        # ping function so you know it's ready
        requests.get('http://{}.azurewebsites.net/api/{}'.format(functionapp_name, function_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp function keys set -g {} -n {} --function-name {} --key-name {} --key-value {}'
                 .format(resource_group, functionapp_name, function_name, key_name, key_value)).assert_with_checks([
                     JMESPathCheck('name', key_name),
                     JMESPathCheck('value', key_value)])

        self.cmd('functionapp function keys delete -g {} -n {} --function-name {} --key-name {}'
                 .format(resource_group, functionapp_name, function_name, key_name))

        self.cmd('functionapp function keys list -g {} -n {} --function-name {}'
                 .format(resource_group, functionapp_name, function_name)).assert_with_checks([
                     JMESPathCheck('{}'.format(key_name), None)])


# LiveScenarioTest due to issue https://github.com/Azure/azure-cli/issues/10705
class FunctionAppFunctionTests(LiveScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_function_show(self, resource_group, storage_account):
        zip_file = os.path.join(TEST_DIR, 'sample_csx_function_httptrigger/sample_csx_function_httptrigger.zip')
        functionapp_name = self.create_random_name('functionappkeys', 40)
        plan_name = self.create_random_name(prefix='functionappkeysplan', length=40)
        function_name = "HttpTrigger"

        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)])

        self.cmd('functionapp function show -g {} -n {} --function-name {}'.format(resource_group, functionapp_name, function_name)).assert_with_checks([
            JMESPathCheck('name', '{}/{}'.format(functionapp_name, function_name)),
            JMESPathCheck('resourceGroup', resource_group),
            JMESPathCheck('scriptHref', 'https://{}.azurewebsites.net/admin/vfs/site/wwwroot/{}/run.csx'.format(functionapp_name, function_name))])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_function_delete(self, resource_group, storage_account):
        zip_file = os.path.join(TEST_DIR, 'sample_csx_function_httptrigger/sample_csx_function_httptrigger.zip')
        functionapp_name = self.create_random_name('functionappkeys', 40)
        plan_name = self.create_random_name(prefix='functionappkeysplan', length=40)
        function_name = "HttpTrigger"

        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)

        self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)])

        self.cmd('functionapp function delete -g {} -n {} --function-name {}'.format(resource_group, functionapp_name, function_name))

        self.cmd('functionapp function show -g {} -n {} --function-name {}'.format(resource_group, functionapp_name, function_name)).assert_with_checks([
            JMESPathCheck('config.bindings[0].type', 'httpTrigger')])


# LiveScenarioTest due to issue https://github.com/Azure/azure-cli/issues/10705
class FunctionappDeploymentLogsScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_show_deployment_logs(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(prefix='show-deployment-functionapp', length=40)
        plan_name = self.create_random_name(prefix='show-deployment-functionapp', length=40)
        zip_file = os.path.join(TEST_DIR, 'sample_dotnet_function/sample_dotnet_function.zip')
        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))
        self.cmd('functionapp log deployment show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)
        deployment_1 = self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)
        ]).get_output_in_json()
        self.cmd('functionapp log deployment show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('length(@) > `0`', True)
        ])

        self.cmd('functionapp log deployment show -g {} -n {} --deployment-id={}'.format(resource_group, functionapp_name, deployment_1['id']), checks=[
            JMESPathCheck('length(@) > `0`', True)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_list_deployment_logs(self, resource_group, storage_account):
        functionapp_name = self.create_random_name(prefix='show-deployment-funcapp', length=40)
        plan_name = self.create_random_name(prefix='show-deployment-funcapp', length=40)
        zip_file = os.path.join(TEST_DIR, 'sample_dotnet_function/sample_dotnet_function.zip')
        self.cmd('functionapp plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('functionapp create -g {} -n {} --plan {} -s {} --runtime dotnet'.format(resource_group, functionapp_name, plan_name, storage_account))
        self.cmd('functionapp log deployment list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)
        deployment_1 = self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)
        ]).get_output_in_json()
        self.cmd('functionapp log deployment list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].id', deployment_1['id']),
        ])

        requests.get('http://{}.scm.azurewebsites.net'.format(functionapp_name), timeout=240)
        time.sleep(30)
        self.cmd('functionapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, functionapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('complete', True)
        ]).get_output_in_json()
        self.cmd('functionapp log deployment list -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('length(@)', 2)
        ])


class FunctionappLocalContextScenarioTest(LocalContextScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_FUNCTIONAPP)
    @StorageAccountPreparer()
    def test_functionapp_local_context(self, resource_group, storage_account):
        from knack.util import CLIError
        self.kwargs.update({
            'plan_name': self.create_random_name(prefix='functionapp-plan-', length=24),
            'functionapp_name': self.create_random_name(prefix='functionapp-', length=24),
            'storage_account': storage_account
        })

        self.cmd('functionapp plan create -g {rg} -n {plan_name} --sku B2')
        self.cmd('functionapp plan show')
        with self.assertRaises(CLIError):
            self.cmd('functionapp plan delete')

        self.cmd('functionapp create -n {functionapp_name} --storage-account {storage_account}')
        self.cmd('functionapp show')
        with self.assertRaises(CLIError):
            self.cmd('functionapp delete')

        self.cmd('functionapp delete -n {functionapp_name}')
        self.cmd('functionapp plan delete -n {plan_name} -y')


if __name__ == '__main__':
    unittest.main()
