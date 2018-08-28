# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsContentKeyPolicyTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_simple(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        content_key_policy = self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('length(options)', 1),
            self.check('description', '{description}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.assertEquals('#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration', content_key_policy['options'][0]['configuration']['odatatype'])
        self.assertEquals('#Microsoft.Media.ContentKeyPolicyOpenRestriction', content_key_policy['options'][0]['restriction']['odatatype'])
