# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit tests for managed-identity connected registry creation, deletion, permissions, update, and settings."""

import unittest
from unittest import mock

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import ArgumentUsageError
from knack.util import CLIError

from azure.mgmt.containerregistry import models
from azure.mgmt.containerregistry.models import (
    ManagedServiceIdentity,
    ManagedServiceIdentityType,
    UserAssignedIdentity,
)

from azure.cli.command_modules.acr._constants import ConnectedRegistryAuthType

from azure.cli.command_modules.acr.connected_registry import (
    _build_user_assigned_identity,
    _get_current_auth_type,
    acr_connected_registry_create,
    acr_connected_registry_delete,
    acr_connected_registry_get_settings,
    acr_connected_registry_permissions_show,
    acr_connected_registry_permissions_update,
    acr_connected_registry_update,
    AUTH_TYPE_MANAGED_IDENTITY,
    AUTH_TYPE_SYNC_TOKEN,
    MSI_TYPE_USER_ASSIGNED,
)


TEST_SUB = '00000000-0000-0000-0000-000000000001'
TEST_RG = 'rg'
TEST_REGISTRY = 'testreg'
TEST_CR = 'testcr123'
TEST_MSI_ID = (
    '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ManagedIdentity/'
    'userAssignedIdentities/msi1'.format(TEST_SUB, TEST_RG)
)
TEST_MSI_ID2 = TEST_MSI_ID.replace('msi1', 'msi2')


def _make_cmd():
    cmd = mock.MagicMock()
    cmd.cli_ctx = mock.MagicMock()
    return cmd


def _fake_cr(auth_type=None, has_identity=False, connection_state=None,
             token_id=None, gateway_endpoint='parent.example.com', client_id='cid-1'):
    """Build a fake connected-registry return object shaped like the SDK model."""
    cr = mock.MagicMock()
    cr.name = TEST_CR
    cr.mode = 'ReadOnly'
    cr.connection_state = connection_state
    cr.client_token_ids = None
    cr.notifications_list = None
    cr.parent = mock.MagicMock()
    cr.parent.id = None
    cr.parent.sync_properties = mock.MagicMock()
    # Real MI-configured connected registries always have authType=ManagedIdentity set alongside
    # the identity. Preserve that invariant when callers don't override auth_type explicitly.
    if auth_type is None and has_identity:
        auth_type = AUTH_TYPE_MANAGED_IDENTITY
    cr.parent.sync_properties.auth_type = auth_type
    cr.parent.sync_properties.token_id = token_id
    cr.parent.sync_properties.gateway_endpoint = gateway_endpoint
    if has_identity:
        cr.identity = mock.MagicMock()
        cr.identity.type = MSI_TYPE_USER_ASSIGNED
        msi = mock.MagicMock()
        msi.client_id = client_id
        cr.identity.user_assigned_identities = {TEST_MSI_ID: msi}
    else:
        cr.identity = None
    return cr


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstantsSourcedFromEnum(unittest.TestCase):
    """The module constants must match the ConnectedRegistryAuthType enum values verbatim."""

    def test_auth_type_constants(self):
        self.assertEqual(AUTH_TYPE_SYNC_TOKEN, ConnectedRegistryAuthType.SYNC_TOKEN.value)
        self.assertEqual(AUTH_TYPE_MANAGED_IDENTITY, ConnectedRegistryAuthType.MANAGED_IDENTITY.value)

    def test_msi_type_constant(self):
        self.assertEqual(MSI_TYPE_USER_ASSIGNED, ManagedServiceIdentityType.USER_ASSIGNED.value)


# ---------------------------------------------------------------------------
# Helper: _get_current_auth_type
# ---------------------------------------------------------------------------


class TestGetCurrentAuthType(unittest.TestCase):

    def test_managed_identity_auth_type(self):
        cr = _fake_cr(auth_type=AUTH_TYPE_MANAGED_IDENTITY, has_identity=True)
        self.assertEqual(_get_current_auth_type(cr), AUTH_TYPE_MANAGED_IDENTITY)

    def test_sync_token_auth_type_no_identity(self):
        cr = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN, has_identity=False)
        self.assertEqual(_get_current_auth_type(cr), AUTH_TYPE_SYNC_TOKEN)

    def test_missing_auth_type_defaults_to_sync_token(self):
        cr = _fake_cr(auth_type=None, has_identity=False)
        self.assertEqual(_get_current_auth_type(cr), AUTH_TYPE_SYNC_TOKEN)

    def test_enum_valued_auth_type_is_coerced_to_string(self):
        cr = _fake_cr(auth_type=ConnectedRegistryAuthType.MANAGED_IDENTITY, has_identity=False)
        result = _get_current_auth_type(cr)
        self.assertEqual(result, AUTH_TYPE_MANAGED_IDENTITY)
        self.assertIsInstance(result, str)
        self.assertNotIn('ConnectedRegistryAuthType.', result)


# ---------------------------------------------------------------------------
# Helper: _build_user_assigned_identity
# ---------------------------------------------------------------------------


