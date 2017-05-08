# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json

from azure.cli.testsdk import JMESPathCheck as JMESPathCheck2
from azure.cli.testsdk import NoneCheck as NoneCheck2
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.vcr_test_base import VCRTestBase, JMESPathCheck, NoneCheck


class ServicePrincipalExpressCreateScenarioTest(VCRTestBase):
    def __init__(self, test_method):
        super(ServicePrincipalExpressCreateScenarioTest, self).__init__(__file__, test_method)

    def test_sp_create_scenario(self):
        if self.playback:
            return  # live-only test, will enable playback once resolve #635
        else:
            self.execute()

    def body(self):
        app_id_uri = 'http://azureclitest-graph'
        # create app through express option
        self.cmd('ad sp create-for-rbac -n {}'.format(app_id_uri), checks=[
            JMESPathCheck('name', app_id_uri)
        ])

        # show/list app
        self.cmd('ad app show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('identifierUris[0]', app_id_uri)
        ])
        self.cmd('ad app list --identifier-uri {}'.format(app_id_uri), checks=[
            JMESPathCheck('[0].identifierUris[0]', app_id_uri),
            JMESPathCheck('length([*])', 1)
        ])

        # show/list sp
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
        # cleanup
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

        # crerate app through general option
        self.cmd('ad app create --display-name {} --homepage {} --identifier-uris {}'
                 .format(display_name, app_id_uri, app_id_uri),
                 checks=[JMESPathCheck('identifierUris[0]', app_id_uri)])

        # show/list app
        self.cmd('ad app show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('identifierUris[0]', app_id_uri)
        ])
        self.cmd('ad app list --display-name {}'.format(display_name), checks=[
            JMESPathCheck('[0].identifierUris[0]', app_id_uri),
            JMESPathCheck('length([*])', 1)
        ])

        # update app
        reply_uri = "http://azureclitest-replyuri"
        self.cmd('ad app update --id {} --reply-urls {}'.format(app_id_uri, reply_uri))
        self.cmd('ad app show --id {}'.format(app_id_uri), checks=[
            JMESPathCheck('replyUrls[0]', reply_uri)
        ])

        # delete app
        self.cmd('ad app delete --id {}'.format(app_id_uri))
        self.cmd('ad app list --identifier-uri {}'.format(app_id_uri), checks=NoneCheck())


class GraphGroupScenarioTest(ScenarioTest):

    def test_graph_group_scenario(self):
        self.user1 = 'deleteme1'
        self.user1 = 'deleteme2'
        upn = self.cmd('account show --query "user.name" -o tsv').output
        _, domain = upn.split('@', 1)
        user1 = 'deleteme1'
        user2 = 'deleteme2'
        group = 'deleteme_g'
        password = 'Test1234!!'
        try:
            # create user1
            user1_result = json.loads(self.cmd('ad user create --display-name {0} --password {1} --user-principal-name {0}@{2}'.format(user1, password, domain)).output)
            # create user2
            user2_result = json.loads(self.cmd('ad user create --display-name {0} --password {1} --user-principal-name {0}@{2}'.format(user2, password, domain)).output)
            # create group
            group_result = json.loads(self.cmd('ad group create --display-name {0} --mail-nickname {0}'.format(group)).output)
            # add user1 into group
            self.cmd('ad group member add -g {} --member-id {}'.format(group, user1_result['objectId']), checks=NoneCheck2())
            # add user2 into group
            self.cmd('ad group member add -g {} --member-id {}'.format(group, user2_result['objectId']), checks=NoneCheck2())
            # show group
            self.cmd('ad group show -g ' + group, checks=[
                JMESPathCheck2('objectId', group_result['objectId']),
                JMESPathCheck2('displayName', group)
            ])
            self.cmd('ad group show -g ' + group_result['objectId'], checks=[
                JMESPathCheck2('displayName', group)
            ])
            # list group
            self.cmd('ad group list --display-name ' + group, checks=[
                JMESPathCheck2('[0].displayName', group)
            ])
            # show member groups
            self.cmd('ad group get-member-groups -g ' + group, checks=[
                JMESPathCheck2('length([])', 0)
            ])
            # check user1 memebership
            self.cmd('ad group member check -g {} --member-id {}'.format(group, user1_result['objectId']), checks=[
                JMESPathCheck2('value', True)
            ])
            # check user2 memebership
            self.cmd('ad group member check -g {} --member-id {}'.format(group, user2_result['objectId']), checks=[
                JMESPathCheck2('value', True)
            ])
            # list memebers
            self.cmd('ad group member list -g ' + group, checks=[
                JMESPathCheck2("length([?displayName=='{}'])".format(user1), 1),
                JMESPathCheck2("length([?displayName=='{}'])".format(user2), 1),
                JMESPathCheck2("length([])", 2),
            ])
            # remove user1
            self.cmd('ad group member remove -g {} --member-id {}'.format(group, user1_result['objectId']))
            # check user1 memebership
            self.cmd('ad group member check -g {} --member-id {}'.format(group, user1_result['objectId']), checks=[
                JMESPathCheck2('value', False)
            ])
            # delete the group
            self.cmd('ad group delete -g ' + group)
            self.cmd('ad group list', checks=[
                JMESPathCheck2("length([?displayName=='{}'])".format(group), 0)
            ])
        finally:
            self.cmd('ad user delete --upn-or-object-id ' + user1_result['objectId'])
            self.cmd('ad user delete --upn-or-object-id ' + user2_result['objectId'])
