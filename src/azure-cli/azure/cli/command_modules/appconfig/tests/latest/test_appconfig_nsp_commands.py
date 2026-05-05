# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, live_only
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.command_modules.appconfig.tests.latest._test_utils import CredentialResponseSanitizer, get_resource_name_prefix


class AppconfigNspLiveScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @live_only()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse(size_kb=99999)
    def test_azconfig_nsp_mgmt(self, resource_group, location):
        store_name_prefix = get_resource_name_prefix('NspStore')
        nsp_name_prefix = get_resource_name_prefix('Nsp')
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=24)
        nsp_name = self.create_random_name(prefix=nsp_name_prefix, length=24)

        store_location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'nsp_name': nsp_name,
            'rg_loc': store_location,
            'rg': resource_group,
            'sku': sku,
            'retention_days': 1,
            'enable_purge_protection': False
        })

        # Ensure the nsp extension is installed; `network perimeter` commands ship in this extension.
        self.cmd('extension add -n nsp')

        # Create the App Configuration store
        self.cmd(
            'appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}',
            checks=[
                self.check('name', '{config_store_name}'),
                self.check('location', '{rg_loc}'),
                self.check('resourceGroup', resource_group),
                self.check('provisioningState', 'Succeeded'),
                self.check('sku.name', sku)
            ])

        # Create a Network Security Perimeter and associate it with the store
        self.cmd(
            'network perimeter create -n {nsp_name} -g {rg} -l {rg_loc}',
            checks=[
                self.check('name', '{nsp_name}'),
                self.check('location', '{rg_loc}')
            ])

        nsp_id = self.cmd('network perimeter show -n {nsp_name} -g {rg}').get_output_in_json()['id']
        store_id = self.cmd('appconfig show -n {config_store_name} -g {rg}').get_output_in_json()['id']

        association_name_prefix = get_resource_name_prefix('NspAssoc')
        profile_name_prefix = get_resource_name_prefix('NspProfile')
        association_name = self.create_random_name(prefix=association_name_prefix, length=24)
        profile_name = self.create_random_name(prefix=profile_name_prefix, length=24)

        self.kwargs.update({
            'nsp_id': nsp_id,
            'store_id': store_id,
            'association_name': association_name,
            'profile_name': profile_name
        })

        # Create an NSP profile, then associate the store with the NSP
        self.cmd(
            'network perimeter profile create -n {profile_name} --perimeter-name {nsp_name} -g {rg}')

        profile_id = self.cmd(
            'network perimeter profile show -n {profile_name} --perimeter-name {nsp_name} -g {rg}'
        ).get_output_in_json()['id']

        self.kwargs.update({'profile_id': profile_id})

        self.cmd(
            'network perimeter association create -n {association_name} --perimeter-name {nsp_name} -g {rg} --private-link-resource "{{\\"id\\":\\"{store_id}\\"}}" --profile "{{\\"id\\":\\"{profile_id}\\"}}" --access-mode Learning')

        # List NSP configurations on the store — should return at least one entry
        nsp_configs = self.cmd(
            'appconfig network-security-perimeter-configuration list -s {config_store_name} -g {rg}',
            checks=[
                self.check('type(@)', 'array')
            ]).get_output_in_json()

        self.assertTrue(len(nsp_configs) > 0, "Expected at least one NSP configuration.")

        nsp_config_name = nsp_configs[0]['name']
        self.kwargs.update({'nsp_config_name': nsp_config_name})

        # Show the specific NSP configuration
        self.cmd(
            'appconfig network-security-perimeter-configuration show -s {config_store_name} -g {rg} -n {nsp_config_name}',
            checks=[
                self.check('name', '{nsp_config_name}')
            ])

        # Reconcile the NSP configuration
        self.cmd(
            'appconfig network-security-perimeter-configuration reconcile -s {config_store_name} -g {rg} -n {nsp_config_name}')

        # Show a non-existent NSP configuration — expect ResourceNotFoundError
        with self.assertRaises(ResourceNotFoundError):
            self.cmd('appconfig network-security-perimeter-configuration show -s {config_store_name} -g {rg} -n nonexistent-nsp-config')

        # Cleanup
        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')