class TestBuildUserAssignedIdentity(unittest.TestCase):

    def test_shape(self):
        cmd = _make_cmd()
        cmd.get_models.return_value = (ManagedServiceIdentity, UserAssignedIdentity)
        identity = _build_user_assigned_identity(cmd, TEST_MSI_ID)
        self.assertIsInstance(identity, ManagedServiceIdentity)
        self.assertEqual(identity.type, MSI_TYPE_USER_ASSIGNED)
        self.assertIn(TEST_MSI_ID, identity.user_assigned_identities)
        self.assertIsInstance(
            identity.user_assigned_identities[TEST_MSI_ID], UserAssignedIdentity)


# ---------------------------------------------------------------------------
# create: client-side argument validation
# ---------------------------------------------------------------------------


class TestConnectedRegistryCreateValidation(unittest.TestCase):

    def _create(self, **overrides):
        kwargs = dict(
            cmd=_make_cmd(),
            client=mock.MagicMock(),
            registry_name=TEST_REGISTRY,
            connected_registry_name=TEST_CR,
            mode='ReadOnly',
        )
        kwargs.update(overrides)
        return acr_connected_registry_create(**kwargs)

    def test_mi_requires_identity(self):
        with self.assertRaises(ArgumentUsageError):
            self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY)

    def test_mi_rejects_sync_token(self):
        with self.assertRaises(ArgumentUsageError):
            self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                         identity=TEST_MSI_ID, sync_token_name='tok')

    def test_mi_rejects_repository(self):
        with self.assertRaises(ArgumentUsageError):
            self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                         identity=TEST_MSI_ID, repositories=['r1'])

    def test_sync_token_rejects_identity(self):
        with self.assertRaises(ArgumentUsageError):
            self._create(auth_type=AUTH_TYPE_SYNC_TOKEN, identity=TEST_MSI_ID,
                         sync_token_name='tok')

    def test_sync_token_requires_exactly_one_of_token_or_repos(self):
        with self.assertRaises(CLIError):
            # neither
            self._create(auth_type=AUTH_TYPE_SYNC_TOKEN)
        with self.assertRaises(CLIError):
            # both
            self._create(auth_type=AUTH_TYPE_SYNC_TOKEN,
                         sync_token_name='tok', repositories=['r1'])

    def test_short_name_rejected(self):
        with self.assertRaises(Exception):  # InvalidArgumentValueError
            self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                         identity=TEST_MSI_ID,
                         connected_registry_name='abc')  # < 5 chars

    def test_mi_rejects_blank_identity(self):
        for identity in ('', ' ', '\t'):
            with self.subTest(identity=identity), self.assertRaises(ArgumentUsageError):
                self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY, identity=identity)

    def test_mi_rejects_explicit_empty_token_or_repositories(self):
        for options in ({'sync_token_name': ''}, {'repositories': []}, {'repositories': ['']}):
            with self.subTest(options=options), self.assertRaises(ArgumentUsageError):
                self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY, identity=TEST_MSI_ID, **options)

    def test_identity_requires_explicit_managed_identity_auth(self):
        for auth_type in (None, AUTH_TYPE_SYNC_TOKEN):
            for identity in ('', TEST_MSI_ID):
                with self.subTest(auth_type=auth_type, identity=identity), \
                     self.assertRaises(ArgumentUsageError):
                    self._create(auth_type=auth_type, identity=identity, sync_token_name='tok')

    def test_mi_rejects_parent_before_registry_lookup(self):
        with mock.patch(UPDATE_MODULE + '.get_registry_by_name') as get_registry, \
             mock.patch(UPDATE_MODULE + '.get_subscription_id') as get_subscription:
            for parent_name in ('parentcr', ''):
                with self.subTest(parent_name=parent_name), self.assertRaisesRegex(ArgumentUsageError, '--parent'):
                    self._create(auth_type=AUTH_TYPE_MANAGED_IDENTITY, identity=TEST_MSI_ID,
                                 parent_name=parent_name)
            get_registry.assert_not_called()
            get_subscription.assert_not_called()

    def test_mi_parent_rejected_before_mutations(self):
        parent = _fake_cr(has_identity=True)
        client = mock.MagicMock()
        registry = mock.MagicMock(data_endpoint_enabled=False)
        with mock.patch(UPDATE_MODULE + '.get_subscription_id', return_value=TEST_SUB), \
             mock.patch(UPDATE_MODULE + '.get_registry_by_name', return_value=(registry, TEST_RG)), \
             mock.patch(UPDATE_MODULE + '.acr_connected_registry_show', return_value=parent) as show, \
             mock.patch(UPDATE_MODULE + '.acr_update_custom') as update_registry, \
             mock.patch(UPDATE_MODULE + '.acr_update_set') as set_registry, \
             mock.patch(UPDATE_MODULE + '._create_sync_token') as create_token, \
             mock.patch(UPDATE_MODULE + '._update_ancestor_permissions') as update_permissions:
            for auth_type in (None, AUTH_TYPE_SYNC_TOKEN, AUTH_TYPE_MANAGED_IDENTITY):
                with self.subTest(auth_type=auth_type), self.assertRaises(ArgumentUsageError):
                    options = {'identity': TEST_MSI_ID} if auth_type == AUTH_TYPE_MANAGED_IDENTITY else {
                        'repositories': ['r1']}
                    self._create(client=client, parent_name='parentcr', auth_type=auth_type, **options)
            self.assertEqual(show.call_count, 2)
            client.list.assert_not_called()
            client.begin_create.assert_not_called()
            update_registry.assert_not_called()
            set_registry.assert_not_called()
            create_token.assert_not_called()
            update_permissions.assert_not_called()


