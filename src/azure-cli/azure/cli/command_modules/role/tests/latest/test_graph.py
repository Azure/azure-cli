# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import os
import sys
from unittest import mock
import unittest
import datetime
import dateutil
import dateutil.parser
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import MOCKED_TENANT_ID
from azure.cli.testsdk import ScenarioTest, MSGraphNameReplacer, MOCKED_USER_NAME
from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer


# This test example is from
# https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-add-app-roles-in-azure-ad-apps#example-user-app-role
TEST_APP_ROLES = '''[
    {
        "allowedMemberTypes": [
            "User"
        ],
        "displayName": "Writer",
        "id": "d1c2ade8-0000-0000-0000-6d06b947c66f",
        "isEnabled": true,
        "description": "Writers Have the ability to create tasks.",
        "value": "Writer"
    },
    {
        "allowedMemberTypes": [
            "Application"
        ],
        "displayName": "ConsumerApps",
        "id": "47fbb575-0000-0000-0000-0f7a6c30beac",
        "isEnabled": true,
        "description": "Consumer apps have access to the consumer data.",
        "value": "Consumer"
    }
]
'''

# This test example is from
# https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-optional-claims#configuring-optional-claims
TEST_OPTIONAL_CLAIMS = '''{
    "idToken": [
        {
            "name": "auth_time",
            "essential": false
        }
    ],
    "accessToken": [
        {
            "name": "ipaddr",
            "essential": false
        }
    ],
    "saml2Token": [
        {
            "name": "upn",
            "essential": false
        },
        {
            "name": "extension_ab603c56068041afb2f6832e2a17e237_skypeId",
            "source": "user",
            "essential": false
        }
    ]
}
'''

TEST_REQUIRED_RESOURCE_ACCESS = '''[
    {
        "resourceAccess": [
            {
                "id": "41094075-9dad-400e-a0bd-54e686782033",
                "type": "Scope"
            }
        ],
        "resourceAppId": "797f4846-ba00-4fd7-ba43-dac1f8f63013"
    },
    {
        "resourceAccess": [
            {
                "id": "c79f8feb-a9db-4090-85f9-90d820caa0eb",
                "type": "Scope"
            },
            {
                "id": "18a4783c-866b-4cc7-a460-3d5e5662c884",
                "type": "Role"
            }
        ],
        "resourceAppId": "00000003-0000-0000-c000-000000000000"
    }
]
'''

# This test example is from
# https://docs.microsoft.com/en-us/azure/active-directory/develop/workload-identity-federation-create-trust-github?tabs=microsoft-graph
TEST_FEDERATED_IDENTITY_CREDENTIAL = '''{
    "name": "Testing",
    "issuer": "https://token.actions.githubusercontent.com/",
    "subject": "repo:octo-org/octo-repo:environment:Production",
    "description": "Testing",
    "audiences": [
        "api://AzureADTokenExchange"
    ]
}
'''


