# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

from azure.cli.core.azclierror import RequiredArgumentMissingError, ValidationError
from azure.cli.command_modules.containerapp._clients import ManagedEnvironmentClient
from azure.cli.command_modules.containerapp._utils import (
    validate_environment_mode_and_workload_profiles_compatible,
)
from azure.cli.command_modules.containerapp.containerapp_env_decorator import (
    ContainerAppEnvCreateDecorator,
    ContainerAppEnvUpdateDecorator,
)


class ContainerappEnvEnvironmentModeTest(unittest.TestCase):
    def setUp(self):
        self.cmd = Mock()
        self.cmd.cli_ctx.data = {'safe_params': []}
        self.client = Mock()
        self.client.show.return_value = None
        self.parameters = {
            'name': 'test-env',
            'resource_group_name': 'test-rg',
            'location': 'eastus2',
            'logs_destination': 'none',
            'enable_workload_profiles': True,
        }
        self.profiles = [{'name': 'Consumption', 'workloadProfileType': 'Consumption'}]
        module = 'azure.cli.command_modules.containerapp.containerapp_env_decorator'
        for name, value in [
                ('validate_environment_location', 'eastus2'),
                ('_ensure_location_allowed', None),
                ('get_default_workload_profiles', self.profiles)]:
            patcher = patch(f'{module}.{name}', return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def create_decorator(self, **parameters):
        return ContainerAppEnvCreateDecorator(
            self.cmd, self.client, dict(self.parameters, **parameters), None)

    def test_containerapp_env_mode_compatibility(self):
        for mode in [None, 'WorkloadProfiles', 'ConsumptionOnly', 'Express',
                     'workloadprofiles', 'CONSUMPTIONONLY', 'express', 'EXPRESS']:
            for enabled in [None, True, False]:
                with self.subTest(mode=mode, enabled=enabled):
                    conflict = mode is not None and enabled is not None and (
                        (mode.lower() != 'consumptiononly') != enabled)
                    if conflict:
                        with self.assertRaisesRegex(ValidationError, "Please use '--environment-mode' alone"):
                            validate_environment_mode_and_workload_profiles_compatible(mode, enabled)
                    else:
                        validate_environment_mode_and_workload_profiles_compatible(mode, enabled)

    def test_containerapp_env_mode_create_payload(self):
        for mode in ['WorkloadProfiles', 'ConsumptionOnly', 'Express',
                     'workloadprofiles', 'CONSUMPTIONONLY', 'express', 'EXPRESS']:
            with self.subTest(mode=mode):
                decorator = self.create_decorator(environment_mode=mode)
                decorator.validate_arguments()
                decorator.construct_payload()
                properties = decorator.managed_env_def['properties']
                self.assertEqual(properties['environmentMode'], mode)
                if mode.lower() == 'consumptiononly':
                    self.assertIsNone(properties.get('workloadProfiles'))
                else:
                    self.assertEqual(properties['workloadProfiles'], self.profiles)
                decorator.create()
                self.assertEqual(
                    self.client.create.call_args.kwargs['managed_environment_envelope'],
                    decorator.managed_env_def)

    def test_containerapp_env_mode_legacy_defaults(self):
        for enabled in [True, False]:
            with self.subTest(enabled=enabled):
                decorator = self.create_decorator(enable_workload_profiles=enabled)
                decorator.validate_arguments()
                decorator.construct_payload()
                properties = decorator.managed_env_def['properties']
                self.assertNotIn('environmentMode', properties)
                self.assertEqual(properties.get('workloadProfiles'), self.profiles if enabled else None)

    def test_containerapp_env_mode_explicit_legacy_flags(self):
        for flag in ['-w', '--enable-workload-profiles']:
            self.cmd.cli_ctx.data['safe_params'] = [flag]
            for mode, enabled in [('ConsumptionOnly', True), ('WorkloadProfiles', False), ('Express', False)]:
                with self.subTest(flag=flag, mode=mode):
                    with self.assertRaises(ValidationError):
                        self.create_decorator(
                            environment_mode=mode, enable_workload_profiles=enabled).validate_arguments()
            for mode, enabled in [('ConsumptionOnly', False), ('WorkloadProfiles', True), ('Express', True)]:
                with self.subTest(flag=flag, mode=mode):
                    self.create_decorator(
                        environment_mode=mode, enable_workload_profiles=enabled).validate_arguments()

    def test_containerapp_env_mode_infrastructure_resource_group(self):
        subnet = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet'
        decorator = self.create_decorator(
            environment_mode='ConsumptionOnly', infrastructure_resource_group='infra-rg',
            infrastructure_subnet_resource_id=subnet)
        with self.assertRaisesRegex(RequiredArgumentMissingError, 'ConsumptionOnly'):
            decorator.validate_arguments()

        for mode in ['WorkloadProfiles', 'Express']:
            with self.subTest(mode=mode):
                decorator = self.create_decorator(
                    environment_mode=mode, infrastructure_resource_group='infra-rg',
                    infrastructure_subnet_resource_id=subnet)
                decorator.validate_arguments()
                decorator.construct_payload()
                self.assertEqual(decorator.managed_env_def['properties']['InfrastructureResourceGroup'], 'infra-rg')

    def test_containerapp_env_mode_existing_environment(self):
        dedicated_profiles = self.profiles + [
            {'name': 'dedicated', 'workloadProfileType': 'D4', 'minimumCount': 1, 'maximumCount': 2}]
        for mode, profiles in [('ConsumptionOnly', None), ('WorkloadProfiles', dedicated_profiles),
                               ('Express', dedicated_profiles)]:
            self.client.show.return_value = {
                'location': 'eastus2', 'properties': {'workloadProfiles': profiles}}
            with self.subTest(mode=mode):
                decorator = self.create_decorator(environment_mode=mode)
                decorator.construct_payload()
                properties = decorator.managed_env_def['properties']
                self.assertEqual(properties['environmentMode'], mode)
                self.assertEqual(properties.get('workloadProfiles'), profiles)

                other_mode = 'WorkloadProfiles' if mode == 'ConsumptionOnly' else 'ConsumptionOnly'
                with self.assertRaises(ValidationError):
                    self.create_decorator(environment_mode=other_mode).construct_payload()

    def test_containerapp_env_mode_existing_consumption_default(self):
        self.client.show.return_value = {
            'location': 'eastus2', 'properties': {'workloadProfiles': None}}
        decorator = self.create_decorator()
        decorator.construct_payload()
        self.assertIsNone(decorator.managed_env_def['properties'].get('workloadProfiles'))
        self.assertNotIn('environmentMode', decorator.managed_env_def['properties'])

    def test_containerapp_env_mode_update_payload(self):
        existing = {
            'location': 'eastus2',
            'properties': {'environmentMode': 'WorkloadProfiles', 'workloadProfiles': self.profiles},
        }
        self.client.show.return_value = existing
        for mode in [None, 'WorkloadProfiles', 'ConsumptionOnly', 'Express']:
            with self.subTest(mode=mode):
                decorator = ContainerAppEnvUpdateDecorator(
                    self.cmd, self.client, {
                        'name': 'test-env', 'resource_group_name': 'test-rg', 'environment_mode': mode,
                    }, None)
                decorator.validate_arguments()
                decorator.construct_payload()
                expected = {'location': 'eastus2'}
                if mode is not None:
                    expected['properties'] = {'environmentMode': mode}
                self.assertEqual(decorator.managed_env_def, expected)
                decorator.update()
                self.assertEqual(
                    self.client.update.call_args.kwargs['managed_environment_envelope'], expected)
        self.assertEqual(existing, {
            'location': 'eastus2',
            'properties': {'environmentMode': 'WorkloadProfiles', 'workloadProfiles': self.profiles},
        })

    def test_containerapp_env_mode_update_with_workload_profile(self):
        self.client.show.return_value = {
            'location': 'eastus2', 'properties': {'workloadProfiles': deepcopy(self.profiles)}}
        decorator = ContainerAppEnvUpdateDecorator(
            self.cmd, self.client, {
                'environment_mode': 'WorkloadProfiles', 'workload_profile_name': 'dedicated',
                'workload_profile_type': 'D4', 'min_nodes': 1, 'max_nodes': 2,
            }, None)
        decorator.construct_payload()
        self.assertEqual(decorator.managed_env_def['properties'], {
            'environmentMode': 'WorkloadProfiles',
            'workloadProfiles': self.profiles + [{
                'name': 'dedicated', 'workloadProfileType': 'D4',
                'minimumCount': 1, 'maximumCount': 2,
            }],
        })

    def test_containerapp_env_mode_rest_requests(self):
        self.cmd.cli_ctx.cloud.endpoints.resource_manager = 'https://management.azure.com'
        module = 'azure.cli.command_modules.containerapp._clients'
        payload = {'location': 'eastus2', 'properties': {'environmentMode': 'WorkloadProfiles'}}
        expected_url = (
            'https://management.azure.com/subscriptions/sub/resourceGroups/test-rg/'
            'providers/Microsoft.App/managedEnvironments/test-env?api-version=2026-07-01')
        with patch(f'{module}.get_subscription_id', return_value='sub'), \
                patch(f'{module}.send_raw_request') as send:
            send.return_value.status_code = 200
            send.return_value.json.return_value = payload
            for operation, method in [(ManagedEnvironmentClient.create, 'PUT'),
                                      (ManagedEnvironmentClient.update, 'PATCH')]:
                with self.subTest(method=method):
                    self.assertEqual(operation(self.cmd, 'test-rg', 'test-env', payload), payload)
                    send.assert_called_with(
                        self.cmd.cli_ctx, method, expected_url, body=json.dumps(payload))
            self.assertEqual(ManagedEnvironmentClient.show(self.cmd, 'test-rg', 'test-env'), payload)
            send.assert_called_with(self.cmd.cli_ctx, 'GET', expected_url)