class TestConnectedRegistryCreatePayload(unittest.TestCase):

    def test_root_auth_payload_and_token_paths(self):
        for auth_type, options in (
                (AUTH_TYPE_MANAGED_IDENTITY, {'identity': TEST_MSI_ID}),
                (None, {'sync_token_name': 'sync-token'}),
                (AUTH_TYPE_SYNC_TOKEN, {'repositories': ['r1']})):
            with self.subTest(auth_type=auth_type):
                cmd = _make_cmd()
                cmd.get_models.side_effect = lambda *names: tuple(getattr(models, name) for name in names)
                client = mock.MagicMock()
                registry = mock.MagicMock(data_endpoint_enabled=True)
                token_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/registries/{}/tokens/sync-token'.format(
                    TEST_SUB, TEST_RG, TEST_REGISTRY)
                client_token_id = token_id.replace('/tokens/sync-token', '/tokens/client-token')
                with mock.patch(UPDATE_MODULE + '.get_subscription_id', return_value=TEST_SUB), \
                     mock.patch(UPDATE_MODULE + '.get_registry_by_name', return_value=(registry, TEST_RG)), \
                     mock.patch(UPDATE_MODULE + '._create_sync_token', return_value=token_id) as create_token, \
                     mock.patch(UPDATE_MODULE + '.cf_acr_tokens') as tokens, \
                     mock.patch(UPDATE_MODULE + '.cf_acr_scope_maps') as scope_maps, \
                     mock.patch(UPDATE_MODULE + '._update_ancestor_permissions') as update_permissions:
                    result = acr_connected_registry_create(
                        cmd, client, TEST_REGISTRY, TEST_CR, mode='ReadOnly', auth_type=auth_type,
                        client_token_list=['client-token'], sync_schedule='0 12 * * *', sync_window='PT4H',
                        sync_message_ttl='P2D', log_level='Information', sync_audit_logs_enabled=True,
                        garbage_collection_enabled=True, garbage_collection_schedule='0 0 * * *',
                        notifications=['hello:latest', 'hello:latest'], **options)
                self.assertIs(result, client.begin_create.return_value)
                client.begin_create.assert_called_once()
                call = client.begin_create.call_args.kwargs
                self.assertEqual(call['resource_group_name'], TEST_RG)
                self.assertEqual(call['registry_name'], TEST_REGISTRY)
                self.assertEqual(call['connected_registry_name'], TEST_CR)
                parameters = call['connected_registry_create_parameters']
                self.assertIsInstance(parameters, models.ConnectedRegistry)
                expected_sync = {
                    'authType': auth_type or AUTH_TYPE_SYNC_TOKEN,
                    'schedule': '0 12 * * *',
                    'messageTtl': 'P2D',
                    'syncWindow': 'PT4H',
                }
                if auth_type == AUTH_TYPE_MANAGED_IDENTITY:
                    self.assertEqual(parameters.identity.as_dict(), {
                        'type': 'UserAssigned', 'userAssignedIdentities': {TEST_MSI_ID: {}}})
                    self.assertIsNone(parameters.parent.sync_properties.token_id)
                    create_token.assert_not_called()
                else:
                    self.assertIsNone(parameters.identity)
                    expected_sync['tokenId'] = token_id
                    if 'repositories' in options:
                        create_token.assert_called_once_with(
                            cmd, TEST_RG, TEST_REGISTRY, TEST_CR, ['r1'], 'readonly')
                    else:
                        create_token.assert_not_called()
                self.assertIsNone(parameters.parent.id)
                self.assertEqual(parameters.parent.sync_properties.as_dict(), expected_sync)
                self.assertEqual(parameters.mode, 'readonly')
                self.assertEqual(parameters.client_token_ids, [client_token_id])
                self.assertEqual(parameters.logging.as_dict(), {
                    'logLevel': 'Information', 'auditLogStatus': 'Enabled'})
                self.assertEqual(parameters.garbage_collection.as_dict(), {
                    'enabled': True, 'schedule': '0 0 * * *'})
                self.assertEqual(parameters.notifications_list, ['hello:latest'])
                client.get.assert_not_called()
                client.list.assert_not_called()
                tokens.assert_not_called()
                scope_maps.assert_not_called()
                update_permissions.assert_not_called()


UPDATE_MODULE = 'azure.cli.command_modules.acr.connected_registry'


