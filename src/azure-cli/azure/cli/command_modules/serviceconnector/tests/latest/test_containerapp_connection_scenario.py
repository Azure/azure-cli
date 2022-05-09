# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import unittest
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk import (
    ScenarioTest,
    record_only
)
from azure.cli.command_modules.serviceconnector._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES
)
from ._test_utils import CredentialReplacer


@unittest.skip('Need containerapp extension installed')
class ContainerAppConnectionScenarioTest(ScenarioTest):
    default_container_name = 'simple-hello-world-container'

    def __init__(self, method_name):
        super(ContainerAppConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )


    # @record_only()
    def test_containerapp_mysql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'app': 'servicelinker-mysql-aca',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.ContainerApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection, test clientType=None
        self.cmd('containerapp connection create mysql --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type none -c {}'.format(name, source_id, target_id, user, password, self.default_container_name))

        # list connection
        connections = self.cmd(
            'containerapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'none')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('containerapp connection update mysql --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('containerapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('containerapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('containerapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('containerapp connection delete --id {} --yes'.format(connection_id))


    def test_containerapp_mysql_e2e_kvsecret(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'app': 'servicelinker-mysql-aca',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        keyvaultUri = "https://cupertino-kv-test.vault.azure.net/secrets/TestDbPassword"

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.ContainerApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection, test clientType=None
        self.cmd('containerapp connection create mysql --connection {} --source-id {} --target-id {} '
                 '--secret name={} keyVaultSecretUri={} --client-type none -c {}'.format(name, source_id, target_id, user, keyvaultUri, self.default_container_name))

        # list connection
        connections = self.cmd(
            'containerapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'none')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # delete connection
        self.cmd('containerapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_containerapp_storageblob_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'app': 'servicelinker-storage-aca',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.ContainerApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('containerapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python -c {}'.format(name, source_id, target_id, self.default_container_name))

        # list connection
        connections = self.cmd(
            'containerapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('containerapp connection update storage-blob --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('containerapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('containerapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('containerapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('containerapp connection delete --id {} --yes'.format(connection_id))
