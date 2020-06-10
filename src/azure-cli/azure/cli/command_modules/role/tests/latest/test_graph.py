# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import mock
import unittest
import datetime
import dateutil
import dateutil.parser
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, AADGraphUserReplacer, MOCKED_USER_NAME
from knack.util import CLIError


class ServicePrincipalExpressCreateScenarioTest(ScenarioTest):

    @AllowLargeResponse(8192)
    def test_sp_create_scenario(self):
        self.kwargs['display_name'] = self.create_random_name('clisp-test-', 20)
        self.kwargs['app_id_uri'] = 'http://' + self.kwargs['display_name']
        # create app through express option
        self.cmd('ad sp create-for-rbac -n {display_name} --skip-assignment',
                 checks=self.check('name', '{app_id_uri}'))

        # show/list app
        self.cmd('ad app show --id {app_id_uri}',
                 checks=self.check('identifierUris[0]', '{app_id_uri}'))
        self.cmd('ad app list --identifier-uri {app_id_uri}', checks=[
            self.check('[0].identifierUris[0]', '{app_id_uri}'),
            self.check('length([*])', 1)
        ])
        self.assertTrue(len(self.cmd('ad app list').get_output_in_json()) <= 100)
        self.cmd('ad app list --show-mine')
        # show/list sp
        self.cmd('ad sp show --id {app_id_uri}',
                 checks=self.check('servicePrincipalNames[0]', '{app_id_uri}'))
        self.cmd('ad sp list --spn {app_id_uri}', checks=[
            self.check('[0].servicePrincipalNames[0]', '{app_id_uri}'),
            self.check('length([*])', 1),
        ])
        self.cmd('ad sp credential reset -n {app_id_uri}',
                 checks=self.check('name', '{app_id_uri}'))
        # cleanup
        self.cmd('ad sp delete --id {app_id_uri}')  # this would auto-delete the app as well
        self.cmd('ad sp list --spn {app_id_uri}',
                 checks=self.is_empty())
        self.cmd('ad app list --identifier-uri {app_id_uri}',
                 checks=self.is_empty())
        self.assertTrue(len(self.cmd('ad sp list').get_output_in_json()) <= 100)
        self.cmd('ad sp list --show-mine')

    def test_native_app_create_scenario(self):
        self.kwargs = {
            'native_app_name': self.create_random_name('cli-native-', 20),
            'required_access': json.dumps([
                {
                    "resourceAppId": "00000002-0000-0000-c000-000000000000",
                    "resourceAccess": [
                        {
                            "id": "5778995a-e1bf-45b8-affa-663a9f3f4d04",
                            "type": "Scope"
                        }
                    ]
                }]),
            'required_access2': json.dumps([
                {
                    "resourceAppId": "00000002-0000-0000-c000-000000000000",
                    "resourceAccess": [
                        {
                            "id": "311a71cc-e848-46a1-bdf8-97ff7156d8e6",
                            "type": "Scope"
                        }
                    ]
                }
            ])
        }
        result = self.cmd("ad app create --display-name {native_app_name} --native-app --required-resource-accesses '{required_access}'", checks=[
            self.check('publicClient', True),
            self.check('requiredResourceAccess|[0].resourceAccess|[0].id',
                       '5778995a-e1bf-45b8-affa-663a9f3f4d04')
        ]).get_output_in_json()
        self.kwargs['id'] = result['appId']
        try:
            self.cmd("ad app update --id {id} --required-resource-accesses '{required_access2}'")
            self.cmd('ad app show --id {id}', checks=[
                self.check('publicClient', True),
                self.check('requiredResourceAccess|[0].resourceAccess|[0].id',
                           '311a71cc-e848-46a1-bdf8-97ff7156d8e6')
            ])
        except Exception:
            self.cmd('ad app delete --id {id}')

    def test_web_app_no_identifier_uris_other_tenants_create_scenario(self):
        self.kwargs = {
            'web_app_name': self.create_random_name('cli-web-', 20)
        }

        self.cmd("ad app create --display-name {web_app_name} --available-to-other-tenants true", checks=[
            self.exists('appId')
        ])

    def test_app_create_idempotent(self):
        self.kwargs = {
            'display_name': self.create_random_name('app', 20)
        }
        app_id = None
        try:
            result = self.cmd("ad app create --display-name {display_name} --available-to-other-tenants true").get_output_in_json()
            app_id = result['appId']
            self.cmd("ad app create --display-name {display_name} --available-to-other-tenants false",
                     checks=self.check('availableToOtherTenants', False))
        finally:
            self.cmd("ad app delete --id " + app_id)

    def test_sp_show_exit_code(self):
        with self.assertRaises(SystemExit):
            self.assertEqual(self.cmd('ad sp show --id non-exist-sp-name').exit_code, 3)
            self.assertEqual(self.cmd('ad sp show --id 00000000-0000-0000-0000-000000000000').exit_code, 3)


