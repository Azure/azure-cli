# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from unittest import mock
import unittest
import datetime
import dateutil
import dateutil.parser
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, AADGraphUserReplacer, MOCKED_USER_NAME
from knack.util import CLIError


class ServicePrincipalExpressCreateScenarioTest(ScenarioTest):

    @AllowLargeResponse(8192)
    def test_sp_create_scenario(self):
        self.kwargs['display_name'] = self.create_random_name('clisp-test-', 20)

        # create app through express option
        result = self.cmd('ad sp create-for-rbac -n {display_name} --skip-assignment',
                          checks=self.check('displayName', '{display_name}')).get_output_in_json()

        self.kwargs['app_id'] = result['appId']

        # show/list app
        self.cmd('ad app show --id {app_id}', checks=self.check('identifierUris', []))

        self.cmd('ad app list --app-id {app_id}', checks=[
            self.check('[0].identifierUris', []),
            self.check('length([*])', 1)
        ])
        self.assertTrue(len(self.cmd('ad app list').get_output_in_json()) <= 100)
        self.cmd('ad app list --show-mine')

        # show/list sp
        self.cmd('ad sp show --id {app_id}',
                 checks=self.check('servicePrincipalNames[0]', '{app_id}'))
        self.cmd('ad sp list --spn {app_id}', checks=[
            self.check('[0].servicePrincipalNames[0]', '{app_id}'),
            self.check('length([*])', 1),
        ])
        self.cmd('ad sp credential reset -n {app_id}',
                 checks=self.check('name', '{app_id}'))
        # cleanup
        self.cmd('ad sp delete --id {app_id}')  # this would auto-delete the app as well
        self.cmd('ad sp list --spn {app_id}',
                 checks=self.is_empty())
        self.cmd('ad app list --app-id {app_id}',
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

        # TODO: https://github.com/Azure/azure-cli/pull/13769 fails to work
        # Cert created with
        # openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 10000 -out certificate.pem
        self.kwargs['cert_file'] = """
MIIDazCCAlOgAwIBAgIUIp5vybhHfKN+ZKL28AntYKhlKXkwDQYJKoZIhvcNAQEL
BQAwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoM
GEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDAeFw0yMDA3MjIwNzE3NDdaFw00NzEy
MDgwNzE3NDdaMEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEw
HwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEB
AQUAA4IBDwAwggEKAoIBAQDMa00H+/p4RP4Eo//1J81Wowo4y1SKOJHbJ6T/lZ73
5FzFX52gdQ/7HalJOwQdbha78RPGA7bXxEmyEo+q3w+IMYzrqboX5S9yf0v1DZvj
a/VEMtUsq79d7NUUEd+smkuqDxDHFIkMeMM8cXy6tc+TPbc28BkQQiKbzOEZDwy4
HPd7FCqCwwcZtgxfxFQx5A2DkAXtT53zQD8k1zY4UQWhkKDcgvINzQfYxJmUbXqH
27MuJuejhpWLjmwEFCQtMJMrEv44YmlDzmL64iN5HFckO65ikV9fe9g9EcR5acSY
2bsO8WyFYzTffVXFpFF011Vi4d/U0h4wSwj5KLMYMHkfAgMBAAGjUzBRMB0GA1Ud
DgQWBBQxgpSKG7fwIHEopaRA10GB8Z8SOTAfBgNVHSMEGDAWgBQxgpSKG7fwIHEo
paRA10GB8Z8SOTAPBgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQAt
I5vbHGxVV3qRtd9PEFe9dUb9Yv9YIa5RUd5l795cgr6qyELfg3xTPZbNf1oUHpGX
NCfm1uqNTorIKOIEoTpA+STVwST/xcqzB6VjS31I/5IIrdK2NQenM+0DVJa+yGhX
+zI3+X3cO2YbyLSKBYqdMsqgnMS/ZC0NnrvigHgq2SC4Vzg8yz5rorjvLJ6ndeht
oWOtdCJKUTPihNh4e+GM2A7UNKdt5WKCiS/n/lShvm+8JEG2lXQmmxR6DOjdDyC4
/6tf7Ln7YoZZ0q6ICp04oMF6bvgGosdOkQATW4X97EmcfIBfHPX2w/Xn47np2rZr
lBMWCjI8gO6W8YQMu7AH""".replace('\n', '')

        result = self.cmd("ad app create --display-name {native_app_name} --key-value {cert_file}", checks=[
            self.check('length(keyCredentials)', 1)
        ])

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
    def test_create_for_rbac_no_role_assignment(self):
        # Verify no role assignment is created by default
        self.kwargs['display_name'] = self.create_random_name(prefix='cli-graph', length=14)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            result = self.cmd('ad sp create-for-rbac -n {display_name}').get_output_in_json()
            self.kwargs['app_id'] = result['appId']

            self.cmd('ad sp list --spn {app_id}',
                     checks=self.check('length([*])', 1))

            self.cmd('ad app list --app-id {app_id}',
                     checks=self.check('length([*])', 1))

            result = self.cmd('role assignment list --assignee {app_id}').get_output_in_json()

            # No role assignment
            self.assertFalse(result)

            self.cmd('ad sp delete --id {app_id}')
            self.cmd('ad sp list --spn {app_id}',
                     checks=self.check('length([])', 0))
            self.cmd('ad app list --app-id {app_id}',
                     checks=self.check('length([])', 0))

    @AllowLargeResponse()
    def test_create_for_rbac_with_role_assignment(self):
        self.kwargs['display_name'] = self.create_random_name(prefix='cli-graph', length=14)

        subscription_id = self.get_subscription_id()
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            result = self.cmd('ad sp create-for-rbac -n {display_name} --role Reader '
                              f'--scopes /subscriptions/{subscription_id}').get_output_in_json()
            self.kwargs['app_id'] = result['appId']

            self.cmd('ad sp list --spn {app_id}',
                     checks=self.check('length([*])', 1))

            self.cmd('ad app list --app-id {app_id}',
                     checks=self.check('length([*])', 1))

            result = self.cmd('role assignment list --assignee {app_id}').get_output_in_json()
            object_id = result[0]['principalId']

            self.cmd('ad sp delete --id {app_id}')

            result2 = self.cmd('role assignment list --all').get_output_in_json()
            self.assertFalse([a for a in result2 if a['id'] == object_id])

            self.cmd('ad sp list --spn {app_id}',
                     checks=self.check('length([])', 0))
            self.cmd('ad app list --app-id {app_id}',
                     checks=self.check('length([])', 0))

    @AllowLargeResponse()
    def test_create_for_rbac_idempotent(self):
        self.kwargs['display_name'] = self.create_random_name(prefix='sp_', length=14)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            try:
                result1 = self.cmd('ad sp create-for-rbac -n {display_name}').get_output_in_json()
                result2 = self.cmd('ad sp create-for-rbac -n {display_name}').get_output_in_json()
                self.assertEqual(result1['appId'], result2['appId'])

                self.kwargs['app_id'] = result1['appId']
                result = self.cmd('ad sp list --spn {app_id}').get_output_in_json()
                self.assertEqual(1, len(result))

                result = self.cmd('role assignment list --assignee {app_id}').get_output_in_json()
                self.assertEqual(1, len(result))
            finally:
                self.cmd('ad sp delete --id {app_id}')


class GraphGroupScenarioTest(ScenarioTest):

    def test_graph_group_scenario(self):
        username = get_signed_in_user(self)
        if not username:
            return  # this test delete users which are beyond a SP's capacity, so quit...

        domain = username.split('@', 1)[1]
        self.kwargs = {
            'user1': self.create_random_name(prefix='deleteme1', length=15),
            'user2': self.create_random_name(prefix='deleteme2', length=15),
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
            group_result = self.cmd('ad group create --display-name {group} --mail-nickname {group} --description {group}').get_output_in_json()
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
                self.check('displayName', '{group}'),
                self.check('description', '{group}')
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
            try:
                self.cmd('ad group delete -g {group}')
            except:
                pass

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

        try:
            result = self.cmd('ad sp create-for-rbac --name {display_name} --skip-assignment').get_output_in_json()
            self.kwargs['app_id'] = result['appId']

            result = self.cmd('ad sp credential list --id {app_id}').get_output_in_json()
            key_id = result[0]['keyId']
            self.cmd('ad sp credential reset -n {app_id} --password {test_pwd} --append --credential-description newCred1')
            self.cmd('ad sp credential list --id {app_id}', checks=[
                self.check('length([*])', 2),
                self.check('[0].customKeyIdentifier', 'newCred1'),
                self.check('[1].customKeyIdentifier', 'rbac')  # auto configured by create-for-rbac
            ])
            self.cmd('ad sp credential delete --id {app_id} --key-id ' + key_id)
            result = self.cmd('ad sp credential list --id {app_id}', checks=self.check('length([*])', 1)).get_output_in_json()
            self.assertTrue(result[0]['keyId'] != key_id)

            # try the same through app commands
            result = self.cmd('ad app credential list --id {app_id}', checks=self.check('length([*])', 1)).get_output_in_json()
            key_id = result[0]['keyId']
            self.cmd('ad app credential reset --id {app_id} --password {test_pwd} --append --credential-description newCred2')
            result = self.cmd('ad app credential list --id {app_id}', checks=[
                self.check('length([*])', 2),
                self.check('[0].customKeyIdentifier', 'newCred2'),
                self.check('[1].customKeyIdentifier', 'newCred1')
            ])
            self.cmd('ad app credential delete --id {app_id} --key-id ' + key_id)
            self.cmd('ad app credential list --id {app_id}', checks=self.check('length([*])', 1))

            # try use --end-date
            self.cmd('ad sp credential reset -n {app_id} --password {test_pwd} --end-date "2100-12-31T11:59:59+00:00" --credential-description newCred3')
            self.cmd('ad app credential reset --id {app_id} --password {test_pwd} --end-date "2100-12-31" --credential-description newCred4')

            # ensure we can update other properties #7728
            self.cmd('ad app update --id {app_id} --set groupMembershipClaims=All')
            self.cmd('ad app show --id {app_id}', checks=self.check('groupMembershipClaims', 'All'))

            # ensure we can update SP's properties #5948
            self.cmd('az ad sp update --id {app_id} --set appRoleAssignmentRequired=true')
            self.cmd('az ad sp show --id {app_id}')

            result = self.cmd('ad sp create-for-rbac --name {display_name2} --skip-assignment --years 10').get_output_in_json()
            self.kwargs['app_id2'] = result['appId']

            result = self.cmd('ad sp credential list --id {app_id2}', checks=self.check('length([*])', 1)).get_output_in_json()
            diff = dateutil.parser.parse(result[0]['endDate']).replace(tzinfo=None) - datetime.datetime.utcnow()
            self.assertTrue(diff.days > 1)  # it is just a smoke test to verify the credential does get applied
        finally:
            if self.kwargs.get('app_id'):
                self.cmd('ad app delete --id {app_id}')
            if self.kwargs.get('app_id2'):
                self.cmd('ad app delete --id {app_id2}')


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
            app_id = result['appId']
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
                try:
                    self.cmd('ad app delete --id ' + app_id)
                except:
                    pass

    @AllowLargeResponse()
    def test_graph_permission(self):
        if not get_signed_in_user(self):
            return
        self.kwargs = {
            'display_name': self.create_random_name('cli-app-', 15),
            # AD Graph
            'ad_graph_resource': '00000002-0000-0000-c000-000000000000',
            # Delegated Directory.AccessAsUser.All
            'ad_target_api': 'a42657d6-7f20-40e3-b6f0-cee03008a62a',
            # Delegated User.Read
            'ad_target_api2': '311a71cc-e848-46a1-bdf8-97ff7156d8e6',
            # MS Graph
            'ms_graph_resource': '00000003-0000-0000-c000-000000000000',
            # Delegated Directory.AccessAsUser.All
            'ms_target_api': '0e263e50-5827-48a4-b97c-d940288653c7',
            # Delegated User.Read
            'ms_target_api2': 'e1fe6dd8-ba31-4d61-89e7-88639da4683d'
        }
        app_id = None
        try:
            result = self.cmd('ad sp create-for-rbac --name {display_name} --skip-assignment').get_output_in_json()
            self.kwargs['app_id'] = result['appId']
            app_id = result['appId']

            # Test add permissions using a list
            self.cmd('ad app permission add --id {app_id} --api {ad_graph_resource} '
                     '--api-permissions {ad_target_api}=Scope {ad_target_api2}=Scope')
            self.cmd('ad app permission add --id {app_id} --api {ms_graph_resource} '
                     '--api-permissions {ms_target_api}=Scope {ms_target_api2}=Scope')
            permissions = self.cmd('ad app permission list --id {app_id}', checks=[self.check('length([*])', 2)]).get_output_in_json()
            # Sample result (required_resource_access):
            # [
            #     {
            #         "additionalProperties": null,
            #         "expiryTime": "",
            #         "resourceAccess": [
            #             {
            #                 "additionalProperties": null,
            #                 "id": "a42657d6-7f20-40e3-b6f0-cee03008a62a",
            #                 "type": "Scope"
            #             },
            #             {
            #                 "additionalProperties": null,
            #                 "id": "311a71cc-e848-46a1-bdf8-97ff7156d8e6",
            #                 "type": "Scope"
            #             }
            #         ],
            #         "resourceAppId": "00000002-0000-0000-c000-000000000000"
            #     },
            #     {
            #         "additionalProperties": null,
            #         "expiryTime": "",
            #         "resourceAccess": [
            #             {
            #                 "additionalProperties": null,
            #                 "id": "0e263e50-5827-48a4-b97c-d940288653c7",
            #                 "type": "Scope"
            #             },
            #             {
            #                 "additionalProperties": null,
            #                 "id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d",
            #                 "type": "Scope"
            #             }
            #         ],
            #         "resourceAppId": "00000003-0000-0000-c000-000000000000"
            #     }
            # ]

            ad_target_api_object = {
                "additionalProperties": None,
                "id": self.kwargs['ad_target_api'],
                "type": "Scope"}
            ad_target_api2_object = {
                "additionalProperties": None,
                "id": self.kwargs['ad_target_api2'],
                "type": "Scope"}
            ms_target_api_object = {
                "additionalProperties": None,
                "id": self.kwargs['ms_target_api'],
                "type": "Scope"}
            ms_target_api2_object = {
                "additionalProperties": None,
                "id": self.kwargs['ms_target_api2'],
                "type": "Scope"}

            def get_required_resource_access(required_resource_access_list, resource_app_id):
                """Search for the RequiredResourceAccess from required_resource_access(list) by resourceAppId."""
                return next(
                    filter(lambda a: a['resourceAppId'] == resource_app_id, required_resource_access_list), None)

            ad_api = get_required_resource_access(permissions, self.kwargs['ad_graph_resource'])
            ms_api = get_required_resource_access(permissions, self.kwargs['ms_graph_resource'])

            # Check initial `permission add` is correct
            self.assertEqual(ad_api['resourceAccess'], [ad_target_api_object, ad_target_api2_object])
            self.assertEqual(ms_api['resourceAccess'], [ms_target_api_object, ms_target_api2_object])

            # Test delete 1 api-permission (ResourceAccess) ms_target_api.
            self.cmd('ad app permission delete --id {app_id} --api {ms_graph_resource} --api-permissions {ms_target_api}')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            ms_api = get_required_resource_access(permissions, self.kwargs['ms_graph_resource'])
            # ms_target_api (ResourceAccess) is deleted and ms_target_api2 (ResourceAccess) remains
            self.assertEqual(ms_api['resourceAccess'], [ms_target_api2_object])

            # Test delete 1 api-permission ms_target_api2 (ResourceAccess)
            self.cmd('ad app permission delete --id {app_id} --api {ms_graph_resource} --api-permissions {ms_target_api2}')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            ms_api = get_required_resource_access(permissions, self.kwargs['ms_graph_resource'])
            # ms_graph_resource (RequiredResourceAccess) is removed automatically
            self.assertIsNone(ms_api)

            # Add ms_target_api and ms_target_api2 back
            self.cmd('ad app permission add --id {app_id} --api {ms_graph_resource} '
                     '--api-permissions {ms_target_api}=Scope {ms_target_api2}=Scope')
            # Delete both ms_target_api and ms_target_api2 at the same time
            self.cmd('ad app permission delete --id {app_id} --api {ms_graph_resource} --api-permissions {ms_target_api} {ms_target_api2}')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            ms_api = get_required_resource_access(permissions, self.kwargs['ms_graph_resource'])
            # ms_graph_resource (RequiredResourceAccess) is removed automatically
            self.assertIsNone(ms_api)

            # Test delete 1 api ad_graph_resource (RequiredResourceAccess)
            self.cmd('ad app permission delete --id {app_id} --api {ad_graph_resource}')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            ad_api = get_required_resource_access(permissions, self.kwargs['ad_graph_resource'])
            self.assertIsNone(ad_api)

            # Test delete non-existing api
            self.cmd('ad app permission delete --id {app_id} --api 11111111-0000-0000-c000-000000000000')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            self.assertEqual(permissions, [])

            # Test delete api permission from non-existing api
            self.cmd('ad app permission delete --id {app_id} --api 11111111-0000-0000-c000-000000000000 --api-permissions {ms_target_api} {ms_target_api2}')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            self.assertEqual(permissions, [])

            # Test delete non-existing api permission from existing api
            self.cmd('ad app permission add --id {app_id} --api {ms_graph_resource} '
                     '--api-permissions {ms_target_api}=Scope {ms_target_api2}=Scope')
            self.cmd('ad app permission delete --id {app_id} --api {ms_graph_resource} --api-permissions 22222222-0000-0000-c000-000000000000')
            permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
            ms_api = get_required_resource_access(permissions, self.kwargs['ms_graph_resource'])
            self.assertEqual(ms_api['resourceAccess'], [ms_target_api_object, ms_target_api2_object])
        finally:
            if app_id:
                try:
                    self.cmd('ad app delete --id ' + app_id)
                except:
                    pass