class TestConnectedRegistryDelete(unittest.TestCase):

    def test_mi_delete_skips_token_cleanup(self):
        token_id = (
            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/'
            'registries/{}/tokens/old-sync'.format(TEST_SUB, TEST_RG, TEST_REGISTRY))
        for cleanup in (False, True):
            for auth_type in (AUTH_TYPE_MANAGED_IDENTITY, models.AuthType.MANAGED_IDENTITY):
                for previous_token in (None, token_id):
                    with self.subTest(cleanup=cleanup, auth_type=auth_type, token_id=previous_token):
                        cr = _fake_cr(auth_type=auth_type, has_identity=True, token_id=previous_token)
                        cmd = _make_cmd()
                        client = mock.MagicMock()
                        client.get.return_value = cr
                        client.begin_delete.return_value.result.return_value = mock.sentinel.deleted
                        with mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                                        return_value=(None, TEST_RG)), \
                             mock.patch(UPDATE_MODULE + '.user_confirmation') as confirm, \
                             mock.patch(UPDATE_MODULE + '.get_token_from_id') as token_lookup, \
                             mock.patch(UPDATE_MODULE + '.get_scope_map_from_id') as scope_lookup, \
                             mock.patch(UPDATE_MODULE + '.cf_acr_tokens') as tokens, \
                             mock.patch(UPDATE_MODULE + '.cf_acr_scope_maps') as scope_maps, \
                             mock.patch('azure.cli.command_modules.acr.token.acr_token_delete') as delete_token, \
                             mock.patch('azure.cli.command_modules.acr.scope_map.acr_scope_map_delete') as delete_scope, \
                             mock.patch(UPDATE_MODULE + '._get_family_tree') as family_tree, \
                             mock.patch(UPDATE_MODULE + '._update_ancestor_permissions') as update_permissions, \
                             mock.patch(UPDATE_MODULE + '.logger.warning') as warning:
                            result = acr_connected_registry_delete(
                                cmd, client, TEST_CR, TEST_REGISTRY, cleanup=cleanup, resource_group_name=TEST_RG)
                        self.assertIs(result, mock.sentinel.deleted)
                        client.get.assert_called_once_with(TEST_RG, TEST_REGISTRY, TEST_CR)
                        client.begin_delete.assert_called_once_with(TEST_RG, TEST_REGISTRY, TEST_CR)
                        client.begin_delete.return_value.result.assert_called_once_with()
                        self.assertEqual(client.mock_calls, [
                            mock.call.get(TEST_RG, TEST_REGISTRY, TEST_CR),
                            mock.call.begin_delete(TEST_RG, TEST_REGISTRY, TEST_CR),
                            mock.call.begin_delete().result(),
                        ])
                        confirm.assert_called_once_with(
                            "Are you sure you want to delete the connected registry '{}' in '{}'{}?".format(
                                TEST_CR, TEST_REGISTRY, '' if cleanup else ' without cleanup flag enabled'), False)
                        token_lookup.assert_not_called()
                        scope_lookup.assert_not_called()
                        tokens.assert_not_called()
                        scope_maps.assert_not_called()
                        delete_token.assert_not_called()
                        delete_scope.assert_not_called()
                        family_tree.assert_not_called()
                        update_permissions.assert_not_called()
                        warning.assert_not_called()

    def test_sync_token_delete_preserves_cleanup_and_warning(self):
        token_id = (
            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/'
            'registries/{}/tokens/sync'.format(TEST_SUB, TEST_RG, TEST_REGISTRY))
        for cleanup in (False, True):
            for auth_type in (AUTH_TYPE_SYNC_TOKEN, models.AuthType.SYNC_TOKEN, None):
                with self.subTest(cleanup=cleanup, auth_type=auth_type):
                    cr = _fake_cr(auth_type=auth_type, token_id=token_id)
                    cr.parent.id = '/connectedRegistries/parent'
                    cmd = _make_cmd()
                    client = mock.MagicMock()
                    client.get.return_value = cr
                    client.begin_delete.return_value.result.return_value = mock.sentinel.deleted
                    client.list.return_value = [mock.sentinel.parent]
                    token = mock.MagicMock()
                    token.name = 'sync'
                    token.scope_map_id = token_id.replace('/tokens/sync', '/scopeMaps/sync-scope')
                    with mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                                    return_value=(None, TEST_RG)), \
                         mock.patch(UPDATE_MODULE + '.user_confirmation') as confirm, \
                         mock.patch(UPDATE_MODULE + '.get_token_from_id', return_value=token) as token_lookup, \
                         mock.patch(UPDATE_MODULE + '.cf_acr_tokens') as tokens, \
                         mock.patch(UPDATE_MODULE + '.cf_acr_scope_maps') as scope_maps, \
                         mock.patch('azure.cli.command_modules.acr.token.acr_token_delete') as delete_token, \
                         mock.patch('azure.cli.command_modules.acr.scope_map.acr_scope_map_delete') as delete_scope, \
                         mock.patch(UPDATE_MODULE + '._get_family_tree',
                                    return_value=(mock.sentinel.family_tree, None)) as family_tree, \
                         mock.patch(UPDATE_MODULE + '._update_ancestor_permissions') as update_permissions, \
                         mock.patch(UPDATE_MODULE + '.logger.warning') as warning:
                        result = acr_connected_registry_delete(
                            cmd, client, TEST_CR, TEST_REGISTRY, cleanup=cleanup, yes=True, resource_group_name=TEST_RG)
                    self.assertIs(result, mock.sentinel.deleted)
                    client.get.assert_called_once_with(TEST_RG, TEST_REGISTRY, TEST_CR)
                    client.begin_delete.assert_called_once_with(TEST_RG, TEST_REGISTRY, TEST_CR)
                    client.begin_delete.return_value.result.assert_called_once_with()
                    confirm.assert_called_once_with(
                        "Are you sure you want to delete the connected registry '{}' in '{}'{}?".format(
                            TEST_CR, TEST_REGISTRY, '' if cleanup else ' without cleanup flag enabled'), True)
                    token_lookup.assert_called_once_with(cmd, token_id)
                    if cleanup:
                        tokens.assert_called_once_with(cmd.cli_ctx)
                        scope_maps.assert_called_once_with(cmd.cli_ctx)
                        delete_token.assert_called_once_with(
                            cmd, tokens.return_value, TEST_REGISTRY, 'sync', True, TEST_RG)
                        delete_token.return_value.result.assert_called_once_with()
                        delete_scope.assert_called_once_with(
                            cmd, scope_maps.return_value, TEST_REGISTRY, 'sync-scope', True, TEST_RG)
                        delete_scope.return_value.result.assert_called_once_with()
                        client.list.assert_called_once_with(TEST_RG, TEST_REGISTRY)
                        family_tree.assert_called_once_with([mock.sentinel.parent], None)
                        update_permissions.assert_called_once_with(
                            cmd, mock.sentinel.family_tree, TEST_RG, TEST_REGISTRY,
                            cr.parent.id, TEST_CR, remove_access=True)
                        warning.assert_not_called()
                    else:
                        tokens.assert_not_called()
                        scope_maps.assert_not_called()
                        delete_token.assert_not_called()
                        delete_scope.assert_not_called()
                        client.list.assert_not_called()
                        family_tree.assert_not_called()
                        update_permissions.assert_not_called()
                        warning.assert_called_once_with(
                            "Connected registry successfully deleted. Please cleanup your sync tokens and scope maps. "
                            "Run the following commands for cleanup: \n\t"
                            "az acr token delete -n sync -r {registry} --yes\n\t"
                            "az acr scope-map delete -n sync-scope -r {registry} --yes\n"
                            "Run the following command on all ascendency to remove the deleted registry gateway access: "
                            "\n\taz acr scope-map update -n <scope-map-name> -r {registry} --remove-gateway "
                            "{connected_registry} config/read config/write message/read message/write".format(
                                registry=TEST_REGISTRY, connected_registry=TEST_CR))