class ApplicationSetScenarioTest(ScenarioTest):

    def test_application_set_scenario(self):
        name = self.create_random_name(prefix='cli-graph', length=14)
        self.kwargs.update({
            'app': 'http://' + name,
            'name': name,
            'app_roles': json.dumps([
                {
                    "allowedMemberTypes": [
                        "User"
                    ],
                    "description": "Approvers can mark documents as approved",
                    "displayName": "Approver",
                    "isEnabled": "true",
                    "value": "approver"
                }
            ])
        })
        app_id = None
        # create app through general option
        self.cmd('ad app create --display-name {name} --homepage {app} --identifier-uris {app}',
                 checks=self.check('identifierUris[0]', '{app}'))

        # set app password
        result = self.cmd('ad app credential reset --id {app} --append --password "test" --years 2').get_output_in_json()
        app_id = result['appId']
        self.assertTrue(app_id)
        self.kwargs['app_id'] = app_id

        try:
            # show by identifierUri
            self.cmd('ad app show --id {app}', checks=self.check('identifierUris[0]', '{app}'))
            # show by appId
            self.cmd('ad app show --id {app_id}', checks=self.check('appId', '{app_id}'))

            self.cmd('ad app list --display-name {name}', checks=[
                self.check('[0].identifierUris[0]', '{app}'),
                self.check('length([*])', 1)
            ])

            # update app
            self.kwargs['reply_uri'] = "http://azureclitest-replyuri"
            self.kwargs['reply_uri2'] = "http://azureclitest-replyuri2"
            self.cmd('ad app update --id {app} --reply-urls {reply_uri}')
            self.cmd('ad app show --id {app}',
                     checks=self.check('replyUrls[0]', '{reply_uri}'))

            # add and remove replyUrl
            self.cmd('ad app update --id {app} --add replyUrls {reply_uri2}')
            self.cmd('ad app show --id {app}', checks=self.check('length(replyUrls)', 2))
            self.cmd('ad app update --id {app} --remove replyUrls 1')
            self.cmd('ad app show --id {app}', checks=[
                self.check('length(replyUrls)', 1),
                self.check('replyUrls[0]', '{reply_uri2}')
            ])

            # update displayName
            name2 = self.create_random_name(prefix='cli-graph', length=14)
            self.kwargs['name2'] = name2
            self.cmd('ad app update --id {app} --display-name {name2}')
            self.cmd('ad app show --id {app}', checks=self.check('displayName', '{name2}'))

            # update homepage
            self.kwargs['homepage2'] = 'http://' + name2
            self.cmd('ad app update --id {app} --homepage {homepage2}')
            self.cmd('ad app show --id {app}', checks=self.check('homepage', '{homepage2}'))

            # invoke generic update
            self.cmd('ad app update --id {app} --set oauth2AllowUrlPathMatching=true')
            self.cmd('ad app show --id {app}',
                     checks=self.check('oauth2AllowUrlPathMatching', True))

            # update app_roles
            self.cmd("ad app update --id {app} --app-roles '{app_roles}'")
            self.cmd('ad app show --id {app}',
                     checks=self.check('length(appRoles)', 1))

            # delete app
            self.cmd('ad app delete --id {app}')
            app_id = None
            self.cmd('ad app list --identifier-uri {app}',
                     checks=self.is_empty())
        finally:
            if app_id:
                self.cmd("ad app delete --id " + app_id)

    def test_app_show_exit_code(self):
        with self.assertRaises(SystemExit):
            self.assertEqual(self.cmd('ad app show --id non-exist-identifierUris').exit_code, 3)
            self.assertEqual(self.cmd('ad app show --id 00000000-0000-0000-0000-000000000000').exit_code, 3)

    def test_application_optional_claims(self):
        name1 = self.create_random_name(prefix='cli-app-', length=14)
        name2 = self.create_random_name(prefix='cli-app-', length=14)
        self.kwargs.update({
            'name1': name1,
            'name2': name2,
            'optional_claims': json.dumps({
                "idToken": [
                    {
                        "name": "auth_time",
                        "source": None,
                        "essential": False
                    }
                ],
                "accessToken": [
                    {
                        "name": "email",
                        "source": None,
                        "essential": False
                    }
                ]
            })
        })
        self.cmd("ad app create --display-name {name1} --optional-claims '{optional_claims}'",
                 checks=[
                     self.check('displayName', '{name1}'),
                     self.check('length(optionalClaims.idToken)', 1),
                     self.check('length(optionalClaims.accessToken)', 1)
                 ])
        app_id = self.cmd('ad app create --display-name {name2}').get_output_in_json()['appId']
        self.kwargs.update({
            'app_id': app_id
        })
        self.cmd("ad app update --id {app_id} --optional-claims '{optional_claims}'")
        self.cmd('ad app show --id {app_id}',
                 checks=[
                     self.check('displayName', '{name2}'),
                     self.check('length(optionalClaims.idToken)', 1),
                     self.check('length(optionalClaims.accessToken)', 1)
                 ])


class CreateForRbacScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    def test_revoke_sp_for_rbac(self):
        self.kwargs['display_name'] = self.create_random_name(prefix='cli-graph', length=14)
        self.kwargs['name'] = 'http://' + self.kwargs['display_name']

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('ad sp create-for-rbac -n {display_name}')

            self.cmd('ad sp list --spn {name}')

            self.cmd('ad app list --identifier-uri {name}')

            result = self.cmd('role assignment list --assignee {name}').get_output_in_json()
            object_id = result[0]['principalId']

            self.cmd('ad sp delete --id {name}')

            result2 = self.cmd('role assignment list --all').get_output_in_json()
            self.assertFalse([a for a in result2 if a['id'] == object_id])

            self.cmd('ad sp list --spn {name}',
                     checks=self.check('length([])', 0))
            self.cmd('ad app list --identifier-uri {name}',
                     checks=self.check('length([])', 0))

    @AllowLargeResponse()
    def test_create_for_rbac_idempotent(self):
        self.kwargs['display_name'] = self.create_random_name(prefix='sp_', length=14)
        self.kwargs['name'] = 'http://' + self.kwargs['display_name']

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            try:
                self.cmd('ad sp create-for-rbac -n {display_name}')
                self.cmd('ad sp create-for-rbac -n {display_name}')
                result = self.cmd('ad sp list --spn {name}').get_output_in_json()
                self.assertEqual(1, len(result))
                result = self.cmd('role assignment list --assignee {name}').get_output_in_json()
                self.assertEqual(1, len(result))
            finally:
                self.cmd('ad sp delete --id {name}')


