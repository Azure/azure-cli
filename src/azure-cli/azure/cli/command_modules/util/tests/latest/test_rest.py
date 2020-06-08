# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class ResourceGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_rest')
    def test_rest(self, resource_group):
        self.kwargs.update({
            'sa': self.create_random_name("tmpst", length=10)
        })

        # Create a storage account
        # https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts/create
        self.cmd('az rest -m PUT -u /subscriptions/{{subscriptionId}}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{sa}?api-version=2019-06-01 '
                 '-b @rest_storage_account_create_body.json')

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
                             '-b @rest_storage_account_sas_body.json').get_output_in_json()["accountSasToken"]

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


if __name__ == '__main__':
    unittest.main()
