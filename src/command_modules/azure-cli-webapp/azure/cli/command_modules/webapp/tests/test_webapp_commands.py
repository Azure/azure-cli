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
        result = self.cmd('webapp plan create -g {} -n {} --tier Basic'.format(self.resource_group, plan))
        self.cmd('webapp plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', plan),
            JMESPathCheck('[0].sku.tier', 'Basic'),
            JMESPathCheck('[0].sku.name', 'B1')
            ])
        self.cmd('webapp plan show -g {} -n {}'.format(self.resource_group, plan), checks=[
            JMESPathCheck('name', plan)
            ])
        #scale up
        self.cmd('webapp plan update  -g {} -n {} --tier Standard'.format(self.resource_group, plan), checks=[
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
        self.assertTrue(result.endswith(webapp_name + '.git'))

        #turn on diagnostics
        test_cmd = ('webapp log set -g {} -n {} --level verbose'.format(self.resource_group, webapp_name) + ' '
                    '--application-logging on --detailed-error-messages on --failed-request-tracing on --web-server-logging filesystem')
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
        result = self.cmd('webapp plan list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 0)
            ])
