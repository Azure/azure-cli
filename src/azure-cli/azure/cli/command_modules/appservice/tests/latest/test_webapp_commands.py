# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import re
import unittest
from unittest import mock
import os
import time
import tempfile
from azure.cli.testsdk.scenario_tests.utilities import create_random_name
import requests
import datetime
import urllib3
from knack.util import CLIError
import certifi

from azure.cli.testsdk.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               StorageAccountPreparer, KeyVaultPreparer, JMESPathCheck, live_only)
from azure.cli.testsdk.checkers import JMESPathCheckNotExists
from azure.cli.command_modules.appservice.utils import get_pool_manager

from azure.cli.core.azclierror import ResourceNotFoundError, ValidationError

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long
# In the future, for any reasons the repository get removed, the source code is under "sample-repo-for-deployment-test"
# you can use to rebuild the repository
TEST_REPO_URL = 'https://github.com/yugangw-msft/azure-site-test.git'
WINDOWS_ASP_LOCATION_WEBAPP = 'westeurope'
WINDOWS_ASP_LOCATION_FUNCTIONAPP = 'francecentral'
LINUX_ASP_LOCATION_WEBAPP = 'eastus2'
LINUX_ASP_LOCATION_FUNCTIONAPP = 'ukwest'
# During the 'webapp vnet-integration remove' call
# Will enter 20s wait for hit geo and 45s wait on app service side in order for NCs to be deleted successfully on machines.
# So add time.sleep(65) for all az webapp vnet-integration related commands.
# This can avoid resource residue caused by appservice related tests.
TIME_SLEEP_FOR_VNET_INTEGRATION = 65


class WebappBasicE2ETest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_e2e(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-e2e', length=24)
        plan = self.create_random_name(prefix='webapp-e2e-plan', length=24)

        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].perSiteScaling', False)
        ])
        # test idempotency
        self.cmd(
            'appservice plan create -g {} -n {} --per-site-scaling'.format(resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1'),
            JMESPathCheck('[0].perSiteScaling', True)
        ])
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck("length([?name=='{}' && resourceGroup=='{}'])".format(
                plan, resource_group), 1)
        ])
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('name', plan)
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --https-only {} --public-network-access {}'.format(resource_group, webapp_name, plan, 'true', 'Enabled'), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net'),
            JMESPathCheck('httpsOnly', 'True'),
            JMESPathCheck('publicNetworkAccess', 'Enabled')
        ])
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name +
                          '.azurewebsites.net')
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        result = self.cmd('webapp deployment source config-local-git -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        self.assertTrue(result['url'].endswith(webapp_name + '.git'))
        self.cmd('webapp deployment source show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck(
                'repoUrl', 'https://{}.scm.azurewebsites.net'.format(webapp_name))
        ])
        # turn on diagnostics
        test_cmd = ('webapp log config -g {} -n {} --level verbose'.format(resource_group, webapp_name) + ' '
                    '--application-logging filesystem --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem')
        self.cmd(test_cmd)
        self.cmd('webapp log show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorMessages.enabled', True),
            JMESPathCheck('failedRequestsTracing.enabled', True)
        ])
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorLoggingEnabled', True),
            JMESPathCheck('httpLoggingEnabled', True),
            JMESPathCheck('scmType', 'LocalGit'),
            JMESPathCheck('requestTracingEnabled', True)
        ])
        # show publish profile info
        result = self.cmd('webapp deployment list-publishing-profiles -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        self.assertTrue(result[1]['publishUrl'].startswith('ftps://'))
        self.cmd('webapp stop -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', webapp_name)
        ])
        self.cmd('webapp start -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name)
        ])
        # show publishing credentials
        result = self.cmd('webapp deployment list-publishing-credentials -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        self.assertTrue('scm' in result['scmUri'])

        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('phpVersion', '5.6')
        ])

    def test_webapp_runtimes(self):
        self.cmd('webapp list-runtimes')
        self.cmd('webapp list-runtimes --os windows')
        self.cmd('webapp list-runtimes --os linux')


class WebappQuickCreateTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_win_webapp_quick_create(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        r = self.cmd('webapp create -g {} -n {} --plan {} --deployment-local-git'.format(
            resource_group, webapp_name, plan)).get_output_in_json()
        self.assertTrue(r['ftpPublishingUrl'].startswith('ftps://'))
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('[0].name', 'WEBSITE_NODE_DEFAULT_VERSION'),
            JMESPathCheck('[0].value', '~16'),
        ])

    @ResourceGroupPreparer(name_prefix="clitest", random_name_length=24, location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_win_webapp_quick_create_runtime(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick', length=24)
        webapp_name_2 = self.create_random_name(prefix='webapp-quick', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        r = self.cmd('webapp create -g {} -n {} --plan {} --deployment-local-git -r "node|16LTS"'.format(
            resource_group, webapp_name, plan)).get_output_in_json()
        self.assertTrue(r['ftpPublishingUrl'].startswith('ftps://'))
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('[0].name', 'WEBSITE_NODE_DEFAULT_VERSION'),
            JMESPathCheck('[0].value', '~16'),
        ])
        r = self.cmd('webapp create -g {} -n {} --plan {} --deployment-local-git -r "dotnet:6"'.format(
            resource_group, webapp_name_2, plan)).get_output_in_json()
        self.assertTrue(r['ftpPublishingUrl'].startswith('ftps://'))

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_win_webapp_quick_create_cd(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick-cd', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-source-url {} -r "node|16LTS"'.format(
            resource_group, webapp_name, plan, TEST_REPO_URL))
        # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        time.sleep(30)
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        # verify the web page
        self.assertTrue('null' in str(r.content))

    @ResourceGroupPreparer(location='canadacentral')
    def test_linux_webapp_quick_create(self, resource_group):
        webapp_name = self.create_random_name(
            prefix='webapp-quick-linux', length=24)
        plan = self.create_random_name(prefix='plan-quick-linux', length=24)

        self.cmd(
            'appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -i patle/ruby-hello'.format(
            resource_group, webapp_name, plan))
        r = requests.get(
            'http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        # verify the web page
        self.assertTrue('Ruby on Rails in Web Apps on Linux' in str(r.content))
        # verify app settings
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('[0].name', 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'),
            JMESPathCheck('[0].value', 'false'),
        ])

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_webapp_multicontainer_create(self, resource_group):
        webapp_name = self.create_random_name(
            prefix='webapp-linux-multi', length=24)
        plan = self.create_random_name(prefix='plan-linux-multi', length=24)
        config_file = os.path.join(TEST_DIR, 'sample-compose.yml')

        self.cmd(
            'appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd("webapp create -g {} -n {} --plan {} --multicontainer-config-file \"{}\" "
                 "--multicontainer-config-type COMPOSE".format(resource_group, webapp_name, plan, config_file))
        self.cmd("webapp show -g {} -n {}".format(resource_group, webapp_name))\
            .assert_with_checks([JMESPathCheck('kind', "app,linux,container")])

        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=400)
        self.assertTrue('Hello World! I have been' in str(r.content))

    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_webapp_quick_create_cd(self, resource_group):
        webapp_name = self.create_random_name(
            prefix='webapp-linux-cd', length=24)
        plan = 'plan-quick-linux-cd'
        self.cmd(
            'appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -u {} -r "NODE|16-lts"'.format(resource_group, webapp_name,
                                                                                    plan, TEST_REPO_URL))
        # 45 seconds should be enough for the deployment finished(Skipped under playback mode)
        time.sleep(45)
        r = requests.get(
            'http://{}.azurewebsites.net'.format(webapp_name), timeout=500)
        # verify the web page
        if "null" not in str(r.content):
            # dump out more info for diagnose
            self.fail("'null' is not found in the web page. We get instead: {}".format(r.content))

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group', parameter_name_for_location='resource_group_location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @ResourceGroupPreparer(parameter_name='resource_group2', parameter_name_for_location='resource_group_location2', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_create_in_different_group(self, resource_group, resource_group_location, resource_group2, resource_group_location2):
        plan = self.create_random_name(prefix='planInOneRG', length=15)
        webapp_name = self.create_random_name(prefix='webInOtherRG', length=24)
        self.cmd('group create -n {} -l {}'.format(resource_group2, resource_group_location))
        plan_id = self.cmd('appservice plan create -g {} -n {}'.format(
            resource_group, plan)).get_output_in_json()['id']
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group2, webapp_name, plan_id), checks=[
            JMESPathCheck('name', webapp_name)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group', parameter_name_for_location='resource_group_location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @ResourceGroupPreparer(parameter_name='resource_group2', parameter_name_for_location='resource_group_location2', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_create_in_different_group_name(self, resource_group, resource_group_location, resource_group2, resource_group_location2):
        plan = self.create_random_name(prefix='planInOneRG', length=15)
        webapp_name = self.create_random_name(prefix='webInOtherRG', length=24)
        self.cmd('group create -n {} -l {}'.format(resource_group2, resource_group_location))
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group2, webapp_name, plan), checks=[
            JMESPathCheck('name', webapp_name)
        ])

    @unittest.skip("This test needs to be updated first to have unique names & re-tested before recording")
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name="resource_group_one", name_prefix="clitest", random_name_length=24, location=WINDOWS_ASP_LOCATION_WEBAPP)
    @ResourceGroupPreparer(parameter_name="resource_group_two", name_prefix="clitest", random_name_length=24, location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_create_names_are_substrings(self, resource_group_one, resource_group_two):

        random_prefix = self.create_random_name("", 10)
        webapp_name_one = random_prefix + "test-webapp-name-on"
        webapp_name_two = random_prefix + "test-webapp-name-one"
        webapp_name_three = random_prefix + "test-webapp-nam"
        plan_name_one = "webapp-plan-one"
        plan_name_two = "webapp-plan-two"
        plan_id_one = self.cmd('appservice plan create -g {} -n {}'.format(
            resource_group_one, plan_name_one)).get_output_in_json()['id']
        plan_id_two = self.cmd('appservice plan create -g {} -n {}'.format(
            resource_group_two, plan_name_two)).get_output_in_json()['id']
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group_one, webapp_name_one, plan_id_one), checks=[
            JMESPathCheck('name', webapp_name_one)
        ])
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group_two, webapp_name_two, plan_id_two), checks=[
            JMESPathCheck('name', webapp_name_two)
        ])
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group_one, webapp_name_three, plan_id_one), checks=[
            JMESPathCheck('name', webapp_name_three)
        ])

        # Re running webapp create to make sure there are no mix ups with existing apps that have names that are substrings of each other.
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group_one, webapp_name_one, plan_id_one), checks=[
            JMESPathCheck('name', webapp_name_one)
        ])
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group_two, webapp_name_two, plan_id_two), checks=[
            JMESPathCheck('name', webapp_name_two)
        ])
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group_one, webapp_name_three, plan_id_one), checks=[
            JMESPathCheck('name', webapp_name_three)
        ])


