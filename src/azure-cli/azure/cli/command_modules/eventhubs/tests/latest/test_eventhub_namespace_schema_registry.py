# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceSchemaRegistry(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eventhub_schema_registry(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'schemagroup1': self.create_random_name(prefix='schema-nscli1', length=20),
            'schemagroup2': self.create_random_name(prefix='schema-nscli2', length=20),
            'schemagroup3': self.create_random_name(prefix='schema-nscli3', length=20),
            'schemagroup4': self.create_random_name(prefix='schema-nscli3', length=20),
            'groupproperty': 'k1=v1 k2=v2'
        })

        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --sku Premium')

        self.cmd('eventhubs namespace schema-registry create -g {rg} --namespace-name {namespacename} --name {schemagroup1} --schema-compatibility Forward --schema-type Avro --group-properties {groupproperty}')

        sg = self.cmd('eventhubs namespace schema-registry show -g {rg} --namespace-name {namespacename} --name {schemagroup1}').get_output_in_json()

        self.assertEqual(sg['name'], self.kwargs['schemagroup1'])
        self.assertEqual(sg['schemaCompatibility'], 'Forward')
        self.assertEqual(sg['schemaType'], 'Avro')
        self.assertEqual(sg['groupProperties'], {'k1':'v1', 'k2':'v2'})

        self.cmd(
            'eventhubs namespace schema-registry create -g {rg} --namespace-name {namespacename} --name {schemagroup2} --schema-compatibility Backward --schema-type Avro --group-properties {groupproperty}')

        sg = self.cmd(
            'eventhubs namespace schema-registry show -g {rg} --namespace-name {namespacename} --name {schemagroup2}').get_output_in_json()

        self.assertEqual(sg['name'], self.kwargs['schemagroup2'])
        self.assertEqual(sg['schemaCompatibility'], 'Backward')
        self.assertEqual(sg['schemaType'], 'Avro')
        self.assertEqual(sg['groupProperties'], {'k1':'v1', 'k2':'v2'})

        self.cmd(
            'eventhubs namespace schema-registry create -g {rg} --namespace-name {namespacename} --name {schemagroup3} --schema-compatibility None --schema-type Avro')

        sg = self.cmd(
            'eventhubs namespace schema-registry show -g {rg} --namespace-name {namespacename} --name {schemagroup3}').get_output_in_json()

        self.assertEqual(sg['name'], self.kwargs['schemagroup3'])
        self.assertEqual(sg['schemaCompatibility'], 'None')
        self.assertEqual(sg['schemaType'], 'Avro')
        self.assertEqual(sg['groupProperties'], {})

        sg = self.cmd(
            'eventhubs namespace schema-registry list -g {rg} --namespace-name {namespacename}').get_output_in_json()

        self.assertEqual(len(sg), 3)

        self.cmd(
            'eventhubs namespace schema-registry delete -g {rg} --namespace-name {namespacename} --name {schemagroup3}')
        self.cmd(
            'eventhubs namespace schema-registry delete -g {rg} --namespace-name {namespacename} --name {schemagroup2}')
        self.cmd(
            'eventhubs namespace schema-registry delete -g {rg} --namespace-name {namespacename} --name {schemagroup1}')

        time.sleep(30)

        sg = self.cmd(
            'eventhubs namespace schema-registry list -g {rg} --namespace-name {namespacename}').get_output_in_json()

        self.assertEqual(len(sg), 0)


