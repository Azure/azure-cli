# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)

DEFAULT_LOCATION = "westus"

class StaticAppBasicE2ETest(ScenarioTest):
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @StorageAccountPreparer()
    def test_staticapp_linked_backends(self, resource_group, storage_account):
        from knack.util import CLIError

        static_site_name = self.create_random_name(prefix='swabackends', length=24)
        self.cmd('staticwebapp create -g {} -n {} --sku=Standard'.format(resource_group, static_site_name))

        plan_name = self.create_random_name(prefix='swabackends', length=24)
        function_app_name = self.create_random_name(prefix='swabackends', length=24)
        self.cmd('acr create --admin-enabled -g {} -n {} --sku Basic'.format(resource_group, function_app_name))
        self.cmd('appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan_name))
        function_app = self.cmd('functionapp create -g {} -n {} -s {} --plan {} --functions-version 3 --runtime node'.format(
            resource_group, function_app_name, storage_account, plan_name)).get_output_in_json()
        function_app_id = function_app['id']

        with self.assertRaises(CLIError):
            self.cmd('staticwebapp backends link -g {} -n {} --backend-resource-id {} --backend-region centralus'.format(
                resource_group, static_site_name, function_app_id))

        self.cmd('staticwebapp backends link -g {} -n {} --backend-resource-id {} --backend-region {}'.format(
            resource_group, static_site_name, function_app_id, DEFAULT_LOCATION), checks=[
                self.check('provisioningState', 'Succeeded')
                ])

        self.kwargs.update({
          'funcname': function_app_name
        })
        self.cmd('staticwebapp backends show -g {} -n {}'.format(resource_group, static_site_name), checks=[
            self.check("[0].name", '{funcname}')
        ])

        self.cmd('staticwebapp backends unlink -g {} -n {}'.format(resource_group, static_site_name))

        linked_backends = self.cmd('staticwebapp backends show -g {} -n {}'.format(
            resource_group, static_site_name)).get_output_in_json()
        assert len(linked_backends) == 0
