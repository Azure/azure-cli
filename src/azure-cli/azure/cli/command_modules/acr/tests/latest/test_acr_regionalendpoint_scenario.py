# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class AcrRegionalEndpointScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_acrre_')
    def test_acr_create_with_regional_endpoints_enabled(self):
        registry_name = self.create_random_name('clitestre', length=16)

        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': 'westus',
            'sku': 'Premium'
        })

        self.cmd('acr create -g {rg} -n {registry_name} --sku {sku} --location {rg_loc} --regional-endpoints enabled', checks=[
            self.check('name', registry_name),
            self.check('regionalEndpoints', 'Enabled'),
            self.check('regionalEndpointHostNames', [f'{registry_name}.westus.geo.azurecr.io']),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('acr show -g {rg} -n {registry_name}', checks=[
            self.check('regionalEndpoints', 'Enabled'),
            self.check('regionalEndpointHostNames', [f'{registry_name}.westus.geo.azurecr.io'])
        ])

        self.cmd('acr show-endpoints --name {registry_name} --resource-group {rg}', checks=[
            self.check('length(dataEndpoints)', 1),
            self.check('length(regionalEndpoints)', 1),
            self.check('dataEndpoints[0].endpoint', '*.blob.core.windows.net'),
            self.check('dataEndpoints[0].region', 'westus'),
            self.check('regionalEndpoints[0].endpoint', f'{registry_name}.westus.geo.azurecr.io'),
            self.check('regionalEndpoints[0].region', 'westus')
        ])

        self.cmd('acr update -g {rg} -n {registry_name} --regional-endpoints disabled', checks=[
            self.check('regionalEndpoints', 'Disabled'),
            self.check('regionalEndpointHostNames', [])
        ])

        self.cmd('acr show-endpoints --name {registry_name} --resource-group {rg}', checks=[
            self.check('length(dataEndpoints)', 1),
            self.check('dataEndpoints[0].endpoint', '*.blob.core.windows.net'),
            self.check('dataEndpoints[0].region', 'westus'),
        ])

        self.cmd('acr delete -g {rg} -n {registry_name} --yes')


    @ResourceGroupPreparer(name_prefix='cli_test_acrre_')
    def test_acr_create_with_regional_endpoints_disabled(self):
        registry_name = self.create_random_name('clitestre', length=16)

        self.kwargs.update({
            'registry_name': registry_name,
            'sku': 'Premium'
        })

        self.cmd('acr create -g {rg} -n {registry_name} --sku {sku} --location westus --regional-endpoints disabled', checks=[
            self.check('name', registry_name),
            self.check('regionalEndpoints', 'Disabled'),
            self.check('regionalEndpointHostNames', []),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('acr show -g {rg} -n {registry_name}', checks=[
            self.check('regionalEndpoints', 'Disabled'),
            self.check('regionalEndpointHostNames', [])
        ])

        self.cmd('acr update -g {rg} -n {registry_name} --regional-endpoints enabled', checks=[
            self.check('regionalEndpoints', 'Enabled'),
            self.check('regionalEndpointHostNames', [f'{registry_name}.westus.geo.azurecr.io'])
        ])

        self.cmd('acr delete -g {rg} -n {registry_name} --yes')


    @ResourceGroupPreparer(name_prefix='cli_test_acrre_')
    def test_acr_login(self):
        registry_name = self.create_random_name('clireg', 20)

        self.kwargs.update({
            'registry_name': registry_name,
            'sku': 'Premium'
        })

        self.cmd('acr create -n {registry_name} -g {rg} --sku {sku} --location westus --regional-endpoints enabled',
                 checks=[self.check('name', registry_name),
                         self.check('regionalEndpoints', 'Enabled'),
                         self.check('provisioningState', 'Succeeded')])

        # using --expose-token and --endpoint at the same time is not supported
        with self.assertRaises(CLIError) as ex:
            self.cmd('acr login -n {} --expose-token --endpoint westus'.format(registry_name))

        self.cmd('acr delete -g {rg} -n {registry_name} --yes')


    @ResourceGroupPreparer(name_prefix='cli_test_acrre_')
    @AllowLargeResponse()
    def test_acr_import_with_regional_endpoints(self):
        source_registry_name = self.create_random_name("sourceregistry", 20)
        registry_name = self.create_random_name("targetregistry", 20)

        self.kwargs.update({
            'resource_id': '/subscriptions/dfb63c8c-7c89-4ef8-af13-75c1d873c895/resourcegroups/resourcegroupdiffsub/providers/Microsoft.ContainerRegistry/registries/sourceregistrydiffsub',
            'source_registry_name': source_registry_name,
            'registry_name': registry_name,
            'rg_loc': 'westus',
            'source_image': 'microsoft:azure-cli',
            'tag': 'repo:v1',
            'source_registry_regional_endpoint': f'{source_registry_name}.westus.geo.azurecr.io',
            'source_image_regional_endpoint': f'{source_registry_name}.westus.geo.azurecr.io/microsoft:azure-cli'
        })

        # Create source registry with regional endpoints enabled
        self.cmd('acr create -n {source_registry_name} -g {rg} -l {rg_loc} --sku Premium --regional-endpoints enabled',
                 checks=[self.check('name', '{source_registry_name}'),
                         self.check('regionalEndpoints', 'Enabled'),
                         self.check('provisioningState', 'Succeeded')])

        # Import image from a registry in a different subscription from the current one
        self.cmd('acr import -n {source_registry_name} -r {resource_id} --source {source_image}')

        # Create a target registry to hold the imported images
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku Standard',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('provisioningState', 'Succeeded')])

        # Import image using regional endpoint URI directly in source
        self.cmd('acr import -n {registry_name} --source {source_image} -r {source_registry_regional_endpoint} -t {tag}')
        self.cmd('acr import -n {registry_name} --source {source_image_regional_endpoint}')

        # Cleanup
        self.cmd('acr delete -g {rg} -n {registry_name} --yes')
        self.cmd('acr delete -g {rg} -n {source_registry_name} --yes')
