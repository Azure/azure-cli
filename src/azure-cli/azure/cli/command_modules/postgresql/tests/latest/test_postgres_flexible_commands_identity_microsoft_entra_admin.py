# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckNotExists,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, DEFAULT_LOCATION


class FlexibleServerIdentityMicrosoftEntraAdminMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_postgresql_flexible_server_identity_microsoft_entra_admin_mgmt(self, resource_group):
        self._test_identity_microsoft_entra_admin_mgmt(resource_group, 'enabled')

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_postgresql_flexible_server_identity_microsoft_entra_admin_only_mgmt(self, resource_group):
        self._test_identity_microsoft_entra_admin_mgmt(resource_group, 'disabled')

    def _test_identity_microsoft_entra_admin_mgmt(self, resource_group, password_auth):
        location = DEFAULT_LOCATION
        server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        storage_size = 128
        sku_name = 'Standard_D4ds_v4'
        tier = 'GeneralPurpose'
        login = 'aaa@foo.com'
        sid = '894ef8da-7971-4f68-972c-f561441eb329'
        admin_id_arg = '-i {}'.format(sid)
        replica = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) for _ in range(2)]

        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} --tier {} --storage-size {} -l {} --public-access none --yes'.format(
                 resource_group, server, sku_name, tier, storage_size, location))

        # Update existing server with authentication settings
        auth_args = '--password-auth {} --microsoft-entra-auth enabled'.format(password_auth)
        self.cmd('postgres flexible-server update -g {} -n {} {}'
                 .format(resource_group, server, auth_args))

        # Create 2 identities
        identity = []
        identity_id = []
        for i in range(2):
            identity.append(self.create_random_name('identity', 32))
            result = self.cmd('identity create -g {} --name {}'.format(resource_group, identity[i])).get_output_in_json()
            identity_id.append(result['id'])

        # Add identity 1 to primary server
        self.cmd('postgres flexible-server identity assign -g {} -s {} -n {}'
                 .format(resource_group, server, identity_id[0]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0]))])

        # Create replica 1
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                 .format(resource_group, replica[0], server))

        # Assign identity 1 to replica 1
        self.cmd('postgres flexible-server identity assign -g {} -s {} -n {}'
                 .format(resource_group, replica[0], identity_id[0]))

        self.cmd('postgres flexible-server identity list -g {} -s {}'
                 .format(resource_group, replica[0]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0]))])

        admins = self.cmd('postgres flexible-server microsoft-entra-admin list -g {} -s {}'
                          .format(resource_group, server)).get_output_in_json()
        self.assertEqual(0, len(admins))

        # Add identity 2 to replica 1 and primary server
        for server_name in [replica[0], server]:
            self.cmd('postgres flexible-server identity assign -g {} -s {} -n {}'
                        .format(resource_group, server_name, identity_id[1]),
                        checks=[
                            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        # Try to add Microsoft Entra admin to replica 1
        self.cmd('postgres flexible-server microsoft-entra-admin create -g {} -s {} -u {} -i {}'
                    .format(resource_group, replica[0], login, sid),
                    expect_failure=True)
        
        # Add Microsoft Entra admin to primary server
        admin_checks = [JMESPathCheck('principalType', 'User'),
                        JMESPathCheck('principalName', login),
                        JMESPathCheck('objectId', sid)]

        self.cmd('postgres flexible-server microsoft-entra-admin create -g {} -s {} -u {} -i {}'
                    .format(resource_group, server, login, sid))

        for server_name in [server, replica[0]]:
            self.cmd('postgres flexible-server microsoft-entra-admin show -g {} -s {} {}'
                    .format(resource_group, server_name, admin_id_arg),
                    checks=admin_checks)

            self.cmd('postgres flexible-server identity list -g {} -s {}'
                    .format(resource_group, server_name),
                    checks=[
                        JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                        JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        # Create replica 2
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                 .format(resource_group, replica[1], server))

        # Assign identities 1 and 2 to replica 2
        self.cmd('postgres flexible-server identity assign -g {} -s {} -n {} {}'
                 .format(resource_group, replica[1], identity_id[0], identity_id[1]))

        self.cmd('postgres flexible-server identity list -g {} -s {}'
                 .format(resource_group, replica[1]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        self.cmd('postgres flexible-server microsoft-entra-admin show -g {} -s {} {}'
                    .format(resource_group, replica[1], admin_id_arg),
                    checks=admin_checks)

        # Verify that authConfig.activeDirectoryAuth=enabled and authConfig.passwordAuth=disabled in primary server and all replicas
        for server_name in [server, replica[0], replica[1]]:
            list_checks = [JMESPathCheck('authConfig.activeDirectoryAuth', 'enabled', False),
                        JMESPathCheck('authConfig.passwordAuth', password_auth, False)]
            self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name), checks=list_checks)

        # Try to remove Microsoft Entra admin from replica 2
        self.cmd('postgres flexible-server microsoft-entra-admin delete -g {} -s {} {} --yes'
                 .format(resource_group, replica[1], admin_id_arg),
                 expect_failure=True)

        # Remove Microsoft Entra admin from primary server
        self.cmd('postgres flexible-server microsoft-entra-admin delete -g {} -s {} {} --yes'
                 .format(resource_group, server, admin_id_arg))

        for server_name in [server, replica[0], replica[1]]:
            admins = self.cmd('postgres flexible-server microsoft-entra-admin list -g {} -s {}'
                              .format(resource_group, server_name)).get_output_in_json()
            self.assertEqual(0, len(admins))

        # Remove identities 1 and 2 from primary server
        self.cmd('postgres flexible-server identity remove -g {} -s {} -n {} {} --yes'
                 .format(resource_group, server, identity_id[0], identity_id[1]))

        # Remove identities 1 and 2 from replica 1 and 2
        for server_name in [replica[0], replica[1]]:
            self.cmd('postgres flexible-server identity remove -g {} -s {} -n {} {} --yes'
                     .format(resource_group, server_name, identity_id[0], identity_id[1]))
        for server_name in [server, replica[0], replica[1]]:
            self.cmd('postgres flexible-server identity list -g {} -s {}'
                     .format(resource_group, server_name),
                     checks=[
                         JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                         JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[1]))])