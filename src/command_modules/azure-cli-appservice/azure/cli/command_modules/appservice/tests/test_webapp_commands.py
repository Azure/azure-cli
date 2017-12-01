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

from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.testsdk import JMESPathCheck as JMESPathCheckV2
from azure.cli.testsdk.vcr_test_base import (ResourceGroupVCRTestBase,
                                             JMESPathCheck, NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long


class WebappBasicE2ETest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappBasicE2ETest, self).__init__(__file__, test_method, resource_group='azurecli-webapp-e2e')

    def test_webapp_e2e(self):
        self.execute()

    def body(self):
        webapp_name = 'webapp-e2e'
        plan = 'webapp-e2e-plan'
        self.cmd('appservice plan create -g {} -n {}'.format(self.resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1')
        ])
        self.cmd('appservice plan list', checks=[
            JMESPathCheck("length([?name=='{}' && resourceGroup=='{}'])".format(plan, self.resource_group), 1)
        ])
        self.cmd('appservice plan show -g {} -n {}'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan)
        ])
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, webapp_name, plan), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('webapp show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        result = self.cmd('webapp deployment source config-local-git -g {} -n {}'.format(self.resource_group, webapp_name))
        self.assertTrue(result['url'].endswith(webapp_name + '.git'))
        self.cmd('webapp deployment source show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('repoUrl', 'https://{}.scm.azurewebsites.net'.format(webapp_name))
        ])
        # turn on diagnostics
        test_cmd = ('webapp log config -g {} -n {} --level verbose'.format(self.resource_group, webapp_name) + ' '
                    '--application-logging true --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem')
        self.cmd(test_cmd)
        self.cmd('webapp log show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorMessages.enabled', True),
            JMESPathCheck('failedRequestsTracing.enabled', True)
        ])
        self.cmd('webapp config show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorLoggingEnabled', True),
            JMESPathCheck('httpLoggingEnabled', True),
            JMESPathCheck('scmType', 'LocalGit'),
            JMESPathCheck('requestTracingEnabled', True)
            # TODO: contact webapp team for where to retrieve 'level'
        ])
        # show publish profile info
        result = self.cmd('webapp deployment list-publishing-profiles -g {} -n {}'.format(self.resource_group, webapp_name))
        self.assertTrue(result[1]['publishUrl'].startswith('ftp://'))
        self.cmd('webapp stop -g {} -n {}'.format(self.resource_group, webapp_name))
        self.cmd('webapp show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', webapp_name)
        ])
        self.cmd('webapp start -g {} -n {}'.format(self.resource_group, webapp_name))
        self.cmd('webapp show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name)
        ])


class WebappQuickCreateTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_win_webapp_quick_create(self, resource_group):
        webapp_name = 'webapp-quick'
        plan = 'plan-quick'
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        r = self.cmd('webapp create -g {} -n {} --plan {} --deployment-local-git -r "node|6.1"'.format(resource_group, webapp_name, plan)).get_output_in_json()
        self.assertTrue(r['ftpPublishingUrl'].startswith('ftp://'))
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name, checks=[
            JMESPathCheckV2('[0].name', 'WEBSITE_NODE_DEFAULT_VERSION'),
            JMESPathCheckV2('[0].value', '6.1.0'),
        ]))

    @ResourceGroupPreparer()
    def test_win_webapp_quick_create_cd(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick-cd', length=24)
        plan = self.create_random_name(prefix='plan-quick', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-source-url https://github.com/yugangw-msft/azure-site-test.git -r "node|6.1"'.format(resource_group, webapp_name, plan))
        time.sleep(30)  # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name))
        # verify the web page
        self.assertTrue('Hello world' in str(r.content))

    @ResourceGroupPreparer(location='japaneast')
    def test_linux_webapp_quick_create(self, resource_group):
        webapp_name = self.create_random_name(prefix='webapp-quick-linux', length=24)
        plan = self.create_random_name(prefix='plan-quick-linux', length=24)

        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -i naziml/ruby-hello'.format(resource_group, webapp_name, plan))
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        # verify the web page
        self.assertTrue('Ruby on Rails in Web Apps on Linux' in str(r.content))
        # verify app settings
        self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name, checks=[
            JMESPathCheckV2('[0].name', 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'),
            JMESPathCheckV2('[0].value', 'false'),
        ]))

    @ResourceGroupPreparer(location='japanwest')
    def test_linux_webapp_quick_create_cd(self, resource_group):
        webapp_name = 'webapp-quick-linux-cd'
        plan = 'plan-quick-linux-cd'
        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -u https://github.com/yugangw-msft/azure-site-test.git -r "node|6.10"'.format(resource_group, webapp_name, plan))
        time.sleep(30)  # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        r = requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        # verify the web page
        self.assertTrue('Hello world' in str(r.content))

    @ResourceGroupPreparer(parameter_name='resource_group', parameter_name_for_location='resource_group_location')
    @ResourceGroupPreparer(parameter_name='resource_group2', parameter_name_for_location='resource_group_location2')
    def test_create_in_different_group(self, resource_group, resource_group_location, resource_group2, resource_group_location2):
        plan = 'planInOneRG'
        self.cmd('group create -n {} -l {}'.format(resource_group2, resource_group_location))
        plan_id = self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan)).get_output_in_json()['id']
        self.cmd('webapp create -g {} -n webInOtherRG --plan {}'.format(resource_group2, plan_id), checks=[
            JMESPathCheckV2('name', 'webInOtherRG')
        ])