# ---------------------------------------------------------------------------
# permissions show / update: blocked on MI
# ---------------------------------------------------------------------------


class TestConnectedRegistryPermissionsMI(unittest.TestCase):

    def test_permissions_show_blocked_on_mi(self):
        cr = _fake_cr(has_identity=True)
        with mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                        return_value=(None, TEST_RG)), \
             mock.patch(UPDATE_MODULE + '.acr_connected_registry_show',
                        return_value=cr):
            with self.assertRaises(ArgumentUsageError):
                acr_connected_registry_permissions_show(
                    cmd=_make_cmd(), client=mock.MagicMock(),
                    connected_registry_name=TEST_CR, registry_name=TEST_REGISTRY,
                    resource_group_name=TEST_RG)

    def test_permissions_update_blocked_on_mi(self):
        cr = _fake_cr(has_identity=True)
        client = mock.MagicMock()
        client.list.return_value = [cr]
        with mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                        return_value=(None, TEST_RG)):
            with self.assertRaises(ArgumentUsageError):
                acr_connected_registry_permissions_update(
                    cmd=_make_cmd(), client=client,
                    connected_registry_name=TEST_CR, registry_name=TEST_REGISTRY,
                    add_repos=['r1'], resource_group_name=TEST_RG)


# ---------------------------------------------------------------------------
# update: input validation and PATCH shape
# ---------------------------------------------------------------------------


