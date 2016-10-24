#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase,
                                                     JMESPathCheck, NoneCheck)
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
        result = self.cmd('appservice plan create -g {} -n {} --sku B1'.format(self.resource_group, plan))
        self.cmd('appservice plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1')
            ])
        self.cmd('appservice plan show -g {} -n {}'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan)
            ])
        #scale up
        self.cmd('appservice plan update  -g {} -n {} --sku S1'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.name', 'S1')
            ])

        result = self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, webapp_name, plan), checks=[
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('state', 'Running'),
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
            ])
        result = self.cmd('appservice web list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name + '.azurewebsites.net')
            ])
        result = self.cmd('appservice web show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('hostNames[0]', webapp_name + '.azurewebsites.net')
            ])

        self.cmd('appservice web git enable-local -g {} -n {}'.format(self.resource_group, webapp_name))
        result = self.cmd('appservice web git show-url -g {} -n {}'.format(self.resource_group, webapp_name))
        self.assertTrue(result['url'].endswith(webapp_name + '.git'))

        #turn on diagnostics
        test_cmd = ('appservice web log config -g {} -n {} --level verbose'.format(self.resource_group, webapp_name) + ' '
                    '--application-logging true --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem')
        self.cmd(test_cmd)
        result = self.cmd('appservice web config show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('detailedErrorLoggingEnabled', True),
            JMESPathCheck('httpLoggingEnabled', True),
            JMESPathCheck('scmType', 'LocalGit'),
            JMESPathCheck('requestTracingEnabled', True)
            #TODO: contact webapp team for where to retrieve 'level'
            ])

        self.cmd('appservice web stop -g {} -n {}'.format(self.resource_group, webapp_name))
        self.cmd('appservice web show -g {} -n {}'.format(self.resource_group, webapp_name), checks=[
            JMESPathCheck('state', 'Stopped'),
            JMESPathCheck('name', webapp_name)
            ])
        self.cmd('appservice web delete -g {} -n {}'.format(self.resource_group, webapp_name))
        #test empty service plan should be automatically deleted.
        result = self.cmd('appservice plan list -g {}'.format(self.resource_group), checks=[
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
        self.cmd('appservice plan create -g {} -n {} --sku B1'.format(self.resource_group, plan))
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, plan))

    def body(self):
        #site config testing

        #verify the baseline
        result = self.cmd('appservice web config show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=[
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
        result = self.cmd('appservice web config update -g {} -n {} --always-on true --auto-heal-enabled true --php-version 5.5 --net-framework-version v3.5 --python-version 3.4 --use-32bit-worker-process=false --web-sockets-enabled=true'.format(
            self.resource_group, self.webapp_name), checks=checks)
        result = self.cmd('appservice web config show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=checks)

        #site appsettings testing

        #update
        result = self.cmd('appservice web config appsettings update -g {} -n {} --settings s1=foo s2=bar s3=bar2'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('s1', 'foo'),
            JMESPathCheck('s2', 'bar'),
            JMESPathCheck('s3', 'bar2')
            ])
        result = self.cmd('appservice web config appsettings show -g {} -n {}'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('s1', 'foo'),
            JMESPathCheck('s2', 'bar'),
            JMESPathCheck('s3', 'bar2')
            ])

        #delete
        self.cmd('appservice web config appsettings delete -g {} -n {} --setting-names s1 s2'.format(self.resource_group, self.webapp_name))
        result = self.cmd('appservice web config appsettings show -g {} -n {}'.format(self.resource_group, self.webapp_name))
        self.assertTrue('s1' not in result)
        self.assertTrue('s2' not in result)
        self.assertTrue('s3' in result)

        self.cmd('appservice web config hostname list -g {} --webapp {}'.format(self.resource_group, self.webapp_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', '{0}/{0}.azurewebsites.net'.format(self.webapp_name))
            ])


class WebappScaleTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(WebappScaleTest, self).__init__(__file__, test_method)
        self.resource_group = 'azurecli-webapp-scale'

    def test_webapp_scale(self):
        self.execute()

    def body(self):
        plan = 'webapp-scale-plan'
        #start with shared sku
        self.cmd('appservice plan create -g {} -n {} --sku SHARED'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'D1'),
            JMESPathCheck('sku.tier', 'Shared'),
            JMESPathCheck('sku.size', 'D1'),
            JMESPathCheck('sku.family', 'D'),
            JMESPathCheck('sku.capacity', 0) #0 means the default value: 1 instance
            ])
        #scale up
        self.cmd('appservice plan update -g {} -n {} --sku S2'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'S2'),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.size', 'S2'),
            JMESPathCheck('sku.family', 'S')
            ])
        #scale down
        self.cmd('appservice plan update -g {} -n {} --sku B1'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B')
            ])
        #scale out
        self.cmd('appservice plan update -g {} -n {} --number-of-workers 2'.format(self.resource_group, plan), checks=[
            JMESPathCheck('sku.name', 'B1'),
            JMESPathCheck('sku.tier', 'Basic'),
            JMESPathCheck('sku.size', 'B1'),
            JMESPathCheck('sku.family', 'B'),
            JMESPathCheck('sku.capacity', 2)
            ])

class AppServiceBadErrorPolishTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(AppServiceBadErrorPolishTest, self).__init__(__file__, test_method)
        self.resource_group = 'clitest-error'
        self.resource_group2 = 'clitest-error2'
        self.webapp_name = 'webapp-error-test123'
        self.plan = 'webapp-error-plan'

    def test_appservice_error_polish(self):
        self.execute()

    def set_up(self):
        super(AppServiceBadErrorPolishTest, self).set_up()
        self.cmd('resource group create -n {} -l westus'.format(self.resource_group2))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(self.resource_group, self.plan))
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, self.webapp_name, self.plan))
        self.cmd('appservice plan create -g {} -n {} --sku b1'.format(self.resource_group2, self.plan))

    def tear_down(self):
        super(AppServiceBadErrorPolishTest, self).tear_down()
        self.cmd('resource group delete -n {}'.format(self.resource_group2))

    def body(self):
        # we will try to produce an error by try creating 2 webapp with same name in different groups
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group2, self.webapp_name, self.plan),
                 allowed_exceptions='Website with given name {} already exists'.format(self.webapp_name))

#this test doesn't contain the ultimate verification which you need to manually load the frontpage in a browser
class LinuxWebappSceanrioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(LinuxWebappSceanrioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli-webapp-linux2'

    def test_linux_webapp(self):
        self.execute()

    def body(self):
        plan = 'webapp-linux-plan'
        webapp = 'webapp-linux'
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux' .format(self.resource_group, plan), checks=[
            JMESPathCheck('reserved', True), #this weird field means it is a linux
            JMESPathCheck('sku.name', 'S1'),
            ])
        self.cmd('appservice web create -g {} -n {} --plan {}'.format(self.resource_group, webapp, plan), checks=[
            JMESPathCheck('name', webapp),
            ])
        self.cmd('appservice web config update -g {} -n {} --startup-file {}'.format(self.resource_group, webapp, 'process.json'), checks=[
            JMESPathCheck('appCommandLine', 'process.json')
            ])
        self.cmd('appservice web config container update -g {} -n {} --docker-custom-image-name {} --docker-registery-server-password {} --docker-registery-server-user {} --docker-registry-server-url {}'.format(
            self.resource_group, webapp, 'foo-image', 'foo-password', 'foo-user', 'foo-url'), checks=[
                JMESPathCheck('DOCKER_CUSTOM_IMAGE_NAME', 'foo-image'),
                JMESPathCheck('DOCKER_REGISTRY_SERVER_URL', 'foo-url'),
                JMESPathCheck('DOCKER_REGISTRY_SERVER_USERNAME', 'foo-user'),
                JMESPathCheck('DOCKER_REGISTRY_SERVER_PASSWORD', 'foo-password')
                ])
        self.cmd('appservice web config container list -g {} -n {} '.format(self.resource_group, webapp), checks=[
            JMESPathCheck('DOCKER_CUSTOM_IMAGE_NAME', 'foo-image'),
            JMESPathCheck('DOCKER_REGISTRY_SERVER_URL', 'foo-url'),
            JMESPathCheck('DOCKER_REGISTRY_SERVER_USERNAME', 'foo-user'),
            JMESPathCheck('DOCKER_REGISTRY_SERVER_PASSWORD', 'foo-password')
            ])
        self.cmd('appservice web config container delete -g {} -n {}'.format(self.resource_group, webapp))
        self.cmd('appservice web config container list -g {} -n {} '.format(self.resource_group, webapp), checks=NoneCheck())