class GraphGroupScenarioTest(ScenarioTest):

    def test_graph_group_scenario(self):
        username = get_signed_in_user(self)
        if not username:
            return  # this test delete users which are beyond a SP's capacity, so quit...

        domain = username.split('@', 1)[1]
        self.kwargs = {
            'user1': 'deleteme1',
            'user2': 'deleteme2',
            'domain': domain,
            'new_mail_nick_name': 'deleteme11',
            'group': 'deleteme_g',
            'pass': 'Test1234!!'
        }
        self.recording_processors.append(AADGraphUserReplacer('@' + domain, '@example.com'))
        try:
            # create user1
            user1_result = self.cmd('ad user create --display-name {user1} --password {pass} --user-principal-name {user1}@{domain}').get_output_in_json()
            self.kwargs['user1_id'] = user1_result['objectId']

            # update user1
            self.cmd('ad user update --display-name {user1}_new --account-enabled false --id {user1}@{domain} --mail-nickname {new_mail_nick_name}')
            user1_update_result = self.cmd('ad user show --upn-or-object-id {user1}@{domain}', checks=[self.check("displayName", '{user1}_new'),
                                                                                                       self.check("accountEnabled", False)]).get_output_in_json()
            self.cmd('ad user update --id {user1}@{domain} --password {pass}')
            self.cmd('ad user update --id {user1}@{domain} --password {pass} --force-change-password-next-login true')
            with self.assertRaises(CLIError):
                self.cmd('ad user update --id {user1}@{domain} --force-change-password-next-login false')
            self.kwargs['user1_id'] = user1_update_result['objectId']

            # create user2
            user2_result = self.cmd('ad user create --display-name {user2} --password {pass} --user-principal-name {user2}@{domain}').get_output_in_json()
            self.kwargs['user2_id'] = user2_result['objectId']
            # create group
            group_result = self.cmd('ad group create --display-name {group} --mail-nickname {group}').get_output_in_json()
            self.kwargs['group_id'] = group_result['objectId']
            # add user1 into group
            self.cmd('ad group member add -g {group} --member-id {user1_id}',
                     checks=self.is_empty())
            # add user2 into group
            self.cmd('ad group member add -g {group} --member-id {user2_id}',
                     checks=self.is_empty())

            # show user's group memberships
            self.cmd('ad user get-member-groups --upn-or-object-id {user1_id}',
                     checks=self.check('[0].displayName', self.kwargs['group']))
            # show group
            self.cmd('ad group show -g {group}', checks=[
                self.check('objectId', '{group_id}'),
                self.check('displayName', '{group}')
            ])
            self.cmd('ad group show -g {group}',
                     checks=self.check('displayName', '{group}'))
            # list group
            self.cmd('ad group list --display-name {group}',
                     checks=self.check('[0].displayName', '{group}'))
            # show member groups
            self.cmd('ad group get-member-groups -g {group}',
                     checks=self.check('length([])', 0))
            # check user1 memebership
            self.cmd('ad group member check -g {group} --member-id {user1_id}',
                     checks=self.check('value', True))

            # check user2 memebership
            self.cmd('ad group member check -g {group} --member-id {user2_id}',
                     checks=self.check('value', True))

            self.cmd('ad group member list -g {group}', checks=[
                self.check("length([?displayName=='{user1}_new'])", 1),
                self.check("length([?displayName=='{user2}'])", 1),
                self.check("length([?displayName=='{user1}'])", 0),
                self.check("length([])", 2),
            ])
            # remove user1
            self.cmd('ad group member remove -g {group} --member-id {user1_id}')
            # check user1 memebership
            self.cmd('ad group member check -g {group} --member-id {user1_id}',
                     checks=self.check('value', False))
            # delete the group
            self.cmd('ad group delete -g {group}')
            self.cmd('ad group list',
                     checks=self.check("length([?displayName=='{group}'])", 0))
        finally:
            try:
                self.cmd('ad user delete --upn-or-object-id {user1_id}')
                self.cmd('ad user delete --upn-or-object-id {user2_id}')
                self.cmd('ad group delete -g {group}')
            except Exception:
                pass

    def test_graph_group_idempotent(self):
        account_info = self.cmd('account show').get_output_in_json()
        if account_info['user']['type'] == 'servicePrincipal':
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.kwargs = {
            'group': 'deleteme_g2',
        }
        try:
            self.cmd('ad group create --display-name {group} --mail-nickname {group}')
            self.cmd('ad group create --display-name {group} --mail-nickname {group}')
            self.cmd('ad group list',
                     checks=self.check("length([?displayName=='{group}'])", 1))
        finally:
            self.cmd('ad group delete -g {group}')

    def test_graph_group_show(self):
        account_info = self.cmd('account show').get_output_in_json()
        if account_info['user']['type'] == 'servicePrincipal':
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.kwargs = {
            'group1': 'show_group_1',
            'group11': 'show_group_11',
            'prefix': 'show_prefix',
            'prefix_group': 'show_prefix_group'
        }

        self.cmd('ad group create --display-name {group1} --mail-nickname {group1}')
        self.cmd('ad group create --display-name {group11} --mail-nickname {group11}')
        self.cmd('ad group create --display-name {prefix_group} --mail-nickname {prefix_group}')
        self.cmd('ad group show --group {group1}',
                 checks=self.check('displayName', '{group1}'))
        self.cmd('ad group show --group {group11}',
                 checks=self.check('displayName', '{group11}'))
        self.cmd('ad group show --group {prefix}',
                 checks=self.check('displayName', '{prefix_group}'))
        self.cmd('ad group delete -g {group1}')
        self.cmd('ad group delete -g {group11}')
        self.cmd('ad group delete -g {prefix}')