class TestConnectedRegistryUpdateMigration(unittest.TestCase):

    def _patch_common(self):
        p_validate = mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                                return_value=(None, TEST_RG))
        p_subid = mock.patch(UPDATE_MODULE + '.get_subscription_id',
                             return_value=TEST_SUB)
        return p_validate, p_subid

    def _run_update(self, current, **overrides):
        client = mock.MagicMock()
        cmd = _make_cmd()
        cmd.get_models.side_effect = lambda *names: tuple(getattr(models, name) for name in names)
        kwargs = dict(
            cmd=cmd,
            client=client,
            registry_name=TEST_REGISTRY,
            connected_registry_name=TEST_CR,
            resource_group_name=TEST_RG,
        )
        kwargs.update(overrides)
        p_validate, p_subid = self._patch_common()
        with p_validate, p_subid, \
             mock.patch(UPDATE_MODULE + '.acr_connected_registry_show', return_value=current):
            acr_connected_registry_update(**kwargs)
        return client

    # ---- error paths ------------------------------------------------------

    def test_identity_without_auth_type_errors(self):
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN)
        for identity in (TEST_MSI_ID, '', ' ', '\t', '\n'):
            with self.subTest(identity=identity):
                client = mock.MagicMock()
                with self.assertRaisesRegex(ArgumentUsageError, '--auth-type is required'):
                    self._run_update(cur, client=client, identity=identity)
                client.begin_update.assert_not_called()

    def test_migration_eligibility_errors_are_deferred_to_rp(self):
        for auth_type, state, identity in (
                (AUTH_TYPE_SYNC_TOKEN, 'Online', TEST_MSI_ID),
                (AUTH_TYPE_MANAGED_IDENTITY, 'Offline', TEST_MSI_ID2),
                (AUTH_TYPE_MANAGED_IDENTITY, 'Offline', TEST_MSI_ID)):
            with self.subTest(auth_type=auth_type, state=state, identity=identity):
                cur = _fake_cr(auth_type=auth_type,
                               has_identity=auth_type == AUTH_TYPE_MANAGED_IDENTITY,
                               connection_state=state)
                client = mock.MagicMock()
                error = HttpResponseError(message='The requested migration is not allowed.')
                client.begin_update.side_effect = error
                with self.assertRaises(HttpResponseError) as caught:
                    self._run_update(cur, client=client, auth_type=AUTH_TYPE_MANAGED_IDENTITY, identity=identity)
                self.assertIs(caught.exception, error)
                client.begin_update.assert_called_once()
                client.list.assert_not_called()

    def test_migrate_to_mi_requires_identity(self):
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN)
        for identity in (None, '', ' ', '\t', '\n'):
            with self.subTest(identity=identity):
                client = mock.MagicMock()
                with self.assertRaisesRegex(ArgumentUsageError, 'non-empty --identity'):
                    self._run_update(cur, client=client, auth_type=AUTH_TYPE_MANAGED_IDENTITY, identity=identity)
                client.begin_update.assert_not_called()

    def test_migrate_to_sync_token_rejected(self):
        cur = _fake_cr(has_identity=True, connection_state='Offline')
        with self.assertRaises(ArgumentUsageError) as ctx:
            self._run_update(cur, auth_type=AUTH_TYPE_SYNC_TOKEN)
        self.assertIn('only migration to --auth-type ManagedIdentity is supported',
                      str(ctx.exception))

    # ---- success paths: assert PATCH body shape ---------------------------

    def _extract_update_body(self, client):
        # begin_update(resource_group_name=..., registry_name=...,
        #              connected_registry_name=..., connected_registry_update_parameters=...)
        self.assertTrue(client.begin_update.called)
        _, kwargs = client.begin_update.call_args
        return kwargs['connected_registry_update_parameters']

    def test_migrate_sync_token_to_mi_sends_identity(self):
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN, connection_state='Offline')
        client = self._run_update(cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                                  identity=TEST_MSI_ID)
        body = self._extract_update_body(client)
        self.assertIsNotNone(body.identity)
        self.assertEqual(body.identity.type, MSI_TYPE_USER_ASSIGNED)
        self.assertIn(TEST_MSI_ID, body.identity.user_assigned_identities)
        self.assertEqual(body.sync_properties.auth_type, AUTH_TYPE_MANAGED_IDENTITY)
        serialized = body.as_dict()
        self.assertEqual(serialized['identity'], {
            'type': 'UserAssigned', 'userAssignedIdentities': {TEST_MSI_ID: {}}})
        self.assertEqual(serialized['properties']['syncProperties'], {
            'authType': AUTH_TYPE_MANAGED_IDENTITY})
        self.assertNotIn('parent', serialized['properties'])
        self.assertNotIn('tokenId', serialized['properties']['syncProperties'])

    def test_migration_combines_with_ordinary_property_updates(self):
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN, connection_state='Offline')
        client = self._run_update(
            cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY, identity=TEST_MSI_ID,
            sync_window='PT4H', log_level='Debug', garbage_collection_enabled=False,
            add_client_token_list=['client-token'], add_notifications=['image:latest'])
        serialized = self._extract_update_body(client).as_dict()
        token_id = (
            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/'
            'registries/{}/tokens/client-token'.format(TEST_SUB, TEST_RG, TEST_REGISTRY)
        )
        self.assertEqual(serialized, {
            'identity': {'type': 'UserAssigned', 'userAssignedIdentities': {TEST_MSI_ID: {}}},
            'properties': {
                'syncProperties': {'authType': AUTH_TYPE_MANAGED_IDENTITY, 'syncWindow': 'PT4H'},
                'logging': {'logLevel': 'Debug'},
                'garbageCollection': {'enabled': False},
                'clientTokenIds': [token_id],
                'notificationsList': ['image:latest'],
            },
        })
        client.begin_update.assert_called_once()
        client.list.assert_not_called()

    def test_ordinary_update_preserves_auth_on_either_mode(self):
        token_prefix = (
            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/'
            'registries/{}/tokens/'.format(TEST_SUB, TEST_RG, TEST_REGISTRY)
        )
        for auth_type in (None, AUTH_TYPE_SYNC_TOKEN, AUTH_TYPE_MANAGED_IDENTITY):
            with self.subTest(auth_type=auth_type):
                cur = _fake_cr(auth_type=auth_type,
                               has_identity=auth_type == AUTH_TYPE_MANAGED_IDENTITY,
                               connection_state='Online')
                cur.client_token_ids = [token_prefix + 'old-token']
                cur.notifications_list = ['old:latest']
                client = self._run_update(
                    cur, add_client_token_list=['new-token'], remove_client_token_list=['old-token'],
                    sync_schedule='0 12 * * *', sync_window='PT4H', sync_message_ttl='P2D',
                    log_level='Information', sync_audit_logs_enabled='Enabled',
                    garbage_collection_enabled=False, garbage_collection_schedule='0 0 * * *',
                    add_notifications=['new:latest'], remove_notifications=['old:latest'])
                serialized = self._extract_update_body(client).as_dict()
                self.assertEqual(serialized, {'properties': {
                    'syncProperties': {
                        'schedule': '0 12 * * *', 'syncWindow': 'PT4H', 'messageTtl': 'P2D'},
                    'logging': {'logLevel': 'Information', 'auditLogStatus': 'Enabled'},
                    'garbageCollection': {'enabled': False, 'schedule': '0 0 * * *'},
                    'clientTokenIds': [token_prefix + 'new-token'],
                    'notificationsList': ['new:latest'],
                }})
                self.assertNotIn('identity', serialized)
                self.assertNotIn('authType', serialized['properties']['syncProperties'])
                client.begin_update.assert_called_once()
                client.list.assert_not_called()