# TODO: https://github.com/Azure/azure-cli/pull/13769 fails to work
# Cert created with
# openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 10000 -out certificate.pem
TEST_CERTIFICATE = """
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


class GraphScenarioTestBase(ScenarioTest):

    def tearDown(self):
        # If self.kwargs contains appId, try best to delete the app.
        for k, v in self.kwargs.items():
            if k.startswith('app_id'):
                try:
                    object_id = self.cmd("ad app show --id " + v).get_output_in_json()['id']
                    self.cmd("ad app delete --id " + v)
                    # Permanently delete item
                    # TODO: Add native commands for deleted items
                    self.cmd("az rest --method DELETE "
                             "--url https://graph.microsoft.com/v1.0/directory/deletedItems/" + object_id)
                except:
                    pass
        super().tearDown()

    def _create_app(self):
        self.kwargs['display_name'] = self.create_random_name(prefix='azure-cli-test', length=30)
        result = self.cmd('ad app create --display-name {display_name}').get_output_in_json()
        self.kwargs['app_id'] = result['appId']

    def _create_sp(self):
        self.kwargs['display_name'] = self.create_random_name(prefix='azure-cli-test', length=30)
        result = self.cmd('ad app create --display-name {display_name}').get_output_in_json()
        self.kwargs['app_id'] = result['appId']
        self.cmd('ad sp create --id {app_id}').get_output_in_json()

    def _get_signed_in_user(self):
        account_info = self.cmd('account show').get_output_in_json()
        if account_info['user']['type'] == 'user':
            return account_info['user']['name']
        return None

    def _test_credential(self, object_type):
        """Test app/sp credential commands. Make sure app_id has been configured in self.kwargs."""
        self.kwargs['object_type'] = object_type

        # Test password
        self.cmd('ad {object_type} credential reset --id {app_id} --append --years 2 --display-name key1',
                 checks=self.check('appId', '{app_id}'))

        result = self.cmd('ad {object_type} credential list --id {app_id}',
                          checks=self.check('length([*])', 1)).get_output_in_json()
        key_id = result[0]['keyId']
        self.cmd('ad {object_type} credential reset --id {app_id} --append --display-name key2')
        self.cmd('ad {object_type} credential list --id {app_id}', checks=[
            self.check('length([*])', 2),
            # Graph API reverses the order of insertion
            self.check('[0].displayName', 'key2'),
            self.check('[1].displayName', 'key1')
        ])
        self.cmd('ad {object_type} credential delete --id {app_id} --key-id ' + key_id)
        self.cmd('ad {object_type} credential list --id {app_id}', checks=self.check('length([*])', 1))

        # try use --end-date
        self.cmd('ad {object_type} credential reset --id {app_id} --end-date "2100-12-31T11:59:59+00:00"')
        self.cmd('ad {object_type} credential list --id {app_id}',
                 checks=self.check('[0].endDateTime', '2100-12-31T11:59:59Z'))

        self.cmd('ad {object_type} credential reset --id {app_id} --end-date "2100-12-31"')
        self.cmd('ad {object_type} credential list --id {app_id}',
                 checks=self.check('[0].endDateTime', '2100-12-31T00:00:00Z'))

    def _test_federated_credential(self, object_type):
        self.kwargs['object_type'] = object_type
        self.kwargs['parameters'] = TEST_FEDERATED_IDENTITY_CREDENTIAL
        self.kwargs['name'] = 'Testing'

        # Create credential
        result = self.cmd("ad {object_type} federated-credential create --id {app_id} --parameters '{parameters}'",
                          checks=[self.check('name', '{name}')]).get_output_in_json()
        self.kwargs['credential_id'] = result['id']

        # List credential
        self.cmd("ad {object_type} federated-credential list --id {app_id}",
                 checks=[self.check('length(@)', 1)])

        # Show credential with credential ID
        self.cmd("ad {object_type} federated-credential show --id {app_id} --credential-id {credential_id}",
                 checks=[self.check('name', '{name}')])
        # Show with credential name
        self.cmd("ad {object_type} federated-credential show --id {app_id} --credential-id {name}",
                 checks=[self.check('name', '{name}')])

        # Update credential's subject
        update_subject = "repo:octo-org/octo-repo:environment:Staging"
        self.kwargs['update_json'] = json.dumps({'subject': update_subject})
        self.cmd("ad {object_type} federated-credential update --id {app_id} --credential-id {credential_id} "
                 "--parameters '{update_json}'")
        self.cmd("ad {object_type} federated-credential show --id {app_id} --credential-id {credential_id}",
                 checks=self.check('subject', update_subject))

        # Delete credential
        self.cmd("ad {object_type} federated-credential delete --id {app_id} --credential-id {credential_id}")
        self.cmd("ad {object_type} federated-credential list --id {app_id}",
                 checks=[self.check('length(@)', 0)])


class ApplicationScenarioTest(GraphScenarioTestBase):

    def test_app_scenario(self):
        """
        - Test creating application with its properties.
        - Test creating application first and update its properties.
        """
        display_name = self.create_random_name(prefix='azure-cli-test', length=30)

        # identifierUris must be on verified domain
        # https://docs.microsoft.com/en-us/azure/active-directory/develop/security-best-practices-for-app-registration#appid-uri-configuration
        self.kwargs.update({
            'display_name': display_name,
            'identifier_uri': f'api://{display_name}',
            'homepage': 'https://myapp.com/',
            'web_redirect_uri_1': 'http://localhost/webtest1',
            'web_redirect_uri_2': 'http://localhost/webtest2',
            'public_client_redirect_uri_1': 'http://localhost/publicclienttest1',
            'public_client_redirect_uri_2': 'http://localhost/publicclienttest2',
            'key_value': TEST_CERTIFICATE,
            'app_roles': TEST_APP_ROLES,
            'optional_claims': TEST_OPTIONAL_CLAIMS,
            'required_resource_accesses': TEST_REQUIRED_RESOURCE_ACCESS,
        })

        # Create
        result = self.cmd(
            'ad app create --display-name {display_name} '
            '--identifier-uris {identifier_uri} '
            '--is-fallback-public-client True '
            '--sign-in-audience AzureADMultipleOrgs '
            # web
            '--web-home-page-url {homepage} '
            '--web-redirect-uris {web_redirect_uri_1} {web_redirect_uri_2} '
            '--enable-access-token-issuance true --enable-id-token-issuance true '
            # publicClient
            '--public-client-redirect-uris {public_client_redirect_uri_1} {public_client_redirect_uri_2} '
            # keyCredentials
            '--key-value {key_value} '
            # JSON properties
            "--app-roles '{app_roles}' "
            "--optional-claims '{optional_claims}' "
            "--required-resource-accesses '{required_resource_accesses}'",
            checks=[
                self.check('displayName', '{display_name}'),
                self.check('identifierUris[0]', '{identifier_uri}'),
                self.check('isFallbackPublicClient', True),
                self.check('signInAudience', 'AzureADMultipleOrgs'),
                self.check('web.homePageUrl', '{homepage}'),
                self.check('web.redirectUris[0]', '{web_redirect_uri_1}'),
                self.check('web.redirectUris[1]', '{web_redirect_uri_2}'),
                self.check('web.implicitGrantSettings.enableIdTokenIssuance', True),
                self.check('web.implicitGrantSettings.enableAccessTokenIssuance', True),
                self.check('publicClient.redirectUris[0]', '{public_client_redirect_uri_1}'),
                self.check('publicClient.redirectUris[1]', '{public_client_redirect_uri_2}'),
                self.check('length(keyCredentials)', 1),
                self.check('length(appRoles)', 2),
                self.check('length(optionalClaims)', 3),
                self.check('length(requiredResourceAccess)', 2)
            ]).get_output_in_json()

        self.kwargs['app_id'] = result['appId']
        self.cmd('ad app delete --id {app_id}')
        self.cmd('ad app show --id {app_id}', expect_failure=True)

        # Create, then update
        display_name_2 = self.create_random_name(prefix='azure-cli-test', length=30)
        display_name_3 = self.create_random_name(prefix='azure-cli-test', length=30)
        self.kwargs.update({
            'display_name_2': display_name_2,
            'display_name_3': display_name_3,
            'identifier_uri_3': f'api://{display_name_3}',
        })

        # Graph cannot create app with same identifierUris even after deleting the previous one. Still confirming with
        # service team.
        result = self.cmd('ad app create --display-name {display_name_2}').get_output_in_json()
        self.kwargs['app_id'] = result['appId']

        self.cmd(
            'ad app update --id {app_id} --display-name {display_name_3} '
            '--identifier-uris {identifier_uri_3} '
            '--is-fallback-public-client True '
            # signInAudience can't be PATCHed currently due to service issue. PATCH first fails with 404, then 500
            # '--sign-in-audience AzureADMultipleOrgs '
            # web
            '--web-home-page-url {homepage} '
            '--web-redirect-uris {web_redirect_uri_1} {web_redirect_uri_2} '
            '--enable-access-token-issuance true --enable-id-token-issuance true '
            # keyCredentials
            '--key-value {key_value} '
            # publicClient
            '--public-client-redirect-uris {public_client_redirect_uri_1} {public_client_redirect_uri_2} '
            "--app-roles '{app_roles}' "
            "--optional-claims '{optional_claims}' "
            "--required-resource-accesses '{required_resource_accesses}'"
        )
        self.cmd(
            'ad app show --id {app_id}',
            checks=[
                self.check('displayName', '{display_name_3}'),
                self.check('identifierUris[0]', '{identifier_uri_3}'),
                self.check('isFallbackPublicClient', True),
                # self.check('signInAudience', 'AzureADMultipleOrgs'),
                self.check('web.homePageUrl', '{homepage}'),
                # redirectUris doesn't preserve item order.
                # self.check('web.redirectUris[0]', '{web_redirect_uri_1}'),
                # self.check('web.redirectUris[1]', '{web_redirect_uri_2}'),
                self.check('length(web.redirectUris)', 2),
                self.check('web.implicitGrantSettings.enableIdTokenIssuance', True),
                self.check('web.implicitGrantSettings.enableAccessTokenIssuance', True),
                # self.check('publicClient.redirectUris[0]', '{public_client_redirect_uri_1}'),
                # self.check('publicClient.redirectUris[1]', '{public_client_redirect_uri_2}'),
                self.check('length(publicClient.redirectUris)', 2),
                self.check('length(keyCredentials)', 1),
                self.check('length(appRoles)', 2),
                self.check('length(optionalClaims)', 3),
                self.check('length(requiredResourceAccess)', 2)
            ]).get_output_in_json()

        # Update with generic update
        self.cmd('ad app update --id {app_id} --set isDeviceOnlyAuthSupported=true')
        self.cmd('ad app show --id {app_id}', checks=self.check('isDeviceOnlyAuthSupported', True))

        self.cmd('ad app delete --id {app_id}')
        self.cmd('ad app show --id {app_id}', expect_failure=True)

    def test_app_create_idempotent(self):
        self.kwargs = {
            'display_name': self.create_random_name('app', 20)
        }
        result = self.cmd("ad app create --display-name {display_name} --is-fallback-public-client true").get_output_in_json()
        self.kwargs['app_id'] = result['appId']
        self.cmd("ad app create --display-name {display_name} --is-fallback-public-client false",
                 checks=[self.check('isFallbackPublicClient', False),
                         self.check('appId', '{app_id}')])

    def test_app_resolution(self):
        """Test application can be resolved with identifierUris, appId, or id."""
        display_name = self.create_random_name(prefix='azure-cli-test', length=30)
        self.kwargs.update({
            'display_name': display_name,
            'identifier_uri': f'api://{display_name}'
        })

        app = self.cmd('ad app create --display-name {display_name} '
                       '--identifier-uris {identifier_uri}').get_output_in_json()

        self.kwargs['app_id'] = app['appId']
        self.kwargs['id'] = app['id']

        # Show with appId
        self.cmd('ad app show --id {app_id}', checks=[self.check('displayName', '{display_name}')])
        # Show with id
        self.cmd('ad app show --id {id}', checks=[self.check('displayName', '{display_name}')])
        # Show with identifierUris
        self.cmd('ad app show --id {identifier_uri}', checks=[self.check('displayName', '{display_name}')])

        self.cmd('ad app delete --id {app_id}')

    def test_app_show_exit_code(self):
        with self.assertRaises(SystemExit):
            self.assertEqual(self.cmd('ad app show --id non-exist-identifierUris').exit_code, 3)
            self.assertEqual(self.cmd('ad app show --id 00000000-0000-0000-0000-000000000000').exit_code, 3)

    def test_app_credential(self):
        self._create_app()
        self._test_credential('app')

    def test_app_owner(self):
        owner = self._get_signed_in_user()
        if not owner:
            return  # this test deletes users which are beyond a SP's capacity, so quit.

        self.kwargs = {
            'owner': owner,
            'display_name': self.create_random_name('azure-cli-test', 30)
        }
        self.recording_processors.append(MSGraphNameReplacer(owner, 'example@example.com'))

        self.kwargs['owner_object_id'] = self.cmd('ad user show --id {owner}').get_output_in_json()['id']
        self.kwargs['app_id'] = self.cmd('ad app create --display-name {display_name}').get_output_in_json()['appId']
        self.cmd('ad app owner add --owner-object-id {owner_object_id} --id {app_id}')
        self.cmd('ad app owner add --owner-object-id {owner_object_id} --id {app_id}')  # test idempotence
        self.cmd('ad app owner list --id {app_id}', checks=self.check('[0].userPrincipalName', owner))
        self.cmd('ad app owner remove --owner-object-id {owner_object_id} --id {app_id}')
        self.cmd('ad app owner list --id {app_id}', checks=self.check('length([*])', 0))

    @AllowLargeResponse()
    def test_app_permission(self):
        if not self._get_signed_in_user():
            return

        self.kwargs = {
            'display_name': self.create_random_name('cli-app-', 15),
            # Microsoft Graph
            'microsoft_graph_api': '00000003-0000-0000-c000-000000000000',
            # Azure Storage
            'azure_service_management_api': '797f4846-ba00-4fd7-ba43-dac1f8f63013',
        }

        # Look up for permission IDs
        graph_sp = self.cmd('ad sp show --id {microsoft_graph_api}').get_output_in_json()
        # Delegated permission Directory.AccessAsUser.All
        self.kwargs['microsoft_graph_permission1'] = _get_id_from_value(
            graph_sp['oauth2PermissionScopes'], 'Application.Read.All')
        # Application permission Application.ReadWrite.OwnedBy
        self.kwargs['microsoft_graph_permission2'] = _get_id_from_value(
            graph_sp['appRoles'], 'Application.ReadWrite.OwnedBy')

        arm_sp = self.cmd('ad sp show --id {azure_service_management_api}').get_output_in_json()
        # Delegated permission user_impersonation
        self.kwargs['azure_service_management_permission'] = _get_id_from_value(
            arm_sp['oauth2PermissionScopes'],'user_impersonation')

        result = self.cmd('ad sp create-for-rbac --name {display_name}').get_output_in_json()
        self.kwargs['app_id'] = result['appId']

        # Test add permissions using a list
        self.cmd('ad app permission add --id {app_id} '
                 '--api {microsoft_graph_api} '
                 '--api-permissions {microsoft_graph_permission1}=Scope {microsoft_graph_permission2}=Role')
        self.cmd('ad app permission add --id {app_id} --api {azure_service_management_api} '
                 '--api-permissions {azure_service_management_permission}=Scope')
        permissions = self.cmd(
            'ad app permission list --id {app_id}', checks=[self.check('length([*])', 2)]).get_output_in_json()
        # Sample result (required_resource_access):
        #   "requiredResourceAccess": [
        #     {
        #       "resourceAccess": [
        #         {
        #           "id": "41094075-9dad-400e-a0bd-54e686782033",
        #           "type": "Scope"
        #         }
        #       ],
        #       "resourceAppId": "797f4846-ba00-4fd7-ba43-dac1f8f63013"
        #     },
        #     {
        #       "resourceAccess": [
        #         {
        #           "id": "c79f8feb-a9db-4090-85f9-90d820caa0eb",
        #           "type": "Scope"
        #         },
        #         {
        #           "id": "18a4783c-866b-4cc7-a460-3d5e5662c884",
        #           "type": "Role"
        #         }
        #       ],
        #       "resourceAppId": "00000003-0000-0000-c000-000000000000"
        #     }
        #   ],

        microsoft_graph_permission1_object = {
            "id": self.kwargs['microsoft_graph_permission1'],
            "type": "Scope"}
        microsoft_graph_permission2_object = {
            "id": self.kwargs['microsoft_graph_permission2'],
            "type": "Role"}
        azure_service_management_permission_object = {
            "id": self.kwargs['azure_service_management_permission'],
            "type": "Scope"}

        def get_required_resource_access(required_resource_access_list, resource_app_id):
            """Search for the RequiredResourceAccess from required_resource_access(list) by resourceAppId."""
            return next(
                filter(lambda a: a['resourceAppId'] == resource_app_id, required_resource_access_list), None)

        microsoft_graph_api_object = get_required_resource_access(permissions, self.kwargs['microsoft_graph_api'])
        azure_service_management_api_object = get_required_resource_access(
            permissions, self.kwargs['azure_service_management_api'])

        # Check initial `permission add` is correct
        self.assertEqual(microsoft_graph_api_object['resourceAccess'],
                         [microsoft_graph_permission1_object, microsoft_graph_permission2_object])
        self.assertEqual(azure_service_management_api_object['resourceAccess'],
                         [azure_service_management_permission_object])

        # Test delete first permission (ResourceAccess) from microsoft_graph_api.
        self.cmd('ad app permission delete --id {app_id} '
                 '--api {microsoft_graph_api} --api-permissions {microsoft_graph_permission1}')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        microsoft_graph_api_object = get_required_resource_access(permissions, self.kwargs['microsoft_graph_api'])
        # microsoft_graph_permission1 (ResourceAccess) is deleted and
        # microsoft_graph_permission2 (ResourceAccess) remains
        self.assertEqual(microsoft_graph_api_object['resourceAccess'], [microsoft_graph_permission2_object])

        # Test delete remaining permission (ResourceAccess) from microsoft_graph_api.
        self.cmd('ad app permission delete --id {app_id} '
                 '--api {microsoft_graph_api} --api-permissions {microsoft_graph_permission2}')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        microsoft_graph_api_object = get_required_resource_access(permissions, self.kwargs['microsoft_graph_api'])
        # microsoft_graph_api (RequiredResourceAccess) is removed automatically
        self.assertIsNone(microsoft_graph_api_object)

        # Add back microsoft_graph_permission1 and microsoft_graph_permission2
        self.cmd('ad app permission add --id {app_id} '
                 '--api {microsoft_graph_api} '
                 '--api-permissions {microsoft_graph_permission1}=Scope {microsoft_graph_permission2}=Role')

        # Delete both microsoft_graph_permission1 and microsoft_graph_permission2 at the same time
        self.cmd('ad app permission delete --id {app_id} '
                 '--api {microsoft_graph_api} '
                 '--api-permissions {microsoft_graph_permission1} {microsoft_graph_permission2}')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        microsoft_graph_api_object = get_required_resource_access(permissions, self.kwargs['microsoft_graph_api'])
        # microsoft_graph_api (RequiredResourceAccess) is removed automatically
        self.assertIsNone(microsoft_graph_api_object)

        # Test delete 1 api azure_service_management_api (RequiredResourceAccess)
        self.cmd('ad app permission delete --id {app_id} --api {azure_service_management_api}')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        azure_service_management_api_object = get_required_resource_access(permissions, self.kwargs['azure_service_management_api'])
        self.assertIsNone(azure_service_management_api_object)

        # Test delete non-existing api
        self.cmd('ad app permission delete --id {app_id} --api 11111111-0000-0000-c000-000000000000')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        self.assertEqual(permissions, [])

        # Test delete api permission from non-existing api
        self.cmd('ad app permission delete --id {app_id} '
                 '--api 11111111-0000-0000-c000-000000000000 '
                 '--api-permissions {microsoft_graph_permission1} {microsoft_graph_permission2}')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        self.assertEqual(permissions, [])

        # Test delete non-existing api permission from existing api
        self.cmd('ad app permission add --id {app_id} '
                 '--api {microsoft_graph_api} '
                 '--api-permissions {microsoft_graph_permission1}=Scope {microsoft_graph_permission2}=Role')
        self.cmd('ad app permission delete --id {app_id} '
                 '--api {microsoft_graph_api} --api-permissions 22222222-0000-0000-c000-000000000000')
        permissions = self.cmd('ad app permission list --id {app_id}').get_output_in_json()
        microsoft_graph_api_object = get_required_resource_access(permissions, self.kwargs['microsoft_graph_api'])
        self.assertEqual(microsoft_graph_api_object['resourceAccess'],
                         [microsoft_graph_permission1_object, microsoft_graph_permission2_object])

        # Test permission type '=Scope' is missing
        from azure.cli.core.azclierror import ArgumentUsageError
        with self.assertRaisesRegex(ArgumentUsageError, 'both permission id and type'):
            self.cmd('ad app permission add --id {app_id} '
                     '--api {microsoft_graph_api} '
                     '--api-permissions {microsoft_graph_permission1}')

    @AllowLargeResponse()
    def test_app_permission_grant(self):
        if not self._get_signed_in_user():
            return  # this test delete users which are beyond a SP's capacity, so quit...
        self.kwargs = {
            'display_name': self.create_random_name('cli-app-', 15),
            'microsoft_graph_api': '00000003-0000-0000-c000-000000000000',
            'microsoft_graph_permission_value1': 'Directory.Read.All',  # Delegated permission
            'microsoft_graph_permission_value2': 'Application.Read.All',  # Delegated permission
            # 'microsoft_graph_permission_value3': 'Application.ReadWrite.OwnedBy'  # Application permission
        }

        # Look up for permission IDs
        graph_sp = self.cmd('ad sp show --id {microsoft_graph_api}').get_output_in_json()
        self.kwargs['microsoft_graph_sp_id'] = graph_sp['id']
        self.kwargs['microsoft_graph_permission1'] = _get_id_from_value(
            graph_sp['oauth2PermissionScopes'], self.kwargs['microsoft_graph_permission_value1'])
        self.kwargs['microsoft_graph_permission2'] = _get_id_from_value(
            graph_sp['oauth2PermissionScopes'], self.kwargs['microsoft_graph_permission_value2'])

        # TODO: support and test application permissions
        # self.kwargs['microsoft_graph_permission3'] = _get_id_from_value(
        #     graph_sp['appRoles'], self.kwargs['microsoft_graph_permission_value2'])

        result = self.cmd('ad sp create-for-rbac --name {display_name}').get_output_in_json()
        self.kwargs['app_id'] = result['appId']
        self.cmd('ad app permission add --id {app_id} '
                 '--api {microsoft_graph_api} --api-permissions {microsoft_graph_permission1}=Scope')

        # Add permissions
        permissions = self.cmd('ad app permission list --id {app_id}', checks=[
            self.check('length([*])', 1)
        ]).get_output_in_json()
        assert permissions[0]['resourceAppId'] == '00000003-0000-0000-c000-000000000000'
        assert permissions[0]['resourceAccess'][0]['id'] == self.kwargs['microsoft_graph_permission1']
        assert permissions[0]['resourceAccess'][0]['type'] == 'Scope'

        # Grant permissions
        self.cmd('ad app permission grant --id {app_id} --api {microsoft_graph_api} '
                 '--scope {microsoft_graph_permission_value1}')
        grants = self.cmd('ad app permission list-grants --id {app_id} --show-resource-name').get_output_in_json()
        assert len(grants) == 1
        assert grants[0]['resourceId'] == self.kwargs['microsoft_graph_sp_id']
        assert grants[0]['resourceDisplayName'] == "Microsoft Graph"
        assert grants[0]['scope'] == self.kwargs['microsoft_graph_permission_value1']

        # Add a second permission
        self.cmd('ad app permission add --id {app_id} '
                 '--api {microsoft_graph_api} --api-permissions {microsoft_graph_permission2}=Scope')

        # Grant permissions
        self.cmd('ad app permission grant --id {app_id} --api {microsoft_graph_api} '
                 '--scope {microsoft_graph_permission_value1} {microsoft_graph_permission_value2}')
        grants = self.cmd('ad app permission list-grants --id {app_id} --show-resource-name').get_output_in_json()
        assert len(grants) == 1
        assert grants[0]['scope'] == (self.kwargs['microsoft_graph_permission_value1'] + " " +
                                      self.kwargs['microsoft_graph_permission_value2'])

        self.cmd('ad app permission delete --id {app_id} --api {microsoft_graph_api}')
        self.cmd('ad app permission list --id {app_id}', checks=self.check('length([*])', 0))

    def test_app_federated_credential(self):
        self._create_app()
        self._test_federated_credential('app')


class ServicePrincipalScenarioTest(GraphScenarioTestBase):

    def test_service_principal_scenario(self):
        """
        - Test service principal creation.
        - Test service principal can be resolved with servicePrincipalNames (appId and identifierUris) or id.
        """
        display_name = self.create_random_name(prefix='azure-cli-test', length=30)

        self.kwargs.update({
            'display_name': display_name,
            'identifier_uri': f'api://{display_name}'
        })

        # Create
        app = self.cmd('ad app create --display-name {display_name} '
                       '--identifier-uris {identifier_uri}').get_output_in_json()

        self.kwargs['app_id'] = app['appId']

        sp = self.cmd('ad sp create --id {app_id}',
                      checks=[
                          self.check('appId', app['appId']),
                          self.check('appDisplayName', app['displayName']),
                          self.check('servicePrincipalNames[0]', '{app_id}')
                      ]).get_output_in_json()

        self.kwargs['id'] = sp['id']

        # Show with appId as one of servicePrincipalNames
        self.cmd('ad sp show --id {app_id}')
        # Show with identifierUri as one of servicePrincipalNames
        self.cmd('ad sp show --id {identifier_uri}')
        # Show with id
        self.cmd('ad sp show --id {id}')

        # Update with generic update
        self.cmd('ad sp update --id {id} --set appRoleAssignmentRequired=true')
        self.cmd('ad sp show --id {id}', checks=self.check('appRoleAssignmentRequired', True))

        self.cmd('ad sp delete --id {app_id}')
        self.cmd('ad app delete --id {app_id}')

        self.cmd('ad sp show --id {app_id}', expect_failure=True)
        self.cmd('ad app show --id {app_id}', expect_failure=True)

    def test_sp_show_exit_code(self):
        with self.assertRaises(SystemExit):
            self.assertEqual(self.cmd('ad sp show --id non-exist-sp-name').exit_code, 3)
            self.assertEqual(self.cmd('ad sp show --id 00000000-0000-0000-0000-000000000000').exit_code, 3)

    def test_sp_owner(self):
        display_name = self.create_random_name(prefix='azure-cli-test', length=30)

        self.kwargs.update({
            'display_name': display_name,
            'identifier_uri': f'api://{display_name}'
        })
        app = self.cmd('ad app create --display-name {display_name}').get_output_in_json()
        self.kwargs['app_id'] = app['appId']
        self.cmd('ad sp create --id {app_id}').get_output_in_json()

        # We don't support create, remove yet
        self.cmd('ad sp owner list --id {app_id}', checks=self.check('length(@)', 0))

    def test_sp_credential(self):
        self._create_sp()
        self._test_credential('sp')

    @unittest.skip("It seems sp doesn't work with federatedIdentityCredentials yet.")
    def test_sp_federated_credential(self):
        self._create_sp()
        self._test_federated_credential('sp')


class UserScenarioTest(GraphScenarioTestBase):
    def test_user_scenario(self):
        self.kwargs = {
            'user1': self.create_random_name(prefix='graphusertest', length=20),
            'user2': self.create_random_name(prefix='graphusertest', length=20),
            'domain': 'AzureSDKTeam.onmicrosoft.com',
            'mail_nickname': 'graphusertest',
            'new_mail_nick_name': 'graphusertestupdate',
            'group': 'graphusertest_g',
            'password': self.create_random_name(prefix='password-', length=40),
            'force_change_password_next_login': True,
        }
        # create
        user1_result = self.cmd(
            'ad user create --display-name {user1} '
            '--mail-nickname {mail_nickname} '
            '--password {password} '
            '--force-change-password-next-sign-in {force_change_password_next_login} '
            '--user-principal-name {user1}@{domain} ',
            checks=[
                self.check("displayName","{user1}"),
                self.check("userPrincipalName", "{user1}@{domain}")
            ]
        ).get_output_in_json()
        self.kwargs['user1_id'] = user1_result['id']
        self.kwargs['user1_newName'] = self.create_random_name(prefix='graphusertest', length=20)

        # update
        self.cmd(
            'ad user update --display-name {user1_newName} '
            '--account-enabled false '
            '--id {user1_id} '
            '--mail-nickname {new_mail_nick_name} '
            '--password {password} '
            '--force-change-password-next-sign-in true '
        )

        # show
        self.cmd('ad user show --id {user1}@{domain}',
                 checks=[
                     self.check("displayName", '{user1_newName}')
                 ])

        # create group
        group_result = self.cmd(
            'ad group create --display-name {group} --mail-nickname {group} --description {group}').get_output_in_json()
        self.kwargs['group_id'] = group_result['id']
        # add user1 into group
        self.cmd('ad group member add -g {group} --member-id {user1_id}',
                 checks=self.is_empty())

        # show user's group memberships
        self.cmd('ad user get-member-groups --id {user1_id}',
                 checks=self.check('[0].displayName', self.kwargs['group']))

        # list
        self.cmd('ad user list')

        # delete
        self.cmd('ad user delete --id {user1_id}')


class GroupScenarioTest(GraphScenarioTestBase):

    def clean_resource(self, resource, type='group'):
        try:
            if type == 'user':
                self.cmd('ad user delete --id {}'.format(resource))
            elif type == 'group':
                self.cmd('ad group delete -g {}'.format(resource))
            elif type == 'app':
                self.cmd('ad app delete --id {}'.format(resource))
        except Exception:
            pass

    def test_group_scenario(self):
        if not self._get_signed_in_user():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        domain = 'AzureSDKTeam.onmicrosoft.com'
        self.kwargs = {
            'group': self.create_random_name(prefix='testgroup', length=24),
            'mail_nick_name': 'deleteme11',
            'child_group': self.create_random_name(prefix='testchildgroup', length=24),
            'leaf_group': self.create_random_name(prefix='testleafgroup', length=24),
            'user1': self.create_random_name(prefix='testgroupuser1', length=24),
            'user2': self.create_random_name(prefix='testgroupuser2', length=24),
            'pass': 'Test1234!!',
            'domain': domain,
            'app_name': self.create_random_name(prefix='testgroupapp', length=24)
        }

        self.recording_processors.append(MSGraphNameReplacer('@' + domain, '@example.com'))
        try:
            # create group
            group_result = self.cmd(
                'ad group create --display-name {group} --mail-nickname {mail_nick_name} --description {group}',
                checks=[self.check('displayName', '{group}'),
                        self.check('mailNickname', '{mail_nick_name}'),
                        self.check('description', '{group}')]
            ).get_output_in_json()
            self.kwargs['group_id'] = group_result['id']

            # create again to test idempotency
            self.cmd('ad group create --display-name {group} --mail-nickname {mail_nick_name}')
            # list groups
            self.cmd('ad group list --display-name {group}', checks=self.check('length([])', 1))
            # show group
            self.cmd('ad group show -g {group}', checks=[
                self.check('id', '{group_id}'),
                self.check('displayName', '{group}'),
                self.check('mailNickname', '{mail_nick_name}'),
                self.check('description', '{group}')
            ])

            # create other groups to test membership transitivity
            group_result = self.cmd('ad group create --display-name {child_group} --mail-nickname {mail_nick_name}').get_output_in_json()
            self.kwargs['child_group_id'] = group_result['id']
            group_result = self.cmd('ad group create --display-name {leaf_group} --mail-nickname {mail_nick_name}').get_output_in_json()
            self.kwargs['leaf_group_id'] = group_result['id']

            # add child_group as member of group
            self.cmd('ad group member add -g {group_id} --member-id {child_group_id}')
            # add leaf_group as member of child_group
            self.cmd('ad group member add -g {child_group_id} --member-id {leaf_group_id}')

            # check member transitivity
            self.cmd('ad group member check -g {group_id} --member-id {child_group_id}',
                     checks=self.check('value', True))
            self.cmd('ad group member check -g {child_group_id} --member-id {leaf_group_id}',
                     checks=self.check('value', True))
            self.cmd('ad group member check -g {group_id} --member-id {leaf_group_id}',
                     checks=self.check('value', True))

            # list members (intransitive)
            self.cmd('ad group member list -g {group_id}', checks=self.check('length([])', 1))
            self.cmd('ad group member list -g {child_group_id}', checks=self.check('length([])', 1))
            self.cmd('ad group member list -g {leaf_group_id}', checks=self.check('length([])', 0))

            # get-member-groups transitivity
            self.cmd('ad group get-member-groups -g {group_id}', checks=self.check('length([])', 0))
            self.cmd('ad group get-member-groups -g {child_group_id}', checks=self.check('length([])', 1))
            self.cmd('ad group get-member-groups -g {leaf_group_id}', checks=self.check('length([])', 2))

            # remove member
            self.cmd('ad group member remove -g {child_group_id} --member-id {leaf_group_id}')
            self.cmd('ad group member check -g {child_group_id} --member-id {leaf_group_id}',
                     checks=self.check('value', False))

            # create user to add group member
            user_result = self.cmd('ad user create --display-name {user1} --password {pass} --user-principal-name {user1}@{domain}').get_output_in_json()
            self.kwargs['user1_id'] = user_result['id']

            # add user as group member
            self.cmd('ad group member add -g {leaf_group_id} --member-id {user1_id}')

            # check user as group member
            self.cmd('ad group member check -g {leaf_group_id} --member-id {user1_id}',
                     checks=self.check('value', True))
            # list member(user is expected)
            self.cmd('ad group member list -g {leaf_group_id}', checks=self.check('length([])', 1))

            # remove user as member
            self.cmd('ad group member remove -g {leaf_group_id} --member-id {user1_id}')
            self.cmd('ad group member check -g {leaf_group_id} --member-id {user1_id}',
                     checks=self.check('value', False))

            # Create service principal to add group member
            with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
                result = self.cmd('ad sp create-for-rbac -n {app_name}').get_output_in_json()
                self.kwargs['app_id'] = result['appId']
                sp = self.cmd('ad sp show --id {app_id}').get_output_in_json()
                self.kwargs['sp_id'] = sp['id']

                # add service principal as group member
                self.cmd('ad group member add -g {leaf_group_id} --member-id {sp_id}')

                # check service principal as group member
                self.cmd('ad group member check -g {leaf_group_id} --member-id {sp_id}',
                         checks=self.check('value', True))

                # TODO: check list sp as member after staged roll-out of service principals on MS Graph
                # list member(service principal is expected)
                # self.cmd('ad group member list -g {leaf_group_id}', checks=self.check('length([])', 1))

                # remove service principal as member
                self.cmd('ad group member remove -g {leaf_group_id} --member-id {sp_id}')
                self.cmd('ad group member check -g {leaf_group_id} --member-id {sp_id}',
                         checks=self.check('value', False))

            # list owners
            self.cmd('ad group owner list -g {group_id}', checks=self.check('length([])', 0))

            # create user to add group owner
            user_result = self.cmd('ad user create --display-name {user2} --password {pass} --user-principal-name {user2}@{domain}').get_output_in_json()
            self.kwargs['user2_id'] = user_result['id']
            # add owner
            self.cmd('ad group owner add -g {group_id} --owner-object-id {user1_id}')
            self.cmd('ad group owner add -g {group_id} --owner-object-id {user2_id}')
            self.cmd('ad group owner list -g {group_id}', checks=self.check('length([])', 2))

            # remove owner
            self.cmd('ad group owner remove -g {group_id} --owner-object-id {user1_id}')
            self.cmd('ad group owner list -g {group_id}', checks=self.check('length([])', 1))

            # delete group
            self.cmd('ad group delete -g {group}')
            self.cmd('ad group show -g {group_id}', expect_failure=True)
        finally:
            self.clean_resource(self.kwargs['group'])
            self.clean_resource(self.kwargs['child_group'])
            self.clean_resource(self.kwargs['leaf_group'])
            self.clean_resource('{}@{}'.format(self.kwargs['user1'], self.kwargs['domain']), type='user')
            self.clean_resource('{}@{}'.format(self.kwargs['user2'], self.kwargs['domain']), type='user')
            if self.kwargs.get('app_id'):
                self.clean_resource(self.kwargs['app_id'], type='app')


class MiscellaneousScenarioTest(GraphScenarioTestBase):
    def test_special_characters(self):
        # Test special characters in object names. Ensure these characters are correctly percent-encoded.
        # For example, displayName with +(%2B), /(%2F)
        from azure.cli.testsdk.scenario_tests.utilities import create_random_name
        prefix = 'azure-cli-test-group+/'
        mock_name = prefix + '000001'
        if self.in_recording:
            display_name = create_random_name(prefix=prefix, length=32)
            self.recording_processors.append(MSGraphNameReplacer(display_name, mock_name))
        else:
            display_name = mock_name

        self.kwargs = {
            'display_name': display_name,
            'mail_nick_name': 'deleteme11'
        }
        self.cmd('ad group create --display-name {display_name} --mail-nickname {mail_nick_name}',
                 checks=self.check('displayName', '{display_name}'))
        self.cmd('ad group show --group {display_name}',
                 checks=self.check('displayName', '{display_name}'))
        self.cmd('ad group list --display-name {display_name}',
                 checks=[self.check('length(@)', 1),
                         self.check('[0].displayName', '{display_name}')])
        self.cmd('ad group delete --group {display_name}')
        self.cmd('ad group list --display-name {display_name}',
                 checks=self.check('length(@)', 0))


def _get_id_from_value(permissions, value):
    """Get id from value for appRoles or oauth2PermissionScopes."""
    # https://docs.microsoft.com/en-us/graph/api/resources/serviceprincipal?view=graph-rest-1.0#properties
    return next(p['id'] for p in permissions if p['value'] == value)