class BackupRestoreTest(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_backup_with_name(self, resource_group):
        plan = self.create_random_name(prefix='plan-backup', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        webapp = self.create_random_name(prefix='backup-webapp', length=24)
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan))
        storage_Account = self.create_random_name(prefix='backup', length=24)
        self.cmd('storage account create -n {} -g {} --location {}'.format(storage_Account, resource_group, WINDOWS_ASP_LOCATION_WEBAPP))
        container = self.create_random_name(prefix='backupcontainer', length=24)
        self.cmd('storage container create --account-name {} --name {}'.format(storage_Account, container))
        expirydate = (datetime.datetime.now() + datetime.timedelta(days=1, hours=3)).strftime("\"%Y-%m-%dT%H:%MZ\"")
        sastoken = self.cmd('storage container generate-sas --account-name {} --name {} --expiry {} --permissions rwdl'.format(storage_Account, container, expirydate))
        sasurl = '\"https://{}.blob.core.windows.net/{}?{}\"'.format(storage_Account, container, sastoken)
        backup_name = self.create_random_name(prefix='backup-name', length=24)
        self.cmd('webapp config backup create -g {} --webapp-name {} --backup-name {} --container-url {}'.format(resource_group, webapp, backup_name, sasurl), checks=[
            JMESPathCheck('blobName', backup_name)
        ])
        self.cmd('webapp config backup list -g {} --webapp-name {}'.format(resource_group, webapp), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].namePropertiesName', backup_name)
        ])

        slot_name = "slot"
        slot_backup_name = self.create_random_name(prefix='sbn-', length=24)
        self.cmd(f"webapp deployment slot create -g {resource_group} -n {webapp} -s {slot_name}")
        self.cmd(f"webapp config backup create -g {resource_group} --webapp-name {webapp} --backup-name {slot_backup_name} --container-url {sasurl} -s {slot_name}", checks=[
            JMESPathCheck('blobName', slot_backup_name)
        ])
        self.cmd(f"webapp config backup list -g {resource_group} --webapp-name {webapp} -s {slot_name}", checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].namePropertiesName', slot_backup_name)
        ])

    @ResourceGroupPreparer(parameter_name='resource_group', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer(name_prefix='backup', length=24, location=WINDOWS_ASP_LOCATION_WEBAPP, sku='Standard_LRS')
    def test_config_backup_restore(self, resource_group, storage_account_info):
        plan = self.create_random_name(prefix='plan-backup', length=24)
        webapp = self.create_random_name(prefix='backup-webapp', length=24)
        container = self.create_random_name(prefix='backupcontainer', length=24)
        backup_name = self.create_random_name(prefix='backup-name', length=24)

        expirydate = (datetime.datetime.now() + datetime.timedelta(days=1, hours=3)).strftime("\"%Y-%m-%dT%H:%MZ\"")
        slot_name = "slot"

        storage_account, account_key = storage_account_info
        self.cmd(f'storage container create --account-name {storage_account} --name {container} --account-key {account_key}')
        sastoken = self.cmd(f'storage container generate-sas --account-name {storage_account} --name {container} --expiry {expirydate} --permissions rwdl -otsv --account-key {account_key}').output.strip()
        sasurl = f'\"https://{storage_account}.blob.core.windows.net/{container}?{sastoken}\"'

        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku S1')
        self.cmd(f'webapp create -g {resource_group} -n {webapp} --plan {plan}')
        self.cmd(f"webapp deployment slot create -g {resource_group} -n {webapp} -s {slot_name}")

        self.cmd(f"webapp config backup create -g {resource_group} --webapp-name {webapp} --backup-name {backup_name} --container-url {sasurl}")
        time.sleep(240)

        # restore a backup
        self.cmd(f"webapp config backup restore -g {resource_group} --webapp-name {webapp} --target-name {webapp} --backup-name {backup_name} --container-url {sasurl} --overwrite --ignore-hostname-conflict")

        # restore a backup to a slot
        self.cmd(f"webapp config backup restore -g {resource_group} --webapp-name {webapp} --target-name {webapp} --slot {slot_name} --backup-name {backup_name} --container-url {sasurl} --overwrite --ignore-hostname-conflict")

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_config_backup_delete(self, resource_group):
        plan = self.create_random_name(prefix='plan-backup', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        webapp = self.create_random_name(prefix='backup-webapp', length=24)
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan))
        slot_name = "slot"
        self.cmd(f"webapp deployment slot create -g {resource_group} -n {webapp} -s {slot_name}")
        storage_Account = self.create_random_name(prefix='backup', length=24)
        self.cmd('storage account create -n {} -g {} --location {}'.format(storage_Account, resource_group, WINDOWS_ASP_LOCATION_WEBAPP))
        container = self.create_random_name(prefix='backupcontainer', length=24)
        self.cmd('storage container create --account-name {} --name {}'.format(storage_Account, container))
        expirydate = (datetime.datetime.now() + datetime.timedelta(days=1, hours=3)).strftime("\"%Y-%m-%dT%H:%MZ\"")
        sastoken = self.cmd('storage container generate-sas --account-name {} --name {} --expiry {} --permissions rwdl'.format(storage_Account, container, expirydate)).get_output_in_json()
        sasurl = '\"https://{}.blob.core.windows.net/{}?{}\"'.format(storage_Account, container, sastoken)
        time.sleep(30)
        backup_name = self.create_random_name(prefix='backup-name', length=24)
        slot_backup_name = self.create_random_name(prefix='sbn-', length=24)

        # Create a webapp backup
        self.cmd('webapp config backup create -g {} --webapp-name {} --backup-name {} --container-url {}'.format(resource_group, webapp, backup_name, sasurl), checks=[
            JMESPathCheck('blobName', backup_name)
        ])

        def get_backup_id(command, backup_name):
            backup_status = 'InProgress'
            list_backups_respone = []
            while backup_status == 'InProgress':
                list_backups_respone = self.cmd(command, checks=[
                    JMESPathCheck('length(@)', 1),
                    JMESPathCheck('[0].namePropertiesName', backup_name)
                ]).get_output_in_json()
                backup_status =  list_backups_respone[0]['status']
                # Backup operation is still in progress, Sleep 30 seconds
                time.sleep(30)
            return list_backups_respone[0]['backupId']

        # Verify webapp backups count
        webapp_backup_id = get_backup_id(f'webapp config backup list -g {resource_group} --webapp-name {webapp}', backup_name)

        # Delete webapp backup
        self.cmd('webapp config backup delete -g {} --webapp-name {} --backup-id {} --yes'.format(resource_group, webapp, webapp_backup_id))

        # Verify webapp backups count
        self.cmd('webapp config backup list -g {} --webapp-name {}'.format(resource_group, webapp), checks=[
            JMESPathCheck('length(@)', 0),
        ])

        # Create a webapp slot backup
        resp = self.cmd(f"webapp config backup create -g {resource_group} --webapp-name {webapp} --backup-name {slot_backup_name} --container-url {sasurl} -s {slot_name}", checks=[
            JMESPathCheck('blobName', slot_backup_name)
        ])

        # Verify webapp slot backups count
        webapp_slot_backup_id = get_backup_id(f"webapp config backup list -g {resource_group} --webapp-name {webapp} -s {slot_name}", slot_backup_name)

        # Delete webapp slot backup
        self.cmd('webapp config backup delete -g {} --webapp-name {} --backup-id {} --slot {} --yes'.format(resource_group, webapp, webapp_slot_backup_id, slot_name))

        # Verify webapp slot backups count
        self.cmd(f"webapp config backup list -g {resource_group} --webapp-name {webapp} -s {slot_name}", checks=[
            JMESPathCheck('length(@)', 0),
        ])




# Test Framework is not able to handle binary file format, hence, only run live
class AppServiceLogTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_download_win_web_log(self, resource_group):
        import zipfile
        webapp_name = self.create_random_name(
            prefix='webapp-win-log', length=24)
        plan = self.create_random_name(prefix='win-log', length=24)
        self.cmd(f'appservice plan create -g {resource_group} -n {plan} -l eastus')
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-source-url {} -r "node|16LTS"'.format(
            resource_group, webapp_name, plan, TEST_REPO_URL))
        # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        time.sleep(30)

        # sanity check the traces
        _, log_file = tempfile.mkstemp()
        log_dir = log_file + '-dir'
        self.cmd('webapp log download -g {} -n {} --log-file "{}"'.format(
            resource_group, webapp_name, log_file))
        zip_ref = zipfile.ZipFile(log_file, 'r')
        zip_ref.extractall(log_dir)
        self.assertTrue(os.path.isdir(os.path.join(
            log_dir, 'LogFiles', 'kudu', 'trace')))


class AppServicePlanScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_elastic_scale_plan(self, resource_group):
        plan = self.create_random_name('plan', 24)
        self.cmd('appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", False)
        ])

        self.cmd('appservice plan update -g {} -n {} --elastic-scale true'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", True)
        ])

        self.cmd('appservice plan update -g {} -n {} --elastic-scale false'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", False)
        ])

        self.cmd('appservice plan update -g {} -n {} --sku free'.format(resource_group, plan))
        self.cmd('appservice plan update -g {} -n {} --elastic-scale true'.format(resource_group, plan), expect_failure=True)

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    @unittest.skip("Temp test")
    def test_elastic_scale_plan_max_workers(self, resource_group):
        plan = self.create_random_name('plan', 24)
        self.cmd('appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", False),
            JMESPathCheck("properties.maximumElasticWorkerCount", 1)
        ])

        self.cmd('appservice plan update -g {} -n {} --elastic-scale true --max-elastic-worker-count 10'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", True),
            JMESPathCheck("properties.maximumElasticWorkerCount", 10)
        ])

        self.cmd('appservice plan update -g {} -n {} --max-elastic-worker-count 20'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", True),
            JMESPathCheck("properties.maximumElasticWorkerCount", 20)
        ])

        # ensure that we can't make --max-elastic-worker-count < the number of workers
        self.cmd('appservice plan update -g {} -n {} --max-elastic-worker-count 9 --number-of-workers 10'.format(resource_group, plan), expect_failure=True)

        self.cmd('appservice plan update -g {} -n {} --max-elastic-worker-count 10 --number-of-workers 10'.format(resource_group, plan))
        self.cmd('appservice plan update -g {} -n {} --max-elastic-worker-count 9'.format(resource_group, plan), expect_failure=True)

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_retain_plan(self, resource_group):
        webapp_name = self.create_random_name('web', 24)
        plan = self.create_random_name('web-plan', 24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp delete -g {} -n {} --keep-dns-registration --keep-empty-plan --keep-metrics'.format(resource_group, webapp_name))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].name', plan)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_auto_delete_plan(self, resource_group):
        webapp_name = self.create_random_name('web-del-test', 24)
        plan = self.create_random_name('web-del-plan', 24)
        self.cmd(
            'appservice plan create -g {} -n {} -l {}'.format(resource_group, plan, WINDOWS_ASP_LOCATION_WEBAPP))

        self.cmd('appservice plan update -g {} -n {} --sku S1'.format(resource_group, plan),
                 checks=[JMESPathCheck('name', plan),
                         JMESPathCheck('sku.tier', 'Standard'),
                         JMESPathCheck('sku.name', 'S1')])

        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))

        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))
        # test empty service plan should be automatically deleted.
        self.cmd('appservice plan list -g {}'.format(resource_group),
                 checks=[JMESPathCheck('length(@)', 0)])

    @ResourceGroupPreparer(location="eastus")
    def test_zone_redundant_plan(self, resource_group):
        plan = self.create_random_name('plan', 24)
        self.cmd(
            'appservice plan create -g {} -n {} -l {} -z --sku P1V3'.format(resource_group, plan, "eastus"))

        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('properties.zoneRedundant', True), JMESPathCheck('properties.numberOfWorkers', 3)])

        # test with unsupported SKU
        plan2 = self.create_random_name('plan', 24)
        self.cmd('appservice plan create -g {} -n {} -l {} -z --sku FREE'.format(resource_group, plan2, "eastus"), expect_failure=True)

        # test with unsupported location
        self.cmd('appservice plan create -g {} -n {} -l {} -z --sku P1V3'.format(resource_group, plan2, WINDOWS_ASP_LOCATION_WEBAPP), expect_failure=True)

        # ensure non zone redundant
        plan = self.create_random_name('plan', 24)
        self.cmd('functionapp plan create -g {} -n {} -l {} --sku FREE'.format(resource_group, plan, "eastus"))

        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[JMESPathCheck('properties.zoneRedundant', False)])


class WebappElasticScaleTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_elastic_scale(self, resource_group):
        plan = self.create_random_name('plan', 24)
        app = self.create_random_name('app', 24)
        self.cmd('appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", False)
        ])
        self.cmd('appservice plan update -g {} -n {} --elastic-scale true --max-elastic-worker-count 10'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", True)
        ])

        self.cmd("webapp create -g {} -n {} --plan {}".format(resource_group, app, plan))

        self.cmd("webapp show -g {} -n {}".format(resource_group, app), checks=[
            JMESPathCheck("siteConfig.minimumElasticInstanceCount", 1),
            JMESPathCheck("siteConfig.preWarmedInstanceCount", 1)
        ])
        self.cmd("webapp update -g {} -n {} --minimum-elastic-instance-count {} --prewarmed-instance-count {}".format(resource_group, app, 3, 5))
        self.cmd("webapp show -g {} -n {}".format(resource_group, app), checks=[
            JMESPathCheck("siteConfig.minimumElasticInstanceCount", 3),
            JMESPathCheck("siteConfig.preWarmedInstanceCount", 5)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_elastic_scale_prewarmed_instance_count(self, resource_group):
        plan = self.create_random_name('plan', 24)
        app = self.create_random_name('app', 24)
        self.cmd('appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))

        self.cmd("webapp create -g {} -n {} --plan {}".format(resource_group, app, plan))

        # ensure we can't set this without the ASP having elastic scale enabled
        self.cmd("webapp update -g {} -n {} --prewarmed-instance-count {}".format(resource_group, app, 5), expect_failure=True)

        self.cmd('appservice plan update -g {} -n {} --elastic-scale true --max-elastic-worker-count {}'.format(resource_group, plan, 4))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", True),
            JMESPathCheck("properties.maximumElasticWorkerCount", 4)
        ])

        # ensure we can't set the prewarmed instance count too high
        self.cmd("webapp update -g {} -n {} --prewarmed-instance-count {}".format(resource_group, app, 5), expect_failure=True)

        self.cmd("webapp update -g {} -n {} --prewarmed-instance-count {}".format(resource_group, app, 4))

        self.cmd("webapp show -g {} -n {}".format(resource_group, app), checks=[
            JMESPathCheck("siteConfig.preWarmedInstanceCount", 4)
        ])


    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_elastic_scale_min_elastic_instance_count(self, resource_group):
        plan = self.create_random_name('plan', 24)
        app = self.create_random_name('app', 24)
        self.cmd('appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))

        self.cmd("webapp create -g {} -n {} --plan {}".format(resource_group, app, plan))

        # ensure we can't set this without the ASP having elastic scale enabled
        self.cmd("webapp update -g {} -n {} --minimum-elastic-instance-count {}".format(resource_group, app, 5), expect_failure=True)

        self.cmd('appservice plan update -g {} -n {} --elastic-scale true --max-elastic-worker-count {}'.format(resource_group, plan, 4))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck("properties.elasticScaleEnabled", True),
            JMESPathCheck("properties.maximumElasticWorkerCount", 4)
        ])

        # ensure we can't set the prewarmed instance count too high
        self.cmd("webapp update -g {} -n {} --minimum-elastic-instance-count {}".format(resource_group, app, 5), expect_failure=True)

        self.cmd("webapp update -g {} -n {} --minimum-elastic-instance-count {}".format(resource_group, app, 4))

        self.cmd("webapp show -g {} -n {}".format(resource_group, app), checks=[
            JMESPathCheck("siteConfig.minimumElasticInstanceCount", 4)
        ])

class WebappConfigureTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_config', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_config(self, resource_group):
        webapp_name = self.create_random_name('webapp-config-test', 40)
        plan_name = self.create_random_name('webapp-config-plan', 40)

        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        # verify the baseline
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('alwaysOn', True),
            JMESPathCheck('autoHealEnabled', False),
            JMESPathCheck('phpVersion', '5.6'),
            JMESPathCheck('netFrameworkVersion', 'v4.0'),
            JMESPathCheck('pythonVersion', ''),
            JMESPathCheck('use32BitWorkerProcess', True),
            JMESPathCheck('webSocketsEnabled', False),
            JMESPathCheck('minTlsVersion', '1.2'),
            JMESPathCheck('ftpsState', 'FtpsOnly')])

        # update and verify
        checks = [
            JMESPathCheck('alwaysOn', True),
            JMESPathCheck('autoHealEnabled', True),
            JMESPathCheck('phpVersion', '7.4'),
            JMESPathCheck('netFrameworkVersion', 'v3.0'),
            JMESPathCheck('pythonVersion', '3.4'),
            JMESPathCheck('use32BitWorkerProcess', False),
            JMESPathCheck('webSocketsEnabled', True),
            JMESPathCheck('minTlsVersion', '1.0'),
            JMESPathCheck('http20Enabled', True),
            JMESPathCheck('ftpsState', 'Disabled')]

        self.cmd('webapp config set -g {} -n {} --always-on true --auto-heal-enabled true --php-version 7.4 '
                 '--net-framework-version v3.5 --python-version 3.4 --use-32bit-worker-process=false '
                 '--web-sockets-enabled=true --http20-enabled true --min-tls-version 1.0 --ftps-state Disabled'.format(resource_group, webapp_name)).assert_with_checks(checks)
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)) \
            .assert_with_checks(checks)

        # site appsettings testing
        # update through key value pairs
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("[?name=='s1']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])

        # show
        result = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        s2 = next((x for x in result if x['name'] == 's2'))
        self.assertEqual(s2['name'], 's2')
        self.assertEqual(s2['slotSetting'], False)
        self.assertEqual(s2['value'], 'bar')
        self.assertEqual(set([x['name'] for x in result]), set(
            ['s1', 's2', 's3', 'WEBSITE_NODE_DEFAULT_VERSION']))
        # delete
        self.cmd('webapp config appsettings delete -g {} -n {} --setting-names s1 s2'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck("[?name=='s3']|[0].value", None),
                     JMESPathCheck("[?name=='WEBSITE_NODE_DEFAULT_VERSION']|[0].value", None)
                 ])
        self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).assert_with_checks([
                JMESPathCheck("length([?name=='s1'])", 0),
                JMESPathCheck("length([?name=='s2'])", 0)])

        # hostnames
        self.cmd('webapp config hostname list -g {} --webapp-name {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', '{0}.azurewebsites.net'.format(webapp_name))])

        # site azure storage account configurations tests
        runtime = 'NODE|16-lts'
        linux_plan = self.create_random_name(
            prefix='webapp-linux-plan', length=24)
        linux_webapp = self.create_random_name(
            prefix='webapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} -l eastus2 --sku S1 --is-linux'.format(resource_group, linux_plan),
                 checks=[
                     # this weird field means it is a linux
                     JMESPathCheck('reserved', True),
                     JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(resource_group, linux_webapp, linux_plan, runtime),
                 checks=[
                     JMESPathCheck('name', linux_webapp),
        ])
        # add
        self.cmd(('webapp config storage-account add -g {} -n {} --custom-id Id --storage-type AzureFiles --account-name name '
                  '--share-name sharename --access-key key --mount-path /path/to/mount')
                  .format(resource_group, linux_webapp)).assert_with_checks([(JMESPathCheck("[?name=='Id']|[0].value.accessKey", None))])
        self.cmd('webapp config storage-account list -g {} -n {}'.format(resource_group, linux_webapp)).assert_with_checks([
            JMESPathCheck('length(@)', 1),
            JMESPathCheck("[?name=='Id']|[0].value.type", "AzureFiles"),
            JMESPathCheck("[?name=='Id']|[0].value.accountName", "name"),
            JMESPathCheck("[?name=='Id']|[0].value.shareName", "sharename"),
            JMESPathCheck("[?name=='Id']|[0].value.accessKey", "key"),
            JMESPathCheck("[?name=='Id']|[0].value.mountPath", "/path/to/mount")])
        # update
        self.cmd('webapp config storage-account update -g {} -n {} --custom-id Id --mount-path /different/path'
                 .format(resource_group, linux_webapp)).assert_with_checks([(JMESPathCheck("[?name=='Id']|[0].value.accessKey", None))])
        self.cmd('webapp config storage-account list -g {} -n {}'.format(resource_group, linux_webapp)).assert_with_checks([
            JMESPathCheck("length(@)", 1),
            JMESPathCheck("[?name=='Id']|[0].value.type", "AzureFiles"),
            JMESPathCheck("[?name=='Id']|[0].value.accountName", "name"),
            JMESPathCheck("[?name=='Id']|[0].value.shareName", "sharename"),
            JMESPathCheck("[?name=='Id']|[0].value.accessKey", "key"),
            JMESPathCheck("[?name=='Id']|[0].value.mountPath", "/different/path")])
        # list
        self.cmd('webapp config storage-account list -g {} -n {}'.format(resource_group, linux_webapp)).assert_with_checks([
            JMESPathCheck("length(@)", 1),
            JMESPathCheck('[0].name', 'Id')])
        # delete
        self.cmd('webapp config storage-account delete -g {} -n {} --custom-id Id'.format(resource_group, linux_webapp)).assert_with_checks([
            JMESPathCheck("length(@)", 0)])

        # site connection string tests
        self.cmd('webapp config connection-string set -t mysql -g {} -n {} --settings c1="conn1" c2=conn2 '
                 '--slot-settings c3=conn3'
                 .format(resource_group, linux_webapp)).assert_with_checks([
                     JMESPathCheck("[?name=='c1']|[0].value", None),
                     JMESPathCheck("[?name=='c2']|[0].value", None)
                     ])
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, linux_webapp)).assert_with_checks([
                     JMESPathCheck('length([])', 3),
                     JMESPathCheck("[?name=='c1']|[0].slotSetting", False),
                     JMESPathCheck("[?name=='c1']|[0].type", 'MySql'),
                     JMESPathCheck("[?name=='c1']|[0].value", 'conn1'),
                     JMESPathCheck("[?name=='c2']|[0].slotSetting", False),
                     JMESPathCheck("[?name=='c3']|[0].slotSetting", True)])
        self.cmd('webapp config connection-string delete -g {} -n {} --setting-names c1 c3'
                 .format(resource_group, linux_webapp)).assert_with_checks([JMESPathCheck("[?name=='c2']|[0].value", None)])
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, linux_webapp)).assert_with_checks([
                     JMESPathCheck('length([])', 1),
                     JMESPathCheck('[0].slotSetting', False),
                     JMESPathCheck('[0].name', 'c2')])
        # site connection string test with json input
        test_json = os.path.join(TEST_DIR, 'test.json')
        print(test_json)
        self.cmd('webapp config connection-string set -g {} -n {} --settings "@{}"'
                 .format(resource_group, linux_webapp, test_json)).assert_with_checks([
                     JMESPathCheck("[?name=='c1']|[0].value", None),
                     JMESPathCheck("[?name=='c2']|[0].value", None),
                     JMESPathCheck("[?name=='c3']|[0].value", None),
                     JMESPathCheck("[?name=='c4']|[0].value", None),])
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, linux_webapp)).assert_with_checks([
                     JMESPathCheck('length([])', 4),
                     JMESPathCheck("[?name=='c4']|[0].slotSetting", False),
                     JMESPathCheck("[?name=='c4']|[0].type", 'SQLServer'),
                     JMESPathCheck("[?name=='c4']|[0].value", 'conn4'),
                     JMESPathCheck("[?name=='c5']|[0].slotSetting", False),
                     JMESPathCheck("[?name=='c6']|[0].slotSetting", True)])
        # see deployment user; just make sure the command does return something
        self.assertTrue(
            self.cmd('webapp deployment user show').get_output_in_json()['type'])

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_update_site_configs_persists_ip_restrictions', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_update_site_configs_persists_ip_restrictions(self, resource_group):
        webapp_name = self.create_random_name('webapp-config-appsettings-persist', 40)
        plan_name = self.create_random_name('webapp-config-appsettings-persist', 40)
        subnet_name = self.create_random_name('testsubnet', 24)
        vnet_name = self.create_random_name('testvnet', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        # make sure access-restrictions is correct
        self.cmd('webapp config set -g {} -n {} --always-on true'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("length(ipSecurityRestrictions)", 1),
            JMESPathCheck("ipSecurityRestrictions[0].action", "Allow")
        ])
        self.cmd('webapp config access-restriction add -g {} -n {} --rule-name testclirule --priority 300 --subnet {} --vnet-name {}'.format(
            resource_group, webapp_name, subnet_name, vnet_name))
        self.cmd('webapp config set -g {} -n {} --always-on true'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("length(ipSecurityRestrictions)", 2),
            JMESPathCheck("ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("ipSecurityRestrictions[1].action", "Deny")
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_config_appsettings', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_config_appsettings(self, resource_group):
        webapp_name = self.create_random_name('webapp-config-appsettings-test', 40)
        plan_name = self.create_random_name('webapp-config-appsettings-plan', 40)

        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        # site appsettings testing
        # update through key value pairs
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=foo s2=bar s3=bar2'
                 .format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("[?name=='s1']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])

        # show
        result = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        s2 = next((x for x in result if x['name'] == 's2'))
        self.assertEqual(s2['name'], 's2')
        self.assertEqual(s2['slotSetting'], False)
        self.assertEqual(s2['value'], 'bar')
        self.assertEqual(set([x['name'] for x in result]), set(
            ['s1', 's2', 's3', 'WEBSITE_NODE_DEFAULT_VERSION']))

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_json', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_update_webapp_settings_thru_json(self, resource_group):
        webapp_name = self.create_random_name('webapp-config-test', 40)
        plan_name = self.create_random_name('webapp-config-plan', 40)
        slot = 'staging'
        # update through a json file with key value pair
        _, settings_file = tempfile.mkstemp()
        with open(settings_file, 'w+') as file:
            file.write(json.dumps({'s2': 'value2'}))

        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp_name, slot),
                 checks=[
            JMESPathCheck('name', slot)
        ])

        self.cmd('webapp config appsettings set -g {} -n {} --settings s=value "@{}"'.format(
            resource_group, webapp_name, settings_file)).assert_with_checks([
            JMESPathCheck("[?name=='s']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None)
        ])
        
        output = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        output = [s for s in output if s['name'] in ['s', 's2']]
        output.sort(key=lambda s: s['name'])
        self.assertEqual(output[0], {
            'name': 's',
            'value': 'value',
            'slotSetting': False
        })
        self.assertEqual(output[1], {
            'name': 's2',
            'value': 'value2',
            'slotSetting': False
        })

        # output using the output of the set/list command
        output.append({
            'name': 's3',
            'value': 'value3',
            'slotSetting': True
        })
        with open(settings_file, 'w') as file:
            file.write(json.dumps(output))

        self.cmd('webapp config appsettings set -g {} -n {} --settings "@{}"'.format(
            resource_group, webapp_name, settings_file)).assert_with_checks([
            JMESPathCheck("[?name=='s']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])
        
        output = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        output = [s for s in output if s['name'] in ['s', 's2', 's3']]
        output.sort(key=lambda s: s['name'])

        self.assertEqual(output[0], {
            'name': 's',
            'value': 'value',
            'slotSetting': False
        })
        self.assertEqual(output[1], {
            'name': 's2',
            'value': 'value2',
            'slotSetting': False
        })
        self.assertEqual(output[2], {
            'name': 's3',
            'value': 'value3',
            'slotSetting': True
        })
        with open(settings_file, 'w') as file:
            file.write(json.dumps(output))

        self.cmd('webapp config appsettings set -g {} -n {} --slot {} --settings "@{}"'.format(
            resource_group, webapp_name, slot, settings_file)).assert_with_checks([
            JMESPathCheck("[?name=='s1']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])
        
        output = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        output = [s for s in output if s['name'] in ['s', 's2', 's3']]
        output.sort(key=lambda s: s['name'])

        self.assertEqual(output[0], {
            'name': 's',
            'value': 'value',
            'slotSetting': False
        })
        self.assertEqual(output[1], {
            'name': 's2',
            'value': 'value2',
            'slotSetting': False
        })
        self.assertEqual(output[2], {
            'name': 's3',
            'value': 'value3',
            'slotSetting': True
        })

        # app settings set with --slot-settings
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings "@{}"'.format(
            resource_group, webapp_name, settings_file)).assert_with_checks([
            JMESPathCheck("[?name=='s']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])
        
        output = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        output = [s for s in output if s['name'] in ['s', 's2', 's3']]
        output.sort(key=lambda s: s['name'])

        self.assertEqual(output[0], {
            'name': 's',
            'value': 'value',
            'slotSetting': False
        })
        self.assertEqual(output[1], {
            'name': 's2',
            'value': 'value2',
            'slotSetting': False
        })
        self.assertEqual(output[2], {
            'name': 's3',
            'value': 'value3',
            'slotSetting': True
        })

        self.cmd('webapp config appsettings set -g {} -n {} --slot {} --slot-settings "@{}"'.format(
            resource_group, webapp_name, slot, settings_file)).assert_with_checks([
            JMESPathCheck("[?name=='s']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None),
            JMESPathCheck("[?name=='s3']|[0].value", None)
        ])
        
        output = self.cmd('webapp config appsettings list -g {} -n {}'.format(
            resource_group, webapp_name)).get_output_in_json()
        output = [s for s in output if s['name'] in ['s', 's2', 's3']]
        output.sort(key=lambda s: s['name'])

        self.assertEqual(output[0], {
            'name': 's',
            'value': 'value',
            'slotSetting': False
        })
        self.assertEqual(output[1], {
            'name': 's2',
            'value': 'value2',
            'slotSetting': False
        })
        self.assertEqual(output[2], {
            'name': 's3',
            'value': 'value3',
            'slotSetting': True
        })

        # update site config
        site_configs = {
            "requestTracingEnabled": True,
            "alwaysOn": True
        }
        with open(settings_file, 'w') as file:
            file.write(json.dumps(site_configs))
        self.cmd('webapp config set -g {} -n {} --generic-configurations "@{}"'.format(resource_group, webapp_name, settings_file)).assert_with_checks([
            JMESPathCheck("requestTracingEnabled", True),
            JMESPathCheck("alwaysOn", True),
        ])



class WebappScaleTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_scale(self, resource_group):
        plan = self.create_random_name(prefix='scale-plan', length=24)
        # start with shared sku
        self.cmd('appservice plan create -g {} -n {} --sku SHARED'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'D1'),
            JMESPathCheck('sku.tier', 'Shared'),
            JMESPathCheck('sku.size', 'D1'),
            JMESPathCheck('sku.family', 'D'),
            # 0 means the default value: 1 instance
            JMESPathCheck('sku.capacity', 0)
        ])
        # scale up
        self.cmd(
            'appservice plan update -g {} -n {} --sku S2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S2'),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.size', 'S2'),
            JMESPathCheck('sku.family', 'S')
        ])
        # scale down
        self.cmd(
            'appservice plan update -g {} -n {} --sku B1'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B')
        ])
        # scale out
        self.cmd(
            'appservice plan update -g {} -n {} --number-of-workers 2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B'),
            JMESPathCheck('sku.capacity', 2)
        ])


@unittest.skip("Test needs to re-done to match the errors")
class AppServiceBadErrorPolishTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='resource_group', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @ResourceGroupPreparer(parameter_name='resource_group2', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_appservice_error_polish(self, resource_group, resource_group2):
        plan = self.create_random_name(prefix='web-error-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-error', length=24)
        self.cmd('group create -n {} -l {}'.format(resource_group2, WINDOWS_ASP_LOCATION_WEBAPP))
        self.cmd(
            'appservice plan create -g {} -n {} --sku b1'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd(
            'appservice plan create -g {} -n {} --sku b1'.format(resource_group2, plan))
        # we will try to produce an error by try creating 2 webapp with same name in different groups
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group2,
                                                              webapp_name, plan), expect_failure=True)
        # TODO: ensure test fx can capture error details for us to verify
        # allowed_exceptions='Website with given name {} already exists'.format(webapp_name)


# this test doesn't contain the ultimate verification which you need to manually load the frontpage in a browser
class LinuxWebappScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_webapp(self, resource_group):
        runtime = 'NODE|16-lts'
        plan = self.create_random_name(prefix='webapp-linux-plan', length=24)
        webapp = self.create_random_name(prefix='webapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(resource_group, webapp, plan, runtime), checks=[
            JMESPathCheck('name', webapp),
        ])
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck('windowsFxVersion', None)
        ])
        # workaround the fact that a new linux web's "kind" won't be settled instantatest_linux_webapp_remote_sshneously
        time.sleep(30)
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', webapp),
            JMESPathCheck('[0].kind', 'app,linux')
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck('name', webapp),
            JMESPathCheck('kind', 'app,linux')
        ])
        self.cmd('webapp config set -g {} -n {} --startup-file {}'.format(resource_group, webapp, 'process.json'), checks=[
            JMESPathCheck('appCommandLine', 'process.json')
        ])

        result = self.cmd('webapp deployment container config -g {} -n {} --enable-cd true'.format(
            resource_group, webapp)).get_output_in_json()

        self.assertTrue(result['CI_CD_URL'].startswith('https://'))
        self.assertTrue(result['CI_CD_URL'].endswith(
            '.scm.azurewebsites.net/docker/hook'))

        result = self.cmd('webapp config container set -g {} -n {} --docker-custom-image-name {} --docker-registry-server-password {} --docker-registry-server-user {} --docker-registry-server-url {} --enable-app-service-storage {}'.format(
            resource_group, webapp, 'foo-image', 'foo-password', 'foo-user', 'foo-url', 'false')).get_output_in_json()
        self.assertEqual(set(x['value'] for x in result if x['name'] ==
                             'DOCKER_REGISTRY_SERVER_PASSWORD'), set([None]))  # we mask the password

        result = self.cmd('webapp config container show -g {} -n {} '.format(
            resource_group, webapp)).get_output_in_json()
        self.assertEqual(set(x['name'] for x in result), set(['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                                                              'DOCKER_CUSTOM_IMAGE_NAME', 'DOCKER_REGISTRY_SERVER_PASSWORD', 'WEBSITES_ENABLE_APP_SERVICE_STORAGE']))
        self.assertEqual(set(x['value'] for x in result if x['name'] ==
                             'DOCKER_REGISTRY_SERVER_PASSWORD'), set([None]))   # we mask the password
        sample = next(
            (x for x in result if x['name'] == 'DOCKER_REGISTRY_SERVER_URL'))
        self.assertEqual(sample, {
                         'name': 'DOCKER_REGISTRY_SERVER_URL', 'slotSetting': False, 'value': 'foo-url'})
        sample = next(
            (x for x in result if x['name'] == 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'))
        self.assertEqual(sample, {
                         'name': 'WEBSITES_ENABLE_APP_SERVICE_STORAGE', 'slotSetting': False, 'value': 'false'})

        result = self.cmd('webapp config container set -g {} -n {} --docker-custom-image-name {} --docker-registry-server-password {} --docker-registry-server-user {} --docker-registry-server-url {} --enable-app-service-storage {}'.format(
            resource_group, webapp, 'foo-image', 'foo-password', 'foo-user', 'foo-url', 'true')).get_output_in_json()
        self.assertEqual(set(x['value'] for x in result if x['name'] ==
                             'DOCKER_REGISTRY_SERVER_PASSWORD'), set([None]))  # we mask the password
        sample = next(
            (x for x in result if x['name'] == 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'))
        self.assertEqual(sample, {
                         'name': 'WEBSITES_ENABLE_APP_SERVICE_STORAGE', 'slotSetting': False, 'value': 'true'})

        result = self.cmd('webapp config container show -g {} -n {} '.format(
            resource_group, webapp)).get_output_in_json()
        self.assertEqual(set(x['name'] for x in result), set(['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                                                              'DOCKER_CUSTOM_IMAGE_NAME', 'DOCKER_REGISTRY_SERVER_PASSWORD', 'WEBSITES_ENABLE_APP_SERVICE_STORAGE']))

        self.cmd(
            'webapp config container delete -g {} -n {}'.format(resource_group, webapp))
        result2 = self.cmd('webapp config container show -g {} -n {} '.format(
            resource_group, webapp)).get_output_in_json()
        self.assertEqual(result2, [])


class LinuxWebappSSHScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_webapp_ssh(self, resource_group):
        # On Windows, test 'webapp ssh' throws error
        import platform
        if platform.system() == "Windows":
            return

        runtime = 'node|16-lts'
        plan = self.create_random_name(prefix='webapp-ssh-plan', length=24)
        webapp = self.create_random_name(prefix='webapp-ssh', length=24)
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(
            resource_group, webapp, plan, runtime))
        time.sleep(30)
        requests.get('http://{}.azurewebsites.net'.format(webapp), timeout=240)
        instance = self.cmd('webapp list-instances -g {} -n {}'.format(resource_group, webapp)).get_output_in_json()
        instance_name=[item.get('name') for item in instance]
        self.cmd('webapp ssh -g {} -n {} --timeout 5'.format(resource_group, webapp, instance_name))
        time.sleep(30)


class LinuxWebappRemoteSSHScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_webapp_remote_ssh(self, resource_group):
        runtime = 'node|16-lts'
        plan = self.create_random_name(
            prefix='webapp-remote-ssh-plan', length=40)
        webapp = self.create_random_name(prefix='webapp-remote-ssh', length=40)
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(
            resource_group, webapp, plan, runtime))
        time.sleep(30)
        requests.get('http://{}.azurewebsites.net'.format(webapp), timeout=240)


class LinuxWebappMulticontainerSlotScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_webapp_multicontainer_slot(self, resource_group):
        webapp_name = self.create_random_name(
            prefix='webapp-linux-multi', length=24)
        plan = self.create_random_name(prefix='plan-linux-multi', length=24)
        config_file = os.path.join(TEST_DIR, 'sample-compose.yml')
        slot = "stage"
        slot_webapp_name = "{}-{}".format(webapp_name, slot)
        slot_config_file = os.path.join(TEST_DIR, 'sample-compose-slot.yml')

        self.cmd(
            'appservice plan create -g {} -n {} --is-linux --sku S1'.format(resource_group, plan))
        self.cmd("webapp create -g {} -n {} --plan {} --multicontainer-config-file \"{}\" "
                 "--multicontainer-config-type COMPOSE".format(resource_group, webapp_name, plan, config_file))

        last_number_seen = 99999999
        for x in range(0, 10):
            r = requests.get(
                'http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
            # verify the web page
            self.assertTrue('Hello World! I have been seen' in str(r.content))
            current_number = [int(s)
                              for s in r.content.split() if s.isdigit()][0]
            self.assertNotEqual(current_number, last_number_seen)
            last_number_seen = current_number

        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(
            resource_group, webapp_name, slot))
        self.cmd("webapp config container set -g {} -n {} --slot {} --multicontainer-config-file \"{}\" "
                 "--multicontainer-config-type COMPOSE".format(resource_group, webapp_name, slot, slot_config_file))

        last_number_seen = 99999999
        for x in range(0, 10):
            r = requests.get(
                'http://{}.azurewebsites.net'.format(slot_webapp_name), timeout=240)
            # verify the web page
            self.assertTrue(
                'Hello from a slot! I have been seen' in str(r.content))
            current_number = [int(s)
                              for s in r.content.split() if s.isdigit()][0]
            self.assertNotEqual(current_number, last_number_seen)
            last_number_seen = current_number


class WebappACRScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_acr_integration(self, resource_group):
        plan = self.create_random_name(prefix='acrtestplan', length=24)
        webapp = self.create_random_name(prefix='webappacrtest', length=24)
        runtime = 'NODE|16-lts'
        acr_registry_name = webapp
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(
            resource_group, acr_registry_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(
            resource_group, webapp, plan, runtime))
        creds = self.cmd('acr credential show -n {} -g {}'.format(
            acr_registry_name, resource_group)).get_output_in_json()
        self.cmd('webapp config container set -g {0} -n {1} --docker-custom-image-name {2}.azurecr.io/image-name:latest --docker-registry-server-url https://{2}.azurecr.io'.format(
            resource_group, webapp, acr_registry_name), checks=[
                JMESPathCheck(
                    "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username'])
        ])


class WebappContainerScenarioTests(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @AllowLargeResponse()
    def test_linux_slot_container_settings_override(self, resource_group):
        app_name = self.create_random_name(prefix="", length=24)
        plan = self.create_random_name(prefix="", length=24)
        acr_registry_name = self.create_random_name(prefix="", length=24)
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(
            resource_group, acr_registry_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        creds = self.cmd('acr credential show -n {} -g {}'.format(
            acr_registry_name, resource_group)).get_output_in_json()
        self.cmd('az webapp create -g {} -n {} -p {} -i {}.azurecr.io/image-name:latest -s {} -w {}'.format(
            resource_group, app_name, plan, acr_registry_name, creds['username'], creds['passwords'][0]['value']
        ))

        self.cmd('webapp config container show -g {} -n {} '.format(resource_group, app_name), checks=[
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username']),
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_URL']|[0].name", 'DOCKER_REGISTRY_SERVER_URL')
        ])
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, app_name), checks=[
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME'].value|[0]", creds['username'])
        ])
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, app_name), checks=[
            JMESPathCheck('linuxFxVersion', 'DOCKER|{}.azurecr.io/image-name:latest'.format(acr_registry_name))])

        slot_name = "slot"
        # note the different image name
        self.cmd('az webapp deployment slot create -g {} -n {} --configuration-source {} -s {} --deployment-container-image-name {}.azurecr.io/image-name-2:latest'.format(
            resource_group, app_name, app_name, slot_name, acr_registry_name
        ))

        self.cmd('webapp config container show -g {} -n {} -s {}'.format(resource_group, app_name, slot_name), checks=[
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username']),
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_URL']|[0].name", 'DOCKER_REGISTRY_SERVER_URL')
        ])
        self.cmd('webapp config appsettings list -g {} -n {} -s {}'.format(resource_group, app_name, slot_name), checks=[
            JMESPathCheck(
                "[?name=='DOCKER_REGISTRY_SERVER_USERNAME'].value|[0]", creds['username'])
        ])
        self.cmd('webapp config show -g {} -n {} -s {}'.format(resource_group, app_name, slot_name), checks=[
            JMESPathCheck('linuxFxVersion', 'DOCKER|{}.azurecr.io/image-name-2:latest'.format(acr_registry_name))])



class WebappGitScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_git(self, resource_group):
        plan = self.create_random_name(prefix='webapp-git-plan5', length=24)
        webapp = self.create_random_name(prefix='web-git-test2', length=24)
        # You can create and use any repros with the 3 files under "./sample_web"
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan))
        self.cmd('webapp deployment source config -g {} -n {} --repo-url {} --branch {} --manual-integration'.format(resource_group, webapp, test_git_repo, 'master'), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('isMercurial', False),
            JMESPathCheck('branch', 'master')
        ])
        self.cmd('webapp deployment source show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('isMercurial', False),
            JMESPathCheck('branch', 'master')
        ])
        self.cmd(
            'webapp deployment source delete -g {} -n {}'.format(resource_group, webapp))
        self.cmd('webapp deployment source show -g {} -n {}'.format(resource_group, webapp),
                 checks=JMESPathCheck('repoUrl', None))


class WebappSlotScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_slot(self, resource_group):
        plan = self.create_random_name(prefix='slot-test-plan', length=24)
        webapp = self.create_random_name(prefix='slot-test-web', length=24)

        plan_result = self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group,
                                                              webapp, plan_result['name']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        slot2 = 'dev'
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        test_php_version = '7.4'
        # create a few app-settings to test they can be cloned
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=v1 --slot-settings s2=v2'
                 .format(resource_group, webapp)).assert_with_checks([
            JMESPathCheck("[?name=='s1']|[0].value", None),
            JMESPathCheck("[?name=='s2']|[0].value", None)
        ])
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck('name', slot)
        ])
        self.cmd('webapp deployment source config -g {} -n {} --repo-url {} --branch {} -s {} --manual-integration'.format(resource_group, webapp, test_git_repo, slot, slot), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('branch', slot)
        ])
        # swap with prod and verify the git branch also switched
        self.cmd(
            'webapp deployment slot swap -g {} -n {} -s {}'.format(resource_group, webapp, slot))
        result = self.cmd('webapp config appsettings list -g {} -n {} -s {}'.format(
            resource_group, webapp, slot)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(
            ['s1', 'WEBSITE_NODE_DEFAULT_VERSION']))
        # create a new slot by cloning from prod slot
        self.cmd('webapp config set -g {} -n {} --php-version {}'.format(
            resource_group, webapp, test_php_version))
        self.cmd('webapp deployment slot create -g {} -n {} --slot {} --configuration-source {}'.format(
            resource_group, webapp, slot2, webapp))
        self.cmd('webapp config show -g {} -n {} --slot {}'.format(resource_group, webapp, slot2), checks=[
            JMESPathCheck("phpVersion", test_php_version),
        ])
        self.cmd('webapp config appsettings set -g {} -n {} --slot {} --settings s3=v3 --slot-settings s4=v4'
                 .format(resource_group, webapp, slot2)).assert_with_checks([
                     JMESPathCheck("[?name=='s3']|[0].value", None)
                     ])

        self.cmd('webapp config connection-string set -g {} -n {} -t mysql --slot {} --settings c1=connection1 --slot-settings c2=connection2'
                 .format(resource_group, webapp, slot2)).assert_with_checks([
                     JMESPathCheck("[?name=='c1']|[0].value", None),
                     JMESPathCheck("[?name=='c2']|[0].value", None)
                 ])
        # verify we can swap with non production slot
        self.cmd('webapp deployment slot swap -g {} -n {} --slot {} --target-slot {}'.format(
            resource_group, webapp, slot, slot2))
        result = self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(
            resource_group, webapp, slot2)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(
            ['s1', 's4', 'WEBSITE_NODE_DEFAULT_VERSION']))
        result = self.cmd('webapp config connection-string list -g {} -n {} --slot {}'.format(
            resource_group, webapp, slot2)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(['c2']))
        result = self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(
            resource_group, webapp, slot)).get_output_in_json()
        self.assertTrue(set(['s3']).issubset(set([x['name'] for x in result])))
        result = self.cmd('webapp config connection-string list -g {} -n {} --slot {}'.format(
            resource_group, webapp, slot)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(['c1']))
        self.cmd('webapp deployment slot list -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck("length([])", 2),
            JMESPathCheck("length([?name=='{}'])".format(slot2), 1),
            JMESPathCheck("length([?name=='{}'])".format(slot), 1),
        ])
        self.cmd('webapp deployment slot auto-swap -g {} -n {} -s {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("autoSwapSlotName", "production")
        ])
        self.cmd('webapp deployment slot auto-swap -g {} -n {} -s {} --disable'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("autoSwapSlotName", None)
        ])
        self.cmd(
            'webapp deployment slot delete -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        # try another way to delete a slot and exercise all options
        self.cmd('webapp delete -g {} -n {} --slot {} --keep-dns-registration --keep-empty-plan --keep-metrics'.format(resource_group, webapp, slot2))


class WebappSlotTrafficRouting(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_traffic_routing(self, resource_group):
        plan = self.create_random_name(prefix='slot-traffic-plan', length=24)
        webapp = self.create_random_name(prefix='slot-traffic-web', length=24)
        plan_result = self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group,
                                                              webapp, plan_result['name']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        # create an empty slot
        self.cmd(
            'webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        self.cmd('webapp traffic-routing set -g {} -n {} -d {}=15'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[0].actionHostName", webapp +
                          '-' + slot + '.azurewebsites.net'),
            JMESPathCheck("[0].reroutePercentage", 15.0)
        ])
        self.cmd('webapp traffic-routing show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck("[0].actionHostName", webapp +
                          '-' + slot + '.azurewebsites.net'),
            JMESPathCheck("[0].reroutePercentage", 15.0)
        ])
        self.cmd(
            'webapp traffic-routing clear -g {} -n {}'.format(resource_group, webapp))


