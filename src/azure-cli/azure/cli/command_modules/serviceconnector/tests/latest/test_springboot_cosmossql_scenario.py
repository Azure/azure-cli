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
from ._test_utils import CredentialReplacer, UserMICredentialReplacer


@unittest.skip('Need spring-cloud and spring extension installed')
class SpringBootCosmosSqlScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(SpringBootCosmosSqlScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer(), UserMICredentialReplacer()]
        )

    # @record_only
    def test_springboot_cosmossql_secret_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmossql',
            'deployment': 'default',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn_secret'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosSql).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-sql --connection {} --source-id {} --target-id {} '
                 '--secret --client-type springBoot'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'springBoot')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id), 
                 checks = [
                     self.check('configurations[0].name', 'azure.cosmos.uri'),
                     self.check('configurations[0].note', 'This configuration property is used in Spring Cloud Azure version 3.x and below.'),
                     self.check('configurations[1].name', 'azure.cosmos.key'),
                     self.check('configurations[1].note', 'This configuration property is used in Spring Cloud Azure version 3.x and below.'),
                     self.check('configurations[2].name', 'azure.cosmos.database'),
                     self.check('configurations[2].note', 'This configuration property is used in Spring Cloud Azure version 3.x and below.'),
                     self.check('configurations[3].name', 'spring.cloud.azure.cosmos.endpoint'),
                     self.check('configurations[3].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[4].name', 'spring.cloud.azure.cosmos.database'),
                     self.check('configurations[4].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[5].name', 'spring.cloud.azure.cosmos.key'),
                     self.check('configurations[5].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                 ])

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))

    # @record_only
    def test_springboot_cosmossql_umi_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmossql',
            'deployment': 'default',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn_umi'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosSql).format(**self.kwargs)

        # get user identity id
        user_identity_name = 'servicelinker-springcloud-identity'
        client_id = self.cmd('identity show -n {} -g {}'.format(user_identity_name, self.kwargs['source_resource_group'])).get_output_in_json().get('clientId')

        # create connection
        self.cmd('spring connection create cosmos-sql --connection {} --source-id {} --target-id {} '
                 '--user-identity client-id={} subs-id={} --client-type springBoot'.format(name, source_id, target_id, client_id, self.kwargs['subscription']))

        # list connection
        connections = self.cmd(
            'spring connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAssignedIdentity'),
                self.check('[0].clientType', 'springBoot')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring connection list-configuration --id {}'.format(connection_id), 
                 checks = [
                     self.check('configurations[0].name', 'spring.cloud.azure.cosmos.endpoint'),
                     self.check('configurations[0].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[1].name', 'spring.cloud.azure.cosmos.database'),
                     self.check('configurations[1].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[2].name', 'spring.cloud.azure.cosmos.credential.managed-identity-enabled'),
                     self.check('configurations[2].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[3].name', 'spring.cloud.azure.cosmos.credential.client-id'),
                     self.check('configurations[3].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                 ])

        # validate connection
        self.cmd('spring connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring connection delete --id {} --yes'.format(connection_id))

    # @record_only
    def test_springboot_cosmossql_smi_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmossql',
            'deployment': 'default',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn_smi'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosSql).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-sql --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type springBoot'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'springBoot')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring connection list-configuration --id {}'.format(connection_id), 
                 checks = [
                     self.check('configurations[0].name', 'spring.cloud.azure.cosmos.endpoint'),
                     self.check('configurations[0].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[1].name', 'spring.cloud.azure.cosmos.database'),
                     self.check('configurations[1].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.'),
                     self.check('configurations[2].name', 'spring.cloud.azure.cosmos.credential.managed-identity-enabled'),
                     self.check('configurations[2].note', 'This configuration property is used in Spring Cloud Azure version 4.0 and above.')
                 ])

        # validate connection
        self.cmd('spring connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring connection delete --id {} --yes'.format(connection_id))
