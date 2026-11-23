# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from unittest import mock

from knack.arguments import ignore_type

from azure.cli.command_modules.acr import ACRCommandsLoader
from azure.cli.command_modules.acr.connected_registry import (
    acr_connected_registry_create,
    acr_connected_registry_update,
)
from azure.cli.core.mock import DummyCli
from azure.cli.core.parser import AzCliCommandParser
from azure.mgmt.containerregistry import models


class ConnectedRegistryArgumentTests(unittest.TestCase):

    def _get_parser(self, action):
        cli = DummyCli()
        loader = ACRCommandsLoader(cli)
        cli.invocation = mock.MagicMock()
        cli.invocation.commands_loader = loader
        command_name = 'acr connected-registry ' + action
        loader.command_name = command_name
        loader.load_command_table(command_name.split())
        with loader.argument_context('') as context:
            context.argument('cmd', ignore_type)
        loader.load_arguments(command_name)
        command = loader.command_table[command_name]
        loader.command_table = {command_name: command}
        command.load_arguments()
        loader._update_command_definitions()  # pylint: disable=protected-access
        parser = AzCliCommandParser(cli)
        parser.load_command_table(loader)
        return parser

    def test_create_garbage_collection_boolean_payload(self):
        parser = self._get_parser('create')
        for options, expected in (
                ([], True),
                (['--gc-enabled'], True),
                (['--gc-enabled', 'true'], True),
                (['--gc-enabled', 'false'], False)):
            with self.subTest(options=options):
                args = parser.parse_args([
                    'acr', 'connected-registry', 'create',
                    '--registry', 'testregistry', '--name', 'testconnectedregistry',
                    '--sync-token', 'testtoken',
                ] + options)
                cmd = mock.MagicMock()
                cmd.get_models.side_effect = lambda *names: tuple(getattr(models, name) for name in names)
                client = mock.MagicMock()
                registry = mock.MagicMock(data_endpoint_enabled=True)
                with mock.patch(
                        'azure.cli.command_modules.acr.connected_registry.get_subscription_id',
                        return_value='00000000-0000-0000-0000-000000000001'), \
                     mock.patch(
                         'azure.cli.command_modules.acr.connected_registry.get_registry_by_name',
                         return_value=(registry, 'testresourcegroup')):
                    acr_connected_registry_create(
                        cmd, client, args.registry_name, args.connected_registry_name,
                        sync_token_name=args.sync_token_name, mode=args.mode,
                        garbage_collection_enabled=args.garbage_collection_enabled,
                        garbage_collection_schedule=args.garbage_collection_schedule)

                client.begin_create.assert_called_once()
                parameters = client.begin_create.call_args.kwargs['connected_registry_create_parameters']
                payload = json.loads(json.dumps(parameters.as_dict()))
                self.assertIs(payload['properties']['garbageCollection']['enabled'], expected)
                self.assertIs(args.garbage_collection_enabled, expected)

    def test_update_garbage_collection_boolean_payload(self):
        parser = self._get_parser('update')
        for options, expected in (
                ([], None),
                (['--gc-enabled'], True),
                (['--gc-enabled', 'true'], True),
                (['--gc-enabled', 'false'], False)):
            with self.subTest(options=options):
                args = parser.parse_args([
                    'acr', 'connected-registry', 'update',
                    '--registry', 'testregistry', '--name', 'testconnectedregistry',
                    '--log-level', 'Debug',
                ] + options)
                cmd = mock.MagicMock()
                cmd.get_models.side_effect = lambda *names: tuple(getattr(models, name) for name in names)
                client = mock.MagicMock()
                current = models.ConnectedRegistry(
                    garbage_collection=models.GarbageCollectionProperties(enabled=False))
                with mock.patch(
                        'azure.cli.command_modules.acr.connected_registry.validate_managed_registry',
                        return_value=(None, 'testresourcegroup')), \
                     mock.patch(
                         'azure.cli.command_modules.acr.connected_registry.get_subscription_id',
                         return_value='00000000-0000-0000-0000-000000000001'), \
                     mock.patch(
                         'azure.cli.command_modules.acr.connected_registry.acr_connected_registry_show',
                         return_value=current):
                    acr_connected_registry_update(
                        cmd, client, args.registry_name, args.connected_registry_name,
                        log_level=args.log_level,
                        garbage_collection_enabled=args.garbage_collection_enabled,
                        garbage_collection_schedule=args.garbage_collection_schedule)

                client.begin_update.assert_called_once()
                parameters = client.begin_update.call_args.kwargs['connected_registry_update_parameters']
                payload = json.loads(json.dumps(parameters.as_dict()))
                self.assertEqual(payload['properties']['logging']['logLevel'], 'Debug')
                self.assertIs(args.garbage_collection_enabled, expected)
                if expected is None:
                    self.assertNotIn('enabled', payload['properties'].get('garbageCollection', {}))
                else:
                    self.assertIs(payload['properties']['garbageCollection']['enabled'], expected)
