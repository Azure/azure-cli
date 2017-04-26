# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk import JMESPathCheck as JMESPathCheckV2
from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase,
                                                     JMESPathCheck, NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long


class WebappBasicE2ETest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappBasicE2ETest, self).__init__(__file__, test_method, resource_group='azurecli-webapp-e2e2')

    def test_webapp_e2e(self):
        self.execute()

    def body(self):
        webapp_name = 'webapp-e2e3'
        plan = 'webapp-e2e-plan'
        self.cmd('appservice plan create -g {} -n {}'.format(self.resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1')
        ])
        self.cmd('appservice plan list', checks=[
            JMESPathCheck("length([?name=='{}'])".format(plan), 1)
        ])
        self.cmd('appservice plan show -g {} -n {}'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan)
        ])
        # scale up
        self.cmd('appservice plan update -g {} -n {} --sku S1'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.name', 'S1')
        ])

        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, webapp_name, plan), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('appservice web list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name + '.azurewebsites.net')
        ])
        self.cmd('appservice web show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
        ])

        result = self.cmd('appservice web source-control config-local-git -g {} -n {}'.format(self.resource_group, webapp_name))
        self.assertTrue(result['url'].endswith(webapp_name + '.git'))
        self.cmd('appservice web source-control show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('repoUrl', 'https://{}.scm.azurewebsites.net'.format(webapp_name))
        ])

        # turn on diagnostics
        test_cmd = ('appservice web log config -g {} -n {} --level verbose'.format(self.resource_group, webapp_name) + ' '
                    '--application-logging true --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem')
        self.cmd(test_cmd)
        self.cmd('appservice web config show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorLoggingEnabled', True),
            JMESPathCheck('httpLoggingEnabled', True),
            JMESPathCheck('scmType', 'LocalGit'),
            JMESPathCheck('requestTracingEnabled', True)
            # TODO: contact webapp team for where to retrieve 'level'
        ])

        # show publish profile info
        result = self.cmd('appservice web deployment list-publishing-profiles -g {} -n {}'.format(self.resource_group, webapp_name))
        self.assertTrue(result[1]['publishUrl'].startswith('ftp://'))

        self.cmd('appservice web stop -g {} -n {}'.format(self.resource_group, webapp_name))
        self.cmd('appservice web show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', webapp_name)
        ])

        self.cmd('appservice web start -g {} -n {}'.format(self.resource_group, webapp_name))
        self.cmd('appservice web show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name)
        ])

        self.cmd('appservice web delete -g {} -n {}'.format(self.resource_group, webapp_name))
        # test empty service plan should be automatically deleted.
        self.cmd('appservice plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 0)
        ])


class WebappConfigureTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappConfigureTest, self).__init__(__file__, test_method, resource_group='azurecli-webapp-config')
        self.webapp_name = 'webapp-config-test'

    def test_webapp_config(self):
        self.execute()

    def set_up(self):
        super(WebappConfigureTest, self).set_up()
        plan = 'webapp-config-plan'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, plan))
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan_result['id']))

    def body(self):
        # site config testing

        # verify the baseline
        result = self.cmd('appservice web config show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('alwaysOn', False),
            JMESPathCheck('autoHealEnabled', False),
            JMESPathCheck('phpVersion', '5.6'),
            JMESPathCheck('netFrameworkVersion', 'v4.0'),
            JMESPathCheck('pythonVersion', ''),
            JMESPathCheck('use32BitWorkerProcess', True),
            JMESPathCheck('webSocketsEnabled', False)
        ])

        # update and verify
        checks = [
            JMESPathCheck('alwaysOn', True),
            JMESPathCheck('autoHealEnabled', True),
            JMESPathCheck('phpVersion', '7.0'),
            JMESPathCheck('netFrameworkVersion', 'v3.0'),
            JMESPathCheck('pythonVersion', '3.4'),
            JMESPathCheck('use32BitWorkerProcess', False),
            JMESPathCheck('webSocketsEnabled', True)
        ]
        self.cmd('appservice web config update -g {} -n {} --always-on true --auto-heal-enabled true --php-version 7.0 --net-framework-version v3.5 --python-version 3.4 --use-32bit-worker-process=false --web-sockets-enabled=true'.format(
            self.resource_group, self.webapp_name), checks=checks)
        self.cmd('appservice web config show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=checks)

        # site appsettings testing

        # update
        self.cmd('appservice web config appsettings update -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('s1', 'foo'),
            JMESPathCheck('s2', 'bar'),
            JMESPathCheck('s3', 'bar2')
        ])

        # show
        result = self.cmd('appservice web config appsettings show -g {} -n {}'.format(self.resource_group, self.webapp_name))
        s2 = next((x for x in result if x['name'] == 's2'))
        self.assertEqual(s2['name'], 's2')
        self.assertEqual(s2['slotSetting'], 'False')
        self.assertEqual(s2['value'], 'bar')
        self.assertEqual(set([x['name'] for x in result]), set(['s1', 's2', 's3', 'WEBSITE_NODE_DEFAULT_VERSION']))

        # delete
        self.cmd('appservice web config appsettings delete -g {} -n {} --setting-names s1 s2'.format(self.resource_group, self.webapp_name))
        result = self.cmd('appservice web config appsettings show -g {} -n {}'.format(self.resource_group, self.webapp_name))
        self.assertEqual(set([x['name'] for x in result]), set(['s3', 'WEBSITE_NODE_DEFAULT_VERSION']))

        # hostnames
        self.cmd('appservice web config hostname list -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', '{0}.azurewebsites.net'.format(self.webapp_name))
        ])

        # see deployment user
        result = self.cmd('appservice web deployment user show')
        self.assertTrue(result['type'])  # just make sure the command does return something


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
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, self.plan))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(self.resource_group2, self.plan))

    def tear_down(self):
        super(AppServiceBadErrorPolishTest, self).tear_down()
        self.cmd('group delete -n {} --yes'.format(self.resource_group2))

    def body(self):
        # we will try to produce an error by try creating 2 webapp with same name in different groups
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group2, self.webapp_name, self.plan),
                 allowed_exceptions='Website with given name {} already exists'.format(self.webapp_name))


