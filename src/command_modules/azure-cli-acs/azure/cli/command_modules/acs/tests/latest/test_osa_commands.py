# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest

from knack.util import CLIError

from azure.cli.testsdk import (
    ResourceGroupPreparer, ManagedApplicationPreparer, ScenarioTest, live_only)
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.checkers import (StringContainCheck, StringContainCheckIgnoreCase)

# flake8: noqa


class AzureOpenShiftServiceScenarioTest(ScenarioTest):
    
    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    @ManagedApplicationPreparer()
    def test_openshift_create_default_service(self, resource_group, resource_group_location, aad_client_app_id, aad_client_app_secret):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'fqdn': self.generate_random_fqdn(osa_name, resource_group_location),
            'location': resource_group_location,
            'aad_client_app_id': aad_client_app_id,
            'aad_client_app_secret': aad_client_app_secret,
            'resource_type': "Microsoft.ContainerService/OpenShiftManagedClusters"
        })

        # create
        create_cmd = 'openshift create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--fqdn={fqdn} --compute-count=1 ' \
                     '--aad-client-app-id {aad_client_app_id} --aad-client-app-secret {aad_client_app_secret}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D4s_v3'),
            self.check('fqdn', '{fqdn}'),
            self.exists('openShiftVersion')
        ])

        # scale up
        self.cmd('openshift scale -g {resource_group} -n {name} --compute-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])
    
    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    @ManagedApplicationPreparer()
    def test_openshift_create_service_no_wait(self, resource_group, resource_group_location, aad_client_app_id, aad_client_app_secret):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'fqdn': self.generate_random_fqdn(osa_name, resource_group_location),
            'location': resource_group_location,
            'aad_client_app_id': aad_client_app_id,
            'aad_client_app_secret': aad_client_app_secret
        })

        # create --no-wait
        create_cmd = 'openshift create -g {resource_group} -n {name} --fqdn {fqdn} ' \
                     '-l {location} -c 1 --aad-client-app-id {aad_client_app_id} ' \
                     '--aad-client-app-secret {aad_client_app_secret} ' \
                     '--tags scenario_test --no-wait'
        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('openshift wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D4s_v3'),
            self.check('fqdn', '{fqdn}'),
            self.check('provisioningState', 'Succeeded'),
            self.exists('openShiftVersion')
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('openshift show -g {resource_group} -n {name}', expect_failure=True)
    
    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    def test_openshift_create_default_service_no_aad(self, resource_group, resource_group_location):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'fqdn': self.generate_random_fqdn(osa_name, resource_group_location),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/OpenShiftManagedClusters'
        })

        # create
        create_cmd = 'openshift create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--fqdn={fqdn} --compute-count=1 '
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D4s_v3'),
            self.check('fqdn', '{fqdn}'),
            self.exists('openShiftVersion')
        ])

        # scale up
        self.cmd('openshift scale -g {resource_group} -n {name} --compute-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @classmethod
    def generate_random_fqdn(self, name, location):
        return "{}.{}.cloudapp.azure.com".format(name, location)
