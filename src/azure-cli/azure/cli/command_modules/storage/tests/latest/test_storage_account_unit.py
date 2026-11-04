# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import io
import json
import shlex
import unittest
from unittest import mock

from azure.core.credentials import AccessToken
from azure.cli.core import get_default_cli
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage import models
from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError
from azure.mgmt.storage.models import SasPolicy

from azure.cli.command_modules.storage.operations.account import (
    _build_sas_policy, create_storage_account, update_storage_account)


class StorageAccountSasPolicyTest(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.MagicMock()
        self.cmd.get_models.return_value = SasPolicy

    def test_no_sas_policy_arguments_returns_none(self):
        self.assertIsNone(_build_sas_policy(self.cmd))

    def test_create_user_bound_sas_policy(self):
        policy = _build_sas_policy(
            self.cmd,
            sas_expiration_period='1.00:00:00',
            require_user_bound_user_delegation_sas=True,
            require_user_bound_user_delegation_sas_action='Block')

        self.assertEqual('1.00:00:00', policy.sas_expiration_period)
        self.assertEqual('Log', policy.expiration_action)
        self.assertTrue(policy.require_user_bound_user_delegation_sas)
        self.assertEqual('Block', policy.require_user_bound_user_delegation_sas_action)

    def test_create_user_bound_sas_policy_requires_expiration_period(self):
        with self.assertRaisesRegex(
                RequiredArgumentMissingError,
                'Specify --sas-expiration-period when configuring a new SAS policy.'):
            _build_sas_policy(
                self.cmd,
                require_user_bound_user_delegation_sas=True)

    def test_expiration_action_still_requires_expiration_period(self):
        existing_policy = SasPolicy(
            sas_expiration_period='1.00:00:00',
            expiration_action='Log')

        with self.assertRaisesRegex(
                InvalidArgumentValueError,
                'Specify --sas-expiration-period when using --sas-expiration-action.'):
            _build_sas_policy(
                self.cmd,
                sas_expiration_action='Block',
                existing_sas_policy=existing_policy)

    def test_update_user_bound_setting_preserves_existing_policy(self):
        existing_policy = SasPolicy(
            sas_expiration_period='1.00:00:00',
            expiration_action='Block',
            require_user_bound_user_delegation_sas=True,
            require_user_bound_user_delegation_sas_action='Log')

        policy = _build_sas_policy(
            self.cmd,
            require_user_bound_user_delegation_sas=False,
            existing_sas_policy=existing_policy)

        self.assertEqual('1.00:00:00', policy.sas_expiration_period)
        self.assertEqual('Block', policy.expiration_action)
        self.assertFalse(policy.require_user_bound_user_delegation_sas)
        self.assertEqual('Log', policy.require_user_bound_user_delegation_sas_action)

    def test_update_expiration_period_preserves_user_bound_settings(self):
        existing_policy = SasPolicy(
            sas_expiration_period='1.00:00:00',
            expiration_action='Block',
            require_user_bound_user_delegation_sas=True,
            require_user_bound_user_delegation_sas_action='Block')

        policy = _build_sas_policy(
            self.cmd,
            sas_expiration_period='2.00:00:00',
            existing_sas_policy=existing_policy)

        self.assertEqual('2.00:00:00', policy.sas_expiration_period)
        self.assertEqual('Block', policy.expiration_action)
        self.assertTrue(policy.require_user_bound_user_delegation_sas)
        self.assertEqual('Block', policy.require_user_bound_user_delegation_sas_action)


class StorageAccountPolicyTest(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.MagicMock()
        self.cmd.get_models.side_effect = self.get_models
        self.client = mock.MagicMock()
        patcher = mock.patch(
            'azure.cli.command_modules.storage.operations.account.storage_client_factory',
            return_value=self.client)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def get_models(*names, **_):
        result = [getattr(models, name) for name in names]
        return result[0] if len(result) == 1 else result

    def create(self, **kwargs):
        create_storage_account(
            self.cmd, resource_group_name='rg', account_name='storageaccount',
            sku='Standard_ZRS', kind='StorageV2', location='westus', **kwargs)
        return self.client.storage_accounts.begin_create.call_args.args[2].as_dict()['properties']

    def update(self, **kwargs):
        instance = models.StorageAccount(
            sku=models.Sku(name='Standard_ZRS'), kind='StorageV2', location='westus',
            encryption=models.Encryption(key_source='Microsoft.Storage'),
            **kwargs.pop('existing', {}))
        before = instance.as_dict()
        result = update_storage_account(self.cmd, instance, **kwargs).as_dict()['properties']
        self.assertEqual(before, instance.as_dict())
        return result

    def test_create_and_update_omit_unspecified_policies(self):
        for operation in [self.create, self.update]:
            with self.subTest(operation=operation.__name__):
                properties = operation()
                for name in ['allowSharedKeyAccessForServices', 'dataCollaborationPolicyProperties',
                             'turboTier', 'enableExtendedGroups', 'allowCrossTenantDelegationSas', 'sasPolicy']:
                    self.assertNotIn(name, properties)

    def test_existing_smart_tier_and_all_copy_scope_are_preserved(self):
        for operation in [self.create, self.update]:
            with self.subTest(operation=operation.__name__):
                arguments = {'access_tier': 'Smart', 'allowed_copy_scope': 'All'}
                if operation == self.update:
                    arguments['yes'] = True
                properties = operation(**arguments)
                self.assertEqual('Smart', properties['accessTier'])
                self.assertEqual('All', properties['allowedCopyScope'])

    def test_shared_key_access_for_each_service_preserves_boolean_values(self):
        for operation in [self.create, self.update]:
            for service in ['blob', 'file', 'table', 'queue']:
                for enabled in [True, False]:
                    with self.subTest(operation=operation.__name__, service=service, enabled=enabled):
                        properties = operation(**{'allow_shared_key_access_for_' + service: enabled})
                        self.assertEqual(
                            {service: {'enabled': enabled}}, properties['allowSharedKeyAccessForServices'])
                        self.assertNotIn('allowSharedKeyAccess', properties)

    def test_shared_key_update_preserves_other_services(self):
        properties = self.update(
            allow_shared_key_access_for_blob=False,
            existing={'allow_shared_key_access_for_services': models.StorageAccountSharedKeyAccessProperties(
                blob=models.ServiceSharedKeyAccessProperties(enabled=True),
                file=models.ServiceSharedKeyAccessProperties(enabled=True),
                table=models.ServiceSharedKeyAccessProperties(enabled=False))})
        self.assertEqual(
            {'blob': {'enabled': False}, 'file': {'enabled': True}, 'table': {'enabled': False}},
            properties['allowSharedKeyAccessForServices'])

    def test_blob_access_point_policy_preserves_boolean_values(self):
        for operation in [self.create, self.update]:
            for enabled in [True, False]:
                with self.subTest(operation=operation.__name__, enabled=enabled):
                    properties = operation(allow_blob_access_points=enabled)
                    self.assertEqual(
                        {'allowBlobAccessPoints': enabled}, properties['dataCollaborationPolicyProperties'])

    def test_collaboration_update_preserves_other_settings(self):
        properties = self.update(
            allow_blob_access_points=False,
            existing={'data_collaboration_policy_properties': models.StorageDataCollaborationPolicyProperties(
                allow_storage_connectors=True, allow_storage_data_shares=False,
                allow_cross_tenant_data_sharing=True, allow_blob_access_points=True)})
        self.assertEqual({
            'allowStorageConnectors': True, 'allowStorageDataShares': False,
            'allowCrossTenantDataSharing': True, 'allowBlobAccessPoints': False
        }, properties['dataCollaborationPolicyProperties'])

    def test_cross_tenant_sas_preserves_boolean_values(self):
        for operation in [self.create, self.update]:
            for enabled in [True, False]:
                with self.subTest(operation=operation.__name__, enabled=enabled):
                    properties = operation(allow_cross_tenant_delegation_sas=enabled)
                    self.assertIs(enabled, properties['allowCrossTenantDelegationSas'])

    def test_turbo_tier_target_boundaries(self):
        for operation in [self.create, self.update]:
            for target in [10, 100]:
                with self.subTest(operation=operation.__name__, target=target):
                    properties = operation(turbo_tier_status='Enabled', turbo_tier_target_percent=target)
                    self.assertEqual({'status': 'Enabled', 'targetPercent': target}, properties['turboTier'])

    def test_turbo_tier_rejects_out_of_range_targets(self):
        for operation in [self.create, self.update]:
            for target in [9, 101]:
                with self.subTest(operation=operation.__name__, target=target):
                    with self.assertRaisesRegex(InvalidArgumentValueError, 'between 10 and 100'):
                        operation(turbo_tier_status='Enabled', turbo_tier_target_percent=target)

    def test_turbo_tier_create_leaves_default_to_service(self):
        properties = self.create(turbo_tier_status='Enabled')
        self.assertEqual({'status': 'Enabled'}, properties['turboTier'])

    def test_turbo_tier_update_preserves_unspecified_fields(self):
        existing = {'turbo_tier': models.TurboTier(status='Enabled', target_percent=35)}
        properties = self.update(turbo_tier_status='Enabled', existing=existing)
        self.assertEqual({'status': 'Enabled', 'targetPercent': 35}, properties['turboTier'])
        properties = self.update(turbo_tier_target_percent=50, existing=existing)
        self.assertEqual({'status': 'Enabled', 'targetPercent': 50}, properties['turboTier'])

    def test_turbo_tier_disable_does_not_send_existing_target(self):
        for target in (10, 35, 100):
            with self.subTest(target=target):
                existing = {'turbo_tier': models.TurboTier(status='Enabled', target_percent=target)}
                properties = self.update(turbo_tier_status='Disabled', existing=existing)
                self.assertEqual({'status': 'Disabled'}, properties['turboTier'])

    def test_create_serializes_sas_policy(self):
        properties = self.create(
            sas_expiration_period='1.00:00:00', require_user_bound_user_delegation_sas=False,
            require_user_bound_user_delegation_sas_action='None')
        self.assertEqual({
            'sasExpirationPeriod': '1.00:00:00', 'expirationAction': 'Log',
            'requireUserBoundUserDelegationSas': False, 'requireUserBoundUserDelegationSasAction': 'None'
        }, properties['sasPolicy'])

    def test_update_serializes_sas_policy_without_resetting_expiration(self):
        properties = self.update(
            require_user_bound_user_delegation_sas=False,
            existing={'sas_policy': SasPolicy(
                sas_expiration_period='1.00:00:00', expiration_action='Block',
                require_user_bound_user_delegation_sas=True,
                require_user_bound_user_delegation_sas_action='Log')})
        self.assertEqual({
            'sasExpirationPeriod': '1.00:00:00', 'expirationAction': 'Block',
            'requireUserBoundUserDelegationSas': False, 'requireUserBoundUserDelegationSasAction': 'Log'
        }, properties['sasPolicy'])

    def capture_request(self, operation):
        class RequestCaptured(Exception):
            pass

        requests = []

        def capture(pipeline_request):
            requests.append(pipeline_request.http_request)
            raise RequestCaptured()

        credential = mock.Mock()
        credential.get_token.return_value = AccessToken('unit-test-token', 4102444800)
        transport = mock.MagicMock()
        with StorageManagementClient(
                credential=credential, subscription_id='00000000-0000-0000-0000-000000000000',
                transport=transport, raw_request_hook=capture) as client:
            client.storage_accounts.check_name_availability = mock.Mock(
                return_value=models.CheckNameAvailabilityResult(name_available=True))
            with self.assertRaises(RequestCaptured):
                operation(client)
        transport.send.assert_not_called()
        self.assertEqual(1, len(requests))
        request = requests[0]
        self.assertIn('api-version=2026-09-01', request.url)
        return request.method, json.loads(request.body)['properties']

    def test_create_sends_2026_09_01_request_without_client_defaults(self):
        def create(client):
            with mock.patch(
                    'azure.cli.command_modules.storage.operations.account.storage_client_factory',
                    return_value=client):
                create_storage_account(
                    self.cmd, resource_group_name='rg', account_name='storageaccount',
                    sku='Standard_ZRS', kind='StorageV2', location='westus',
                    allow_shared_key_access_for_blob=False, allow_blob_access_points=True,
                    turbo_tier_status='Enabled')

        method, properties = self.capture_request(create)
        self.assertEqual('PUT', method)
        self.assertEqual({'blob': {'enabled': False}}, properties['allowSharedKeyAccessForServices'])
        self.assertEqual({'allowBlobAccessPoints': True}, properties['dataCollaborationPolicyProperties'])
        self.assertEqual({'status': 'Enabled'}, properties['turboTier'])

    def test_update_sends_2026_09_01_patch_preserving_policy_fields(self):
        def update(client):
            instance = models.StorageAccount(
                encryption=models.Encryption(key_source='Microsoft.Storage'),
                data_collaboration_policy_properties=models.StorageDataCollaborationPolicyProperties(
                    allow_storage_connectors=True, allow_blob_access_points=True))
            params = update_storage_account(self.cmd, instance, allow_blob_access_points=False)
            client.storage_accounts.update('rg', 'storageaccount', params)

        method, properties = self.capture_request(update)
        self.assertEqual('PATCH', method)
        self.assertEqual({
            'allowStorageConnectors': True, 'allowBlobAccessPoints': False
        }, properties['dataCollaborationPolicyProperties'])
        self.assertNotIn('allowSharedKeyAccessForServices', properties)
        self.assertNotIn('turboTier', properties)


class StorageManagementCliTest(unittest.TestCase):

    def setUp(self):
        self.cli_ctx = get_default_cli()
        self.client = mock.MagicMock()
        account = models.StorageAccount(
            location='westus', sku=models.Sku(name='Standard_ZRS'), kind='StorageV2',
            encryption=models.Encryption(key_source='Microsoft.Storage'), provisioning_state='Succeeded')
        self.client.storage_accounts.begin_create.return_value = account
        self.client.storage_accounts.check_name_availability.return_value = \
            models.CheckNameAvailabilityResult(name_available=True)
        self.client.blob_containers.create.return_value = models.BlobContainer()
        for target, value in [
                ('azure.cli.core._profile.Profile.get_subscription', {
                    'id': '00000000-0000-0000-0000-000000000000', 'name': 'unit-test',
                    'tenantId': '00000000-0000-0000-0000-000000000000',
                    'user': {'name': 'unit-test', 'type': 'user'}}),
                ('azure.cli.command_modules.storage.commands.cf_sa', self.client.storage_accounts),
                ('azure.cli.command_modules.storage.commands.cf_blob_container_mgmt',
                 self.client.blob_containers),
                ('azure.cli.command_modules.storage.operations.account.storage_client_factory', self.client)]:
            patcher = mock.patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'azure.mgmt.storage.operations.StorageAccountsOperations.get_properties',
            autospec=True, return_value=account)
        self.get_properties = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'azure.mgmt.storage.operations.StorageAccountsOperations.update',
            autospec=True, return_value=account)
        self.update = patcher.start()
        self.addCleanup(patcher.stop)

    def cmd(self, command):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                result = self.cli_ctx.invoke(
                    shlex.split(command) + ['--subscription', '00000000-0000-0000-0000-000000000000'],
                    out_file=output)
            except SystemExit as error:
                result = error.code
        self.assertEqual(0, result or 0, output.getvalue())

    def assert_policies(self, parameters):
        properties = parameters.as_dict()['properties']
        expected = {
            'allowCrossTenantDelegationSas': False,
            'sasPolicy': {
                'sasExpirationPeriod': '1.00:00:00', 'expirationAction': 'Block',
                'requireUserBoundUserDelegationSas': False, 'requireUserBoundUserDelegationSasAction': 'Log'},
            'allowSharedKeyAccessForServices': {
                'blob': {'enabled': False}, 'file': {'enabled': True},
                'table': {'enabled': False}, 'queue': {'enabled': True}},
            'dataCollaborationPolicyProperties': {
                'allowBlobAccessPoints': True},
            'turboTier': {'status': 'Enabled', 'targetPercent': 10}
        }
        for name, value in expected.items():
            self.assertEqual(value, properties[name], name)

    def test_create_policy_arguments_reach_sdk(self):
        self.cmd('storage account create -g rg -n storageaccount --location westus --sku Standard_ZRS '
                 '--kind StorageV2 --sas-expiration-period 1.00:00:00 --sas-expiration-action Block '
                 '--allow-cross-tenant-delegation-sas false '
                 '--require-user-bound-user-delegation-sas false --require-user-bound-user-delegation-sas-action Log '
                 '--allow-shared-key-access-for-blob false --allow-shared-key-access-for-file true '
                 '--allow-shared-key-access-for-table false --allow-shared-key-access-for-queue true '
                 '--allow-blob-access-points true '
                 '--turbo-tier-status Enabled --turbo-tier-target-percent 10')
        self.client.storage_accounts.begin_create.assert_called_once()
        self.assert_policies(self.client.storage_accounts.begin_create.call_args.args[2])

    def test_update_policy_arguments_reach_sdk(self):
        self.cmd('storage account update -g rg -n storageaccount '
                 '--sas-expiration-period 1.00:00:00 --sas-expiration-action Block '
                 '--allow-cross-tenant-delegation-sas false '
                 '--require-user-bound-user-delegation-sas false --require-user-bound-user-delegation-sas-action Log '
                 '--allow-shared-key-access-for-blob false --allow-shared-key-access-for-file true '
                 '--allow-shared-key-access-for-table false --allow-shared-key-access-for-queue true '
                 '--allow-blob-access-points true '
                 '--turbo-tier-status Enabled --turbo-tier-target-percent 10')
        self.update.assert_called_once()
        self.get_properties.assert_called_once()
        self.assert_policies(self.update.call_args.kwargs['parameters'])

    def test_container_attachment_arguments_reach_sdk(self):
        self.cmd('storage container-rm create -g rg --storage-account storageaccount -n container '
                 '--blob-access-point-configuration-name accesspoint '
                 '--blob-access-point-configuration-unique-id 00000000-0000-0000-0000-000000000001')
        self.client.blob_containers.create.assert_called_once()
        properties = self.client.blob_containers.create.call_args.kwargs['blob_container'].as_dict()['properties']
        self.assertEqual({
            'blobAccessPointConfigurationName': 'accesspoint',
            'blobAccessPointConfigurationUniqueId': '00000000-0000-0000-0000-000000000001'
        }, properties['blobAccessPointConfiguration'])


