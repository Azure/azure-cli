# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock
import uuid
import os
import time
import tempfile
import requests

from azure_devtools.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk import (ScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               StorageAccountPreparer, JMESPathCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long


class WebappBasicE2ETest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_e2e(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-e2e', length=24)
        plan = self.create_random_name(prefix='webapp-e2e-plan', length=24)

        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1')
        ])
        self.cmd('appservice plan list', checks=[
            JMESPathCheck("length([?name=='{}' && resourceGroup=='{}'])".format(plan, resource_group), 1)
        ])
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('name', plan)
        ])
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        result = self.cmd('webapp deployment source config-local-git -g {} -n {}'.format(resource_group, webapp_name)).get_output_in_json()
        self.assertTrue(result['url'].endswith(webapp_name + '.git'))
        self.cmd('webapp deployment source show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('repoUrl', 'https://{}.scm.azurewebsites.net'.format(webapp_name))
        ])
        # turn on diagnostics
        test_cmd = ('webapp log config -g {} -n {} --level verbose'.format(resource_group, webapp_name) + ' '
                    '--application-logging true --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem')
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
            # TODO: contact webapp team for where to retrieve 'level'
        ])
        # show publish profile info
        result = self.cmd('webapp deployment list-publishing-profiles -g {} -n {}'.format(resource_group, webapp_name)).get_output_in_json()
        self.assertTrue(result[1]['publishUrl'].startswith('ftp://'))
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


class WebappQuickCreateTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_win_webapp_quick_create(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        r = self.cmd('webapp create -g {} -n {} --plan {} --deployment-local-git'.format(resource_group, webapp_name, plan)).get_output_in_json()
        self.assertTrue(r['ftpPublishingUrl'].startswith('ftp://'))
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name, checks=[
            JMESPathCheck('[0].name', 'WEBSITE_NODE_DEFAULT_VERSION'),
            JMESPathCheck('[0].value', '6.9.1'),
        ]))

    @ResourceGroupPreparer()
    def test_win_webapp_quick_create_runtime(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        r = self.cmd('webapp create -g {} -n {} --plan {} --deployment-local-git -r "node|6.12"'.format(resource_group, webapp_name, plan)).get_output_in_json()
        self.assertTrue(r['ftpPublishingUrl'].startswith('ftp://'))
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name, checks=[
            JMESPathCheck('[0].name', 'WEBSITE_NODE_DEFAULT_VERSION'),
            JMESPathCheck('[0].value', '6.12.0'),
        ]))

    @ResourceGroupPreparer()
    def test_win_webapp_quick_create_cd(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick-cd', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-source-url https://github.com/yugangw-msft/azure-site-test.git -r "node|6.12"'.format(resource_group, webapp_name, plan))
        time.sleep(30)  # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name))
        # verify the web page
        self.assertTrue('Hello world' in str(r.content))

    @ResourceGroupPreparer(location='japaneast')
    def test_linux_webapp_quick_create(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick-linux', length=24)
        plan = self.create_random_name(prefix='plan-quick-linux', length=24)

        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -i patle/ruby-hello'.format(resource_group, webapp_name, plan))
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        # verify the web page
        self.assertTrue('Ruby on Rails in Web Apps on Linux' in str(r.content))
        # verify app settings
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name, checks=[
            JMESPathCheck('[0].name', 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'),
            JMESPathCheck('[0].value', 'false'),
        ]))

    @ResourceGroupPreparer()
    def test_linux_webapp_multicontainer_create(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-linux-multi', length=24)
        plan = self.create_random_name(prefix='plan-linux-multi', length=24)
        config_file = os.path.join(TEST_DIR, 'sample-compose.yml')

        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd("webapp create -g {} -n {} --plan {} --multicontainer-config-file \"{}\" "
                 "--multicontainer-config-type COMPOSE".format(resource_group, webapp_name, plan, config_file))

        last_number_seen = 99999999
        for x in range(0, 10):
            r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
            # verify the web page
            self.assertTrue('Hello World! I have been seen' in str(r.content))
            current_number = [int(s) for s in r.content.split() if s.isdigit()][0]
            self.assertNotEqual(current_number, last_number_seen)
            last_number_seen = current_number

    @ResourceGroupPreparer(location='japanwest')
    def test_linux_webapp_quick_create_cd(self, resource_group):
        webapp_name = 'webapp-quick-linux-cd'
        plan = 'plan-quick-linux-cd'
        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -u https://github.com/yugangw-msft/azure-site-test.git -r "node|6.11"'.format(resource_group, webapp_name, plan))
        time.sleep(30)  # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        # verify the web page
        if 'Hello world' not in str(r.content):
            # dump out more info for diagnose
            self.fail("'Hello world' is not found in the web page. We get instead:" + str(r.content))

    @ResourceGroupPreparer(parameter_name='resource_group', parameter_name_for_location='resource_group_location')
    @ResourceGroupPreparer(parameter_name='resource_group2', parameter_name_for_location='resource_group_location2')
    def test_create_in_different_group(self, resource_group, resource_group_location, resource_group2, resource_group_location2):
        plan = 'planInOneRG'
        self.cmd('group create -n {} -l {}'.format(resource_group2, resource_group_location))
        plan_id = self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('webapp create -g {} -n webInOtherRG --plan {}'.format(resource_group2, plan_id), checks=[
            JMESPathCheck('name', 'webInOtherRG')
        ])


# Test Framework is not able to handle binary file format, hence, only run live
class AppServiceLogTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_download_win_web_log(self, resource_group):
        import zipfile
        webapp_name = self.create_random_name(prefix='webapp-win-log', length=24)
        plan = self.create_random_name(prefix='win-log', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-source-url https://github.com/yugangw-msft/azure-site-test.git -r "node|6.12"'.format(resource_group, webapp_name, plan))
        time.sleep(30)  # 30 seconds should be enough for the deployment finished(Skipped under playback mode)

        # sanity check the traces
        _, log_file = tempfile.mkstemp()
        log_dir = log_file + '-dir'
        self.cmd('webapp log download -g {} -n {} --log-file "{}"'.format(resource_group, webapp_name, log_file))
        zip_ref = zipfile.ZipFile(log_file, 'r')
        zip_ref.extractall(log_dir)
        self.assertTrue(os.path.isdir(os.path.join(log_dir, 'LogFiles', 'kudu', 'trace')))

    @ResourceGroupPreparer()
    def test_download_linux_web_log(self, resource_group):
        import zipfile
        webapp_name = self.create_random_name(prefix='webapp-linux-log', length=24)
        plan = self.create_random_name(prefix='linux-log', length=24)
        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -i patle/ruby-hello'.format(resource_group, webapp_name, plan))
        # load the site to produce a few traces
        requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)

        # sanity check the traces
        _, log_file = tempfile.mkstemp()
        log_dir = log_file + '-dir'
        self.cmd('webapp log download -g {} -n {} --log-file "{}"'.format(resource_group, webapp_name, log_file))
        zip_ref = zipfile.ZipFile(log_file, 'r')
        zip_ref.extractall(log_dir)
        self.assertTrue(os.path.isdir(os.path.join(log_dir, 'LogFiles', 'kudu', 'trace')))


class AppServicePlanScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_retain_plan(self, resource_group):
        webapp_name = self.create_random_name('web', 24)
        plan = self.create_random_name('web-plan', 24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp delete -g {} -n {} --keep-dns-registration --keep-empty-plan --keep-metrics'.format(resource_group, webapp_name))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].name', plan)
        ])

    @ResourceGroupPreparer()
    def test_auto_delete_plan(self, resource_group):
        webapp_name = self.create_random_name('web-del-test', 24)
        plan = self.create_random_name('web-del-plan', 24)
        self.cmd('appservice plan create -g {} -n {} -l westus'.format(resource_group, plan))

        self.cmd('appservice plan update -g {} -n {} --sku S1'.format(resource_group, plan),
                 checks=[JMESPathCheck('name', plan),
                         JMESPathCheck('sku.tier', 'Standard'),
                         JMESPathCheck('sku.name', 'S1')])

        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))

        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))
        # test empty service plan should be automatically deleted.
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[JMESPathCheck('length(@)', 0)])


class WebappConfigureTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_config')
    def test_webapp_config(self, resource_group):
        webapp_name = self.create_random_name('webapp-config-test', 40)
        plan_name = self.create_random_name('webapp-config-plan', 40)

        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        # verify the baseline
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('alwaysOn', False),
            JMESPathCheck('autoHealEnabled', False),
            JMESPathCheck('phpVersion', '5.6'),
            JMESPathCheck('netFrameworkVersion', 'v4.0'),
            JMESPathCheck('pythonVersion', ''),
            JMESPathCheck('use32BitWorkerProcess', True),
            JMESPathCheck('webSocketsEnabled', False),
            JMESPathCheck('minTlsVersion', '1.2'),
            JMESPathCheck('ftpsState', 'AllAllowed')])

        # update and verify
        checks = [
            JMESPathCheck('alwaysOn', True),
            JMESPathCheck('autoHealEnabled', True),
            JMESPathCheck('phpVersion', '7.0'),
            JMESPathCheck('netFrameworkVersion', 'v3.0'),
            JMESPathCheck('pythonVersion', '3.4'),
            JMESPathCheck('use32BitWorkerProcess', False),
            JMESPathCheck('webSocketsEnabled', True),
            JMESPathCheck('minTlsVersion', '1.0'),
            JMESPathCheck('http20Enabled', True),
            JMESPathCheck('ftpsState', 'Disabled')]

        self.cmd('webapp config set -g {} -n {} --always-on true --auto-heal-enabled true --php-version 7.0 '
                 '--net-framework-version v3.5 --python-version 3.4 --use-32bit-worker-process=false '
                 '--web-sockets-enabled=true --http20-enabled true --min-tls-version 1.0 --ftps-state Disabled'.format(resource_group, webapp_name)).assert_with_checks(checks)
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)) \
            .assert_with_checks(checks)

        # site appsettings testing
        # update
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("length([?name=='s1'])", 1),
            JMESPathCheck("length([?name=='s2'])", 1),
            JMESPathCheck("length([?name=='s3'])", 1),
            JMESPathCheck("length([?value=='foo'])", 1),
            JMESPathCheck("length([?value=='bar'])", 1),
            JMESPathCheck("length([?value=='bar2'])", 1)
        ])
        # show
        result = self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name)).get_output_in_json()
        s2 = next((x for x in result if x['name'] == 's2'))
        self.assertEqual(s2['name'], 's2')
        self.assertEqual(s2['slotSetting'], False)
        self.assertEqual(s2['value'], 'bar')
        self.assertEqual(set([x['name'] for x in result]), set(['s1', 's2', 's3', 'WEBSITE_NODE_DEFAULT_VERSION']))
        # delete
        self.cmd('webapp config appsettings delete -g {} -n {} --setting-names s1 s2'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck("length([?name=='s3'])", 1),
                     JMESPathCheck("length([?name=='s1'])", 0),
                     JMESPathCheck("length([?name=='s2'])", 0)])

        # hostnames
        self.cmd('webapp config hostname list -g {} --webapp-name {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', '{0}.azurewebsites.net'.format(webapp_name))])

        # site azure storage account configurations tests
        # add
        self.cmd(('webapp config storage-account add -g {} -n {} --custom-id Id --storage-type AzureFiles --account-name name '
                 '--share-name sharename --access-key key --mount-path /path/to/mount').format(resource_group, webapp_name))
        self.cmd('webapp config storage-account list -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('length(@)', 1),
            JMESPathCheck("[?name=='Id']|[0].value.type", "AzureFiles"),
            JMESPathCheck("[?name=='Id']|[0].value.accountName", "name"),
            JMESPathCheck("[?name=='Id']|[0].value.shareName", "sharename"),
            JMESPathCheck("[?name=='Id']|[0].value.accessKey", "key"),
            JMESPathCheck("[?name=='Id']|[0].value.mountPath", "/path/to/mount")])
        # update
        self.cmd('webapp config storage-account update -g {} -n {} --custom-id Id --mount-path /different/path'
                 .format(resource_group, webapp_name))
        self.cmd('webapp config storage-account list -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("length(@)", 1),
            JMESPathCheck("[?name=='Id']|[0].value.type", "AzureFiles"),
            JMESPathCheck("[?name=='Id']|[0].value.accountName", "name"),
            JMESPathCheck("[?name=='Id']|[0].value.shareName", "sharename"),
            JMESPathCheck("[?name=='Id']|[0].value.accessKey", "key"),
            JMESPathCheck("[?name=='Id']|[0].value.mountPath", "/different/path")])
        # list
        self.cmd('webapp config storage-account list -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("length(@)", 1),
            JMESPathCheck('[0].name', 'Id')])
        # delete
        self.cmd('webapp config storage-account delete -g {} -n {} --custom-id Id'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck("length(@)", 0)])

        # site connection string tests
        self.cmd('webapp config connection-string set -t mysql -g {} -n {} --settings c1="conn1" c2=conn2 '
                 '--slot-settings c3=conn3'.format(resource_group, webapp_name))
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck('length([])', 3),
                     JMESPathCheck("[?name=='c1']|[0].slotSetting", False),
                     JMESPathCheck("[?name=='c1']|[0].value.type", 'MySql'),
                     JMESPathCheck("[?name=='c1']|[0].value.value", 'conn1'),
                     JMESPathCheck("[?name=='c2']|[0].slotSetting", False),
                     JMESPathCheck("[?name=='c3']|[0].slotSetting", True)])
        self.cmd('webapp config connection-string delete -g {} -n {} --setting-names c1 c3'
                 .format(resource_group, webapp_name))
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheck('length([])', 1),
                     JMESPathCheck('[0].slotSetting', False),
                     JMESPathCheck('[0].name', 'c2')])

        # see deployment user; just make sure the command does return something
        self.assertTrue(self.cmd('webapp deployment user show').get_output_in_json()['type'])


class WebappScaleTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_scale(self, resource_group):
        plan = self.create_random_name(prefix='scale-plan', length=24)
        # start with shared sku
        self.cmd('appservice plan create -g {} -n {} --sku SHARED'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'D1'),
            JMESPathCheck('sku.tier', 'Shared'),
            JMESPathCheck('sku.size', 'D1'),
            JMESPathCheck('sku.family', 'D'),
            JMESPathCheck('sku.capacity', 0)  # 0 means the default value: 1 instance
        ])
        # scale up
        self.cmd('appservice plan update -g {} -n {} --sku S2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S2'),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.size', 'S2'),
            JMESPathCheck('sku.family', 'S')
        ])
        # scale down
        self.cmd('appservice plan update -g {} -n {} --sku B1'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B')
        ])
        # scale out
        self.cmd('appservice plan update -g {} -n {} --number-of-workers 2'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B'),
            JMESPathCheck('sku.capacity', 2)
        ])


class AppServiceBadErrorPolishTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='resource_group')
    @ResourceGroupPreparer(parameter_name='resource_group2')
    def test_appservice_error_polish(self, resource_group, resource_group2):
        plan = self.create_random_name(prefix='web-error-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-error', length=24)
        self.cmd('group create -n {} -l westus'.format(resource_group2))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(resource_group2, plan))
        # we will try to produce an error by try creating 2 webapp with same name in different groups
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group2, webapp_name, plan), expect_failure=True)
        # TODO: ensure test fx can capture error details for us to verify
        # allowed_exceptions='Website with given name {} already exists'.format(webapp_name)