class AppServiceCors(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_cors(self, resource_group):
        self.kwargs.update({
            'plan': self.create_random_name(prefix='slot-traffic-plan', length=24),
            'web': self.create_random_name(prefix='slot-traffic-web', length=24),
            'slot': 'slot1'
        })
        self.cmd('appservice plan create -g {rg} -n {plan} --sku S1')
        self.cmd('webapp create -g {rg} -n {web} --plan {plan}')
        self.cmd(
            'webapp cors add -g {rg} -n {web} --allowed-origins https://msdn.com https://msn.com')
        self.cmd('webapp cors show -g {rg} -n {web}',
                 checks=self.check('allowedOrigins', ['https://msdn.com', 'https://msn.com']))
        self.cmd(
            'webapp cors remove -g {rg} -n {web} --allowed-origins https://msn.com')
        self.cmd('webapp cors show -g {rg} -n {web}',
                 checks=self.check('allowedOrigins', ['https://msdn.com']))

        self.cmd(
            'webapp deployment slot create -g {rg} -n {web} --slot {slot}')
        self.cmd(
            'webapp cors add -g {rg} -n {web} --slot {slot} --allowed-origins https://foo.com')
        self.cmd('webapp cors show -g {rg} -n {web} --slot {slot}',
                 checks=self.check('allowedOrigins', ['https://foo.com']))
        self.cmd(
            'webapp cors remove -g {rg} -n {web} --slot {slot} --allowed-origins https://foo.com')
        self.cmd('webapp cors show -g {rg} -n {web} --slot {slot}',
                 checks=self.check('allowedOrigins', []))

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_cors(self, resource_group, storage_account):
        self.kwargs.update({
            'plan': self.create_random_name(prefix='slot-traffic-plan', length=24),
            'function': self.create_random_name(prefix='slot-traffic-web', length=24),
            'storage': self.create_random_name(prefix='storage', length=24)
        })
        self.cmd('appservice plan create -g {rg} -n {plan} --sku S1')
        self.cmd(
            'storage account create --name {storage} -g {rg} --sku Standard_LRS')
        self.cmd(
            'functionapp create -g {rg} -n {function} --plan {plan} -s {storage} --functions-version 4')
        self.cmd(
            'functionapp cors add -g {rg} -n {function} --allowed-origins https://msdn.com https://msn.com')
        result = self.cmd(
            'functionapp cors show -g {rg} -n {function}').get_output_in_json()['allowedOrigins']
        # functionapp has pre-defined cors. We verify the ones we added are in the list
        self.assertTrue(
            set(['https://msdn.com', 'https://msn.com']).issubset(set(result)))


class WebappSlotSwapScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_slot_swap(self, resource_group):
        plan = self.create_random_name(prefix='slot-swap-plan', length=24)
        webapp = self.create_random_name(prefix='slot-swap-web', length=24)
        plan_result = self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group,
                                                              webapp, plan_result['name']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings s1=prod'
                 .format(resource_group, webapp)).assert_with_checks([
                     JMESPathCheck("[?name=='s1']|[0].value", None)
                     ])
        # create an empty slot
        self.cmd(
            'webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings s1=slot --slot {}'
                 .format(resource_group, webapp, slot)).assert_with_checks([
                     JMESPathCheck("[?name=='s1']|[0].value", None),
                     JMESPathCheck("[?name=='s2']|[0].value", None),
                     JMESPathCheck("[?name=='s3']|[0].value", None)
                     ])
        # swap with preview
        self.cmd('webapp deployment slot swap -g {} -n {} -s {} --action preview'.format(
            resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[?name=='s1']|[0].value", 'prod')
        ])
        # complete the swap
        self.cmd(
            'webapp deployment slot swap -g {} -n {} -s {}'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[?name=='s1']|[0].value", 'slot')
        ])
        # reset
        self.cmd('webapp deployment slot swap -g {} -n {} -s {} --action reset'.format(
            resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[?name=='s1']|[0].value", 'slot')
        ])


class WebappSSLCertTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_ssl(self, resource_group, resource_group_location):
        plan = self.create_random_name(prefix='ssl-test-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-ssl-test', length=20)
        slot_name = self.create_random_name(prefix='slot-ssl-test', length=20)
        # Cert Generated using
        # https://docs.microsoft.com/azure/app-service-web/web-sites-configure-ssl-certificate#bkmk_ssopenssl
        pfx_file = os.path.join(TEST_DIR, 'server.pfx')
        cert_password = 'test'
        cert_thumbprint = '9E9735C45C792B03B3FFCCA614852B32EE71AD6B'
        # we configure tags here in a hope to capture a repro for https://github.com/Azure/azure-cli/issues/6929
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --tags plan=plan1'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group,
                                                           plan), self.check('tags.plan', 'plan1'))
        self.cmd('webapp create -g {} -n {} --plan {} --tags web=web1'.format(
            resource_group, webapp_name, plan))
        self.cmd('webapp config ssl upload -g {} -n {} --certificate-file "{}" --certificate-password {} --certificate-name {}'.format(resource_group, webapp_name, pfx_file, cert_password, "test123"), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint),
            JMESPathCheck('name', 'test123')
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group,
                                                  webapp_name), self.check('tags.web', 'web1'))
        self.cmd('webapp config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {}'.format(resource_group, webapp_name, cert_thumbprint, 'SNI'), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(
                webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(
                webapp_name), cert_thumbprint)
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group,
                                                  webapp_name), self.check('tags.web', 'web1'))
        self.cmd('webapp config ssl unbind -g {} -n {} --certificate-thumbprint {}'.format(resource_group, webapp_name, cert_thumbprint), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(
                webapp_name), 'Disabled'),
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group,
                                                  webapp_name), self.check('tags.web', 'web1'))
        self.cmd('webapp config ssl delete -g {} --certificate-thumbprint {}'.format(
            resource_group, cert_thumbprint))
        self.cmd('webapp show -g {} -n {}'.format(resource_group,
                                                  webapp_name), self.check('tags.web', 'web1'))
        # test with slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(
            resource_group, webapp_name, slot_name))
        self.cmd('webapp config ssl upload -g {} -n {} --certificate-file "{}" --certificate-password {} -s {}'.format(resource_group, webapp_name, pfx_file, cert_password, slot_name), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint)
        ])
        self.cmd(
            'webapp show -g {} -n {} -s {}'.format(resource_group, webapp_name, slot_name))
        self.cmd('webapp config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {} -s {}'.format(resource_group, webapp_name, cert_thumbprint, 'SNI', slot_name), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}-{}.azurewebsites.net']|[0].sslState".format(
                webapp_name, slot_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}-{}.azurewebsites.net']|[0].thumbprint".format(
                webapp_name, slot_name), cert_thumbprint)
        ])
        self.cmd(
            'webapp show -g {} -n {} -s {}'.format(resource_group, webapp_name, slot_name))
        self.cmd('webapp config ssl unbind -g {} -n {} --certificate-thumbprint {} -s {}'.format(resource_group, webapp_name, cert_thumbprint, slot_name), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}-{}.azurewebsites.net']|[0].sslState".format(
                webapp_name, slot_name), 'Disabled'),
        ])
        self.cmd(
            'webapp show -g {} -n {} -s {}'.format(resource_group, webapp_name, slot_name))
        self.cmd('webapp config ssl delete -g {} --certificate-thumbprint {}'.format(
            resource_group, cert_thumbprint))
        self.cmd(
            'webapp show -g {} -n {} -s {}'.format(resource_group, webapp_name, slot_name))
        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_ssl_specify_hostname(self, resource_group, resource_group_location):
        plan = self.create_random_name(prefix='ssl-test-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-ssl-test', length=20)
        # Cert Generated using
        # https://docs.microsoft.com/azure/app-service-web/web-sites-configure-ssl-certificate#bkmk_ssopenssl
        pfx_file = os.path.join(TEST_DIR, 'server.pfx')
        cert_password = 'test'
        cert_thumbprint = '9E9735C45C792B03B3FFCCA614852B32EE71AD6B'
        hostname = f"{webapp_name}.azurewebsites.net"
        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku S1 --tags plan=plan1')
        self.cmd(f'webapp create -g {resource_group} -n {webapp_name} --plan {plan} --tags web=web1')
        self.cmd(f'webapp config ssl upload -g {resource_group} -n {webapp_name} --certificate-file "{pfx_file}" --certificate-password {cert_password}', checks=[
            JMESPathCheck('thumbprint', cert_thumbprint)
        ])
        self.cmd(f'webapp config ssl bind -g {resource_group} -n {webapp_name} --certificate-thumbprint {cert_thumbprint} --hostname {hostname} --ssl-type SNI', checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(
                webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(
                webapp_name), cert_thumbprint)
        ])
        self.cmd(f'webapp config ssl unbind -g {resource_group} -n {webapp_name} --certificate-thumbprint {cert_thumbprint} --hostname {hostname}', checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(
                webapp_name), 'Disabled'),
        ])


class WebappSSLImportCertTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    @KeyVaultPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, name_prefix='kv-ssl-test', name_len=20)
    def test_webapp_ssl_import(self, resource_group, key_vault):
        plan_name = self.create_random_name(prefix='ssl-test-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-ssl-test', length=20)
        # Cert Generated using
        # https://docs.microsoft.com/azure/app-service-web/web-sites-configure-ssl-certificate#bkmk_ssopenssl
        pfx_file = os.path.join(TEST_DIR, 'server.pfx')
        cert_password = 'test'
        cert_thumbprint = '9E9735C45C792B03B3FFCCA614852B32EE71AD6B'
        cert_name = 'test-cert'
        # we configure tags here in a hope to capture a repro for https://github.com/Azure/azure-cli/issues/6929
        self.cmd(
            'appservice plan create -g {} -n {} --sku B1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        self.cmd('keyvault set-policy -g {} --name {} --spn {} --secret-permissions get'.format(
            resource_group, key_vault, 'Microsoft.Azure.WebSites'))
        self.cmd('keyvault certificate import --name {} --vault-name {} --file "{}" --password {}'.format(
            cert_name, key_vault, pfx_file, cert_password))

        self.cmd('webapp config ssl import --resource-group {} --name {}  --key-vault {} --key-vault-certificate-name {} --certificate-name {}'.format(resource_group, webapp_name, key_vault, cert_name, "test123"), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint),
			JMESPathCheck('name', 'test123')
        ])

        self.cmd('webapp config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {}'.format(resource_group, webapp_name, cert_thumbprint, 'SNI'), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(
                webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(
                webapp_name), cert_thumbprint)
        ])

    @ResourceGroupPreparer(parameter_name='kv_resource_group', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_ssl_import_crossrg(self, resource_group, kv_resource_group):
        plan_name = self.create_random_name(prefix='ssl-test-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-ssl-test', length=20)
        kv_name = self.create_random_name(prefix='kv-ssl-test', length=20)
        # Cert Generated using
        # https://docs.microsoft.com/azure/app-service-web/web-sites-configure-ssl-certificate#bkmk_ssopenssl
        pfx_file = os.path.join(TEST_DIR, 'server.pfx')
        cert_password = 'test'
        cert_thumbprint = '9E9735C45C792B03B3FFCCA614852B32EE71AD6B'
        cert_name = 'test-cert'
        # we configure tags here in a hope to capture a repro for https://github.com/Azure/azure-cli/issues/6929
        self.cmd(
            'appservice plan create -g {} -n {} --sku B1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        kv_id = self.cmd('keyvault create -g {} -n {}'.format(kv_resource_group, kv_name)).get_output_in_json()['id']
        self.cmd('keyvault set-policy -g {} --name {} --spn {} --secret-permissions get'.format(
            kv_resource_group, kv_name, 'Microsoft.Azure.WebSites'))
        self.cmd('keyvault certificate import --name {} --vault-name {} --file "{}" --password {}'.format(
            cert_name, kv_name, pfx_file, cert_password))

        self.cmd('webapp config ssl import --resource-group {} --name {}  --key-vault {} --key-vault-certificate-name {}'.format(resource_group, webapp_name, kv_id, cert_name), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint)
        ])

        self.cmd('webapp config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {}'.format(resource_group, webapp_name, cert_thumbprint, 'SNI'), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(
                webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(
                webapp_name), cert_thumbprint)
        ])


class WebappUndeleteTest(ScenarioTest):
    @unittest.skip("Flaky test")
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_deleted_list(self, resource_group):
        plan = self.create_random_name(prefix='delete-me-plan', length=24)
        webapp_name = self.create_random_name(
            prefix='delete-me-web', length=24)
        self.cmd(
            'appservice plan create -g {} -n {} --sku B1 --tags plan=plan1'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp deleted list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].deletedSiteName', webapp_name)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_deleted_restore_to_existing_site(self, resource_group):
        plan = self.create_random_name(prefix='delete-me-plan', length=24)
        webapp_1_name = self.create_random_name(prefix='delete-me-web', length=24)
        webapp_2_name = self.create_random_name(prefix='delete-me-web', length=24)

        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku B1 --tags plan=plan1')

        # create webapp_1 and webapp_2
        self.cmd(f'webapp create -g {resource_group} -n {webapp_1_name} --plan {plan}')
        self.cmd(f'webapp create -g {resource_group} -n {webapp_2_name} --plan {plan}')

        # delete webapp_1
        self.cmd(f'webapp delete -g {resource_group} -n {webapp_1_name}')

        # collect list of deleted webapps
        deleted_list = self.cmd(f'webapp deleted list -g {resource_group} -n {webapp_1_name}', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].deletedSiteName', webapp_1_name)
        ]).get_output_in_json()
        deleted_id = deleted_list[0]["id"]

        # restore deleted webapp to existing app i.e webapp_2
        self.cmd(f'webapp deleted restore -g {resource_group} -n {webapp_2_name} --deleted-id "{deleted_id}"')

        # list/get the restored webapp_2
        self.cmd(f'az webapp show --name {webapp_2_name} -g {resource_group}', checks=[
            JMESPathCheck('name', webapp_2_name)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_deleted_restore_to_non_existent_site(self, resource_group):
        plan = self.create_random_name(prefix='delete-me-plan', length=24)
        webapp_1_name = self.create_random_name(prefix='delete-me-web', length=24)
        placeholder_app = self.create_random_name(prefix='delete-me-web', length=24)
        webapp_2_name = self.create_random_name(prefix='delete-me-web', length=24)

        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku B1 --tags plan=plan1')

        # create webapp_1
        self.cmd(f'webapp create -g {resource_group} -n {webapp_1_name} --plan {plan}')
        # create a placeholder/dummy app to make the ASP not auto deleted when
        self.cmd(f'webapp create -g {resource_group} -n {placeholder_app} --plan {plan}')

        # delete webapp_1
        self.cmd(f'webapp delete -g {resource_group} -n {webapp_1_name}')

        # collect list of deleted webapps
        deleted_list = self.cmd(f'webapp deleted list -g {resource_group} -n {webapp_1_name}', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].deletedSiteName', webapp_1_name)
        ]).get_output_in_json()
        deleted_id = deleted_list[0]["id"]

        # restore deleted webapp to non existent app i.e webapp_2
        self.cmd(f'webapp deleted restore -g {resource_group} -n {webapp_2_name} --deleted-id "{deleted_id}" --target-app-svc-plan {plan}')

        # get the details of the newly created webapp i.e webapp_2
        self.cmd(f'az webapp show --name {webapp_2_name} -g {resource_group}', checks=[
            JMESPathCheck('name', webapp_2_name)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_deleted_restore_to_non_existent_site_fails_when_asp_argument_is_not_provided_or_does_not_exist(self, resource_group):
        plan = self.create_random_name(prefix='delete-me-plan', length=24)
        webapp_1_name = self.create_random_name(prefix='delete-me-web', length=24)
        webapp_2_name = self.create_random_name(prefix='delete-me-web', length=24)

        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku B1 --tags plan=plan1')

        # create webapp_1
        self.cmd(f'webapp create -g {resource_group} -n {webapp_1_name} --plan {plan}')

        # delete webapp_1
        self.cmd(f'webapp delete -g {resource_group} -n {webapp_1_name}')


        # collect list of deleted webapps
        deleted_list = self.cmd(f'webapp deleted list -g {resource_group} -n {webapp_1_name}', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].deletedSiteName', webapp_1_name)
        ]).get_output_in_json()
        deleted_id = deleted_list[0]["id"]

        # restore deleted webapp to non existent app i.e webapp_2 without ASP, raises ValidationError
        with self.assertRaises(ValidationError) as ctx:
             self.cmd(f'webapp deleted restore -g {resource_group} -n {webapp_2_name} --deleted-id "{deleted_id}"')

        # # restore deleted webapp to non existent app i.e webapp_2 with non existent ASP, raises ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.cmd(f'webapp deleted restore -g {resource_group} -n {webapp_2_name} --deleted-id "{deleted_id}" --target-app-svc-plan idontexistplan')



class WebappAuthenticationTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_authentication', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_authentication(self, resource_group):
        webapp_name = self.create_random_name('webapp-authentication-test', 40)
        plan_name = self.create_random_name('webapp-authentication-plan', 40)
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        # testing show command for newly created app and initial fields
        self.cmd('webapp auth show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('unauthenticatedClientAction', None),
            JMESPathCheck('defaultProvider', None),
            JMESPathCheck('enabled', False),
            JMESPathCheck('tokenStoreEnabled', None),
            JMESPathCheck('allowedExternalRedirectUrls', None),
            JMESPathCheck('tokenRefreshExtensionHours', None),
            JMESPathCheck('runtimeVersion', None),
            JMESPathCheck('clientId', None),
            JMESPathCheck('clientSecret', None),
            JMESPathCheck('clientSecretCertificateThumbprint', None),
            JMESPathCheck('allowedAudiences', None),
            JMESPathCheck('issuer', None),
            JMESPathCheck('facebookAppId', None),
            JMESPathCheck('facebookAppSecret', None),
            JMESPathCheck('facebookOauthScopes', None)
        ])

        # update and verify
        result = self.cmd('webapp auth update -g {} -n {} --enabled true --action LoginWithFacebook '
                          '--token-store false --token-refresh-extension-hours 7.2 --runtime-version 1.2.8 '
                          '--aad-client-id aad_client_id --aad-client-secret aad_secret --aad-client-secret-certificate-thumbprint aad_thumbprint '
                          '--aad-allowed-token-audiences https://audience1 --aad-token-issuer-url https://issuer_url '
                          '--facebook-app-id facebook_id --facebook-app-secret facebook_secret '
                          '--facebook-oauth-scopes public_profile email'
                          .format(resource_group, webapp_name)).assert_with_checks([
                              JMESPathCheck(
                                  'unauthenticatedClientAction', 'RedirectToLoginPage'),
                              JMESPathCheck('defaultProvider', 'Facebook'),
                              JMESPathCheck('enabled', True),
                              JMESPathCheck('tokenStoreEnabled', False),
                              JMESPathCheck('tokenRefreshExtensionHours', 7.2),
                              JMESPathCheck('runtimeVersion', '1.2.8'),
                              JMESPathCheck('clientId', 'aad_client_id'),
                              JMESPathCheck('clientSecret', 'aad_secret'),
                              JMESPathCheck('clientSecretCertificateThumbprint', 'aad_thumbprint'),
                              JMESPathCheck('issuer', 'https://issuer_url'),
                              JMESPathCheck('facebookAppId', 'facebook_id'),
                              JMESPathCheck('facebookAppSecret', 'facebook_secret')]).get_output_in_json()

        self.assertIn('https://audience1', result['allowedAudiences'])


class WebappUpdateTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_update(self, resource_group):
        webapp_name = self.create_random_name('webapp-update-test', 40)
        plan_name = self.create_random_name('webapp-update-plan', 40)
        self.cmd('appservice plan create -g {} -n {} --sku S1'
                 .format(resource_group, plan_name))

        self.cmd('webapp create -g {} -n {} --plan {}'
                 .format(resource_group, webapp_name, plan_name)).assert_with_checks([
                     JMESPathCheck('clientAffinityEnabled', True)])
        # testing update command with --set
        self.cmd('webapp update -g {} -n {} --client-affinity-enabled false --set tags.foo=bar'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck('name', webapp_name),
                     JMESPathCheck('tags.foo', 'bar'),
                     JMESPathCheck('clientAffinityEnabled', False)])

        # try out on slots
        self.cmd(
            'webapp deployment slot create -g {} -n {} -s s1'.format(resource_group, webapp_name))
        self.cmd('webapp update -g {} -n {} -s s1 --client-affinity-enabled true'.format(resource_group, webapp_name), checks=[
            self.check('clientAffinityEnabled', True)
        ])


class WebappZipDeployScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_zipDeploy', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_deploy_zip(self, resource_group):
        webapp_name = self.create_random_name('webapp-zipDeploy-test', 40)
        plan_name = self.create_random_name('webapp-zipDeploy-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'test.zip')
        self.cmd(
            f'appservice plan create -g {resource_group} -n {plan_name} --sku S1 -l eastus')
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        self.cmd('webapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, webapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'ZipDeploy'),
            JMESPathCheck('message', 'Created via a push deployment'),
            JMESPathCheck('complete', True)
        ])


class WebappImplictIdentityTest(ScenarioTest):
    @unittest.skip("Flaky test")
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    @unittest.skip("Temp skip")
    def test_webapp_assign_system_identity(self, resource_group):
        scope = '/subscriptions/{}/resourcegroups/{}'.format(
            self.get_subscription_id(), resource_group)
        role = 'Reader'
        plan_name = self.create_random_name('web-msi-plan', 20)
        webapp_name = self.create_random_name('web-msi', 20)
        self.cmd(
            'appservice plan create -g {} -n {}'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            result = self.cmd('webapp identity assign -g {} -n {} --role {} --scope {}'.format(
                resource_group, webapp_name, role, scope)).get_output_in_json()
            self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
                self.check('principalId', result['principalId'])
            ])

        self.cmd('role assignment list -g {} --assignee {}'.format(resource_group, result['principalId']), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].roleDefinitionName', role)
        ])
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group,
                                                           webapp_name), checks=self.check('principalId', result['principalId']))
        self.cmd(
            'webapp identity remove -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group,
                                                           webapp_name), checks=self.is_empty())

    @unittest.skip("Known issue https://github.com/Azure/azure-cli/issues/17296")
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=24)
    def test_webapp_assign_user_identity(self, resource_group):
        plan_name = self.create_random_name('web-msi-plan', 20)
        webapp_name = self.create_random_name('web-msi', 20)
        identity_name = self.create_random_name('id1', 8)

        msi_result = self.cmd('identity create -g {} -n {}'.format(resource_group, identity_name), checks=[
            self.check('name', identity_name)]).get_output_in_json()
        self.cmd(
            'appservice plan create -g {} -n {}'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        self.cmd('webapp identity assign -g {} -n {}'.format(resource_group, webapp_name))
        result = self.cmd('webapp identity assign -g {} -n {} --identities {}'.format(
            resource_group, webapp_name, msi_result['id'])).get_output_in_json()
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            self.check('principalId', result['principalId']),
            self.check('userAssignedIdentities."{}".clientId'.format(msi_result['id']), msi_result['clientId']),
        ])

        self.cmd('webapp identity remove -g {} -n {} --identities {}'.format(
            resource_group, webapp_name, msi_result['id']))
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            self.check('principalId', result['principalId']),
            self.check('userAssignedIdentities', None),
        ])

    @unittest.skip("Known issue https://github.com/Azure/azure-cli/issues/17296")
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=24)
    def test_webapp_remove_identity(self, resource_group):
        plan_name = self.create_random_name('web-msi-plan', 20)
        webapp_name = self.create_random_name('web-msi', 20)
        identity_name = self.create_random_name('id1', 8)
        identity2_name = self.create_random_name('id1', 8)

        msi_result = self.cmd('identity create -g {} -n {}'.format(resource_group, identity_name), checks=[
            self.check('name', identity_name)]).get_output_in_json()
        msi2_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity2_name)).get_output_in_json()
        self.cmd(
            'appservice plan create -g {} -n {}'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        self.cmd('webapp identity assign -g {} -n {} --identities [system] {} {}'.format(
            resource_group, webapp_name, msi_result['id'], msi2_result['id']))

        result = self.cmd('webapp identity remove -g {} -n {} --identities {}'.format(
            resource_group, webapp_name, msi2_result['id'])).get_output_in_json()
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            self.check('principalId', result['principalId']),
            self.check('userAssignedIdentities."{}".clientId'.format(msi_result['id']), msi_result['clientId']),
        ])

        self.cmd('webapp identity remove -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            self.check('principalId', None),
            self.check('userAssignedIdentities."{}".clientId'.format(msi_result['id']), msi_result['clientId']),
        ])

        self.cmd('webapp identity remove -g {} -n {} --identities [system] {}'.format(
            resource_group, webapp_name, msi_result['id']))
        self.cmd('webapp identity show -g {} -n {}'.format(
            resource_group, webapp_name), checks=self.is_empty())


class WebappListLocationsTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_list-locations-free-sku-test')
    def test_webapp_list_locations_free_sku(self, resource_group):
        asp_F1 = self.cmd(
            'appservice list-locations --sku F1').get_output_in_json()
        result = self.cmd(
            'appservice list-locations --sku Free').get_output_in_json()
        self.assertEqual(asp_F1, result)

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_list-locations-hyperv-workers-enabled-test')
    def test_webapp_list_locations_hyperv_workers_enabled(self, resource_group):
        self.cmd('appservice list-locations --sku P1V3 --hyperv-workers-enabled', checks = [
            JMESPathCheck('length(@) > `0`', True)
        ])        
        self.cmd('appservice list-locations --sku P1MV3 --hyperv-workers-enabled', checks = [
            JMESPathCheck('length(@) > `0`', True)
        ])


class ContainerWebappE2ETest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test', location='australiaeast')
    def test_container_webapp_long_server_url(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-container-e2e', length=24)
        plan = self.create_random_name(prefix='webapp-hyperv-plan', length=24)
        self.cmd('appservice plan create --hyper-v -n {} -g {} --sku p1v3 -l australiaeast'.format(plan, resource_group))
        container = "mcr.microsoft.com/azure-app-service/windows/parkingpage:latest"
        self.cmd('webapp create -n {} -g {} -p {} -i {}'.format(webapp_name, resource_group, plan, container), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test', location='australiaeast')
    def test_container_webapp_docker_image_name(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-container', length=24)
        plan = self.create_random_name(prefix='webapp-plan', length=24)
        self.cmd('appservice plan create --is-linux -n {} -g {} -l australiaeast'.format(plan, resource_group))
        container = "nginx"
        self.cmd('webapp create -n {} -g {} -p {} -i {}'.format(webapp_name, resource_group, plan, container), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])


@unittest.skip("Known issue with creating windows containers")
class WebappWindowsContainerBasicE2ETest(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='webapp_hyperv_e2e', location='westus2')
    def test_webapp_hyperv_e2e(self, resource_group):
        webapp_name = self.create_random_name(
            prefix='webapp-hyperv-e2e', length=24)
        plan = self.create_random_name(prefix='webapp-hyperv-plan', length=24)

        self.cmd('appservice plan create -g {} -n {} --hyper-v --sku P1V3'.format(resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'PremiumV3'),
            JMESPathCheck('[0].sku.name', 'P1v3')
        ])
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck("length([?name=='{}' && resourceGroup=='{}'])".format(
                plan, resource_group), 1)
        ])
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('name', plan)
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-container-image-name "DOCKER|microsoft/iis:windowsservercore-ltsc2022"'
                 .format(resource_group, webapp_name, plan), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name +
                          '.azurewebsites.net')
        ])
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('windowsFxVersion',
                          "DOCKER|microsoft/iis"),
            JMESPathCheck('linuxFxVersion', "")
        ])
        self.cmd('webapp config set -g {} -n {} --windows-fx-version "DOCKER|microsoft/iis"'.format(
            resource_group, webapp_name))
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('windowsFxVersion', "DOCKER|microsoft/iis"),
            JMESPathCheck('linuxFxVersion', "")
        ])

    # Always on is not supported on all SKUs this is to test that we don't fail create trying to enable AlwaysOn
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_alwaysOn', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_create_noAlwaysOn(self, resource_group):
        webapp_name = self.create_random_name('webapp-create-alwaysOn-e2e', 44)
        plan = self.create_random_name('plan-create-alwaysOn-e2e', 44)

        self.cmd(
            'appservice plan create -g {} -n {} --sku SHARED'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        # verify alwaysOn
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('alwaysOn', False)])

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_linux_free', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_create_linux_free(self, resource_group):
        webapp_name = self.create_random_name('webapp-linux-free', 24)
        plan = self.create_random_name('plan-linux-free', 24)

        self.cmd('appservice plan create -g {} -n {} --sku F1 --is-linux'.format(resource_group, plan), checks=[
            # this weird field means it is a linux
            JMESPathCheck('reserved', True),
            JMESPathCheck('sku.tier', 'LinuxFree')])
        self.cmd('webapp create -g {} -n {} --plan {} -u {} -r "NODE|16-lts"'.format(resource_group, webapp_name, plan,
                                                                                    TEST_REPO_URL))
        # verify alwaysOn
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('alwaysOn', False)])

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='rg', random_name_length=6)
    def test_webapp_create_with_msi(self, resource_group):
        scope = '/subscriptions/{}/resourcegroups/{}'.format(
            self.get_subscription_id(), resource_group)
        role = 'Reader'
        webapp_name = self.create_random_name('webapp-with-msi', 26)
        plan = self.create_random_name('plan-create-with-msi', 26)
        identity_name = self.create_random_name('app-create', 16)

        msi_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            result = self.cmd('webapp create -g {} -n {} --plan {} --assign-identity [system] {} --role {} --scope {}'.format(
                resource_group, webapp_name, plan, msi_result['id'], role, scope)).get_output_in_json()

        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            self.check('principalId', result['identity']['principalId']),
            self.check('userAssignedIdentities."{}".clientId'.format(msi_result['id']), msi_result['clientId']),
        ])
        self.cmd('role assignment list -g {} --assignee {}'.format(resource_group, result['identity']['principalId']), checks=[
            self.check('length([])', 1),
            self.check('[0].roleDefinitionName', role)
        ])


