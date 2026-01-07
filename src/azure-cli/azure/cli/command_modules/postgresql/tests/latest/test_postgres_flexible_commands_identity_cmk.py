# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    ResourceGroupPreparer,
    KeyVaultPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class FlexibleServerIdentityCMKMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @KeyVaultPreparer(name_prefix='pgvault', parameter_name='vault_name', location=postgres_location, additional_params='--enable-purge-protection true --retention-days 90 --no-self-perms')
    def test_postgres_flexible_server_cmk_mgmt(self, resource_group, vault_name):
        self._test_flexible_server_cmk_mgmt(resource_group, vault_name)

    def _test_flexible_server_cmk_mgmt(self, resource_group, vault_name):
        live_test = os.environ.get(ENV_LIVE_TEST, False)
        key_name = self.create_random_name('pgkey', 32)
        identity_name = self.create_random_name('identity', 32)
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        tier = 'GeneralPurpose'
        sku_name = 'Standard_D2ds_v4'
        location = self.postgres_location
        replication_role = 'AsyncReplica'
        scope = '/subscriptions/{}/resourceGroups/{}'.format(self.get_subscription_id(), resource_group)

        # Create identity and assign role
        key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                       .format(key_name, vault_name)).get_output_in_json()

        identity = self.cmd('identity create -g {} --name {} --location {}'.format(resource_group, identity_name, location)).get_output_in_json()
        if (live_test):
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Crypto User" --scope {}'.format( identity['principalId'], scope))
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Certificate User" --scope {}'.format( identity['principalId'], scope))

        # create primary flexible server with data encryption
        self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} --location {}'.format(
                    resource_group,
                    server_name,
                    tier,
                    sku_name,
                    key['key']['kid'],
                    identity['id'],
                    location
                ))

        # should fail because we can't remove identity used for data encryption
        self.cmd('postgres flexible-server identity remove -g {} -s {} -n {} --yes'
                    .format(resource_group, server_name, identity['id']),
                    expect_failure=True)

        main_checks = [
            JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity['id'])),
            JMESPathCheck('dataEncryption.primaryKeyUri', key['key']['kid']),
            JMESPathCheck('dataEncryption.primaryUserAssignedIdentityId', identity['id'])
        ]

        # create replica 1 with data encryption            
        replica_1_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {} --key {} --identity {}'.format(
                    resource_group,
                    replica_1_name,
                    server_name,
                    key['key']['kid'],
                    identity['id']
        ), checks=main_checks + [JMESPathCheck('replicationRole', replication_role)])

        # delete all servers
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, replica_1_name))
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, server_name))