def get_signed_in_user(test_case):
    playback = not (test_case.is_live or test_case.in_recording)
    if playback:
        return MOCKED_USER_NAME
    else:
        account_info = test_case.cmd('account show').get_output_in_json()
        if account_info['user']['type'] != 'servicePrincipal':
            return account_info['user']['name']
    return None


class GraphOwnerScenarioTest(ScenarioTest):

    def test_graph_application_ownership(self):
        owner = get_signed_in_user(self)
        if not owner:
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.kwargs = {
            'owner': owner,
            'display_name': self.create_random_name('sp', 15)
        }
        self.recording_processors.append(AADGraphUserReplacer(owner, 'example@example.com'))
        try:
            self.kwargs['owner_object_id'] = self.cmd('ad user show --upn-or-object-id {owner}').get_output_in_json()['objectId']
            self.kwargs['app_id'] = self.cmd('ad sp create-for-rbac -n {display_name} --skip-assignment').get_output_in_json()['appId']
            self.cmd('ad app owner add --owner-object-id {owner_object_id} --id {app_id}')
            self.cmd('ad app owner add --owner-object-id {owner_object_id} --id {app_id}')  # test idempotent
            self.cmd('ad app owner list --id {app_id}', checks=self.check('[0].userPrincipalName', owner))
            self.cmd('ad app owner remove --owner-object-id {owner_object_id} --id {app_id}')
            self.cmd('ad app owner list --id {app_id}', checks=self.check('length([*])', 0))
        finally:
            if self.kwargs['app_id']:
                self.cmd('ad sp delete --id {app_id}')

    def test_graph_group_ownership(self):
        owner = get_signed_in_user(self)
        if not owner:
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.kwargs = {
            'owner': owner,
            'group': self.create_random_name('cli-grp', 15),
        }
        self.recording_processors.append(AADGraphUserReplacer(owner, 'example@example.com'))
        try:
            self.kwargs['owner_object_id'] = self.cmd('ad user show --upn-or-object-id {owner}').get_output_in_json()['objectId']
            self.kwargs['group_object_id'] = self.cmd('ad group create --display-name {group} --mail-nickname {group}').get_output_in_json()['objectId']
            self.cmd('ad group owner add -g {group_object_id} --owner-object-id {owner_object_id}')
            self.cmd('ad group owner add -g {group_object_id} --owner-object-id {owner_object_id}')
            self.cmd('ad group owner list -g {group_object_id}', checks=self.check('length([*])', 1))
        finally:
            if self.kwargs['group_object_id']:
                self.cmd('ad group delete -g ' + self.kwargs['group_object_id'])


