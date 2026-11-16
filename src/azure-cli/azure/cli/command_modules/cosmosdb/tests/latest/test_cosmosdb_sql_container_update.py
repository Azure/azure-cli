# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import shlex
import unittest
from unittest import mock

from azure.cli.core import MainCommandsLoader
from azure.cli.core.commands import _load_module_command_loader
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.reverse_dependency import get_dummy_cli
from azure.cli.command_modules.cosmosdb.custom import cli_cosmosdb_sql_container_update
from azure.mgmt.cosmosdb.models import (
    ComputedProperty,
    ContainerPartitionKey,
    IncludedPath,
    IndexingPolicy,
    SqlContainerCreateUpdateParameters,
    SqlContainerResource,
    SqlContainerGetPropertiesResource,
    SqlContainerGetResults,
)


class _SqlContainerTestCommandsLoader(MainCommandsLoader):

    def load_command_table(self, args):
        command_table, group_table, loader = _load_module_command_loader(self, args, 'cosmosdb')
        self.command_table.update(command_table)
        self.command_group_table.update(group_table)
        self.cmd_to_loader_map.update({name: [loader] for name in command_table})
        return self.command_table


class CosmosdbSqlContainerUpdateTest(unittest.TestCase):

    def setUp(self):
        self.computed_properties = [
            ComputedProperty(name='normalizedName', query='SELECT VALUE UPPER(c.name) FROM c'),
            ComputedProperty(name='nameLength', query='SELECT VALUE LENGTH(c.name) FROM c'),
        ]
        self.resource = SqlContainerGetPropertiesResource(
            id='container',
            partition_key=ContainerPartitionKey(paths=['/pk'], kind='Hash'),
            indexing_policy=IndexingPolicy(
                indexing_mode='consistent', included_paths=[IncludedPath(path='/*')]),
            default_ttl=-1,
            computed_properties=self.computed_properties,
        )
        self.client = mock.Mock()
        self.client.get_sql_container.return_value = SqlContainerGetResults(resource=self.resource)

    def _assert_request(self):
        update = self.client.begin_create_update_sql_container
        update.assert_called_once()
        parameters = update.call_args.args[-1]
        update.assert_called_once_with(
            'resource-group', 'account', 'database', 'container', parameters)
        self.assertIs(type(parameters), SqlContainerCreateUpdateParameters)
        self.assertIs(type(parameters.resource), SqlContainerResource)
        if parameters.resource.computed_properties is not None:
            for prop in parameters.resource.computed_properties:
                self.assertIs(type(prop), ComputedProperty)
        payload = parameters.as_dict()['properties']['resource']
        self.assertEqual(payload['id'], self.resource.id)
        self.assertEqual(payload['partitionKey'], self.resource.partition_key.as_dict())
        return payload

    def _update(self, **kwargs):
        result = cli_cosmosdb_sql_container_update(
            self.client, 'resource-group', 'account', 'database', 'container', **kwargs)
        self.client.get_sql_container.assert_called_once_with(
            'resource-group', 'account', 'database', 'container')
        self.assertIs(result, self.client.begin_create_update_sql_container.return_value)
        return self._assert_request()

    def test_indexing_update_preserves_computed_properties(self):
        indexing_policy = {
            'indexingMode': 'consistent',
            'includedPaths': [{'path': '/normalizedName/?'}, {'path': '/nameLength/?'}],
        }
        payload = self._update(indexing_policy=indexing_policy)
        self.assertEqual(payload['indexingPolicy'], indexing_policy)
        self.assertEqual(payload['computedProperties'], [prop.as_dict() for prop in self.computed_properties])
        self.assertEqual(payload['defaultTtl'], -1)
        self.assertEqual(self.resource.indexing_policy.included_paths[0].path, '/*')

    def test_non_indexing_updates_preserve_computed_properties(self):
        for argument, field in [('default_ttl', 'defaultTtl'), ('analytical_storage_ttl', 'analyticalStorageTtl')]:
            with self.subTest(argument=argument):
                self.client.reset_mock()
                payload = self._update(**{argument: 3600})
                self.assertEqual(payload[field], 3600)
                self.assertEqual(payload['indexingPolicy'], self.resource.indexing_policy.as_dict())
                self.assertEqual(payload['computedProperties'], [prop.as_dict() for prop in self.computed_properties])

    def test_update_without_computed_properties(self):
        for computed_properties in [None, []]:
            with self.subTest(computed_properties=computed_properties):
                self.client.reset_mock()
                self.resource.computed_properties = computed_properties
                payload = self._update(default_ttl=3600)
                self.assertEqual(payload['defaultTtl'], 3600)
                self.assertEqual(payload['indexingPolicy'], self.resource.indexing_policy.as_dict())
                if computed_properties is None:
                    self.assertNotIn('computedProperties', payload)
                else:
                    self.assertEqual(payload['computedProperties'], [])

    def test_public_update_and_show_preserve_computed_properties(self):
        def update(*args):
            resource = SqlContainerGetPropertiesResource(args[-1].resource.as_dict())
            response = SqlContainerGetResults(resource=resource)
            self.client.get_sql_container.return_value = response
            return response

        self.client.begin_create_update_sql_container.side_effect = update
        cli = get_dummy_cli(commands_loader_cls=_SqlContainerTestCommandsLoader)
        command = 'az cosmosdb sql container {} -g resource-group -a account -d database -n container'
        indexing_policy = {'indexingMode': 'consistent', 'includedPaths': [{'path': '/normalizedName/?'}]}
        expected = [prop.as_dict() for prop in self.computed_properties]
        with mock.patch('azure.cli.command_modules.cosmosdb.commands.cf_sql_resources', return_value=self.client):
            for option in ['--idx ' + shlex.quote(json.dumps(indexing_policy)), '--ttl 3600']:
                with self.subTest(option=option):
                    self.client.reset_mock()
                    output = execute(cli, command.format('update') + ' ' + option).get_output_in_json()
                    self._assert_request()
                    self.assertEqual(output['resource']['computedProperties'], expected)
                    with mock.patch('azure.mgmt.cosmosdb.operations.SqlResourcesOperations.get_sql_container',
                                    autospec=True, return_value=self.client.get_sql_container.return_value):
                        output = execute(cli, command.format('show')).get_output_in_json()
                    self.assertEqual(output['resource']['computedProperties'], expected)
