# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json

from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.azclierror import ResourceNotFoundError
from azure.cli.command_modules.appconfig.tests.latest._test_utils import CredentialResponseSanitizer

class AppconfigReplicaLiveScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_replica_mgmt(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='ReplicaStore', length=24)
        replica_name = self.create_random_name(prefix='Replica', length=24)

        store_location = 'eastus'
        replica_location = 'westus'
        sku = 'standard'
        tag_key = "key"
        tag_value = "value"
        tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        system_assigned_identity = '[system]'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'replica_name': replica_name,
            'rg_loc': store_location,
            'replica_loc': replica_location,
            'rg': resource_group,
            'sku': sku,
            'tags': tag,
            'identity': system_assigned_identity,
            'retention_days': 1,
            'enable_purge_protection': False
        })

        store = self.cmd(
            'appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('sku.name', sku),
                    self.check('tags', structured_tag),
                    self.check('identity.type', 'SystemAssigned'),
                    self.check('softDeleteRetentionInDays', '{retention_days}'),
                    self.check('enablePurgeProtection', '{enable_purge_protection}')]).get_output_in_json()

        self.cmd('appconfig replica create -s {config_store_name} -g {rg} -l {replica_loc} -n {replica_name}',
                 checks=[self.check('name', '{replica_name}'),
                         self.check('location', '{replica_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('appconfig replica show -s {config_store_name} -g {rg} -n {replica_name}',
                 checks=[self.check('name', '{replica_name}'),
                         self.check('location', '{replica_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('appconfig replica list -s {config_store_name}',
                 checks=[self.check('[0].name', '{replica_name}'),
                         self.check('[0].location', '{replica_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded')])

        self.cmd('appconfig replica delete -s {config_store_name} -g {rg} -n {replica_name} -y')

        with self.assertRaisesRegex(ResourceNotFoundError, f"The replica '{replica_name}' for App Configuration '{config_store_name}' not found."):
            self.cmd('appconfig replica show -s {config_store_name} -g {rg} -n {replica_name}')

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')
