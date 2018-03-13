# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from knack.util import CLIError


class AmsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_ams_list(self, resource_group):
        list = self.cmd('az ams account list -g {}'.format(resource_group)).get_output_in_json()
        assert len(list) > 0

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_create_show(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams account show -n {amsname} -g {rg}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_ams_storage_add_remove(self, resource_group, storage_account_for_create, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.kwargs.update({
            'storageAccount': storage_account_for_update
        })

        self.cmd('az ams storage add -a {amsname} -g {rg} -n {storageAccount}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams storage remove -a {amsname} -g {rg} -n {storageAccount}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_sp_create(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        spName = self.create_random_name(prefix='spn', length=10)
        spPassword = self.create_random_name(prefix='spp', length=10)

        self.kwargs.update({
            'spName': spName,
            'spPassword': spPassword,
            'role': 'Owner'
        })

        self.cmd('az ams sp create -a {amsname} -n {spName} -g {rg} -p {spPassword} --role {role}', checks=[
            self.check('AadSecret', '{spPassword}'),
            self.check('ResourceGroup', '{rg}'),
            self.check('AccountName', '{amsname}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_transform(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetName': 'AACGoodQualityAudio'
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset-name {presetName} -l {location}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams transform show -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}')
        ])

        list = self.cmd('az ams transform list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams transform delete -n {transformName} -a {amsname} -g {rg}')