# this test doesn't contain the ultimate verification which you need to manually load the frontpage in a browser
class LinuxWebappSceanrioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(LinuxWebappSceanrioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-linux2')

    def test_linux_webapp(self):
        self.execute()

    def body(self):
        plan = 'webapp-linux-plan'
        webapp = 'webapp-linux1'
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(self.resource_group, plan), checks=[
            JMESPathCheck('reserved', True),  # this weird field means it is a linux
            JMESPathCheck('sku.name', 'S1'),
        ])
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, webapp, plan), checks=[
            JMESPathCheck('name', webapp),
        ])
        self.cmd('appservice web config update -g {} -n {} --startup-file {}'.format(self.resource_group, webapp, 'process.json'), checks=[
            JMESPathCheck('appCommandLine', 'process.json')
        ])
        self.cmd('appservice web config container update -g {} -n {} --docker-custom-image-name {} --docker-registry-server-password {} --docker-registry-server-user {} --docker-registry-server-url {}'.format(
            self.resource_group, webapp, 'foo-image', 'foo-password', 'foo-user', 'foo-url'))
        result = self.cmd('appservice web config container show -g {} -n {} '.format(self.resource_group, webapp))
        self.assertEqual(set(x['name'] for x in result), set(['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME', 'DOCKER_CUSTOM_IMAGE_NAME', 'DOCKER_REGISTRY_SERVER_PASSWORD']))
        sample = next((x for x in result if x['name'] == 'DOCKER_REGISTRY_SERVER_URL'))
        self.assertEqual(sample, {'name': 'DOCKER_REGISTRY_SERVER_URL', 'slotSetting': 'False', 'value': 'foo-url'})
        self.cmd('appservice web config container delete -g {} -n {}'.format(self.resource_group, webapp))
        result2 = self.cmd('appservice web config container show -g {} -n {} '.format(self.resource_group, webapp), checks=NoneCheck())
        self.assertEqual(result2, [])


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
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, webapp, plan))

        self.cmd('appservice web source-control config -g {} -n {} --repo-url {} --branch {} --manual-integration'.format(self.resource_group, webapp, test_git_repo, 'master'), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('isMercurial', False),
            JMESPathCheck('branch', 'master')
        ])

        '''
        import time
        time.sleep(30) # 30 seconds should be enough for the deployment finished(Skipped under playback mode)

        import requests
        r = requests.get('http://{}.azurewebsites.net'.format(webapp))
        #verify the web page
        self.assertTrue('Hello world' in str(r.content))
        '''

        self.cmd('appservice web source-control show -g {} -n {}'.format(self.resource_group, webapp), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('isMercurial', False),
            JMESPathCheck('branch', 'master')
        ])
        self.cmd('appservice web source-control delete -g {} -n {}'.format(self.resource_group, webapp), checks=[
            JMESPathCheck('repoUrl', None)
        ])


class WebappSlotScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(WebappSlotScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-slot')
        self.plan = 'webapp-slot-test2-plan'
        self.webapp = 'web-slot-test2'

    def test_webapp_slot(self):
        self.execute()

    def body(self):
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, self.plan))
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp, plan_result['id']))
        # You can create and use any repros with the 3 files under "./sample_web" and with a 'staging 'branch
        slot = 'staging'
        slot2 = 'dev'
        test_git_repo = 'https://github.com/yugangw-msft/azure-site-test'
        test_node_version = '6.6.0'

        # create a few app-settings to test they can be cloned
        self.cmd('appservice web config appsettings update -g {} -n {} --settings s1=v1 --slot-settings s2=v2'.format(self.resource_group, self.webapp))

        # create an empty slot
        self.cmd('appservice web deployment slot create -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot), checks=[
            JMESPathCheck('name', slot)
        ])
        self.cmd('appservice web source-control config -g {} -n {} --repo-url {} --branch {} -s {} --manual-integration'.format(self.resource_group, self.webapp, test_git_repo, slot, slot), checks=[
            JMESPathCheck('repoUrl', test_git_repo),
            JMESPathCheck('branch', slot)
        ])

        import time
        import requests

        # comment out the git sync testing as it requires to pre-load a git token
        # the rest test steps should be sufficient to verify the slot functionalities.

        # verify the slot wires up the git repo/branch
        # time.sleep(30) # 30 seconds should be enough for the deployment finished(Skipped under playback mode)
        # r = requests.get('http://{}-{}.azurewebsites.net'.format(self.webapp, slot))
        # self.assertTrue('Staging' in str(r.content))

        # swap with prod and verify the git branch also switched
        self.cmd('appservice web deployment slot swap -g {} -n {} -s {}'.format(self.resource_group, self.webapp, slot))
        # time.sleep(30)  # 30 seconds should be enough for the slot swap finished(Skipped under playback mode)
        # r = requests.get('http://{}.azurewebsites.net'.format(self.webapp))
        # self.assertTrue('Staging' in str(r.content))
        result = self.cmd('appservice web config appsettings show -g {} -n {} -s {}'.format(self.resource_group, self.webapp, slot))
        self.assertEqual(set([x['name'] for x in result]), set(['WEBSITE_NODE_DEFAULT_VERSION', 's1']))

        # create a new slot by cloning from prod slot
        self.cmd('appservice web config update -g {} -n {} --node-version {}'.format(self.resource_group, self.webapp, test_node_version))
        self.cmd('appservice web deployment slot create -g {} -n {} --slot {} --configuration-source {}'.format(self.resource_group, self.webapp, slot2, self.webapp))
        self.cmd('appservice web config appsettings show -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot2), checks=[
            JMESPathCheck("length([])", 1),
            JMESPathCheck('[0].name', 'WEBSITE_NODE_DEFAULT_VERSION')
        ])
        self.cmd('appservice web config show -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot2), checks=[
            JMESPathCheck("nodeVersion", test_node_version),
        ])
        self.cmd('appservice web config appsettings update -g {} -n {} --slot {} --settings s3=v3 --slot-settings s4=v4'.format(self.resource_group, self.webapp, slot2))

        # verify we can swap with non production slot
        self.cmd('appservice web deployment slot swap -g {} -n {} --slot {} --target-slot {}'.format(self.resource_group, self.webapp, slot, slot2), checks=NoneCheck())
        result = self.cmd('appservice web config appsettings show -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot2))
        self.assertEqual(set([x['name'] for x in result]), set(['WEBSITE_NODE_DEFAULT_VERSION', 's1', 's4']))

        result = self.cmd('appservice web config appsettings show -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot))
        self.assertEqual(set([x['name'] for x in result]), set(['WEBSITE_NODE_DEFAULT_VERSION', 's3']))

        self.cmd('appservice web deployment slot list -g {} -n {}'.format(self.resource_group, self.webapp), checks=[
            JMESPathCheck("length([])", 2),
            JMESPathCheck("length([?name=='{}'])".format(slot2), 1),
            JMESPathCheck("length([?name=='{}'])".format(slot), 1),
        ])
        self.cmd('appservice web deployment slot delete -g {} -n {} --slot {}'.format(self.resource_group, self.webapp, slot), checks=NoneCheck())


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
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan, self.location))
        self.cmd('appservice web config ssl upload -g {} -n {} --certificate-file "{}" --certificate-password {}'.format(self.resource_group, self.webapp_name, pfx_file, cert_password), checks=[
            JMESPathCheck('thumbprint', cert_thumbprint)
        ])
        self.cmd('appservice web config ssl bind -g {} -n {} --certificate-thumbprint {} --ssl-type {}'.format(self.resource_group, self.webapp_name, cert_thumbprint, 'SNI'), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(self.webapp_name), 'SniEnabled'),
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].thumbprint".format(self.webapp_name), cert_thumbprint)
        ])
        self.cmd('appservice web config ssl unbind -g {} -n {} --certificate-thumbprint {}'.format(self.resource_group, self.webapp_name, cert_thumbprint), checks=[
            JMESPathCheck("hostNameSslStates|[?name=='{}.azurewebsites.net']|[0].sslState".format(self.webapp_name), 'Disabled'),
        ])
        self.cmd('appservice web config ssl delete -g {} --certificate-thumbprint {}'.format(self.resource_group, cert_thumbprint))
        self.cmd('appservice web delete -g {} -n {}'.format(self.resource_group, self.webapp_name))


class WebappBackupConfigScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappBackupConfigScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-backup')
        self.webapp_name = 'azurecli-webapp-backupconfigtest'

    def test_webapp_backup_config(self):
        self.execute()

    def set_up(self):
        super(WebappBackupConfigScenarioTest, self).set_up()
        plan = 'webapp-backup-plan'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, plan))
        self.cmd('appservice web create -g {} -n {} --plan {} -l {}'.format(self.resource_group, self.webapp_name, plan_result['id'], self.location))

    def body(self):
        sas_url = 'https://azureclistore.blob.core.windows.net/sitebackups?sv=2015-04-05&sr=c&sig=%2FjH1lEtbm3uFqtMI%2BfFYwgrntOs1qhGnpGv9uRibJ7A%3D&se=2017-02-14T04%3A53%3A28Z&sp=rwdl'
        frequency = '1d'
        db_conn_str = 'Server=tcp:cli-backup.database.windows.net,1433;Initial Catalog=cli-db;Persist Security Info=False;User ID=cliuser;Password=cli!password1;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        retention_period = 5

        # set without databases
        self.cmd('appservice web config backup update -g {} --webapp-name {} --frequency {} --container-url {}  --retain-one true --retention {}'
                 .format(self.resource_group, self.webapp_name, frequency, sas_url, retention_period), checks=NoneCheck())

        checks = [
            JMESPathCheck('backupSchedule.frequencyInterval', 1),
            JMESPathCheck('backupSchedule.frequencyUnit', 'Day'),
            JMESPathCheck('backupSchedule.keepAtLeastOneBackup', True),
            JMESPathCheck('backupSchedule.retentionPeriodInDays', retention_period)
        ]
        self.cmd('appservice web config backup show -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=checks)

        # update with databases
        database_name = 'cli-db'
        database_type = 'SqlAzure'
        self.cmd('appservice web config backup update -g {} --webapp-name {} --db-connection-string "{}" --db-name {} --db-type {} --retain-one true'
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
        self.cmd('appservice web config backup show -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=checks)

        # update frequency and retention only
        frequency = '18h'
        retention_period = 7
        self.cmd('appservice web config backup update -g {} --webapp-name {} --frequency {} --retain-one false --retention {}'
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
        self.cmd('appservice web config backup show -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=checks)


class WebappBackupRestoreScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappBackupRestoreScenarioTest, self).__init__(__file__, test_method, resource_group='cli-webapp-backup')
        self.webapp_name = 'azurecli-webapp-backuptest3'

    def test_webapp_backup_restore(self):
        self.execute()

    def set_up(self):
        super(WebappBackupRestoreScenarioTest, self).set_up()
        plan = 'webapp-backup-plan'
        plan_result = self.cmd('appservice plan create -g {} -n {} --sku S1'.format(self.resource_group, plan))
        self.cmd('appservice web create -g {} -n {} --plan {} -l {}'.format(self.resource_group, self.webapp_name, plan_result['id'], self.location))

    def body(self):
        sas_url = 'https://azureclistore.blob.core.windows.net/sitebackups?sv=2015-04-05&sr=c&sig=PJpE6swgZ6oZNFTlUz0GOIl87KKdvvgX7Ap8YXKHRp8%3D&se=2017-03-10T23%3A40%3A24Z&sp=rwdl'
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
        self.cmd('appservice web config backup create -g {} --webapp-name {} --container-url {} --db-connection-string "{}" --db-name {} --db-type {} --backup-name {}'
                 .format(self.resource_group, self.webapp_name, sas_url, db_conn_str, database_name, database_type, backup_name), checks=create_checks)

        list_checks = [
            JMESPathCheck('[-1].backupItemName', backup_name),
            JMESPathCheck('[-1].storageAccountUrl', sas_url),
            JMESPathCheck('[-1].databases[0].connectionString', db_conn_str),
            JMESPathCheck('[-1].databases[0].databaseType', database_type),
            JMESPathCheck('[-1].databases[0].name', database_name)
        ]
        self.cmd('appservice web config backup list -g {} --webapp-name {}'.format(self.resource_group, self.webapp_name), checks=list_checks)

        import time
        time.sleep(300)  # Allow plenty of time for a backup to finish -- database backup takes a while (skipped in playback)

        self.cmd('appservice web config backup restore -g {} --webapp-name {} --container-url {} --backup-name {} --db-connection-string "{}" --db-name {} --db-type {} --ignore-hostname-conflict --overwrite --debug'
                 .format(self.resource_group, self.webapp_name, sas_url, backup_name, db_conn_str, database_name, database_type), checks=JMESPathCheck('name', self.webapp_name))


if __name__ == '__main__':
    unittest.main()
