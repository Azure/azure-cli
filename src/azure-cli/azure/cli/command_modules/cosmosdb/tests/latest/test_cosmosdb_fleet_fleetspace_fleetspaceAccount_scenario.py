# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import os
import json
import tempfile
import shlex
import unittest
from argparse import Namespace
from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

import yaml
from azure.cli.core import MainCommandsLoader
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.commands import _load_module_command_loader
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.reverse_dependency import get_dummy_cli
from azure.cli.command_modules.cosmosdb._validators import (
    validate_fleetspace_body, validate_fleetspace_create_body, validate_fleetspaceAccount_body,
)
from azure.cli.command_modules.cosmosdb.custom import (
    cli_cosmosdb_fleetspace_create, cli_cosmosdb_fleetspace_update, cli_cosmosdb_fleetspace_account_create,
)
from azure.mgmt.cosmosdb.models import (
    FleetspaceResource, FleetspacePropertiesThroughputPoolConfiguration,
    FleetspaceAccountResource, FleetspaceAccountPropertiesGlobalDatabaseAccountProperties,
)


class CosmosdbFleetValidationTest(unittest.TestCase):

    def setUp(self):
        self.properties = {
            'serviceTier': 'GeneralPurpose', 'dataRegions': ['West US 2'],
            'throughputPoolConfiguration': {'minThroughput': 100000, 'maxThroughput': 300000},
        }
        self.account_id = ('/subscriptions/00000000-0000-0000-0000-000000000000/'
                           'resourceGroups/example-rg/providers/Microsoft.DocumentDB/databaseAccounts/myaccount')
        self.account_properties = {'resourceId': self.account_id, 'armLocation': 'westus2'}
        self.client = mock.Mock()

    def _validate(self, body, is_create=True):
        namespace = Namespace(fleetspace_body=json.dumps(body))
        validator = validate_fleetspace_create_body if is_create else validate_fleetspace_body
        validator(None, namespace)
        return namespace.fleetspace_body

    def _validate_account(self, properties):
        namespace = Namespace(fleetspace_account_body=json.dumps({
            'properties': {'globalDatabaseAccountProperties': properties}}))
        validate_fleetspaceAccount_body(None, namespace)
        return namespace.fleetspace_account_body

    def test_non_pooled_create_normalizes_and_omits_pool(self):
        for configuration in ['absent', None, {}]:
            with self.subTest(configuration=configuration):
                properties = deepcopy(self.properties)
                if configuration == 'absent':
                    del properties['throughputPoolConfiguration']
                else:
                    properties['throughputPoolConfiguration'] = configuration
                body = self._validate({'properties': properties})
                self.assertNotIn('throughputPoolConfiguration', body['properties'])
                cli_cosmosdb_fleetspace_create(self.client, 'rg', 'fleet', 'space', body)
                resource = self.client.begin_create.call_args.kwargs['body']
                self.assertIs(type(resource), FleetspaceResource)
                self.assertIsNone(resource.throughput_pool_configuration)
                self.assertEqual(resource.as_dict(), {'properties': {
                    'fleetspaceApiKind': 'NoSQL', 'serviceTier': 'GeneralPurpose', 'dataRegions': ['West US 2']}})

    def test_pooled_create_and_update_keep_typed_request(self):
        for is_create in [True, False]:
            with self.subTest(is_create=is_create):
                body = self._validate({'properties': self.properties}, is_create=is_create)
                handler = cli_cosmosdb_fleetspace_create if is_create else cli_cosmosdb_fleetspace_update
                handler(self.client, 'rg', 'fleet', 'space', body)
                operation = self.client.begin_create if is_create else self.client.begin_update
                resource = operation.call_args.kwargs['body']
                self.assertIs(type(resource), FleetspaceResource)
                self.assertIs(type(resource.throughput_pool_configuration), FleetspacePropertiesThroughputPoolConfiguration)
                self.assertEqual(resource.as_dict(), {'properties': dict(self.properties, fleetspaceApiKind='NoSQL')})

    def test_numeric_types_values_and_bounds(self):
        for is_create in [True, False]:
            for field in ['minThroughput', 'maxThroughput']:
                for value in [True, False, 1.5, '100000', None, 0, -1]:
                    with self.subTest(is_create=is_create, field=field, value=value):
                        properties = deepcopy(self.properties)
                        properties['throughputPoolConfiguration'][field] = value
                        with self.assertRaisesRegex(InvalidArgumentValueError, 'positive integer'):
                            self._validate({'properties': properties}, is_create=is_create)
            properties = deepcopy(self.properties)
            properties['throughputPoolConfiguration'] = {'minThroughput': 300000, 'maxThroughput': 100000}
            with self.assertRaisesRegex(InvalidArgumentValueError, 'greater than or equal'):
                self._validate({'properties': properties}, is_create=is_create)
            for value in [100000, 2 ** 40]:
                properties['throughputPoolConfiguration'] = {'minThroughput': value, 'maxThroughput': value}
                self._validate({'properties': properties}, is_create=is_create)

    def test_partial_configuration_is_rejected_for_create_and_update(self):
        for is_create in [True, False]:
            for field in ['minThroughput', 'maxThroughput']:
                with self.subTest(is_create=is_create, field=field):
                    properties = deepcopy(self.properties)
                    del properties['throughputPoolConfiguration'][field]
                    with self.assertRaisesRegex(InvalidArgumentValueError, 'Missing'):
                        self._validate({'properties': properties}, is_create=is_create)

    def test_update_still_rejects_absent_null_empty_pool(self):
        for properties in [{}, {'throughputPoolConfiguration': None}, {'throughputPoolConfiguration': {}}]:
            with self.subTest(properties=properties):
                with self.assertRaisesRegex(InvalidArgumentValueError, 'throughputPoolConfiguration'):
                    self._validate({'properties': properties}, is_create=False)

    def test_malformed_body_and_pool_are_rejected(self):
        for is_create in [True, False]:
            for body in [None, [], True, 'body', {}, {'properties': None}, {'properties': []}]:
                with self.subTest(is_create=is_create, body=body):
                    with self.assertRaises(InvalidArgumentValueError):
                        self._validate(body, is_create=is_create)
            for configuration in [False, True, 0, '', [], 'pool']:
                with self.subTest(is_create=is_create, configuration=configuration):
                    with self.assertRaises(InvalidArgumentValueError):
                        self._validate({'properties': dict(self.properties, throughputPoolConfiguration=configuration)},
                                       is_create=is_create)

    def test_create_requires_nonblank_tier_and_regions(self):
        for field, values in [('serviceTier', [None, '', '  ', 1, False]),
                              ('dataRegions', [None, [], '', [''], ['  '], [1], ['westus2', None]])]:
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(InvalidArgumentValueError):
                        self._validate({'properties': dict(self.properties, **{field: value})})
            properties = deepcopy(self.properties)
            del properties[field]
            with self.assertRaises(InvalidArgumentValueError):
                self._validate({'properties': properties})

    def test_account_id_and_name_preserve_case_and_typed_body(self):
        for resource_id in [self.account_id, self.account_id.upper()]:
            for name in ['myaccount', 'MyAccount']:
                with self.subTest(resource_id=resource_id, name=name):
                    body = self._validate_account(dict(self.account_properties, resourceId=resource_id))
                    cli_cosmosdb_fleetspace_account_create(self.client, 'rg', 'fleet', 'space', name, body)
                    arguments = self.client.begin_create.call_args.kwargs
                    self.assertEqual(arguments['fleetspace_account_name'], name)
                    resource = arguments['body']
                    self.assertIs(type(resource), FleetspaceAccountResource)
                    self.assertIs(type(resource.global_database_account_properties),
                                  FleetspaceAccountPropertiesGlobalDatabaseAccountProperties)
                    self.assertEqual(resource.as_dict(), {'properties': {'globalDatabaseAccountProperties': {
                        'resourceId': resource_id, 'armLocation': 'westus2'}}})

    def test_invalid_account_resource_ids(self):
        invalid_ids = [None, 1, True, '', '/subscriptions/', 'https://management.azure.com' + self.account_id,
                       self.account_id + '/sqlDatabases/db', self.account_id + '/',
                       self.account_id.replace('Microsoft.DocumentDB', 'Microsoft.Storage'),
                       self.account_id.replace('databaseAccounts', 'storageAccounts'),
                       self.account_id.replace('/resourceGroups/example-rg', ''),
                       self.account_id.replace('example-rg', ''), self.account_id.replace('example-rg', ' '),
                       self.account_id.replace('00000000-0000-0000-0000-000000000000', ''),
                       self.account_id.replace('myaccount', ''), self.account_id.replace('myaccount', ' ')]
        for resource_id in invalid_ids:
            with self.subTest(resource_id=resource_id):
                with self.assertRaises(InvalidArgumentValueError):
                    self._validate_account(dict(self.account_properties, resourceId=resource_id))
        with self.assertRaises(InvalidArgumentValueError):
            self._validate_account({'armLocation': 'westus2'})

    def test_account_location_must_be_nonblank(self):
        for value in [None, 1, False, '', '  ', '\t\n']:
            with self.subTest(value=value):
                with self.assertRaisesRegex(InvalidArgumentValueError, 'armLocation'):
                    self._validate_account(dict(self.account_properties, armLocation=value))
        with self.assertRaisesRegex(InvalidArgumentValueError, 'armLocation'):
            self._validate_account({'resourceId': self.account_id})
        body = self._validate_account(dict(self.account_properties, armLocation='Custom Region'))
        self.assertEqual(body['properties']['globalDatabaseAccountProperties']['armLocation'], 'Custom Region')

    def test_account_name_mismatch_and_malformed_id_do_not_write(self):
        body = self._validate_account(self.account_properties)
        with self.assertRaisesRegex(InvalidArgumentValueError, '"alias".*"myaccount"'):
            cli_cosmosdb_fleetspace_account_create(self.client, 'rg', 'fleet', 'space', 'alias', body)
        body['properties']['globalDatabaseAccountProperties']['resourceId'] = '/subscriptions/'
        with self.assertRaises(InvalidArgumentValueError):
            cli_cosmosdb_fleetspace_account_create(self.client, 'rg', 'fleet', 'space', 'myaccount', body)
        self.client.begin_create.assert_not_called()