# ---------------------------------------------------------------------------
# get-settings: MI-flavored connection string
# ---------------------------------------------------------------------------


class TestConnectedRegistryGetSettingsMI(unittest.TestCase):

    def _invoke(self, cr, **kw):
        with mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                        return_value=(None, TEST_RG)), \
             mock.patch(UPDATE_MODULE + '.acr_connected_registry_show',
                        return_value=cr):
            return acr_connected_registry_get_settings(
                cmd=_make_cmd(), client=mock.MagicMock(),
                connected_registry_name=TEST_CR, registry_name=TEST_REGISTRY,
                parent_protocol='https', resource_group_name=TEST_RG, **kw)

    def test_generate_password_rejected_on_mi(self):
        cr = _fake_cr(has_identity=True)
        with self.assertRaises(ArgumentUsageError):
            self._invoke(cr, generate_password='1', yes=True)

    def test_missing_user_assigned_errors(self):
        cr = _fake_cr(has_identity=True)
        cr.identity.user_assigned_identities = None
        with self.assertRaises(CLIError):
            self._invoke(cr)

    def test_missing_client_id_errors(self):
        cr = _fake_cr(has_identity=True, client_id=None)
        with self.assertRaises(CLIError):
            self._invoke(cr)

    def test_happy_path_returns_mi_connection_string(self):
        cr = _fake_cr(has_identity=True, client_id='cid-happy')
        result = self._invoke(cr)
        self.assertIn('ManagedIdentityClientId=cid-happy',
                      result['ACR_REGISTRY_CONNECTION_STRING'])
        self.assertNotIn('SyncTokenName', result['ACR_REGISTRY_CONNECTION_STRING'])
        self.assertNotIn('SYNC_TOKEN_USER', result)
        self.assertNotIn('SYNC_TOKEN_PASSWORD', result)
        self.assertNotIn('ACR_MANAGED_IDENTITY_CLIENT_ID', result)
        self.assertNotIn('ACR_MANAGED_IDENTITY_RESOURCE_ID', result)

    def test_source_settings_use_get_without_token_or_credential_calls(self):
        cr = _fake_cr(has_identity=True, client_id='cid-happy')
        cr.name = 'name-returned-by-get'
        client = mock.MagicMock()
        client.get.return_value = cr
        with mock.patch(UPDATE_MODULE + '.validate_managed_registry', return_value=(None, TEST_RG)), \
             mock.patch(UPDATE_MODULE + '.get_token_from_id') as token_lookup, \
             mock.patch(UPDATE_MODULE + '.cf_acr_tokens') as token_factory, \
             mock.patch('azure.cli.command_modules.acr._client_factory.cf_acr_token_credentials') as cred_factory, \
             mock.patch('azure.cli.command_modules.acr.token.acr_token_credential_generate') as generate, \
             mock.patch(UPDATE_MODULE + '.user_confirmation') as confirm:
            result = acr_connected_registry_get_settings(
                cmd=_make_cmd(), client=client,
                connected_registry_name=TEST_CR, registry_name=TEST_REGISTRY,
                parent_protocol='http', resource_group_name=TEST_RG)
        client.get.assert_called_once_with(TEST_RG, TEST_REGISTRY, TEST_CR)
        self.assertEqual(client.method_calls, [mock.call.get(TEST_RG, TEST_REGISTRY, TEST_CR)])
        token_lookup.assert_not_called()
        token_factory.assert_not_called()
        cred_factory.assert_not_called()
        generate.assert_not_called()
        confirm.assert_not_called()
        # Preserve the pinned source format (including its request name), not a verified spec contract.
        self.assertEqual(result, {
            'ACR_REGISTRY_CERTIFICATE_VOLUME': '/var/acr/certs',
            'ACR_REGISTRY_DATA_VOLUME': '/var/acr/data',
            'ACR_REGISTRY_CONNECTION_STRING': (
                'ConnectedRegistryName={};ManagedIdentityClientId=cid-happy;'
                'ParentGatewayEndpoint=parent.example.com;ParentEndpointProtocol=https'.format(TEST_CR)),
            'ACR_REGISTRY_LOGIN_SERVER': (
                '<Optional: connected registry login server. '
                'More info at https://aka.ms/acr/connected-registry>'),
        })