class StorageManagementArgumentHelpTest(unittest.TestCase):

    @staticmethod
    def get_help(command):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                result = get_default_cli().invoke(command + ['--help'], out_file=output)
            except SystemExit as error:
                result = error.code
        return result, output.getvalue()

    def test_account_create_and_update_expose_policy_aliases(self):
        flags = [
            '--blob-shared-key', '--file-shared-key', '--table-shared-key', '--queue-shared-key',
            '--allow-access-points',
            '--cross-tenant-sas', '--user-bound-sas', '--user-bound-action',
            '--turbo-tier-status', '--turbo-tier-target'
        ]
        for operation in ['create', 'update']:
            with self.subTest(operation=operation):
                result, output = self.get_help(['storage', 'account', operation])
                self.assertEqual(0, result, output)
                for flag in flags:
                    self.assertIn(flag, output)
                for flag in ['--allow-storage-connectors', '--allow-connectors',
                             '--allow-storage-data-shares', '--allow-data-shares',
                             '--allow-cross-tenant-data-sharing', '--cross-tenant-sharing']:
                    self.assertNotIn(flag, output)

    def test_existing_in_scope_account_options_remain_public(self):
        cases = [
            (['storage', 'account', 'create'], ['Smart', 'All']),
            (['storage', 'account', 'update'], ['Smart', 'All']),
            (['storage', 'account', 'or-policy', 'create'], ['--tags-replication']),
            (['storage', 'account', 'or-policy', 'update'], ['--tags-replication']),
            (['storage', 'account', 'blob-service-properties', 'update'],
             ['--enable-static-website', '--default-index-document-path'])
        ]
        for command, options in cases:
            with self.subTest(command=command):
                result, output = self.get_help(command)
                self.assertEqual(0, result, output)
                for option in options:
                    self.assertIn(option, output)

    def test_container_attachment_arguments_are_create_only(self):
        result, output = self.get_help(['storage', 'container-rm', 'create'])
        self.assertEqual(0, result, output)
        self.assertIn('--access-point-config', output)
        self.assertIn('--access-point-uid', output)
        result, output = self.get_help(['storage', 'container-rm', 'update'])
        self.assertEqual(0, result, output)
        self.assertNotIn('--access-point-config', output)
        self.assertNotIn('--access-point-uid', output)


if __name__ == '__main__':
    unittest.main()