# Test Framework is not able to handle binary file format, hence, only run live
class AppServiceLogTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_download_win_web_log(self, resource_group):
        import zipfile
        from pathlib import Path
        webapp_name = self.create_random_name(prefix='webapp-win-log', length=24)
        plan = self.create_random_name(prefix='win-log', length=24)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --deployment-source-url https://github.com/yugangw-msft/azure-site-test.git -r "node|6.1"'.format(resource_group, webapp_name, plan))
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
        from pathlib import Path
        webapp_name = self.create_random_name(prefix='webapp-linux-log', length=24)
        plan = self.create_random_name(prefix='linux-log', length=24)
        self.cmd('appservice plan create -g {} -n {} --is-linux'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} -i naziml/ruby-hello'.format(resource_group, webapp_name, plan))
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
        webapp_name = 'webapp-quick'
        plan = 'plan-quick'
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))
        self.cmd('webapp delete -g {} -n {} --keep-dns-registration --keep-empty-plan --keep-metrics'.format(resource_group, webapp_name))
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[
            JMESPathCheckV2('[0].name', plan)
        ])

    @ResourceGroupPreparer()
    def test_auto_delete_plan(self, resource_group):
        webapp_name = 'webapp-delete2'
        plan = 'webapp-delete-plan2'
        self.cmd('appservice plan create -g {} -n {} -l westus'.format(resource_group, plan))

        self.cmd('appservice plan update -g {} -n {} --sku S1'.format(resource_group, plan),
                 checks=[JMESPathCheckV2('name', plan),
                         JMESPathCheckV2('sku.tier', 'Standard'),
                         JMESPathCheckV2('sku.name', 'S1')])

        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan))

        self.cmd('webapp delete -g {} -n {}'.format(resource_group, webapp_name))
        # test empty service plan should be automatically deleted.
        self.cmd('appservice plan list -g {}'.format(resource_group), checks=[JMESPathCheckV2('length(@)', 0)])


class WebappConfigureTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_config')
    def test_webapp_config(self, resource_group):
        webapp_name = self.create_random_name('webapp-config-test', 40)
        plan_name = self.create_random_name('webapp-config-plan', 40)

        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        # verify the baseline
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheckV2('alwaysOn', False),
            JMESPathCheckV2('autoHealEnabled', False),
            JMESPathCheckV2('phpVersion', '5.6'),
            JMESPathCheckV2('netFrameworkVersion', 'v4.0'),
            JMESPathCheckV2('pythonVersion', ''),
            JMESPathCheckV2('use32BitWorkerProcess', True),
            JMESPathCheckV2('webSocketsEnabled', False)])

        # update and verify
        checks = [
            JMESPathCheckV2('alwaysOn', True),
            JMESPathCheckV2('autoHealEnabled', True),
            JMESPathCheckV2('phpVersion', '7.0'),
            JMESPathCheckV2('netFrameworkVersion', 'v3.0'),
            JMESPathCheckV2('pythonVersion', '3.4'),
            JMESPathCheckV2('use32BitWorkerProcess', False),
            JMESPathCheckV2('webSocketsEnabled', True)
        ]
        self.cmd('webapp config set -g {} -n {} --always-on true --auto-heal-enabled true --php-version 7.0 '
                 '--net-framework-version v3.5 --python-version 3.4 --use-32bit-worker-process=false '
                 '--web-sockets-enabled=true'.format(resource_group, webapp_name)).assert_with_checks(checks)
        self.cmd('webapp config show -g {} -n {}'.format(resource_group, webapp_name)) \
            .assert_with_checks(checks)

        # site appsettings testing
        # update
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(resource_group, webapp_name)).assert_with_checks([
            JMESPathCheckV2("length([?name=='s1'])", 1),
            JMESPathCheckV2("length([?name=='s2'])", 1),
            JMESPathCheckV2("length([?name=='s3'])", 1),
            JMESPathCheckV2("length([?value=='foo'])", 1),
            JMESPathCheckV2("length([?value=='bar'])", 1),
            JMESPathCheckV2("length([?value=='bar2'])", 1)
        ])
        # show
        result = self.cmd('webapp config appsettings list -g {} -n {}'.format(resource_group, webapp_name)).get_output_in_json()
        s2 = next((x for x in result if x['name'] == 's2'))
        self.assertEqual(s2['name'], 's2')
        self.assertEqual(s2['slotSetting'], False)
        self.assertEqual(s2['value'], 'bar')
        self.assertEqual(set([x['name'] for x in result]), set(['s1', 's2', 's3']))
        # delete
        self.cmd('webapp config appsettings delete -g {} -n {} --setting-names s1 s2'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheckV2("length([?name=='s3'])", 1),
                     JMESPathCheckV2("length([?name=='s1'])", 0),
                     JMESPathCheckV2("length([?name=='s2'])", 0)])

        # hostnames
        self.cmd('webapp config hostname list -g {} --webapp-name {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheckV2('length(@)', 1),
                     JMESPathCheckV2('[0].name', '{0}.azurewebsites.net'.format(webapp_name))])

        # site connection string tests
        self.cmd('webapp config connection-string set -t mysql -g {} -n {} --settings c1="conn1" c2=conn2 '
                 '--slot-settings c3=conn3'.format(resource_group, webapp_name))
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheckV2('length([])', 3),
                     JMESPathCheckV2("[?name=='c1']|[0].slotSetting", False),
                     JMESPathCheckV2("[?name=='c1']|[0].value.type", 'MySql'),
                     JMESPathCheckV2("[?name=='c1']|[0].value.value", 'conn1'),
                     JMESPathCheckV2("[?name=='c2']|[0].slotSetting", False),
                     JMESPathCheckV2("[?name=='c3']|[0].slotSetting", True)])
        self.cmd('webapp config connection-string delete -g {} -n {} --setting-names c1 c3'
                 .format(resource_group, webapp_name))
        self.cmd('webapp config connection-string list -g {} -n {}'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheckV2('length([])', 1),
                     JMESPathCheckV2('[0].slotSetting', False),
                     JMESPathCheckV2('[0].name', 'c2')])

        # see deployment user; just make sure the command does return something
        self.assertTrue(self.cmd('webapp deployment user show').get_output_in_json()['type'])


class WebappScaleTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappScaleTest, self).__init__(__file__, test_method, resource_group='azurecli-webapp-scale')

    def test_webapp_scale(self):
        self.execute()

    def body(self):
        plan = 'webapp-scale-plan'
        # start with shared sku
        self.cmd('appservice plan create -g {} -n {} --sku SHARED'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'D1'),
            JMESPathCheck('sku.tier', 'Shared'),
            JMESPathCheck('sku.size', 'D1'),
            JMESPathCheck('sku.family', 'D'),
            JMESPathCheck('sku.capacity', 0)  # 0 means the default value: 1 instance
        ])
        # scale up
        self.cmd('appservice plan update -g {} -n {} --sku S2'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S2'),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.size', 'S2'),
            JMESPathCheck('sku.family', 'S')
        ])
        # scale down
        self.cmd('appservice plan update -g {} -n {} --sku B1'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B')
        ])
        # scale out
        self.cmd('appservice plan update -g {} -n {} --number-of-workers 2'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B'),
            JMESPathCheck('sku.capacity', 2)
        ])


class AppServiceBadErrorPolishTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(AppServiceBadErrorPolishTest, self).__init__(__file__, test_method, resource_group='clitest-error')
        self.resource_group2 = 'clitest-error2'
        self.webapp_name = 'webapp-error-test123'
        self.plan = 'webapp-error-plan'

    def test_appservice_error_polish(self):
        self.execute()

    def set_up(self):
        super(AppServiceBadErrorPolishTest, self).set_up()
        self.cmd('group create -n {} -l westus'.format(self.resource_group2))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(self.resource_group, self.plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, self.plan))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(self.resource_group2, self.plan))

    def tear_down(self):
        super(AppServiceBadErrorPolishTest, self).tear_down()
        self.cmd('group delete -n {} --yes'.format(self.resource_group2))

    def body(self):
        # we will try to produce an error by try creating 2 webapp with same name in different groups
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group2, self.webapp_name, self.plan),
                 allowed_exceptions='Website with given name {} already exists'.format(self.webapp_name))