class TestConnectedRegistryGetSettingsSyncToken(unittest.TestCase):

    def test_legacy_settings_passwords_endpoints_and_protocols(self):
        token_id = (
            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/'
            'registries/{}/tokens/sync'.format(TEST_SUB, TEST_RG, TEST_REGISTRY))
        parent_id = '/connectedRegistries/parent'
        for auth_type, parent, gateway, protocol, password, expected_protocol in (
                (None, None, 'parent.example.com', 'http', None, 'https'),
                (AUTH_TYPE_SYNC_TOKEN, None, None, 'https', None, 'https'),
                (AUTH_TYPE_SYNC_TOKEN, parent_id, '', 'http', None, 'http'),
                (AUTH_TYPE_SYNC_TOKEN, parent_id, 'parent.example.com', 'https', None, 'https'),
                (AUTH_TYPE_SYNC_TOKEN, None, 'parent.example.com', 'http', '1', 'https'),
                (AUTH_TYPE_SYNC_TOKEN, parent_id, 'parent.example.com', 'http', '2', 'http')):
            with self.subTest(auth_type=auth_type, parent=parent, gateway=gateway,
                              protocol=protocol, password=password):
                cr = _fake_cr(auth_type=auth_type, token_id=token_id, gateway_endpoint=gateway)
                cr.parent.id = parent
                cmd = _make_cmd()
                credentials = mock.MagicMock()
                credentials.username = 'generated-sync'
                credentials.passwords = [
                    mock.Mock(value='test-only-password-1'),
                    mock.Mock(value='test-only-password-2'),
                ]
                credentials.passwords[0].name = 'password1'
                credentials.passwords[1].name = 'password2'
                with mock.patch(UPDATE_MODULE + '.validate_managed_registry', return_value=(None, TEST_RG)), \
                     mock.patch(UPDATE_MODULE + '.acr_connected_registry_show', return_value=cr), \
                     mock.patch(UPDATE_MODULE + '.user_confirmation') as confirm, \
                     mock.patch('azure.cli.command_modules.acr._client_factory.cf_acr_token_credentials') as factory, \
                     mock.patch('azure.cli.command_modules.acr.token.acr_token_credential_generate') as generate, \
                     mock.patch(UPDATE_MODULE + '.LongRunningOperation') as lro:
                    lro.return_value.return_value = credentials
                    result = acr_connected_registry_get_settings(
                        cmd=cmd, client=mock.MagicMock(),
                        connected_registry_name=TEST_CR, registry_name=TEST_REGISTRY,
                        parent_protocol=protocol, generate_password=password, yes=True,
                        resource_group_name=TEST_RG)
                username = credentials.username if password else 'sync'
                expected_password = ('test-only-password-' + password if password else
                                     '<use --generate-password to generate a new password>')
                self.assertEqual(result, {
                    'SYNC_TOKEN_USER': username,
                    'SYNC_TOKEN_PASSWORD': expected_password,
                    'ACR_REGISTRY_CERTIFICATE_VOLUME': '/var/acr/certs',
                    'ACR_REGISTRY_DATA_VOLUME': '/var/acr/data',
                    'ACR_REGISTRY_CONNECTION_STRING': (
                        'ConnectedRegistryName={};SyncTokenName={};SyncTokenPassword={};'
                        'ParentGatewayEndpoint={};ParentEndpointProtocol={}'.format(
                            TEST_CR, username, expected_password,
                            gateway or '<parent gateway endpoint>', expected_protocol)),
                    'ACR_REGISTRY_LOGIN_SERVER': (
                        '<Optional: connected registry login server. '
                        'More info at https://aka.ms/acr/connected-registry>'),
                })
                if password:
                    confirm.assert_called_once_with(
                        "Are you sure you want to generate a new sync token 'sync' password{}?".format(password), True)
                    factory.assert_called_once_with(cmd.cli_ctx)
                    generate.assert_called_once_with(
                        cmd, factory.return_value, TEST_REGISTRY, 'sync',
                        password1=password == '1', password2=password == '2', resource_group_name=TEST_RG)
                    lro.assert_called_once_with(cmd.cli_ctx)
                    lro.return_value.assert_called_once_with(generate.return_value)
                else:
                    confirm.assert_not_called()
                    factory.assert_not_called()
                    generate.assert_not_called()
                    lro.assert_not_called()


if __name__ == '__main__':
    unittest.main()
