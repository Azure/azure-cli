#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.utils.vcr_test_base import (ResourceGroupVCRTestBase,
                                                JMESPathCheck)

#pylint: disable=line-too-long

class WebappBasicE2ETest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappBasicE2ETest, self).__init__(__file__, test_method)
        self.resource_group = 'azurecli-webapp-e2e'

    def test_webapp_e2e(self):
        self.execute()

    def body(self):
        webapp_name = 'webapp-e2e'
        plan = 'webapp-e2e-plan'
        result = self.cmd('app-service-plan create -g {} -n {} --tier B1'.format(self.resource_group, plan))
        self.cmd('app-service-plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1')
            ])
        self.cmd('app-service-plan show -g {} -n {}'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan)
            ])
        #scale up
        self.cmd('app-service-plan update  -g {} -n {} --tier S1'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.name', 'S1')
            ])

        result = self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, webapp_name, plan), checks=[
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
            ])
        result = self.cmd('webapp list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name + '.azurewebsites.net')
            ])
        result = self.cmd('webapp show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
            ])

        self.cmd('webapp git enable-local -g {} -n {}'.format(self.resource_group, webapp_name))
        result = self.cmd('webapp git show-url -g {} -n {}'.format(self.resource_group, webapp_name))
        self.assertTrue(result['url'].endswith(webapp_name + '.git'))

        #turn on diagnostics
        test_cmd = ('webapp log set -g {} -n {} --level verbose'.format(self.resource_group, webapp_name) + ' '
                    '--application-logging true --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem')
        self.cmd(test_cmd)
        result = self.cmd('webapp config show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorLoggingEnabled', True),
            JMESPathCheck('httpLoggingEnabled', True),
            JMESPathCheck('scmType', 'LocalGit'),
            JMESPathCheck('requestTracingEnabled', True)
            #TODO: contact webapp team for where to retrieve 'level'
            ])

        self.cmd('webapp stop -g {} -n {}'.format(self.resource_group, webapp_name))
        self.cmd('webapp show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', webapp_name)
            ])
        self.cmd('webapp delete -g {} -n {}'.format(self.resource_group, webapp_name))
        #test empty service plan should be automatically deleted.
        result = self.cmd('app-service-plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 0)
            ])

class WebappConfigureTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappConfigureTest, self).__init__(__file__, test_method)
        self.resource_group = 'azurecli-webapp-config'
        self.webapp_name = 'webapp-config-test'

    def test_webapp_config(self):
        self.execute()

    def set_up(self):
        super(WebappConfigureTest, self).set_up()
        plan = 'webapp-config-plan'
        self.cmd('app-service-plan create -g {} -n {} --tier B1'.format(self.resource_group, plan))
        self.cmd('webapp create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan))

    def body(self):
        #site config testing

        #verify the baseline
        result = self.cmd('webapp config show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('alwaysOn', False),
            JMESPathCheck('autoHealEnabled', False),
            JMESPathCheck('phpVersion', '5.4'),
            JMESPathCheck('netFrameworkVersion', 'v4.0'),
            JMESPathCheck('pythonVersion', ''),
            JMESPathCheck('use32BitWorkerProcess', True),
            JMESPathCheck('webSocketsEnabled', False)
            ])

        #update and verify
        checks = [
            JMESPathCheck('alwaysOn', True),
            JMESPathCheck('autoHealEnabled', True),
            JMESPathCheck('phpVersion', '5.5'),
            JMESPathCheck('netFrameworkVersion', 'v3.0'),
            JMESPathCheck('pythonVersion', '3.4'),
            JMESPathCheck('use32BitWorkerProcess', False),
            JMESPathCheck('webSocketsEnabled', True)
            ]
        result = self.cmd('webapp config update -g {} -n {} --always-on true --auto-heal-enabled true --php-version 5.5 --net-framework-version v3.5 --python-version 3.4 --use-32bit-worker-process=false --web-sockets-enabled=true'.format(
            self.resource_group, self.webapp_name), checks=checks)
        result = self.cmd('webapp config show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=checks)

        #site appsettings testing

        #update
        result = self.cmd('webapp config appsettings update -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('s1', 'foo'),
            JMESPathCheck('s2', 'bar'),
            JMESPathCheck('s3', 'bar2')
            ])
        result = self.cmd('webapp config appsettings show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('s1', 'foo'),
            JMESPathCheck('s2', 'bar'),
            JMESPathCheck('s3', 'bar2')
            ])

        #delete
        self.cmd('webapp config appsettings delete -g {} -n {} --setting-names s1 s2'.format(self.resource_group, self.webapp_name))
        result = self.cmd('webapp config appsettings show -g {} -n {}'.format(self.resource_group, self.webapp_name))
        self.assertTrue('s1' not in result)
        self.assertTrue('s2' not in result)
        self.assertTrue('s3' in result)