# this test doesn't contain the ultimate verification which you need to manually load the frontpage in a browser
class LinuxWebappScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(location='japanwest')
    def test_linux_webapp(self, resource_group):
        runtime = 'node|6.6'
        plan = self.create_random_name(prefix='webapp-linux-plan', length=24)
        webapp = self.create_random_name(prefix='webapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            JMESPathCheck('reserved', True),  # this weird field means it is a linux
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(resource_group, webapp, plan, runtime), checks=[
            JMESPathCheck('name', webapp),
        ])
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck('windowsFxVersion', None)
        ])
        time.sleep(30)  # workaround the fact that a new linux web's "kind" won't be settled instantaneously
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

        result = self.cmd('webapp deployment container config -g {} -n {} --enable-cd true'.format(resource_group, webapp)).get_output_in_json()

        self.assertTrue(result['CI_CD_URL'].startswith('https://'))
        self.assertTrue(result['CI_CD_URL'].endswith('.scm.azurewebsites.net/docker/hook'))

        result = self.cmd('webapp config container set -g {} -n {} --docker-custom-image-name {} --docker-registry-server-password {} --docker-registry-server-user {} --docker-registry-server-url {} --enable-app-service-storage {}'.format(
            resource_group, webapp, 'foo-image', 'foo-password', 'foo-user', 'foo-url', 'false')).get_output_in_json()
        self.assertEqual(set(x['value'] for x in result if x['name'] == 'DOCKER_REGISTRY_SERVER_PASSWORD'), set([None]))  # we mask the password

        result = self.cmd('webapp config container show -g {} -n {} '.format(resource_group, webapp)).get_output_in_json()
        self.assertEqual(set(x['name'] for x in result), set(['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME', 'DOCKER_CUSTOM_IMAGE_NAME', 'DOCKER_REGISTRY_SERVER_PASSWORD', 'WEBSITES_ENABLE_APP_SERVICE_STORAGE']))
        self.assertEqual(set(x['value'] for x in result if x['name'] == 'DOCKER_REGISTRY_SERVER_PASSWORD'), set([None]))   # we mask the password
        sample = next((x for x in result if x['name'] == 'DOCKER_REGISTRY_SERVER_URL'))
        self.assertEqual(sample, {'name': 'DOCKER_REGISTRY_SERVER_URL', 'slotSetting': False, 'value': 'foo-url'})
        sample = next((x for x in result if x['name'] == 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'))
        self.assertEqual(sample, {'name': 'WEBSITES_ENABLE_APP_SERVICE_STORAGE', 'slotSetting': False, 'value': 'false'})
        self.cmd('webapp config container delete -g {} -n {}'.format(resource_group, webapp))
        result2 = self.cmd('webapp config container show -g {} -n {} '.format(resource_group, webapp)).get_output_in_json()
        self.assertEqual(result2, [])


class WebappACRScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='japanwest')
    def test_acr_integration(self, resource_group):
        plan = self.create_random_name(prefix='acrtestplan', length=24)
        webapp = self.create_random_name(prefix='webappacrtest', length=24)
        runtime = 'node|6.6'
        acr_registry_name = webapp
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(resource_group, acr_registry_name))
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(resource_group, webapp, plan, runtime))
        creds = self.cmd('acr credential show -n {}'.format(acr_registry_name)).get_output_in_json()
        self.cmd('webapp config container set -g {0} -n {1} --docker-custom-image-name {2}.azurecr.io/image-name:latest --docker-registry-server-url https://{2}.azurecr.io'.format(
            resource_group, webapp, acr_registry_name), checks=[
                JMESPathCheck("[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username'])
        ])


class WebappGitScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_git(self, resource_group):
        plan = self.create_random_name(prefix='webapp-git-plan5', length=24)
        webapp = self.create_random_name(prefix='web-git-test2', length=24)
        # You can create and use any repros with the 3 files under "./sample_web"
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan))
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
        self.cmd('webapp deployment source delete -g {} -n {}'.format(resource_group, webapp))
        self.cmd('webapp deployment source show -g {} -n {}'.format(resource_group, webapp),
                 checks=JMESPathCheck('repoUrl', None))


class WebappSlotScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_slot(self, resource_group):
        plan = self.create_random_name(prefix='slot-test-plan', length=24)
        webapp = self.create_random_name(prefix='slot-test-web', length=24)

        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan_result['name']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        slot2 = 'dev'
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        test_php_version = '5.6'
        # create a few app-settings to test they can be cloned
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=v1 --slot-settings s2=v2'.format(resource_group, webapp))
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck('name', slot)
        ])
        self.cmd('webapp deployment source config -g {} -n {} --repo-url {} --branch {} -s {} --manual-integration'.format(resource_group, webapp, test_git_repo, slot, slot), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('branch', slot)
        ])
        # swap with prod and verify the git branch also switched
        self.cmd('webapp deployment slot swap -g {} -n {} -s {}'.format(resource_group, webapp, slot))
        result = self.cmd('webapp config appsettings list -g {} -n {} -s {}'.format(resource_group, webapp, slot)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(['s1', 'WEBSITE_NODE_DEFAULT_VERSION']))
        # create a new slot by cloning from prod slot
        self.cmd('webapp config set -g {} -n {} --php-version {}'.format(resource_group, webapp, test_php_version))
        self.cmd('webapp deployment slot create -g {} -n {} --slot {} --configuration-source {}'.format(resource_group, webapp, slot2, webapp))
        self.cmd('webapp config show -g {} -n {} --slot {}'.format(resource_group, webapp, slot2), checks=[
            JMESPathCheck("phpVersion", test_php_version),
        ])
        self.cmd('webapp config appsettings set -g {} -n {} --slot {} --settings s3=v3 --slot-settings s4=v4'.format(resource_group, webapp, slot2), checks=[
            JMESPathCheck("[?name=='s4']|[0].slotSetting", True),
            JMESPathCheck("[?name=='s3']|[0].slotSetting", False),
        ])

        self.cmd('webapp config connection-string set -g {} -n {} -t mysql --slot {} --settings c1=connection1 --slot-settings c2=connection2'.format(resource_group, webapp, slot2))
        # verify we can swap with non production slot
        self.cmd('webapp deployment slot swap -g {} -n {} --slot {} --target-slot {}'.format(resource_group, webapp, slot, slot2))
        result = self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot2)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(['s1', 's4', 'WEBSITE_NODE_DEFAULT_VERSION']))
        result = self.cmd('webapp config connection-string list -g {} -n {} --slot {}'.format(resource_group, webapp, slot2)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(['c2']))
        result = self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot)).get_output_in_json()
        self.assertTrue(set(['s3']).issubset(set([x['name'] for x in result])))
        result = self.cmd('webapp config connection-string list -g {} -n {} --slot {}'.format(resource_group, webapp, slot)).get_output_in_json()
        self.assertEqual(set([x['name'] for x in result]), set(['c1']))
        self.cmd('webapp deployment slot list -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck("length([])", 2),
            JMESPathCheck("length([?name=='{}'])".format(slot2), 1),
            JMESPathCheck("length([?name=='{}'])".format(slot), 1),
        ])
        self.cmd('webapp deployment slot delete -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        # try another way to delete a slot and exercise all options
        self.cmd('webapp delete -g {} -n {} --slot {} --keep-dns-registration --keep-empty-plan --keep-metrics'.format(resource_group, webapp, slot2))


class WebappSlotTrafficRouting(ScenarioTest):
    @ResourceGroupPreparer()
    def test_traffic_routing(self, resource_group):
        plan = self.create_random_name(prefix='slot-traffic-plan', length=24)
        webapp = self.create_random_name(prefix='slot-traffic-web', length=24)
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan_result['name']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        self.cmd('webapp traffic-routing set -g {} -n {} -d {}=15'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[0].actionHostName", slot + '.azurewebsites.net'),
            JMESPathCheck("[0].reroutePercentage", 15.0)
        ])
        self.cmd('webapp traffic-routing show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheck("[0].actionHostName", slot + '.azurewebsites.net'),
            JMESPathCheck("[0].reroutePercentage", 15.0)
        ])
        self.cmd('webapp traffic-routing clear -g {} -n {}'.format(resource_group, webapp))


