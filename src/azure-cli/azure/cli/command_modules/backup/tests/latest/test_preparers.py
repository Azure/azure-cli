# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, call, patch

from azure.core.exceptions import HttpResponseError
from azure.cli.command_modules.backup.tests.latest.preparers import ResourceGroupPreparer


class _CommandResult:
    def __init__(self, output):
        self.output = output

    def get_output_in_json(self):
        return self.output


class ResourceGroupPreparerTests(unittest.TestCase):
    def test_remove_locks_deletes_resource_locks_without_deleting_inherited_locks(self):
        resource_group = 'test-rg'
        resource_id = ('/subscriptions/test-sub/resourceGroups/test-rg/providers/'
                       'Microsoft.Storage/storageAccounts/test-account')
        group_lock_id = ('/subscriptions/test-sub/resourceGroups/test-rg/providers/'
                         'Microsoft.Authorization/locks/group-lock')
        resource_lock_id = resource_id + '/providers/Microsoft.Authorization/locks/resource-lock'
        subscription_lock_id = '/subscriptions/test-sub/providers/Microsoft.Authorization/locks/sub-lock'

        results = {
            'az lock list -g test-rg --subscription test-sub -o json': [
                {'id': group_lock_id}
            ],
            'az resource list -g test-rg --subscription test-sub -o json': [
                {'id': resource_id}
            ],
            'az lock list --resource {} --subscription test-sub -o json'.format(resource_id): [
                {'id': group_lock_id},
                {'id': resource_lock_id},
                {'id': subscription_lock_id},
            ],
        }

        def execute(_cli_ctx, command):
            if command.startswith('az lock delete '):
                return None
            return _CommandResult(results[command])

        preparer = ResourceGroupPreparer(subscription='test-sub')
        preparer.live_only_execute = Mock(side_effect=execute)

        preparer._remove_locks(resource_group, ' --subscription test-sub', include_resource_locks=True)

        preparer.live_only_execute.assert_has_calls([
            call(preparer.cli_ctx, 'az lock list -g test-rg --subscription test-sub -o json'),
            call(preparer.cli_ctx, 'az resource list -g test-rg --subscription test-sub -o json'),
            call(preparer.cli_ctx, 'az lock list --resource {} --subscription test-sub -o json'.format(resource_id)),
            call(preparer.cli_ctx, 'az lock delete --ids {} --subscription test-sub'.format(group_lock_id)),
            call(preparer.cli_ctx, 'az lock delete --ids {} --subscription test-sub'.format(resource_lock_id)),
        ])
        self.assertNotIn(
            call(preparer.cli_ctx,
                 'az lock delete --ids {} --subscription test-sub'.format(subscription_lock_id)),
            preparer.live_only_execute.call_args_list,
        )

    def test_remove_resource_scans_resource_locks_only_after_scope_locked(self):
        resource_id = ('/subscriptions/test-sub/resourceGroups/test-rg/providers/'
                       'Microsoft.Storage/storageAccounts/test-account')
        lock_id = resource_id + '/providers/Microsoft.Authorization/locks/backup-lock'
        locked = True

        def execute(_cli_ctx, command):
            nonlocal locked
            if command.startswith('az lock list -g '):
                return _CommandResult([])
            if command.startswith('az resource list '):
                return _CommandResult([{'id': resource_id}])
            if command.startswith('az lock list --resource '):
                return _CommandResult([{'id': lock_id}])
            if command.startswith('az lock delete '):
                locked = False
                return None
            if command.startswith('az group delete '):
                if locked:
                    raise HttpResponseError(message='ScopeLocked')
                return None
            self.fail('Unexpected command: ' + command)

        preparer = ResourceGroupPreparer(subscription='test-sub')
        preparer.dev_setting_name = None
        preparer.live_only_execute = Mock(side_effect=execute)

        with patch('time.sleep') as sleep:
            preparer.remove_resource('test-rg')

        commands = [args[1] for args, _ in preparer.live_only_execute.call_args_list]
        delete_command = 'az group delete --name test-rg --yes --no-wait --subscription test-sub'
        resource_list_command = 'az resource list -g test-rg --subscription test-sub -o json'
        self.assertLess(commands.index(delete_command), commands.index(resource_list_command))
        self.assertEqual(commands.count(delete_command), 2)
        self.assertFalse(locked)
        sleep.assert_called_once_with(preparer._DELETE_RETRY_WAIT)

    def test_remove_resource_does_not_scan_resources_when_delete_succeeds(self):
        preparer = ResourceGroupPreparer()
        preparer.dev_setting_name = None
        preparer.live_only_execute = Mock(return_value=_CommandResult([]))

        with patch('time.sleep') as sleep:
            preparer.remove_resource('test-rg')

        self.assertEqual(preparer.live_only_execute.call_args_list, [
            call(preparer.cli_ctx, 'az lock list -g test-rg -o json'),
            call(preparer.cli_ctx, 'az group delete --name test-rg --yes --no-wait'),
        ])
        sleep.assert_not_called()

    def test_remove_resource_preserves_dev_setting_guard(self):
        preparer = ResourceGroupPreparer()
        preparer.dev_setting_name = 'existing-dev-resource-group'
        preparer.live_only_execute = Mock()

        preparer.remove_resource('test-rg')

        preparer.live_only_execute.assert_not_called()

    def test_remove_locks_preserves_inherited_subscription_lock(self):
        subscription_lock = '/subscriptions/test-sub/providers/Microsoft.Authorization/locks/sub-lock'
        preparer = ResourceGroupPreparer(subscription='test-sub')
        preparer.live_only_execute = Mock(return_value=_CommandResult([{'id': subscription_lock}]))

        preparer._remove_locks('test-rg', ' --subscription test-sub')

        preparer.live_only_execute.assert_called_once_with(
            preparer.cli_ctx, 'az lock list -g test-rg --subscription test-sub -o json')

    def test_remove_resource_does_not_retry_unrelated_errors(self):
        error = HttpResponseError(message='AuthorizationFailed')

        def execute(_cli_ctx, command):
            if command.startswith('az group delete '):
                raise error
            return _CommandResult([])

        preparer = ResourceGroupPreparer()
        preparer.dev_setting_name = None
        preparer.live_only_execute = Mock(side_effect=execute)

        with patch('time.sleep') as sleep:
            with self.assertRaises(HttpResponseError) as raised:
                preparer.remove_resource('test-rg')

        self.assertIs(raised.exception, error)
        self.assertEqual(preparer.live_only_execute.call_count, 2)
        sleep.assert_not_called()

    def test_remove_resource_raises_scope_locked_after_bounded_retries(self):
        def execute(_cli_ctx, command):
            if command.startswith('az group delete '):
                raise HttpResponseError(message='ScopeLocked')
            return _CommandResult([])

        preparer = ResourceGroupPreparer()
        preparer.dev_setting_name = None
        preparer.live_only_execute = Mock(side_effect=execute)

        with patch('time.sleep') as sleep:
            with self.assertRaisesRegex(HttpResponseError, 'ScopeLocked'):
                preparer.remove_resource('test-rg')

        delete_calls = [
            args[1] for args, _ in preparer.live_only_execute.call_args_list
            if args[1].startswith('az group delete ')
        ]
        self.assertEqual(len(delete_calls), preparer._MAX_DELETE_ATTEMPTS)
        self.assertEqual(sleep.call_count, preparer._MAX_DELETE_ATTEMPTS - 1)

    def test_remove_locks_logs_cleanup_errors(self):
        resource_id = ('/subscriptions/test-sub/resourceGroups/test-rg/providers/'
                       'Microsoft.Storage/storageAccounts/test-account')
        lock_id = resource_id + '/providers/Microsoft.Authorization/locks/backup-lock'
        results = {
            'az lock list -g test-rg --subscription test-sub -o json': [],
            'az resource list -g test-rg --subscription test-sub -o json': [{'id': resource_id}],
            'az lock list --resource {} --subscription test-sub -o json'.format(resource_id): [{'id': lock_id}],
            'az lock delete --ids {} --subscription test-sub'.format(lock_id): [],
        }

        for failed_command in results:
            with self.subTest(command=failed_command):
                error = HttpResponseError(message='AuthorizationFailed')

                def execute(_cli_ctx, command):
                    if command == failed_command:
                        raise error
                    return _CommandResult(results[command])

                preparer = ResourceGroupPreparer(subscription='test-sub')
                preparer.live_only_execute = Mock(side_effect=execute)
                with patch('azure.cli.command_modules.backup.tests.latest.preparers.logger.warning') as warning:
                    preparer._remove_locks('test-rg', ' --subscription test-sub', include_resource_locks=True)

                warning.assert_called_once()
                self.assertIs(warning.call_args.args[-1], error)


if __name__ == '__main__':
    unittest.main()
