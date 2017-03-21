# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.test_utils.vcr_test_base import VCRTestBase, JMESPathCheck, NoneCheck

class ServicePrincipalExpressCreateScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(ServicePrincipalExpressCreateScenarioTest, self).__init__(__file__, test_method)

    def test_sp_create_scenario(self):
        if self.playback:
            return #live-only test, will enable playback once resolve #635
        else:
            self.execute()

    def body(self):
        app_id_uri = 'http://azureclitest-graph'
        #create app through express option
        self.cmd('ad sp create-for-rbac -n {}'.format(app_id_uri), checks=[
            JMESPathCheck('name', app_id_uri)
            ])

        #show/list app
        self.cmd('ad app show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('identifierUris[0]', app_id_uri)
            ])
        self.cmd('ad app list --identifier-uri {}'.format(app_id_uri), checks=[
            JMESPathCheck('[0].identifierUris[0]', app_id_uri),
            JMESPathCheck('length([*])', 1)
            ])

        #show/list sp
        self.cmd('ad sp show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('servicePrincipalNames[0]', app_id_uri)
            ])
        self.cmd('ad sp list --spn {}'.format(app_id_uri), checks=[
            JMESPathCheck('[0].servicePrincipalNames[0]', app_id_uri),
            JMESPathCheck('length([*])', 1),
            ])
        self.cmd('ad sp reset-credentials -n {}'.format(app_id_uri), checks=[
            JMESPathCheck('name', app_id_uri)
            ])
        #cleanup        
        self.cmd('ad sp delete --id {}'.format(app_id_uri), None)
        self.cmd('ad sp list --spn {}'.format(app_id_uri), checks=NoneCheck())
        self.cmd('ad app delete --id {}'.format(app_id_uri), None)
        self.cmd('ad app list --identifier-uri {}'.format(app_id_uri), checks=NoneCheck())
         
class ApplicationSetScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(ApplicationSetScenarioTest, self).__init__(__file__, test_method)

    def test_application_set_scenario(self):
        self.execute()

    def body(self):
        app_id_uri = 'http://azureclitest-graph'
        display_name = 'azureclitest'

        #crerate app through general option
        self.cmd('ad app create --display-name {} --homepage {} --identifier-uris {}'.format(display_name, app_id_uri, app_id_uri),
                 checks=[JMESPathCheck('identifierUris[0]', app_id_uri)])

        #show/list app
        self.cmd('ad app show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('identifierUris[0]', app_id_uri)
            ])
        self.cmd('ad app list --display-name {}'.format(display_name), checks=[
            JMESPathCheck('[0].identifierUris[0]', app_id_uri),
            JMESPathCheck('length([*])', 1)
            ])
        
        #update app
        reply_uri = "http://azureclitest-replyuri"
        self.cmd('ad app update --id {} --reply-urls {}'.format(app_id_uri, reply_uri))      
        self.cmd('ad app show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('replyUrls[0]', reply_uri)
            ])      
        
        #delete app
        self.cmd('ad app delete --id {}'.format(app_id_uri))
        self.cmd('ad app list --identifier-uri {}'.format(app_id_uri), checks=NoneCheck())
         