class WebappNetworkConnectionTests(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_hybridconnectionE2E(self, resource_group):
        webapp_name = self.create_random_name('hcwebapp', 24)
        plan = self.create_random_name('hcplan', 24)
        namespace_name = self.create_random_name('hcnamespace', 24)
        hyco_name = self.create_random_name('hcname', 24)
        um = "[{{\\\"key\\\":\\\"endpoint\\\",\\\"value\\\":\\\"vmsq1:80\\\"}}]"
        slot = "stage"
        slot_webapp_name = "{}-{}".format(webapp_name, slot)

        self.cmd(
            'appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd(
            'relay namespace create -g {} --name {}'.format(resource_group, namespace_name))
        self.cmd('relay hyco create -g {} --namespace-name {} --name {} --user-metadata {}'.format(
            resource_group, namespace_name, hyco_name, um))
        self.cmd('webapp hybrid-connection add -g {} -n {} --namespace {} --hybrid-connection {}'.format(
            resource_group, webapp_name, namespace_name, hyco_name))
        self.cmd('webapp hybrid-connection list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', hyco_name)
        ])

        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(
            resource_group, webapp_name, slot_webapp_name))
        self.cmd('webapp hybrid-connection add -g {} -n {} --namespace {} --hybrid-connection {} --slot {}'.format(
            resource_group, webapp_name, namespace_name, hyco_name, slot_webapp_name))
        self.cmd('webapp hybrid-connection list -g {} -n {} --slot {}'.format(resource_group, webapp_name, slot_webapp_name), checks=[
            JMESPathCheck('length(@)', 1)
        ])
        self.cmd('webapp hybrid-connection remove -g {} -n {} --namespace {} --hybrid-connection {}'.format(
            resource_group, webapp_name, namespace_name, hyco_name))
        self.cmd('webapp hybrid-connection list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])
        self.cmd('webapp hybrid-connection remove -g {} -n {} --namespace {} --hybrid-connection {} --slot {}'.format(
            resource_group, webapp_name, namespace_name, hyco_name, slot_webapp_name))
        self.cmd(
            'webapp hybrid-connection list -g {} -n {} --slot {}'.format(resource_group, webapp_name, slot_webapp_name),
            checks=[
                JMESPathCheck('length(@)', 0)
            ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_vnetE2E(self, resource_group):
        webapp_name = self.create_random_name('swiftwebapp', 24)
        plan = self.create_random_name('swiftplan', 24)
        subnet_name = self.create_random_name('swiftsubnet', 24)
        vnet_name = self.create_random_name('swiftname', 24)
        slot = "stage"
        slot_webapp_name = "{}-{}".format(webapp_name, slot)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, webapp_name, vnet_name, subnet_name))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(
            resource_group, webapp_name, slot_webapp_name))
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {} --slot {}'.format(
            resource_group, webapp_name, vnet_name, subnet_name, slot_webapp_name))
        self.cmd('webapp vnet-integration list -g {} -n {} --slot {}'.format(resource_group, webapp_name, slot_webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {} --slot {}'.format(resource_group, webapp_name, slot_webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {} --slot {}'.format(resource_group, webapp_name, slot_webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_create_vnetE2E(self, resource_group):
        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {} --subnet {}'.format(resource_group,
                                                                               webapp_name, plan, vnet_name,
                                                                               subnet_name))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, parameter_name="webapp_rg")
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, parameter_name="vnet_rg")
    def test_webapp_create_with_vnet_by_subnet_rid(self, webapp_rg, vnet_rg):
        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        subnet_id = self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            vnet_rg, vnet_name, subnet_name)).get_output_in_json()["newVNet"]["subnets"][0]["id"]
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(webapp_rg, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --subnet {}'.format(webapp_rg, webapp_name, plan, subnet_id))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(webapp_rg, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(webapp_rg, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(webapp_rg, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, parameter_name="webapp_rg")
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, parameter_name="vnet_rg")
    def test_webapp_create_with_vnet_by_vnet_rid(self, webapp_rg, vnet_rg):
        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        vnet_id = self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            vnet_rg, vnet_name, subnet_name)).get_output_in_json()["newVNet"]["id"]
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(webapp_rg, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {} --subnet {}'.format(webapp_rg, webapp_name, plan, vnet_id, subnet_name))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(webapp_rg, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(webapp_rg, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(webapp_rg, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_create_with_vnet_wrong_sku(self, resource_group):
        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku FREE'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {} --subnet {}'.format(resource_group,
                                                                               webapp_name, plan, vnet_name,
                                                                               subnet_name), expect_failure=True)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, parameter_name="webapp_rg")
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP, parameter_name="vnet_rg")
    def test_webapp_create_with_vnet_wrong_location(self, webapp_rg, vnet_rg):
        self.assertNotEqual(WINDOWS_ASP_LOCATION_WEBAPP, LINUX_ASP_LOCATION_WEBAPP)

        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        vnet_id = self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            vnet_rg, vnet_name, subnet_name)).get_output_in_json()["newVNet"]["id"]
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(webapp_rg, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {} --subnet {}'.format(webapp_rg, webapp_name, plan, vnet_id, subnet_name), expect_failure=True)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_create_with_vnet_no_vnet(self, resource_group):
        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {} --subnet {}'.format(resource_group,
                                                                               webapp_name, plan, vnet_name,
                                                                               subnet_name), expect_failure=True)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP, parameter_name="webapp_rg")
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP, parameter_name="vnet_rg")
    def test_webapp_create_with_vnet_wrong_rg(self, webapp_rg, vnet_rg):
        self.assertNotEqual(WINDOWS_ASP_LOCATION_WEBAPP, LINUX_ASP_LOCATION_WEBAPP)

        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            vnet_rg, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(webapp_rg, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {} --subnet {}'.format(webapp_rg,
                                                                               webapp_name, plan, vnet_name,
                                                                               subnet_name), expect_failure=True)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_create_with_vnet_no_subnet(self, resource_group):
        webapp_name = self.create_random_name('vnetwebapp', 24)
        plan = self.create_random_name('vnetplan', 24)
        subnet_name = self.create_random_name('subnet', 24)
        vnet_name = self.create_random_name('vnet', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} --vnet {}'.format(resource_group,
                                                                               webapp_name, plan, vnet_name,
                                                                               subnet_name), expect_failure=True)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_vnetDelegation(self, resource_group):
        webapp_name = self.create_random_name('swiftwebapp', 24)
        plan = self.create_random_name('swiftplan', 24)
        subnet_name = self.create_random_name('swiftsubnet', 24)
        vnet_name = self.create_random_name('swiftname', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd('network vnet subnet update -g {} --vnet {} --name {} --delegations Microsoft.Web/serverfarms --service-endpoints Microsoft.Storage'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, webapp_name, vnet_name, subnet_name))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(' network vnet subnet show -g {} -n {} --vnet-name {}'.format(resource_group, subnet_name, vnet_name), checks=[
            JMESPathCheck('serviceEndpoints[0].service', "Microsoft.Storage")
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_vnetSameName(self, resource_group):
        resource_group_2 = self.create_random_name('swiftwebapp', 24)
        webapp_name = self.create_random_name('swiftwebapp', 24)
        plan = self.create_random_name('swiftplan', 24)
        subnet_name = self.create_random_name('swiftsubnet', 24)
        subnet_name_2 = self.create_random_name('swiftsubnet', 24)
        vnet_name = self.create_random_name('swiftname', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        self.cmd('group create -n {} -l {}'.format(resource_group_2, WINDOWS_ASP_LOCATION_WEBAPP))
        vnet = self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group_2, vnet_name, subnet_name_2)).get_output_in_json()
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))

        # Add vnet integration where theres two vnets of the same name. Chosen vnet should default to the one in the same RG
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, webapp_name, vnet_name, subnet_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

        # Add vnet integration using vnet resource ID
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, webapp_name, vnet['newVNet']['id'], subnet_name_2))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name_2)
        ])
        # self.cmd(
        #     'webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        # time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        # self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
        #     JMESPathCheck('length(@)', 0)
        # ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_vnetSubnetId(self, resource_group):
        webapp_name = self.create_random_name('swiftwebapp', 24)
        plan = self.create_random_name('swiftplan', 24)
        subnet_name = self.create_random_name('swiftsubnet', 24)
        vnet_name = self.create_random_name('swiftname', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        subnet = self.cmd('network vnet subnet update -g {} --vnet {} --name {} --delegations Microsoft.Web/serverfarms'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        self.cmd(
            'appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, webapp_name, vnet_name, subnet['id']))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd(
            'webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_vnetRouteAll(self, resource_group):
        webapp_name = self.create_random_name('swiftwebapp', 24)
        plan = self.create_random_name('swiftplan', 24)
        subnet_name = self.create_random_name('swiftsubnet', 24)
        vnet_name = self.create_random_name('swiftname', 24)

        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16 --subnet-name {} --subnet-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name))
        subnet = self.cmd('network vnet subnet update -g {} --vnet {} --name {} --delegations Microsoft.Web/serverfarms'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        self.cmd('appservice plan create -g {} -n {} --sku P1V2'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp vnet-integration add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, webapp_name, vnet_name, subnet['id']))
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', subnet_name)
        ])
        self.cmd('webapp vnet-integration remove -g {} -n {}'.format(resource_group, webapp_name))
        time.sleep(TIME_SLEEP_FOR_VNET_INTEGRATION)
        self.cmd('webapp vnet-integration list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

class WebappDeploymentLogsScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_show_deployment_logs(self, resource_group):
        webapp_name = self.create_random_name('show-deployment-webapp', 40)
        plan_name = self.create_random_name('show-deployment-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'test.zip')

        self.cmd(f'appservice plan create -g {resource_group} -n {plan_name} --sku S1 -l eastus')
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        self.cmd('webapp log deployment show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

        deployment_1 = self.cmd('webapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, webapp_name, zip_file)).get_output_in_json()
        self.cmd('webapp log deployment show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@) > `0`', True),
        ])

        self.cmd('webapp log deployment show -g {} -n {} --deployment-id={}'.format(resource_group, webapp_name, deployment_1['id']), checks=[
            JMESPathCheck('length(@) > `0`', True),
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_list_deployment_logs(self, resource_group):
        webapp_name = self.create_random_name('list-deployment-webapp', 40)
        plan_name = self.create_random_name('list-deployment-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'test.zip')

        self.cmd(f'appservice plan create -g {resource_group} -n {plan_name} --sku S1 -l eastus')
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        self.cmd('webapp log deployment list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

        deployment_1 = self.cmd('webapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, webapp_name, zip_file)).get_output_in_json()
        self.cmd('webapp log deployment list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].id', deployment_1['id']),
        ])

        self.cmd('webapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, webapp_name, zip_file)).get_output_in_json()
        self.cmd('webapp log deployment list -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('length(@)', 2)
        ])


class WebappLocalContextScenarioTest(LocalContextScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_local_context(self, resource_group):
        from knack.util import CLIError
        self.kwargs.update({
            'plan_name': self.create_random_name(prefix='webapp-plan-', length=24),
            'webapp_name': self.create_random_name(prefix='webapp-', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('appservice plan show')
        with self.assertRaises(CLIError):
            self.cmd('appservice plan delete')

        self.cmd('webapp create -n {webapp_name}')
        self.cmd('webapp show')
        with self.assertRaises(CLIError):
            self.cmd('webapp delete')

        self.cmd('webapp delete -n {webapp_name}')
        self.cmd('appservice plan delete -n {plan_name} -y')


class WebappOneDeployScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_OneDeploy', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_one_deploy_scm(self, resource_group):
        webapp_name = self.create_random_name('webapp-oneDeploy-test', 40)
        plan_name = self.create_random_name('webapp-oneDeploy-plan', 40)
        war_file = os.path.join(TEST_DIR, 'data', 'sample.war')
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {} -r "TOMCAT|9.0-java11"'.format(resource_group, webapp_name, plan_name))
        self.cmd('webapp deploy -g {} --n {} --src-path "{}" --type war --async true'.format(resource_group, webapp_name, war_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'OneDeploy'),
            JMESPathCheck('message', 'OneDeploy'),
            JMESPathCheck('complete', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_OneDeploy', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_one_deploy_arm(self, resource_group):
        webapp_name = self.create_random_name('webapp-oneDeploy-test', 40)
        plan_name = self.create_random_name('webapp-oneDeploy-plan', 40)
        war_url = "https://tomcat.apache.org/tomcat-7.0-doc/appdev/sample/sample.war"
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {} -r "TOMCAT|9.0-java11"'.format(resource_group, webapp_name, plan_name))
        
        self.cmd(f'webapp deploy -g {resource_group} -n {webapp_name} --src-url {war_url} --type war').assert_with_checks([
            JMESPathCheck('deployer', 'OneDeploy'),
            JMESPathCheck('message', 'OneDeploy'),
        ])


class TrackRuntimeStatusTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_deploy_runtimestatus', location='eastus')
    def test_webapp_track_runtimestatus_runtimesucessful(self, resource_group):
        webapp_name = self.create_random_name('webapp-runtimestatus-test', 40)
        plan_name = self.create_random_name('webapp-runtimestatus-plan', 40)
        war_file = os.path.join(TEST_DIR, 'data', 'sample.war')
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {} -r "TOMCAT|9.0-java11"'.format(resource_group, webapp_name, plan_name))
        self.cmd('webapp deploy -g {} --n {} --src-path "{}" --type war --async --track-status'.format(resource_group, webapp_name, war_file)).assert_with_checks([
            JMESPathCheck('resourceGroup', resource_group),
            JMESPathCheck('properties.errors', None),
            JMESPathCheck('properties.numberOfInstancesFailed', '0'),
            JMESPathCheck('properties.numberOfInstancesInProgress', '0'),
            JMESPathCheck('properties.numberOfInstancesSuccessful', '1'),
            JMESPathCheck('properties.status', 'RuntimeSuccessful'),
            JMESPathCheck('type', 'Microsoft.Web/sites/deploymentStatus'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_deploy_runtimestatus', location='eastus')
    def test_webapp_track_runtimestatus_buildfailed(self, resource_group):
        webapp_name = self.create_random_name('webapp-runtimestatus-test', 40)
        plan_name = self.create_random_name('webapp-runtimestatus-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'data', 'nodebuildfailed.zip')
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {} -r "NODE|20-LTS"'.format(resource_group, webapp_name, plan_name))
        with self.assertRaisesRegexp(CLIError, "Deployment failed because the build process failed"):
            self.cmd('webapp deploy -g {} --n {} --src-path "{}" --type zip --async --track-status'.format(resource_group, webapp_name, zip_file))

    @ResourceGroupPreparer(name_prefix='cli_test_webapp_deploy_runtimestatus', location='eastus')
    def test_webapp_track_runtimestatus_runtimefailed(self, resource_group):
        webapp_name = self.create_random_name('webapp-runtimestatus-test', 40)
        plan_name = self.create_random_name('webapp-runtimestatus-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'data', 'noderuntimefailed.zip')
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan_name))
        self.cmd(
            'webapp create -g {} -n {} --plan {} -r "NODE|20-LTS"'.format(resource_group, webapp_name, plan_name))
        with self.assertRaisesRegexp(CLIError, "Deployment failed because the site failed to start within 10 mins."):
            self.cmd('webapp deploy -g {} --n {} --src-path "{}" --type zip --async --track-status'.format(resource_group, webapp_name, zip_file))

class DomainScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_domain_create(self, resource_group):
        contacts = os.path.join(TEST_DIR, 'domain-contact.json')
        self.cmd("appservice domain create -g {} --hostname {} --contact-info=@\'{}\' --dryrun".format(
            resource_group, "testuniquedomainname1.com", contacts)
        ).assert_with_checks([
            JMESPathCheck('agreement_keys', "['DNRA', 'DNPA']")
        ])


class TunnelProxyTest(unittest.TestCase):
    def setUp(self):
        # Clean pre-existing proxy env vars
        for env_var in [
            'NO_PROXY',
            'no_proxy',
            'HTTPS_PROXY',
            'https_proxy',
            'AZURE_CLI_DISABLE_CONNECTION_VERIFICATION',
            'REQUESTS_CA_BUNDLE',
        ]:
            if env_var in os.environ:
                del os.environ[env_var]
        os.environ['HTTPS_PROXY'] = 'http://myproxy.local:8888'

    def test_with_proxy(self):
        http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertEqual(http.proxy.netloc, 'myproxy.local:8888')
        with self.assertRaises(KeyError):
            http.proxy_headers['proxy-authorization']
        self.assertEqual(http.connection_pool_kw['cert_reqs'], 'CERT_REQUIRED')
        self.assertIsInstance(http, urllib3.ProxyManager)

    def test_without_proxy(self):
        del os.environ['HTTPS_PROXY']
        http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertIsNone(http.proxy)
        self.assertIsInstance(http, urllib3.PoolManager)
        self.assertNotIsInstance(http, urllib3.ProxyManager)

    def test_no_proxy(self):
        os.environ['NO_PROXY'] = 'azurewebsites.net'
        http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertIsNone(http.proxy)
        self.assertIsInstance(http, urllib3.PoolManager)
        self.assertNotIsInstance(http, urllib3.ProxyManager)

    def test_proxy_auth(self):
        os.environ['HTTPS_PROXY'] = 'http://test_user:secret_p@ss@myproxy.local:8888'
        http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertEqual(
            http.proxy_headers['proxy-authorization'],
            'Basic dGVzdF91c2VyOnNlY3JldF9wQHNz',
        )

    def test_proxy_custom_ca_bundle(self):
        with tempfile.TemporaryFile() as file:
            file = tempfile.NamedTemporaryFile(suffix='-ca-certificates.crt')
            os.environ['REQUESTS_CA_BUNDLE'] = file.name
            http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertEqual(http.connection_pool_kw['ca_certs'], file.name)

    def test_proxy_custom_ca_bundle_incorrect(self):
        with tempfile.TemporaryDirectory() as empty_folder:
            os.environ['REQUESTS_CA_BUNDLE'] = f'{empty_folder}/ca-certificates.crt'

            self.assertRaises(CLIError, get_pool_manager, 'https://scm.azurewebsites.net')

    def test_proxy_default_ca_bundle(self):
        http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertEqual(http.connection_pool_kw['ca_certs'], certifi.where())

    def test_proxy_unsafe_ssl(self):
        os.environ['AZURE_CLI_DISABLE_CONNECTION_VERIFICATION'] = '1'
        http = get_pool_manager('https://scm.azurewebsites.net')

        self.assertEqual(http.connection_pool_kw['cert_reqs'], 'CERT_NONE')


class WebappSlotTest(ScenarioTest):
    @live_only()  # Uses storage account keys, so must be live_only to not fail credscan
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_slot_create_from_configuration_source(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-e2e', length=24)
        plan = self.create_random_name(prefix='webapp-e2e-plan', length=24)
        storage_account = self.create_random_name(prefix='storage', length=24)
        container = self.create_random_name(prefix='container', length=24)
        store_id = "store"
        store_type = "AzureBlob"

        self.cmd(f'appservice plan create -g {resource_group} -n {plan} --sku S1 --is-linux')
        self.cmd(f'webapp create -g {resource_group} -n {webapp_name} --plan {plan} --runtime "python|3.9"')
        self.cmd(f'storage account create -n {storage_account} -g {resource_group} --location {LINUX_ASP_LOCATION_WEBAPP}')
        self.cmd(f"storage container create -n {container} -g {resource_group} --account-name {storage_account}")
        key = self.cmd(f"storage account keys list -n {storage_account}").get_output_in_json()[0]["value"]
        self.cmd(f'webapp config storage-account add -g {resource_group} -n {webapp_name} -k {key} -a {storage_account} -i {store_id} --sn {container} -t {store_type}')

        self.cmd(f'webapp deployment slot create -g {resource_group} -n {webapp_name} -s "slot" --configuration-source {webapp_name}')

        self.cmd(f'webapp show -g {resource_group} -n {webapp_name} -s "slot"', checks=[
            JMESPathCheck(f"siteConfig.azureStorageAccounts.{store_id}.accessKey", None),
            JMESPathCheck(f"siteConfig.azureStorageAccounts.{store_id}.accountName", storage_account),
            JMESPathCheck(f"siteConfig.azureStorageAccounts.{store_id}.state", "Ok"),
            JMESPathCheck(f"siteConfig.azureStorageAccounts.{store_id}.type", store_type),
        ])


if __name__ == '__main__':
    unittest.main()