class AppServiceCors(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_cors(self, resource_group):
        self.kwargs.update({
            'plan': self.create_random_name(prefix='slot-traffic-plan', length=24),
            'web': self.create_random_name(prefix='slot-traffic-web', length=24),
            'slot': 'slot1'
        })
        self.cmd('appservice plan create -g {rg} -n {plan} --sku S1')
        self.cmd('webapp create -g {rg} -n {web} --plan {plan}')
        self.cmd('webapp cors add -g {rg} -n {web} --allowed-origins https://msdn.com https://msn.com')
        self.cmd('webapp cors show -g {rg} -n {web}',
                 checks=self.check('allowedOrigins', ['https://msdn.com', 'https://msn.com']))
        self.cmd('webapp cors remove -g {rg} -n {web} --allowed-origins https://msn.com')
        self.cmd('webapp cors show -g {rg} -n {web}', checks=self.check('allowedOrigins', ['https://msdn.com']))

        self.cmd('webapp deployment slot create -g {rg} -n {web} --slot {slot}')
        self.cmd('webapp cors add -g {rg} -n {web} --slot {slot} --allowed-origins https://foo.com')
        self.cmd('webapp cors show -g {rg} -n {web} --slot {slot}',
                 checks=self.check('allowedOrigins', ['https://foo.com']))
        self.cmd('webapp cors remove -g {rg} -n {web} --slot {slot} --allowed-origins https://foo.com')
        self.cmd('webapp cors show -g {rg} -n {web} --slot {slot}', checks=self.check('allowedOrigins', []))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_functionapp_cors(self, resource_group, storage_account):
        self.kwargs.update({
            'plan': self.create_random_name(prefix='slot-traffic-plan', length=24),
            'function': self.create_random_name(prefix='slot-traffic-web', length=24),
            'storage': storage_account
        })
        self.cmd('appservice plan create -g {rg} -n {plan} --sku S1')
        self.cmd('storage account create --name {storage} -g {rg} --sku Standard_LRS')
        self.cmd('functionapp create -g {rg} -n {function} --plan {plan} -s {storage}')
        self.cmd('functionapp cors add -g {rg} -n {function} --allowed-origins https://msdn.com https://msn.com')
        result = self.cmd('functionapp cors show -g {rg} -n {function}').get_output_in_json()['allowedOrigins']
        # functionapp has pre-defined cors. We verify the ones we added are in the list
        self.assertTrue(set(['https://msdn.com', 'https://msn.com']).issubset(set(result)))


class WebappSlotSwapScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_slot_swap(self, resource_group):
        plan = self.create_random_name(prefix='slot-swap-plan', length=24)
        webapp = self.create_random_name(prefix='slot-swap-web', length=24)
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan_result['name']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings s1=prod'.format(resource_group, webapp))
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings s1=slot --slot {}'.format(resource_group, webapp, slot))
        # swap with preview
        self.cmd('webapp deployment slot swap -g {} -n {} -s {} --action preview'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[?name=='s1']|[0].value", 'prod')
        ])
        # complete the swap
        self.cmd('webapp deployment slot swap -g {} -n {} -s {}'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[?name=='s1']|[0].value", 'slot')
        ])
        # reset
        self.cmd('webapp deployment slot swap -g {} -n {} -s {} --action reset'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheck("[?name=='s1']|[0]", None)
        ])


class WebappSSLCertTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_ssl(self, resource_group, resource_group_location):
        plan = self.create_random_name(prefix='ssl-test-plan', length=24)
        webapp_name = self.create_random_name(prefix='web-ssl-test', length=20)
        # Cert Generated using
        # https://docs.microsoft.com/en-us/azure/app-service-web/web-sites-configure-ssl-certificate#bkmk_ssopenssl
        pfx_file = os.path.join(TEST_DIR, 'server.pfx')
        cert_password = 'test'
        cert_thumbprint = '9E9735C45C792B03B3FFCCA614852B32EE71AD6B'
        # we configure tags here in a hope to capture a repro for https://github.com/Azure/azure-cli/issues/6929
        self.cmd('appservice plan create -g {} -n {} --sku B1 --tags plan=plan1'.format(resource_group, plan))
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), self.check('tags.plan', 'plan1'))
        self.cmd('webapp create -g {} -n {} --plan {} --tags web=web1'.format(resource_group, webapp_name, plan, resource_group_location))
        self.cmd('webapp config ssl upload -g {} -n {} --certificate-file "{}" --certificate-password {}'.format(resource_group, webapp_name, pfx_file, cert_password), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint)
        ])
        self.cmd('webapp show -g {} -n {}'.format(resource_group, webapp_name), self.check('tags.web', 'web1'))
        self.cmd('webapp config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {}'.format(resource_group, webapp_name, cert_thumbprint, 'SNI'), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(webapp_name), cert_thumbprint)
        ])
        self.cmd('webapp config ssl unbind -g {} -n {} --certificate-thumbprint {}'.format(resource_group, webapp_name, cert_thumbprint), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(webapp_name), 'Disabled'),
        ])
        self.cmd('webapp config ssl delete -g {} --certificate-thumbprint {}'.format(resource_group, cert_thumbprint))
        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))