class _FleetTestCommandsLoader(MainCommandsLoader):

    def load_command_table(self, args):
        command_table, group_table, loader = _load_module_command_loader(self, args, 'cosmosdb')
        self.command_table.update(command_table)
        self.command_group_table.update(group_table)
        self.cmd_to_loader_map.update({name: [loader] for name in command_table})
        return self.command_table


class CosmosdbFleetCommandTest(unittest.TestCase):

    def setUp(self):
        self.client = mock.Mock()
        self.client.begin_create.return_value = FleetspaceResource(
            fleetspace_api_kind='NoSQL', service_tier='GeneralPurpose', data_regions=['West US 2'])
        self.client.begin_update.return_value = self.client.begin_create.return_value
        factory = mock.patch('azure.cli.command_modules.cosmosdb.commands.cf_fleetspace', return_value=self.client)
        factory.start()
        self.addCleanup(factory.stop)

    def _execute(self, command, expect_failure=False):
        return execute(get_dummy_cli(commands_loader_cls=_FleetTestCommandsLoader), command,
                       expect_failure=expect_failure)

    def _render_help(self, command):
        output = StringIO()
        cli = get_dummy_cli(commands_loader_cls=_FleetTestCommandsLoader)
        with redirect_stdout(output), self.assertRaises(SystemExit) as exit_context:
            cli.invoke(shlex.split(command + ' --help')[1:], out_file=output)
        self.assertEqual(exit_context.exception.code, 0)
        return output.getvalue()

    def test_non_pooled_create_inline_and_file(self):
        for configuration in ['absent', None, {}]:
            for from_file in [False, True]:
                with self.subTest(configuration=configuration, from_file=from_file):
                    properties = {'serviceTier': 'GeneralPurpose', 'dataRegions': ['West US 2']}
                    if configuration != 'absent':
                        properties['throughputPoolConfiguration'] = configuration
                    body_json = json.dumps({'properties': properties})
                    with tempfile.TemporaryDirectory() as directory:
                        path = os.path.join(directory, 'body.json')
                        with open(path, 'w', encoding='utf-8') as body_file:
                            body_file.write(body_json)
                        body_argument = shlex.quote('@' + path) if from_file else shlex.quote(body_json)
                        result = self._execute('az cosmosdb fleetspace create -g rg --fleet-name fleet -n space --body ' + body_argument)
                    self.assertEqual(result.get_output_in_json()['serviceTier'], 'GeneralPurpose')
                    resource = self.client.begin_create.call_args.kwargs['body']
                    self.assertIs(type(resource), FleetspaceResource)
                    self.assertNotIn('throughputPoolConfiguration', resource.as_dict()['properties'])

    def test_pooled_create_from_file_keeps_wire_body(self):
        properties = {
            'serviceTier': 'GeneralPurpose', 'dataRegions': ['West US 2'],
            'throughputPoolConfiguration': {'minThroughput': 100000, 'maxThroughput': 300000},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.json')
            with open(path, 'w', encoding='utf-8') as body_file:
                json.dump({'properties': properties}, body_file)
            self._execute('az cosmosdb fleetspace create -g rg --fleet-name fleet -n space --body ' + shlex.quote('@' + path))
        resource = self.client.begin_create.call_args.kwargs['body']
        self.assertIs(type(resource), FleetspaceResource)
        self.assertIs(type(resource.throughput_pool_configuration), FleetspacePropertiesThroughputPoolConfiguration)
        self.assertEqual(resource.as_dict(), {'properties': dict(properties, fleetspaceApiKind='NoSQL')})

    def test_invalid_create_and_strict_update_do_not_write(self):
        for operation, properties in [('create', {'serviceTier': ' ', 'dataRegions': ['westus2']}),
                                      ('create', {'serviceTier': 'GeneralPurpose', 'dataRegions': []}),
                                      ('create', {'serviceTier': 'GeneralPurpose', 'dataRegions': ['westus2'],
                                                  'throughputPoolConfiguration': {'minThroughput': True, 'maxThroughput': 300000}}),
                                      ('update', {}), ('update', {'throughputPoolConfiguration': None}),
                                      ('update', {'throughputPoolConfiguration': {}}),
                                      ('update', {'throughputPoolConfiguration': {'minThroughput': 100000}})]:
            with self.subTest(operation=operation, properties=properties):
                command = 'az cosmosdb fleetspace ' + operation + ' -g rg --fleet-name fleet -n space --body '
                self._execute(command + shlex.quote(json.dumps({'properties': properties})), expect_failure=True)
                self.client.begin_create.assert_not_called()
                self.client.begin_update.assert_not_called()

    def test_account_attachment_from_file_preserves_case(self):
        properties = {
            'resourceId': '/SUBSCRIPTIONS/sub/RESOURCEGROUPS/rg/PROVIDERS/MICROSOFT.DOCUMENTDB/DATABASEACCOUNTS/MyAccount',
            'armLocation': 'westus2',
        }
        self.client.begin_create.return_value = FleetspaceAccountResource(
            global_database_account_properties=FleetspaceAccountPropertiesGlobalDatabaseAccountProperties(
                resource_id=properties['resourceId'], arm_location=properties['armLocation']))
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.json')
            with open(path, 'w', encoding='utf-8') as body_file:
                json.dump({'properties': {'globalDatabaseAccountProperties': properties}}, body_file)
            with mock.patch('azure.cli.command_modules.cosmosdb.commands.cf_fleetspace_account', return_value=self.client):
                result = self._execute('az cosmosdb fleetspace account create -g rg --fleet-name fleet --fleetspace-name space '
                                       '--fleetspace-account-name myaccount --body ' + shlex.quote('@' + path))
        self.assertEqual(result.get_output_in_json()['globalDatabaseAccountProperties'], properties)
        arguments = self.client.begin_create.call_args.kwargs
        self.assertEqual(arguments['fleetspace_account_name'], 'myaccount')
        resource = arguments['body']
        self.assertIs(type(resource), FleetspaceAccountResource)
        self.assertIs(type(resource.global_database_account_properties),
                      FleetspaceAccountPropertiesGlobalDatabaseAccountProperties)
        self.assertEqual(resource.as_dict(), {'properties': {'globalDatabaseAccountProperties': properties}})

    def test_account_name_mismatch_fails_through_command(self):
        body = {'properties': {'globalDatabaseAccountProperties': {
            'resourceId': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.DocumentDB/databaseAccounts/myaccount',
            'armLocation': 'westus2'}}}
        with mock.patch('azure.cli.command_modules.cosmosdb.commands.cf_fleetspace_account', return_value=self.client):
            self._execute('az cosmosdb fleetspace account create -g rg --fleet-name fleet --fleetspace-name space '
                          '--fleetspace-account-name alias --body ' + shlex.quote(json.dumps(body)), expect_failure=True)
        self.client.begin_create.assert_not_called()

    def test_help_and_examples(self):
        from azure.cli.command_modules.cosmosdb._help import helps
        from azure.cli.command_modules.cosmosdb._params import (
            FLEETSPACE_PROPERTIES_EXAMPLE, FLEETSPACE_UPDATE_PROPERTIES_EXAMPLE, FLEETSPACE_ACCOUNT_PROPERTIES_EXAMPLE,
        )

        for command in ['cosmosdb fleet create', 'cosmosdb fleetspace create', 'cosmosdb fleetspace update',
                        'cosmosdb fleetspace account create']:
            with self.subTest(command=command):
                output = self._render_help('az ' + command)
                self.assertIn('--fleet-name', output)
                if 'fleetspace' in command:
                    self.assertIn('--body', output)
                for example in yaml.safe_load(helps[command]).get('examples', []):
                    tokens = shlex.split(example['text'].replace('\\\n', ''))
                    if '--body' in tokens:
                        body = tokens[tokens.index('--body') + 1]
                        if not body.startswith('@'):
                            json.loads(body)
                            self._execute(example['text'].replace('\\\n', ''))
        for example in [FLEETSPACE_PROPERTIES_EXAMPLE, FLEETSPACE_UPDATE_PROPERTIES_EXAMPLE, FLEETSPACE_ACCOUNT_PROPERTIES_EXAMPLE]:
            json.loads(shlex.split(example)[1])


class CosmosdbFleetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_nonpooled', location='westus2')
    def test_cosmosdb_fleetspace_non_pooled(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'fleet': self.create_random_name('fleet', 15),
            'fsp': self.create_random_name('fs', 10),
        })
        with tempfile.TemporaryDirectory() as directory:
            body_path = os.path.join(directory, 'fleetspace.json')
            with open(body_path, 'w', encoding='utf-8') as body_file:
                json.dump({'properties': {
                    'serviceTier': 'GeneralPurpose',
                    'dataRegions': ['West US 2'],
                }}, body_file)
            self.kwargs['fspbody'] = body_path

            self.cmd('az cosmosdb fleet create -g {rg} -n {fleet} -l westus2')
            self.cmd('az cosmosdb fleetspace create -g {rg} --fleet-name {fleet} -n {fsp} --body "@{fspbody}"')
            fleetspace = self.cmd('az cosmosdb fleetspace show -g {rg} --fleet-name {fleet} -n {fsp}').get_output_in_json()
            self.assertEqual(fleetspace['provisioningState'], 'Succeeded')
            self.assertEqual(fleetspace['serviceTier'], 'GeneralPurpose')
            self.assertEqual(fleetspace['dataRegions'], ['West US 2'])
            pool = fleetspace.get('throughputPoolConfiguration')
            if pool is not None:
                self.assertIsNone(pool.get('minThroughput'))
                self.assertIsNone(pool.get('maxThroughput'))
            self.cmd('az cosmosdb fleetspace delete -g {rg} --fleet-name {fleet} -n {fsp} --yes')
            self.cmd('az cosmosdb fleet delete -g {rg} -n {fleet} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_fleet', location='westus2')
    def test_cosmosdb_fleet_fleetspace_fleetspaceAccount(self, resource_group):
        # Names
        fleet_name = self.create_random_name('fleet', 15)
        fleetspace_name = self.create_random_name('fs', 10)
        account_name = self.create_random_name('acct', 15)
        storage_account_name = account_name + 'st'

        # JSON
        fleetspace_body = self._write_temp_json({
            "properties": {
                "serviceTier": "GeneralPurpose",
                "dataRegions": ["West US 2"],
                "throughputPoolConfiguration": {
                    "minThroughput": 100000,
                    "maxThroughput": 400000
                }
            }
        })

        fleetspace_update_body = self._write_temp_json({
            "properties": {
                "serviceTier": "GeneralPurpose",
                "dataRegions": ["West US 2"],
                "throughputPoolConfiguration": {
                    "minThroughput": 200000,
                    "maxThroughput": 600000
                }
            }
        })

        fleetspace_account_body = self._write_temp_json({
            "properties": {
                "globalDatabaseAccountProperties": {
                    "resourceId": f"/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.DocumentDb/databaseAccounts/{account_name}",
                    "armLocation": "westus2"
                }
            }
        })

        # Feature being updated with a different contract. Will be enabled in the future.
        '''
        fleet_analytics_body = self._write_temp_json({
            "properties": {
                "storageLocationType": "StorageAccount",
                "storageLocationUri": f"/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}",
            }
        })
        '''

        self.kwargs.update({
            'rg': resource_group,
            'acct': account_name,
            'storage': storage_account_name,
            'fleet': fleet_name,
            'fsp': fleetspace_name,
            'fspacct': account_name,
            'fspbody': fleetspace_body,
            'fspupdate': fleetspace_update_body,
            'fspacctbody': fleetspace_account_body
        })

        # Fleet
        self.cmd('az cosmosdb fleet create -g {rg} -n {fleet} -l westus2')
        self.cmd('az cosmosdb fleet show -g {rg} -n {fleet}')
        self.cmd('az cosmosdb fleet list -g {rg}')
        
        # Create Storage Account for Fleet Analytics
        self.cmd('az storage account create -g {rg} -n {storage} --sku Standard_LRS --location westus2 --allow-shared-key-access false')

        # Feature being updated with a different contract. Will be enabled in the future.
        '''
        # Fleet Analytics
        self.cmd('az cosmosdb fleet analytics create -g {rg} --fleet-name {fleet} -n {fanalytics} --body @{fanalyticsbody}')
        self.cmd('az cosmosdb fleet analytics show -g {rg} --fleet-name {fleet} -n {fanalytics}')
        self.cmd('az cosmosdb fleet analytics list -g {rg} --fleet-name {fleet}')
        '''
        # Fleetspace
        self.cmd('az cosmosdb fleetspace create -g {rg} --fleet-name {fleet} -n {fsp} --body @{fspbody}')
        self.cmd('az cosmosdb fleetspace update -g {rg} --fleet-name {fleet} -n {fsp} --body @{fspupdate}')
        self.cmd('az cosmosdb fleetspace show -g {rg} --fleet-name {fleet} -n {fsp}')
        self.cmd('az cosmosdb fleetspace list -g {rg} --fleet-name {fleet}')

        # Create Cosmos DB account dynamically
        self.cmd('az cosmosdb create -g {rg} -n {acct} --disable-local-auth true --locations regionName=westus2 failoverPriority=0 isZoneRedundant=False')

        # Fleetspace Account
        self.cmd('az cosmosdb fleetspace account create -g {rg} --fleet-name {fleet} --fleetspace-name {fsp} --fleetspace-account-name {fspacct} --body @{fspacctbody}')
        self.cmd('az cosmosdb fleetspace account show -g {rg} --fleet-name {fleet} --fleetspace-name {fsp} --fleetspace-account-name {fspacct}')
        self.cmd('az cosmosdb fleetspace account list -g {rg} --fleet-name {fleet} --fleetspace-name {fsp}')

        # Deletes
        # self.cmd('az cosmosdb fleet analytics delete -g {rg} --fleet-name {fleet} -n {fanalytics} --yes')
        self.cmd('az cosmosdb fleetspace account delete -g {rg} --fleet-name {fleet} --fleetspace-name {fsp} --fleetspace-account-name {fspacct} --yes')
        self.cmd('az cosmosdb fleetspace delete -g {rg} --fleet-name {fleet} -n {fsp} --yes')
        self.cmd('az cosmosdb fleet delete -g {rg} -n {fleet} --yes')

    def _write_temp_json(self, data):
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
        return os.path.abspath(path).replace('\\', '/')
