# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsContentKeyPolicyTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_basic(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('length(options)', 1),
            self.check('description', '{description}'),
            self.check('resourceGroup', '{rg}'),
            self.check('options[0].name', '{policyOptionName}'),
            self.check('options[0].configuration.odatatype', '{configurationODataType}'),
            self.check('options[0].restriction.odatatype', '{restrictionODataType}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_show')
    def test_content_key_policy_show_basic(self, storage_account_for_show):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_show,
            'location': 'westus2',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}')

        self.cmd('az ams content-key-policy show -a {amsname} -n {contentKeyPolicyName} -g {rg}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('length(options)', 1),
            self.check('description', '{description}'),
            self.check('resourceGroup', '{rg}'),
            self.check('options[0].name', '{policyOptionName}'),
            self.check('options[0].configuration.odatatype', '{configurationODataType}'),
            self.check('options[0].restriction.odatatype', '{restrictionODataType}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_delete(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}')
        ])

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams content-key-policy delete -a {amsname} -g {rg} -n {contentKeyPolicyName}')

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 0)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_list(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_name2 = self.create_random_name(prefix='pn', length=10)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'contentKeyPolicyName': policy_name,
            'contentKeyPolicyName2': policy_name2,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}')
        ])

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName2} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName2}')
        ])

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('az ams content-key-policy delete -a {amsname} -g {rg} -n {contentKeyPolicyName}')

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
