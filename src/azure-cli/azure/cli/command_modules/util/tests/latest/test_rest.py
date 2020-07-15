# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


class ResourceGroupScenarioTest(ScenarioTest):

    def test_rest_arm(self):
        from knack.util import CLIError

        self.kwargs.update({
            'rg': self.create_random_name("test-rest-rg", length=20)
        })

        # Test ARM Subscriptions - List
        # https://docs.microsoft.com/en-us/rest/api/resources/subscriptions/list
        self.cmd('az rest -u /subscriptions?api-version=2020-01-01',
                 checks=[self.exists("value")])

        # Test ARM Tenants - List
        # https://docs.microsoft.com/en-us/rest/api/resources/tenants/list
        self.cmd('az rest -u /tenants?api-version=2020-01-01',
                 checks=[self.exists("value")])

        # Resource Groups - Create Or Update
        # https://docs.microsoft.com/en-us/rest/api/resources/resourcegroups/createorupdate
        self.cmd('az rest -m PUT -u https://management.azure.com/subscriptions/{{subscriptionId}}/resourcegroups/{rg}?api-version=2019-10-01 '
                 '--body \'{{"location": "eastus"}}\'',
                 checks=[self.check("name", '{rg}')])

        # Resource Groups - Get
        # https://docs.microsoft.com/en-us/rest/api/resources/resourcegroups/get
        self.cmd('az rest -u https://management.azure.com/subscriptions/{{subscriptionId}}/resourcegroups/{rg}?api-version=2019-10-01',
                 checks=[self.check("name", '{rg}')])

        # Resource Groups - Delete
        # https://docs.microsoft.com/en-us/rest/api/resources/resourcegroups/delete
        self.cmd('az rest -m DELETE -u https://management.azure.com/subscriptions/{{subscriptionId}}/resourcegroups/{rg}?api-version=2019-10-01',
                 checks=[])

        # Resource Groups - Get
        # Polling for 404
        # TODO: return 3 for 404
        with self.assertRaises(CLIError):
            while True:
                time.sleep(5)
                self.cmd('az rest -u https://management.azure.com/subscriptions/{{subscriptionId}}/resourcegroups/{rg}?api-version=2019-10-01',
                         checks=[])

    @ResourceGroupPreparer(name_prefix='cli_test_rest')
    def test_rest_storage(self, resource_group):

        self.kwargs.update({
            'sa': self.create_random_name("tmpst", length=10),
            # Please remember to add double quote to the variable reference of the file path in tests,
            # otherwise \\ will be parsed to \, which will lead to the wrong path
            'storage_account_create_body': os.path.join(TEST_DIR, 'rest_storage_account_create_body.json'),
            'storage_account_sas_body': os.path.join(TEST_DIR, 'rest_storage_account_sas_body.json')
        })

        # Create a storage account
        # https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts/create
        self.cmd('az rest -m PUT -u /subscriptions/{{subscriptionId}}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{sa}?api-version=2019-06-01 '
                 '-b @"{storage_account_create_body}"')

        # Poll on the provisioning state
        state = None
        while state != 'Succeeded':
            time.sleep(5)
            # Show the storage account
            # https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts/getproperties
            state = self.cmd('az rest -m GET -u /subscriptions/{{subscriptionId}}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{sa}?api-version=2019-06-01') \
                .get_output_in_json()["properties"]["provisioningState"]

        # Create an account SAS token https://docs.microsoft.com/en-us/rest/api/storageservices/create-account-sas
        # https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts/listaccountsas
        sas_token = self.cmd('az rest -m POST -u "/subscriptions/{{subscriptionId}}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{sa}/ListAccountSas?api-version=2019-06-01" '
                             '-b @"{storage_account_sas_body}"').get_output_in_json()["accountSasToken"]

        # Create a container with the SAS token
        # https://docs.microsoft.com/en-us/rest/api/storageservices/create-container
        self.cmd('az rest -m PUT -u https://{sa}.blob.core.windows.net/mycontainer?restype=container&' + sas_token + ' '
                 '--skip-authorization-header')

        # Show the container properties
        # https://docs.microsoft.com/en-us/rest/api/storageservices/get-container-properties
        self.cmd('az rest -m HEAD -u https://{sa}.blob.core.windows.net/mycontainer?restype=container&' + sas_token + ' '
                 '--skip-authorization-header')

        # Create a blob
        # https://docs.microsoft.com/en-us/rest/api/storageservices/put-blob
        self.cmd('az rest -m PUT -u https://{sa}.blob.core.windows.net/mycontainer/myblob?' + sas_token + ' '
                 '--headers "Content-Type=text/plain; charset=UTF-8" "x-ms-blob-type=BlockBlob" '
                 '--skip-authorization-header '
                 '--body "hello world"')

        # Show the blob
        # https://docs.microsoft.com/en-us/rest/api/storageservices/get-blob
        self.cmd('az rest -m GET -u https://{sa}.blob.core.windows.net/mycontainer/myblob?' + sas_token + ' '
                 '--skip-authorization-header')

        # List blobs in the container
        # https://docs.microsoft.com/en-us/rest/api/storageservices/list-blobs
        self.cmd('az rest -m GET -u https://{sa}.blob.core.windows.net/mycontainer?restype=container&comp=list&' + sas_token + ' '
                 '--skip-authorization-header')

        # Delete the blob
        # https://docs.microsoft.com/en-us/rest/api/storageservices/delete-blob
        self.cmd('az rest -m DELETE -u https://{sa}.blob.core.windows.net/mycontainer/myblob?' + sas_token + ' '
                 '--skip-authorization-header')

        # Delete the container
        # https://docs.microsoft.com/en-us/rest/api/storageservices/delete-container
        self.cmd('az rest -m DELETE -u https://{sa}.blob.core.windows.net/mycontainer?restype=container&' + sas_token + ' '
                 '--skip-authorization-header')

        # Delete the storage account
        # https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts/delete
        self.cmd('az rest -m DELETE -u "/subscriptions/{{subscriptionId}}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{sa}?api-version=2019-06-01"')

    def test_rest_microsoft_graph(self):
        from knack.util import CLIError

        display_name_prefix = "az-rest-test-app"
        self.kwargs.update({
            'display_name_prefix': display_name_prefix,
            'display_name': self.create_random_name(display_name_prefix, length=25)
        })

        # Create application
        # https://docs.microsoft.com/en-us/graph/api/application-post-applications?view=graph-rest-1.0&tabs=http
        # Escape single quotes for `shlex` and curly braces for `format`
        app = self.cmd('az rest --method POST --url https://graph.microsoft.com/v1.0/applications --body \'{{"displayName": "{display_name}"}}\'',
                       checks=[
                           self.check('displayName', '{display_name}')
                       ]).get_output_in_json()

        self.kwargs["app_object_id"] = app["id"]
        self.kwargs["app_id"] = app["appId"]

        # Get application
        # https://docs.microsoft.com/en-us/graph/api/application-get?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method GET --url https://graph.microsoft.com/v1.0/applications/{app_object_id}',
                 checks=[self.check('displayName', '{display_name}')])

        # Update application
        # https://docs.microsoft.com/en-us/graph/api/application-update?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method PATCH --url https://graph.microsoft.com/v1.0/applications/{app_object_id} --body \'{{"web":{{"redirectUris":["https://myapp.com"]}}}}\'')

        # application: addPassword
        # https://docs.microsoft.com/en-us/graph/api/application-addpassword?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method POST --url https://graph.microsoft.com/v1.0/applications/{app_object_id}/addPassword '
                 '--body \'{{"passwordCredential": {{"displayName": "Password friendly name"}}}}\'',
                 checks=[self.check('displayName', "Password friendly name")])

        # Create servicePrincipal
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-post-serviceprincipals?view=graph-rest-1.0&tabs=http
        sp = self.cmd('az rest --method POST --url https://graph.microsoft.com/v1.0/serviceprincipals --body \'{{"appId": "{app_id}"}}\'').get_output_in_json()
        self.kwargs["sp_object_id"] = sp["id"]

        # Get servicePrincipal
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-get?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method GET --url https://graph.microsoft.com/v1.0/servicePrincipals/{sp_object_id}',
                 checks=[self.check('appId', '{app_id}'),
                         self.check('id', '{sp_object_id}')])

        # Update servicePrincipal
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-update?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method PATCH --url https://graph.microsoft.com/v1.0/servicePrincipals/{sp_object_id} '
                 '--body \'{{"appRoleAssignmentRequired": true}}\'')

        # servicePrincipal: addPassword
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-addpassword?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method POST --url https://graph.microsoft.com/v1.0/servicePrincipals/{sp_object_id}/addPassword '
                 '--body \'{{"passwordCredential": {{"displayName": "Password friendly name"}}}}\'',
                 checks=[self.check('displayName', "Password friendly name")])

        # Delete servicePrincipal
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-delete?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method DELETE --url https://graph.microsoft.com/v1.0/serviceprincipals/{sp_object_id}')

        with self.assertRaisesRegex(CLIError, "Request_ResourceNotFound"):
            self.cmd('az rest --method GET --url https://graph.microsoft.com/v1.0/servicePrincipals/{sp_object_id}')

        # Delete application
        # https://docs.microsoft.com/en-us/graph/api/application-delete?view=graph-rest-1.0&tabs=http
        self.cmd('az rest --method DELETE --url https://graph.microsoft.com/v1.0/applications/{app_object_id}')

        with self.assertRaisesRegex(CLIError, "Request_ResourceNotFound"):
            self.cmd('az rest --method GET --url https://graph.microsoft.com/v1.0/applications/{app_object_id}')

        # Clear the trash left behind by failed tests
        response = self.cmd('az rest -m GET -u "https://graph.microsoft.com/v1.0/applications?$filter=startswith(displayName, \'{display_name_prefix}\')"').get_output_in_json()
        apps = response['value']
        for app in apps:
            self.cmd('az rest --method DELETE --url https://graph.microsoft.com/v1.0/applications/{}'.format(app['id']))


if __name__ == '__main__':
    unittest.main()