# this test doesn't contain the ultimate verification which you need to manually load the frontpage in a browser
class LinuxWebappSceanrioTest(ScenarioTest):

    @ResourceGroupPreparer(location='japanwest')
    def test_linux_webapp(self, resource_group):
        runtime = 'node|6.4'
        plan = self.create_random_name(prefix='webapp-linux-plan', length=24)
        webapp = self.create_random_name(prefix='webapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            JMESPathCheckV2('reserved', True),  # this weird field means it is a linux
            JMESPathCheckV2('sku.name', 'S1'),
        ])
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(resource_group, webapp, plan, runtime), checks=[
            JMESPathCheckV2('name', webapp),
        ])
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheckV2('length([])', 1),
            JMESPathCheckV2('[0].name', webapp)
        ])
        self.cmd('webapp config set -g {} -n {} --startup-file {}'.format(resource_group, webapp, 'process.json'), checks=[
            JMESPathCheckV2('appCommandLine', 'process.json')
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


class WebappACRSceanrioTest(ScenarioTest):
    @ResourceGroupPreparer(location='japanwest')
    def test_acr_integration(self, resource_group):
        plan = self.create_random_name(prefix='acrtestplan', length=24)
        webapp = self.create_random_name(prefix='webappacrtest', length=24)
        runtime = 'node|6.4'
        acr_registry_name = webapp
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(resource_group, acr_registry_name))
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {} --runtime {}'.format(resource_group, webapp, plan, runtime))
        creds = self.cmd('acr credential show -n {}'.format(acr_registry_name)).get_output_in_json()
        self.cmd('webapp config container set -g {0} -n {1} --docker-custom-image-name {2}.azurecr.io/image-name:latest --docker-registry-server-url https://{2}.azurecr.io'.format(
            resource_group, webapp, acr_registry_name), checks=[
                JMESPathCheckV2("[?name=='DOCKER_REGISTRY_SERVER_USERNAME']|[0].value", creds['username'])
        ])


class WebappGitScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappGitScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-git4')

    def test_webapp_git(self):
        self.execute()

    def body(self):
        plan = 'webapp-git-plan5'
        webapp = 'web-git-test2'
        # You can create and use any repros with the 3 files under "./sample_web"
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, webapp, plan))
        self.cmd('webapp deployment source config -g {} -n {} --repo-url {} --branch {} --manual-integration'.format(self.resource_group, webapp, test_git_repo, 'master'), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('isMercurial', False),
            JMESPathCheck('branch', 'master')
        ])
        self.cmd('webapp deployment source show -g {} -n {}'.format(self.resource_group, webapp), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('isMercurial', False),
            JMESPathCheck('branch', 'master')
        ])
        self.cmd('webapp deployment source delete -g {} -n {}'.format(self.resource_group, webapp), checks=[
            JMESPathCheck('repoUrl', None)
        ])


class WebappSlotScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappSlotScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-slot')
        self.plan = 'webapp-slot-test-plan1'
        self.webapp = 'web-slot-test1'

    def test_webapp_slot(self):
        self.execute()

    def body(self):
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, self.plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp, plan_result['appServicePlanName']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        slot2 = 'dev'
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        test_php_version = '5.6'
        # create a few app-settings to test they can be cloned
        self.cmd('webapp config appsettings set -g {} -n {} --settings s1=v1 --slot-settings s2=v2'.format(self.resource_group, self.webapp))
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot), checks=[
            JMESPathCheck('name', slot)
        ])
        self.cmd('webapp deployment source config -g {} -n {} --repo-url {} --branch {} -s {} --manual-integration'.format(self.resource_group, self.webapp, test_git_repo, slot, slot), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('branch', slot)
        ])
        # swap with prod and verify the git branch also switched
        self.cmd('webapp deployment slot swap -g {} -n {} -s {}'.format(self.resource_group, self.webapp, slot))
        result = self.cmd('webapp config appsettings list -g {} -n {} -s {}'.format(self.resource_group, self.webapp, slot))
        self.assertEqual(set([x['name'] for x in result]), set(['s1']))
        # create a new slot by cloning from prod slot
        self.cmd('webapp config set -g {} -n {} --php-version {}'.format(self.resource_group, self.webapp, test_php_version))
        self.cmd('webapp deployment slot create -g {} -n {} --slot {} --configuration-source {}'.format(self.resource_group, self.webapp, slot2, self.webapp))
        self.cmd('webapp config show -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot2), checks=[
            JMESPathCheck("phpVersion", test_php_version),
        ])
        self.cmd('webapp config appsettings set -g {} -n {} --slot {} --settings s3=v3 --slot-settings s4=v4'.format(self.resource_group, self.webapp, slot2), checks=[
            JMESPathCheck("[?name=='s4']|[0].slotSetting", True),
            JMESPathCheck("[?name=='s3']|[0].slotSetting", False),
        ])

        self.cmd('webapp config connection-string set -g {} -n {} -t mysql --slot {} --settings c1=connection1 --slot-settings c2=connection2'.format(self.resource_group, self.webapp, slot2))
        # verify we can swap with non production slot
        self.cmd('webapp deployment slot swap -g {} -n {} --slot {} --target-slot {}'.format(self.resource_group, self.webapp, slot, slot2), checks=NoneCheck())
        result = self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot2))
        self.assertEqual(set([x['name'] for x in result]), set(['s1', 's4']))
        result = self.cmd('webapp config connection-string list -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot2))
        self.assertEqual(set([x['name'] for x in result]), set(['c2']))
        result = self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot))
        self.assertTrue(set(['s3']).issubset(set([x['name'] for x in result])))
        result = self.cmd('webapp config connection-string list -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot))
        self.assertEqual(set([x['name'] for x in result]), set(['c1']))
        self.cmd('webapp deployment slot list -g {} -n {}'.format(self.resource_group, self.webapp), checks=[
            JMESPathCheck("length([])", 2),
            JMESPathCheck("length([?name=='{}'])".format(slot2), 1),
            JMESPathCheck("length([?name=='{}'])".format(slot), 1),
        ])
        self.cmd('webapp deployment slot delete -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot), checks=NoneCheck())


class WebappSlotTrafficRouting(ScenarioTest):
    @ResourceGroupPreparer()
    def test_traffic_routing(self, resource_group):
        webapp = 'clitestwebtraffic'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, 'clitesttrafficplan')).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan_result['appServicePlanName']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        self.cmd('webapp traffic-routing set -g {} -n {} -d {}=15'.format(resource_group, webapp, slot), checks=[
            JMESPathCheckV2("[0].actionHostName", slot + '.azurewebsites.net'),
            JMESPathCheckV2("[0].reroutePercentage", 15.0)
        ])
        self.cmd('webapp traffic-routing show -g {} -n {}'.format(resource_group, webapp), checks=[
            JMESPathCheckV2("[0].actionHostName", slot + '.azurewebsites.net'),
            JMESPathCheckV2("[0].reroutePercentage", 15.0)
        ])
        self.cmd('webapp traffic-routing clear -g {} -n {}'.format(resource_group, webapp))


class WebappSlotSwapScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_webapp_slot_swap(self, resource_group):
        plan = 'slot-swap-plan'
        webapp = 'slot-swap-web'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan)).get_output_in_json()
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp, plan_result['appServicePlanName']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings s1=prod'.format(resource_group, webapp))
        # create an empty slot
        self.cmd('webapp deployment slot create -g {} -n {} --slot {}'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings set -g {} -n {} --slot-settings s1=slot --slot {}'.format(resource_group, webapp, slot))
        # swap with preview
        self.cmd('webapp deployment slot swap -g {} -n {} -s {} --action preview'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheckV2("[?name=='s1']|[0].value", 'prod')
        ])
        # complete the swap
        self.cmd('webapp deployment slot swap -g {} -n {} -s {}'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheckV2("[?name=='s1']|[0].value", 'slot')
        ])
        # reset
        self.cmd('webapp deployment slot swap -g {} -n {} -s {} --action reset'.format(resource_group, webapp, slot))
        self.cmd('webapp config appsettings list -g {} -n {} --slot {}'.format(resource_group, webapp, slot), checks=[
            JMESPathCheckV2("[?name=='s1']|[0]", None)
        ])


class WebappSSLCertTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappSSLCertTest, self).__init__(__file__, test_method, resource_group='test_cli_webapp_ssl')
        self.webapp_name = 'webapp-ssl-test123'

    def test_webapp_ssl(self):
        self.execute()

    def body(self):
        plan = 'webapp-ssl-test-plan'
        # Cert Generated using
        # https://docs.microsoft.com/en-us/azure/app-service-web/web-sites-configure-ssl-certificate#bkmk_ssopenssl
        pfx_file = os.path.join(TEST_DIR, 'server.pfx')
        cert_password = 'test'
        cert_thumbprint = 'DB2BA6898D0B330A93E7F69FF505C61EF39921B6'
        self.cmd('appservice plan create -g {} -n {} --sku B1'.format(self.resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan, self.location))
        self.cmd('webapp config ssl upload -g {} -n {} --certificate-file "{}" --certificate-password {}'.format(self.resource_group, self.webapp_name, pfx_file, cert_password), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint)
        ])
        self.cmd('webapp config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {}'.format(self.resource_group, self.webapp_name, cert_thumbprint, 'SNI'), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(self.webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(self.webapp_name), cert_thumbprint)
        ])
        self.cmd('webapp config ssl unbind -g {} -n {} --certificate-thumbprint {}'.format(self.resource_group, self.webapp_name, cert_thumbprint), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(self.webapp_name), 'Disabled'),
        ])
        self.cmd('webapp config ssl delete -g {} --certificate-thumbprint {}'.format(self.resource_group, cert_thumbprint))
        self.cmd('webapp delete -g {} -n {}'.format(self.resource_group, self.webapp_name))


class WebappBackupConfigScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappBackupConfigScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-backup')
        self.webapp_name = 'azurecli-webapp-backupconfigtest1'

    def test_webapp_backup_config(self):
        self.execute()

    def set_up(self):
        super(WebappBackupConfigScenarioTest, self).set_up()
        plan = 'webapp-backup-plan'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan_result['appServicePlanName']))

    def body(self):
        sas_url = 'https://azureclistore.blob.core.windows.net/sitebackups?st=2017-10-03T16%3A52%3A00Z&se=2017-10-04T16%3A52%3A00Z&sp=rwdl&sv=2016-05-31&sr=c&sig=YC1rbFebcY6Ku0xCI9Nj3C50%2Fk3e8%2BpdgB9W805Lz1s%3D'
        frequency = '1d'
        db_conn_str = 'Server=tcp:cli-backup.database.windows.net,1433;Initial Catalog=cli-db;Persist Security Info=False;User ID=cliuser;Password=cli!password1;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        retention_period = 5

        # set without databases
        self.cmd('webapp config backup update -g {} --webapp-name {} --frequency {} --container-url {}  --retain-one true --retention {}'
                 .format(self.resource_group, self.webapp_name, frequency, sas_url, retention_period), checks=NoneCheck())

        checks = [
            JMESPathCheck('backupSchedule.frequencyInterval', 1),
            JMESPathCheck('backupSchedule.frequencyUnit', 'Day'),
            JMESPathCheck('backupSchedule.keepAtLeastOneBackup', True),
            JMESPathCheck('backupSchedule.retentionPeriodInDays', retention_period)
        ]
        self.cmd('webapp config backup show -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=checks)

        # update with databases
        database_name = 'cli-db'
        database_type = 'SqlAzure'
        self.cmd('webapp config backup update -g {} --webapp-name {} --db-connection-string "{}" --db-name {} --db-type {} --retain-one true'
                 .format(self.resource_group, self.webapp_name, db_conn_str, database_name, database_type), checks=NoneCheck())

        checks = [
            JMESPathCheck('backupSchedule.frequencyInterval', 1),
            JMESPathCheck('backupSchedule.frequencyUnit', 'Day'),
            JMESPathCheck('backupSchedule.keepAtLeastOneBackup', True),
            JMESPathCheck('backupSchedule.retentionPeriodInDays', retention_period),
            JMESPathCheck('databases[0].connectionString', db_conn_str),
            JMESPathCheck('databases[0].databaseType', database_type),
            JMESPathCheck('databases[0].name', database_name)
        ]
        self.cmd('webapp config backup show -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=checks)

        # update frequency and retention only
        frequency = '18h'
        retention_period = 7
        self.cmd('webapp config backup update -g {} --webapp-name {} --frequency {} --retain-one false --retention {}'
                 .format(self.resource_group, self.webapp_name, frequency, retention_period), checks=NoneCheck())

        checks = [
            JMESPathCheck('backupSchedule.frequencyInterval', 18),
            JMESPathCheck('backupSchedule.frequencyUnit', 'Hour'),
            JMESPathCheck('backupSchedule.keepAtLeastOneBackup', False),
            JMESPathCheck('backupSchedule.retentionPeriodInDays', retention_period),
            JMESPathCheck('databases[0].connectionString', db_conn_str),
            JMESPathCheck('databases[0].databaseType', database_type),
            JMESPathCheck('databases[0].name', database_name)
        ]
        self.cmd('webapp config backup show -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=checks)


class WebappBackupRestoreScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappBackupRestoreScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-backup')
        self.webapp_name = 'azurecli-webapp-backuptest7'

    def test_webapp_backup_restore(self):
        self.execute()

    def set_up(self):
        super(WebappBackupRestoreScenarioTest, self).set_up()
        plan = 'webapp-backup-plan2'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan_result['appServicePlanName']))

    def body(self):
        sas_url = 'https://azureclistore.blob.core.windows.net/sitebackups?st=2017-10-03T16%3A52%3A00Z&se=2017-10-04T16%3A52%3A00Z&sp=rwdl&sv=2016-05-31&sr=c&sig=YC1rbFebcY6Ku0xCI9Nj3C50%2Fk3e8%2BpdgB9W805Lz1s%3D'
        db_conn_str = 'Server=tcp:cli-backup.database.windows.net,1433;Initial Catalog=cli-db;Persist Security Info=False;User ID=cliuser;Password=cli!password1;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        database_name = 'cli-db'
        database_type = 'SqlAzure'
        backup_name = 'mybackup'
        create_checks = [
            JMESPathCheck('backupItemName', backup_name),
            JMESPathCheck('storageAccountUrl', sas_url),
            JMESPathCheck('databases[0].connectionString', db_conn_str),
            JMESPathCheck('databases[0].databaseType', database_type),
            JMESPathCheck('databases[0].name', database_name)
        ]
        self.cmd('webapp config backup create -g {} --webapp-name {} --container-url "{}" --db-connection-string "{}" --db-name {} --db-type {} --backup-name {}'
                 .format(self.resource_group, self.webapp_name, sas_url, db_conn_str, database_name, database_type, backup_name), checks=create_checks)
        list_checks = [
            JMESPathCheck('[-1].backupItemName', backup_name),
            JMESPathCheck('[-1].storageAccountUrl', sas_url),
            JMESPathCheck('[-1].databases[0].connectionString', db_conn_str),
            JMESPathCheck('[-1].databases[0].databaseType', database_type),
            JMESPathCheck('[-1].databases[0].name', database_name)
        ]
        self.cmd('webapp config backup list -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=list_checks)
        time.sleep(900)  # Allow plenty of time for a backup to finish -- database backup takes a while (skipped in playback)
        self.cmd('webapp config backup restore -g {} --webapp-name {} --container-url "{}" --backup-name {} --db-connection-string "{}" --db-name {} --db-type {} --ignore-hostname-conflict --overwrite'
                 .format(self.resource_group, self.webapp_name, sas_url, backup_name, db_conn_str, database_name, database_type), checks=JMESPathCheck('name', self.webapp_name))


class FunctionAppWithPlanE2ETest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(FunctionAppWithPlanE2ETest, self).__init__(__file__, test_method, resource_group='azurecli-functionapp-e2e')

    def test_functionapp_asp_e2e(self):
        self.execute()

    def body(self):
        functionapp_name = 'functionapp-e2e3'
        plan = 'functionapp-e2e-plan'
        storage = 'functionappplanstorage'
        self.cmd('appservice plan create -g {} -n {}'.format(self.resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(self.resource_group))

        self.cmd('storage account create --name {} -g {} -l westus --sku Standard_LRS'.format(storage, self.resource_group))

        self.cmd('functionapp create -g {} -n {} -p {} -s {}'.format(self.resource_group, functionapp_name, plan, storage), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', functionapp_name),
            JMESPathCheck('hostNames[0]', functionapp_name + '.azurewebsites.net')
        ])

        self.cmd('functionapp delete -g {} -n {}'.format(self.resource_group, functionapp_name))


class FunctionAppWithConsumptionPlanE2ETest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='azurecli-functionapp-c-e2e', location='westus')
    @StorageAccountPreparer()
    def test_functionapp_consumption_e2e(self, resource_group, storage_account):
        functionapp_name = self.create_random_name('functionappconsumption', 40)

        self.cmd('functionapp create -g {} -n {} -c westus -s {}'
                 .format(resource_group, functionapp_name, storage_account)).assert_with_checks([
                     JMESPathCheckV2('state', 'Running'),
                     JMESPathCheckV2('name', functionapp_name),
                     JMESPathCheckV2('hostNames[0]', functionapp_name + '.azurewebsites.net')])

        self.cmd('functionapp delete -g {} -n {}'.format(resource_group, functionapp_name))


class FunctionAppOnLinux(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer()
    def test_functionapp_on_linux_asp(self, resource_group, storage_account):
        plan = self.create_random_name(prefix='funcapplinplan', length=24)
        functionapp = self.create_random_name(prefix='functionapp-linux', length=24)
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(resource_group, plan), checks=[
            JMESPathCheckV2('reserved', True),  # this weird field means it is a linux
            JMESPathCheckV2('sku.name', 'S1'),
        ])
        self.cmd('functionapp create -g {} -n {} --plan {} -s {}'.format(resource_group, functionapp, plan, storage_account), checks=[
            JMESPathCheckV2('name', functionapp)
        ])
        self.cmd('functionapp list -g {}'.format(resource_group), checks=[
            JMESPathCheckV2('length([])', 1),
            JMESPathCheckV2('[0].name', functionapp),
            JMESPathCheckV2('[0].kind', 'functionapp,linux')
        ])
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
            JMESPathCheckV2('unauthenticatedClientAction', None),
            JMESPathCheckV2('defaultProvider', None),
            JMESPathCheckV2('enabled', False),
            JMESPathCheckV2('tokenStoreEnabled', None),
            JMESPathCheckV2('runtimeVersion', None),
            JMESPathCheckV2('allowedExternalRedirectUrls', None),
            JMESPathCheckV2('tokenRefreshExtensionHours', None),
            JMESPathCheckV2('clientId', None),
            JMESPathCheckV2('clientSecret', None),
            JMESPathCheckV2('allowedAudiences', None),
            JMESPathCheckV2('issuer', None),
            JMESPathCheckV2('facebookAppId', None),
            JMESPathCheckV2('facebookAppSecret', None),
            JMESPathCheckV2('facebookOauthScopes', None)
        ])

        # update and verify
        result = self.cmd('webapp auth update -g {} -n {} --enabled true --action LoginWithFacebook '
                          '--token-store false --runtime-version v5.0 --token-refresh-extension-hours 7.2 '
                          '--aad-client-id aad_client_id --aad-client-secret aad_secret '
                          '--aad-allowed-token-audiences audience1 --aad-token-issuer-url issuer_url '
                          '--facebook-app-id facebook_id --facebook-app-secret facebook_secret '
                          '--facebook-oauth-scopes public_profile email'
                          .format(resource_group, webapp_name)).assert_with_checks([
                              JMESPathCheckV2('unauthenticatedClientAction', 'RedirectToLoginPage'),
                              JMESPathCheckV2('defaultProvider', 'Facebook'),
                              JMESPathCheckV2('enabled', True),
                              JMESPathCheckV2('tokenStoreEnabled', False),
                              JMESPathCheckV2('runtimeVersion', 'v5.0'),
                              JMESPathCheckV2('tokenRefreshExtensionHours', 7.2),
                              JMESPathCheckV2('clientId', 'aad_client_id'),
                              JMESPathCheckV2('clientSecret', 'aad_secret'),
                              JMESPathCheckV2('issuer', 'issuer_url'),
                              JMESPathCheckV2('facebookAppId', 'facebook_id'),
                              JMESPathCheckV2('facebookAppSecret', 'facebook_secret')]).get_output_in_json()

        self.assertIn('audience1', result['allowedAudiences'])
        self.assertIn('email', result['facebookOauthScopes'])
        self.assertIn('public_profile', result['facebookOauthScopes'])


class WebappUpdateTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_update')
    def test_webapp_update(self, resource_group):
        webapp_name = self.create_random_name('webapp-update-test', 40)
        plan_name = self.create_random_name('webapp-update-plan', 40)
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'
                 .format(resource_group, webapp_name, plan_name)).assert_with_checks([
                     JMESPathCheckV2('clientAffinityEnabled', True)])
        # testing update command with --set
        self.cmd('webapp update -g {} -n {} --client-affinity-enabled false --set tags.foo=bar'
                 .format(resource_group, webapp_name)).assert_with_checks([
                     JMESPathCheckV2('name', webapp_name),
                     JMESPathCheckV2('tags.foo', 'bar'),
                     JMESPathCheckV2('clientAffinityEnabled', False)])


class WebappZipDeployScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_webapp_zipDeploy')
    def test_deploy_zip(self, resource_group):
        webapp_name = self.create_random_name('webapp-zipDeploy-test', 40)
        plan_name = self.create_random_name('webapp-zipDeploy-plan', 40)
        zip_file = os.path.join(TEST_DIR, 'test.zip')
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        self.cmd('webapp deployment source config-zip -g {} -n {} --src "{}"'.format(resource_group, webapp_name, zip_file)).assert_with_checks([
            JMESPathCheckV2('status', 4),
            JMESPathCheckV2('deployer', 'Zip-Push'),
            JMESPathCheckV2('message', 'Created via zip push deployment'),
            JMESPathCheckV2('complete', True)])


class WebappImplictIdentityTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_assign_identity(self, resource_group):
        scope = '/subscriptions/{}/resourcegroups/{}'.format(self.get_subscription_id(), resource_group)
        role = 'Reader'
        plan_name = self.create_random_name('web-msi-plan', 20)
        webapp_name = self.create_random_name('web-msi', 20)
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan_name))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))
        guids = [uuid.UUID('88DAAF5A-EA86-4A68-9D45-477538D46667')]
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=guids, autospec=True):
            result = self.cmd('webapp assign-identity -g {} -n {} --role {} --scope {}'.format(resource_group, webapp_name, role, scope)).get_output_in_json()
        self.cmd('role assignment list -g {} --assignee {}'.format(resource_group, result['principalId']), checks=[
            JMESPathCheckV2('length([])', 1),
            JMESPathCheckV2('[0].properties.roleDefinitionName', role)
        ])


if __name__ == '__main__':
    unittest.main()
