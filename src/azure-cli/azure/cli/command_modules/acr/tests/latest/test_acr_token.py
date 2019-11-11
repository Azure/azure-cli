# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AcrTokenCommandsTests(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @unittest.skip('blocked till the feature gets deployed to production')
    def test_repository_token_create(self):
        self.kwargs.update({
            'registry': self.create_random_name('clireg', 20),
            'scope_map': 'scope-map',
            'token': 'acr-token',
            'token2': 'token-2'
        })
        self.cmd('acr create -g {rg} -n {registry} --sku premium')

        # quick create
        # ACR ever verifies the existence of the repository, hence we will feed a fake
        self.cmd('acr token create -r {registry} -n {token} --repository foo content/read', checks=[
            self.check('status', 'enabled'),
            self.check('credentials.passwords[0].name', 'password1'),
            self.check('credentials.passwords[1].name', 'password2'),
            self.check('credentials.username', self.kwargs['token'])
        ])
        self.cmd('acr scope-map show -r {registry} -n {token}-scope-map', checks=[
            self.check('actions', ['repositories/foo/content/read'])
        ])

        # create from an existing scope map
        self.cmd('acr scope-map create -r {registry} -n {scope_map} --repository foo content/read metadata/read', checks=[
            self.check('actions', ['repositories/foo/content/read', 'repositories/foo/metadata/read'])
        ])
        self.cmd('acr token create -r {registry} --scope-map {scope_map} -n {token2} --no-passwords', checks=[
            self.check('credentials.passwords', [])
        ])
        self.cmd('acr token credential generate -r {registry} -n {token2} --password1 --password2', checks=[
            self.check('passwords[0].name', 'password1'),
            self.check('passwords[1].name', 'password2')
        ])