class GraphAppCredsScenarioTest(ScenarioTest):
    def test_graph_app_cred_e2e(self):
        if not get_signed_in_user(self):
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.kwargs = {
            'display_name': self.create_random_name('cli-app-', 15),
            'display_name2': self.create_random_name('cli-app-', 15),
            'test_pwd': 'verysecretpwd123*'
        }
        self.kwargs['app'] = 'http://' + self.kwargs['display_name']
        self.kwargs['app2'] = 'http://' + self.kwargs['display_name2']
        app_id = None
        app_id2 = None
        try:
            result = self.cmd('ad sp create-for-rbac --name {display_name} --skip-assignment').get_output_in_json()
            app_id = result['appId']

            result = self.cmd('ad sp credential list --id {app}').get_output_in_json()
            key_id = result[0]['keyId']
            self.cmd('ad sp credential reset -n {app} --password {test_pwd} --append --credential-description newCred1')
            self.cmd('ad sp credential list --id {app}', checks=[
                self.check('length([*])', 2),
                self.check('[0].customKeyIdentifier', 'newCred1'),
                self.check('[1].customKeyIdentifier', 'rbac')  # auto configured by create-for-rbac
            ])
            self.cmd('ad sp credential delete --id {app} --key-id ' + key_id)
            result = self.cmd('ad sp credential list --id {app}', checks=self.check('length([*])', 1)).get_output_in_json()
            self.assertTrue(result[0]['keyId'] != key_id)

            # try the same through app commands
            result = self.cmd('ad app credential list --id {app}', checks=self.check('length([*])', 1)).get_output_in_json()
            key_id = result[0]['keyId']
            self.cmd('ad app credential reset --id {app} --password {test_pwd} --append --credential-description newCred2')
            result = self.cmd('ad app credential list --id {app}', checks=[
                self.check('length([*])', 2),
                self.check('[0].customKeyIdentifier', 'newCred2'),
                self.check('[1].customKeyIdentifier', 'newCred1')
            ])
            self.cmd('ad app credential delete --id {app} --key-id ' + key_id)
            self.cmd('ad app credential list --id {app}', checks=self.check('length([*])', 1))

            # try use --end-date
            self.cmd('ad sp credential reset -n {app} --password {test_pwd} --end-date "2100-12-31T11:59:59+00:00" --credential-description newCred3')
            self.cmd('ad app credential reset --id {app} --password {test_pwd} --end-date "2100-12-31" --credential-description newCred4')

            # ensure we can update other properties #7728
            self.cmd('ad app update --id {app} --set groupMembershipClaims=All')
            self.cmd('ad app show --id {app}', checks=self.check('groupMembershipClaims', 'All'))

            # ensure we can update SP's properties #5948
            self.cmd('az ad sp update --id {app} --set appRoleAssignmentRequired=true')
            self.cmd('az ad sp show --id {app}')

            result = self.cmd('ad sp create-for-rbac --name {display_name2} --skip-assignment --years 10').get_output_in_json()
            app_id2 = result['appId']
            result = self.cmd('ad sp credential list --id {app2}', checks=self.check('length([*])', 1)).get_output_in_json()
            diff = dateutil.parser.parse(result[0]['endDate']).replace(tzinfo=None) - datetime.datetime.utcnow()
            self.assertTrue(diff.days > 1)  # it is just a smoke test to verify the credential does get applied
        finally:
            if app_id:
                self.cmd('ad app delete --id ' + app_id)
            if app_id2:
                self.cmd('ad app delete --id ' + app_id2)


class GraphAppRequiredAccessScenarioTest(ScenarioTest):

    def test_graph_required_access_e2e(self):
        if not get_signed_in_user(self):
            return  # this test delete users which are beyond a SP's capacity, so quit...
        self.kwargs = {
            'display_name': self.create_random_name('cli-app-', 15),
            'graph_resource': '00000002-0000-0000-c000-000000000000',
            'target_api': 'a42657d6-7f20-40e3-b6f0-cee03008a62a',
            'target_api2': '311a71cc-e848-46a1-bdf8-97ff7156d8e6'
        }
        app_id = None
        try:
            result = self.cmd('ad sp create-for-rbac --name {display_name} --skip-assignment').get_output_in_json()
            self.kwargs['app_id'] = result['appId']
            self.cmd('ad app permission add --id {app_id} --api {graph_resource} --api-permissions {target_api}=Scope')
            self.cmd('ad app permission grant --id {app_id} --api {graph_resource}')
            permissions = self.cmd('ad app permission list --id {app_id}', checks=[
                self.check('length([*])', 1)
            ]).get_output_in_json()
            self.assertTrue(dateutil.parser.parse(permissions[0]['expiryTime']))  # verify it is a time
            self.cmd('ad app permission list-grants --id {app_id}', checks=self.check('length([*])', 1))
            self.cmd('ad app permission list-grants --id {app_id} --show-resource-name',
                     checks=self.check('[0].resourceDisplayName', "Windows Azure Active Directory"))
            self.cmd('ad app permission add --id {app_id} --api {graph_resource} --api-permissions {target_api2}=Scope')
            self.cmd('ad app permission grant --id {app_id} --api {graph_resource}')
            self.cmd('ad app permission delete --id {app_id} --api {graph_resource}')
            self.cmd('ad app permission list --id {app_id}', checks=self.check('length([*])', 0))
        finally:
            if app_id:
                self.cmd('ad app delete --id ' + app_id)
