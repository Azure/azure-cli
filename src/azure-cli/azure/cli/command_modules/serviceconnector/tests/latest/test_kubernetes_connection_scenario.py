# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import unittest

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk import (
    ScenarioTest,
    record_only,
    live_only
)
from azure.cli.command_modules.serviceconnector._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES
)
from ._test_utils import CredentialReplacer, ConfigCredentialReplacer


class KubernetesConnectionScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(KubernetesConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer(), ConfigCredentialReplacer()]
        )

    @record_only()
    def test_kubernetes_keyvault_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-keyvault-cluster',
            'vault': 'servicelinker-test-kv'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection, test csi feature
        self.cmd('aks connection create keyvault --connection {} --source-id {} --target-id {} '
                 '--client-type python --enable-csi'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAssignedIdentity'),
                self.check('[0].clientType', 'python'),
                self.check('[0].targetService.resourceProperties.type', 'KeyVault'),
                self.check('[0].targetService.resourceProperties.connectAsKubernetesCsiDriver', True)
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update keyvault --id {} --client-type dotnet --enable-csi'.format(connection_id),
                 checks = [ 
                    self.check('clientType', 'dotnet'),
                    self.check('authInfo.authType', 'userAssignedIdentity'), 
                ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_kubernetes_mysql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-mysql-cluster',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection, test clientType=None
        self.cmd('aks connection create mysql --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type none'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'none')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update mysql --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_kubernetes_storageblob_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-storage-cluster',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('aks connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update storage-blob --id {} --client-type dotnet'.format(connection_id),
                 checks = [ 
                     self.check('clientType', 'dotnet'),
                     self.check('authInfo.authType', 'secret')
                ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_kubernetes_servicebus_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-servicebus-cluster',
            'namespace': 'servicelinkertestservicebus'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.ServiceBus).format(**self.kwargs)

        # create connection
        self.cmd('aks connection create servicebus --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update servicebus --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_kubernetes_confluentkafka_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-kafka-cluster',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)

        # create connection
        self.cmd('aks connection create confluent-cloud --connection {} --source-id {} '
                 '--bootstrap-server xxx.eastus.azure.confluent.cloud:9092 --kafka-key Name --kafka-secret Secret '
                 '--schema-registry https://xxx.eastus.azure.confluent.cloud --schema-key Name --schema-secret Secret '
                 '--client-type python'.format(name, source_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 2),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update confluent-cloud --connection {} '
                 '--source-id {} --client-type dotnet --kafka-secret Secret'.format(name, source_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @live_only()
    # "run_cli_cmd" could only work at live mode
    def test_kubernetes_storageblob_workload_identity_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-storage-cluster',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # get user identity id
        user_identity_name = 'servicelinker-k8s-identity'
        user_identity_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{}'.format(
            self.kwargs['subscription'],
            'clitest',
            user_identity_name
        )

        # create connection
        self.cmd('aks connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--workload-identity {} --client-type python'.format(name, source_id, target_id, user_identity_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update storage-blob --id {} --client-type dotnet'.format(connection_id),
                 checks = [
                    self.check('clientType', 'dotnet'),
                    self.check('authInfo.authType', 'userAssignedIdentity')
                ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @unittest.skip("secret store not supported.")
    # key vault connection name differs every run
    def test_kubernetes_storageblob_secretstore_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-storage-cluster',
            'account': 'servicelinkerstorage',
            'vault': 'servicelinker-test-kv',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)
        keyvault_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('aks connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python --vault-id {}'.format(name, source_id, target_id, keyvault_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 2),
                self.check('[0].authInfo.authType', 'userAssignedIdentity'),
                self.check('[0].targetService.resourceProperties.type', 'KeyVault'),
                self.check('[0].targetService.resourceProperties.connectAsKubernetesCsiDriver', True),
                self.check('[1].authInfo.authType', 'secret'),
                self.check('[1].clientType', 'python')
            ]
        ).get_output_in_json()
        storage_connection_id = connections[1].get('id')

        # list configuration
        self.cmd(
            'aks connection list-configuration --id {}'.format(storage_connection_id),
            checks = [
                self.check('configurations[0].name', 'AZURE_STORAGEBLOB_CONNECTIONSTRING'),
                self.check('configurations[0].description', 'Key vault secret.')
            ]    
        )

        # update connection
        self.cmd('aks connection update storage-blob --id {} --client-type dotnet'.format(storage_connection_id),
                 checks = [
                     self.check('clientType', 'dotnet'),
                     self.check('authInfo.authType', 'secret')
                ])

        # validate connection
        self.cmd('aks connection validate --id {}'.format(storage_connection_id))

        # delete connections
        for connection in connections:
            self.cmd('aks connection delete --id {} --yes'.format(connection.get('id')))


    @record_only()
    def test_kubernetes_cognitive_secret_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'sctestcluster',
            'account': 'servicelinkercognitiveservicetest'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CognitiveServices).format(**self.kwargs)

        # create connection
        self.cmd('aks connection create cognitiveservices --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('[-1].targetService.id', target_id),
                self.check('[-1].authInfo.authType', 'secret'),
                self.check('[-1].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[-1].get('id')

        # update connection
        self.cmd('aks connection update cognitiveservices --id {} --client-type dotnet'.format(connection_id),
                 checks = [ 
                     self.check('clientType', 'dotnet'),
                     self.check('authInfo.authType', 'secret')
                ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))


    @live_only()
    # "run_cli_cmd" could only work at live mode
    def test_kubernetes_cognitive_workload_identity_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'sctestcluster',
            'account': 'servicelinkercognitiveservicetest'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CognitiveServices).format(**self.kwargs)

        # get user identity id
        user_identity_name = 'aitest'
        user_identity_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{}'.format(
            self.kwargs['subscription'],
            'servicelinker-test-linux-group',
            user_identity_name
        )

        # create connection
        self.cmd('aks connection create cognitiveservices --connection {} --source-id {} --target-id {} '
                 '--workload-identity {} --client-type python'.format(name, source_id, target_id, user_identity_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks = [
                self.check('[-1].targetService.id', target_id),
                self.check('[-1].authInfo.authType', 'userAssignedIdentity'),
                self.check('[-1].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[-1].get('id')

        # update connection
        self.cmd('aks connection update storage-blob --id {} --client-type dotnet'.format(connection_id),
                 checks = [
                    self.check('clientType', 'dotnet'),
                    self.check('authInfo.authType', 'userAssignedIdentity')
                ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_kubernetes_appconfig_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'cluster': 'servicelinker-storage-cluster',
            'config_store': 'servicelinker-app-configuration'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.KubernetesCluster).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.AppConfig).format(**self.kwargs)

        # create connection
        self.cmd('aks connection create appconfig --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python --use-appconfig-extension'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'aks connection list --source-id {}'.format(source_id),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python'),
                self.check('[0].targetService.resourceProperties.connectWithKubernetesExtension', True)
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('aks connection update appconfig --id {} --client-type dotnet'.format(connection_id),
                 checks=[
                     self.check('clientType', 'dotnet'),
                     self.check('authInfo.authType', 'secret')
        ])

        # list configuration
        self.cmd('aks connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('aks connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('aks connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('aks connection delete --id {} --yes'.format(connection_id))