class WebappUndeleteTest(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_webapp_deleted_list(self, resource_group):
        plan = self.create_random_name(prefix='delete-me-plan', length=24)
        webapp_name = self.create_random_name(prefix='delete-me-web', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku B1 --tags plan=plan1'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp deleted list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].deletedSiteName', webapp_name)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_webapp_deleted_restore(self, resource_group):
        plan = self.create_random_name(prefix='undelete-plan', length=24)
        webapp_name = self.create_random_name(prefix='undelete-web', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku B1 --tags plan=plan1'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        # A snapshot must be available to restore a deleted app. The app must exist for at least an hour prior to deletion to have a snapshot.
        # Using a pre-configured deleted app in this test.
        deleted_app_id = self.cmd('webapp deleted list -g {} -n {}'.format('nicking', 'nickingdeletedwordpress')).get_output_in_json()[0]['id']
        self.cmd('webapp deleted restore --deleted-id {} -g {} -n {}'.format(deleted_app_id, resource_group, webapp_name))


class FunctionAppWithPlanE2ETest(ScenarioTest):
    @ResourceGroupPreparer()
    @ResourceGroupPreparer(parameter_name='resource_group2')
    def test_functionapp_e2e(self, resource_group, resource_group2):
        functionapp_name, functionapp_name2 = self.create_random_name('func-e2e', 24), self.create_random_name('func-e2e', 24)
        plan = self.create_random_name('func-e2e-plan', 24)
        storage, storage2 = 'functionappplanstorage', 'functionappplanstorage2'
        plan_id = self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('appservice plan list -g {}'.format(resource_group))
        self.cmd('storage account create --name {} -g {} -l westus --sku Standard_LRS'.format(storage, resource_group))
        storage_account_id2 = self.cmd('storage account create --name {} -g {} -l westus --sku Standard_LRS'.format(storage2, resource_group2)).get_output_in_json()['id']

        self.cmd('functionapp create -g {} -n {} -p {} -s {}'.format(resource_group, functionapp_name, plan, storage), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', functionapp_name),
            JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')
        ])
        self.cmd('functionapp create -g {} -n {} -p {} -s {}'.format(resource_group2, functionapp_name2, plan_id, storage_account_id2))
        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppWithConsumptionPlanE2ETest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-c-e2e', location='westus')
    @StorageAccountPreparer()
    def test_functionapp_consumption_e2e(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c westus -s {}'
                 .format(resource_group, functionapp_name, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].kind', 'functionapp'),
            JMESPathCheck('[0].name', functionapp_name)
        ])
        self.cmd('functionapp show -g {} -n {}'.format(resource_group, functionapp_name), checks=[
            JMESPathCheck('kind', 'functionapp'),
            JMESPathCheck('name', functionapp_name)
        ])
        self.cmd('functionapp update -g {} -n {} --set clientAffinityEnabled=true'.format(resource_group, functionapp_name), checks=[
            self.check('clientAffinityEnabled', True)
        ])

        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppWithLinuxConsumptionPlanTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-linux', location='westus')
    @StorageAccountPreparer()
    def test_functionapp_consumption_linux(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionapplinuxconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c westus -s {} --os-type Linux --runtime node'
                 .format(resource_group, functionapp_name, storage_account)).assert_with_checks([
                     JMESPathCheck('state', 'Running'),
                     JMESPathCheck('name', functionapp_name),
                     JMESPathCheck('reserved', True),
                     JMESPathCheck('kind', 'functionapp,linux'),
                     JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppOnLinux(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer()
    def test_functionapp_on_linux(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(prefix='functionapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            JMESPathCheck('reserved', True),  # this weird field means it is a linux
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {}'.format(resource_group, functionapp, plan, storage_account), checks=[
            JMESPathCheck('name', functionapp)
        ])
        result = self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].name', functionapp)
        ]).get_output_in_json()
        self.assertTrue('functionapp,linux' in result[0]['kind'])
        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp))


class WebappAuthenticationTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_authentication')
    def test_webapp_authentication(self, resource_group):
        webapp_name = self.create_random_name('webapp-authentication-test', 40)
        plan_name = self.create_random_name('webapp-authentication-plan', 40)
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        # testing show command for newly created app and initial fields
        self.cmd('webapp auth show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheck('unauthenticatedClientAction', None),
            JMESPathCheck('defaultProvider', None),
            JMESPathCheck('enabled', False),
            JMESPathCheck('tokenStoreEnabled', None),
            JMESPathCheck('allowedExternalRedirectUrls', None),
            JMESPathCheck('tokenRefreshExtensionHours', None),
            JMESPathCheck('clientId', None),
            JMESPathCheck('clientSecret', None),
            JMESPathCheck('allowedAudiences', None),
            JMESPathCheck('issuer', None),
            JMESPathCheck('facebookAppId', None),
            JMESPathCheck('facebookAppSecret', None),
            JMESPathCheck('facebookOauthScopes', None)
        ])

        # update and verify
        result = self.cmd('webapp auth update -g {} -n {} --enabled true --action LoginWithFacebook '
                          '--token-store false --token-refresh-extension-hours 7.2 '
                          '--aad-client-id aad_client_id --aad-client-secret aad_secret '
                          '--aad-allowed-token-audiences https://audience1 --aad-token-issuer-url https://issuer_url '
                          '--facebook-app-id facebook_id --facebook-app-secret facebook_secret '
                          '--facebook-oauth-scopes public_profile email'
                          .format(resource_group, webapp_name)).assert_with_checks([
                              JMESPathCheck('unauthenticatedClientAction', 'RedirectToLoginPage'),
                              JMESPathCheck('defaultProvider', 'Facebook'),
                              JMESPathCheck('enabled', True),
                              JMESPathCheck('tokenStoreEnabled', False),
                              JMESPathCheck('tokenRefreshExtensionHours', 7.2),
                              JMESPathCheck('clientId', 'aad_client_id'),
                              JMESPathCheck('clientSecret', 'aad_secret'),
                              JMESPathCheck('issuer', 'https://issuer_url'),
                              JMESPathCheck('facebookAppId', 'facebook_id'),
                              JMESPathCheck('facebookAppSecret', 'facebook_secret')]).get_output_in_json()

        self.assertIn('https://audience1', result['allowedAudiences'])
        self.assertIn('email', result['facebookOauthScopes'])
        self.assertIn('public_profile', result['facebookOauthScopes'])


class WebappUpdateTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_update')
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
        self.cmd('webapp deployment slot create -g {} -n {} -s s1'.format(resource_group, webapp_name))
        self.cmd('webapp update -g {} -n {} -s s1 --client-affinity-enabled true'.format(resource_group, webapp_name), checks=[
            self.check('clientAffinityEnabled', True)
        ])


class WebappZipDeployScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_zipDeploy')
    def test_deploy_zip(self, resource_group):
        webapp_name = self.create_random_name('webapp-zipDeploy-test', 40)
        plan_name = self.create_random_name('webapp-zipDeploy-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'test.zip')
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        self.cmd('webapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, webapp_name, zip_file)).assert_with_checks([
            JMESPathCheck('status', 4),
            JMESPathCheck('deployer', 'Push-Deployer'),
            JMESPathCheck('message', 'Created via a push deployment'),
            JMESPathCheck('complete', True)
        ])


class WebappImplictIdentityTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_assign_system_identity(self, resource_group):
        scope = '/subscriptions/{}/resourcegroups/{}'.format(self.get_subscription_id(), resource_group)
        role = 'Reader'
        plan_name = self.create_random_name('web-msi-plan', 20)
        webapp_name = self.create_random_name('web-msi', 20)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            result = self.cmd('webapp identity assign -g {} -n {} --role {} --scope {}'.format(resource_group, webapp_name, role, scope)).get_output_in_json()
            self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=[
                self.check('principalId', result['principalId'])
            ])
        self.cmd('role assignment list -g {} --assignee {}'.format(resource_group, result['principalId']), checks=[
            JMESPathCheck('length([])', 1),
            JMESPathCheck('[0].roleDefinitionName', role)
        ])

        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=self.check('principalId', result['principalId']))
        self.cmd('webapp identity remove -g {} -n {}'.format(resource_group, webapp_name))
        self.cmd('webapp identity show -g {} -n {}'.format(resource_group, webapp_name), checks=self.is_empty())


class WebappListLocationsFreeSKUTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_list-locations-free-sku-test')
    def test_webapp_list_locations_free_sku(self, resource_group):
        asp_F1 = self.cmd('appservice list-locations --sku F1').get_output_in_json()
        result = self.cmd('appservice list-locations --sku Free').get_output_in_json()
        self.assertEqual(asp_F1, result)


class WebappTriggeredWebJobListTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_triggeredWebjob_list(self, resource_group):
        # testing this using a webjob already created
        # given there is no create command inorder to re-record please create a webjob before
        # recording this
        resource_group_name = 'cliTestApp'
        webapp_name = 'cliTestApp'
        webjob_name = 'test-triggered'

        # list test
        self.cmd('webapp webjob triggered list -g {} -n {}'
                 .format(resource_group_name, webapp_name)).assert_with_checks([
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', '{}/{}'.format(webapp_name, webjob_name)),
                     JMESPathCheck('[0].type', 'Microsoft.Web/sites/triggeredwebjobs')])


class WebappContinuousWebJobE2ETest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_continuousWebjob_e2e(self, resource_group):
        # testing this using a webjob already created
        # given there is no create command inorder to re-record please create a webjob before
        # recording this
        resource_group_name = 'cliTestApp'
        webapp_name = 'cliTestApp'
        webjob_name = 'test-continuous'

        # list test
        self.cmd('webapp webjob continuous list -g {} -n {}'
                 .format(resource_group_name, webapp_name)).assert_with_checks([
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', '{}/{}'.format(webapp_name, webjob_name)),
                     JMESPathCheck('[0].type', 'Microsoft.Web/sites/continuouswebjobs')])
        # start
        self.cmd('webapp webjob continuous start -g {} -n {} -w {}'
                 .format(resource_group_name, webapp_name, webjob_name)).assert_with_checks([
                     JMESPathCheck('status', 'Running')])
        # stop
        self.cmd('webapp webjob continuous stop -g {} -n {} -w {}'
                 .format(resource_group_name, webapp_name, webjob_name)).assert_with_checks([
                     JMESPathCheck('status', 'Disabling')])


class WebappWindowsContainerBasicE2ETest(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_webapp_hyperv_e2e(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-hyperv-e2e', length=24)
        plan = self.create_random_name(prefix='webapp-hyperv-plan', length=24)

        self.cmd('appservice plan create -g {} -n {} --hyper-v --sku PC2'.format(resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'PremiumContainer'),
            JMESPathCheck('[0].sku.name', 'PC2')
        ])
        self.cmd('appservice plan list', checks=[
            JMESPathCheck("length([?name=='{}' && resourceGroup=='{}'])".format(plan, resource_group), 1)
        ])
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan), checks=[
            JMESPathCheck('name', plan)
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-container-image-name "DOCKER|microsoft/iis:nanoserver-sac2016"'.format(resource_group, webapp_name, plan), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('windowsFxVersion', "DOCKER|microsoft/iis:nanoserver-sac2016"),
            JMESPathCheck('linuxFxVersion', "")
        ])
        self.cmd('webapp config set -g {} -n {} --windows-fx-version "DOCKER|microsoft/iis"'.format(resource_group, webapp_name))
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name), checks=[
            JMESPathCheck('windowsFxVersion', "DOCKER|microsoft/iis"),
            JMESPathCheck('linuxFxVersion', "")
        ])


if __name__ == '__main__':
    unittest.main()
