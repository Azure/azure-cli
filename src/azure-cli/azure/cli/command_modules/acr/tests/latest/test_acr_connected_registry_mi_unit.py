# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit tests for the managed-identity code paths in
``azure.cli.command_modules.acr.connected_registry``.

These tests deliberately import SDK models so a future flat-namespace reshape breaks the
import surface loudly (the recorded scenario in test_acr_connectedregistry_commands.py
stays SDK-shape-proof).
"""

import enum
import unittest
from unittest import mock

from azure.cli.core.azclierror import ArgumentUsageError
from knack.util import CLIError

from azure.mgmt.containerregistry.models import (
    ConnectionState,
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
    CONNECTION_STATE_OFFLINE,
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

    def test_connection_state_constant(self):
        self.assertEqual(CONNECTION_STATE_OFFLINE, ConnectionState.OFFLINE.value)


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
        identity = _build_user_assigned_identity(TEST_MSI_ID)
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


# ---------------------------------------------------------------------------
# update: migration state machine (client-side validation + PATCH shape)
# ---------------------------------------------------------------------------


UPDATE_MODULE = 'azure.cli.command_modules.acr.connected_registry'


class TestConnectedRegistryUpdateMigration(unittest.TestCase):

    def _patch_common(self):
        p_validate = mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                                return_value=(None, TEST_RG))
        p_subid = mock.patch(UPDATE_MODULE + '.get_subscription_id',
                             return_value=TEST_SUB)
        return p_validate, p_subid

    def _run_update(self, current, **overrides):
        client = mock.MagicMock()
        kwargs = dict(
            cmd=_make_cmd(),
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
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN,
                       connection_state=CONNECTION_STATE_OFFLINE)
        with self.assertRaises(ArgumentUsageError):
            self._run_update(cur, identity=TEST_MSI_ID)

    def test_same_mode_rotation_rejected(self):
        cur = _fake_cr(has_identity=True, connection_state=CONNECTION_STATE_OFFLINE)
        with self.assertRaises(ArgumentUsageError) as ctx:
            self._run_update(cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                             identity=TEST_MSI_ID2)
        self.assertIn('already using', str(ctx.exception))

    def test_not_offline_rejected(self):
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN, connection_state='Online')
        with self.assertRaises(ArgumentUsageError) as ctx:
            self._run_update(cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                             identity=TEST_MSI_ID)
        self.assertIn('Offline', str(ctx.exception))

    def test_migrate_to_mi_requires_identity(self):
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN,
                       connection_state=CONNECTION_STATE_OFFLINE)
        with self.assertRaises(ArgumentUsageError):
            self._run_update(cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY)

    def test_migrate_to_sync_token_rejected(self):
        cur = _fake_cr(has_identity=True, connection_state=CONNECTION_STATE_OFFLINE)
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
        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN,
                       connection_state=CONNECTION_STATE_OFFLINE)
        client = self._run_update(cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                                  identity=TEST_MSI_ID)
        body = self._extract_update_body(client)
        self.assertIsNotNone(body.identity)
        self.assertEqual(body.identity.type, MSI_TYPE_USER_ASSIGNED)
        self.assertIn(TEST_MSI_ID, body.identity.user_assigned_identities)
        self.assertEqual(body.sync_properties.auth_type, AUTH_TYPE_MANAGED_IDENTITY)
        self.assertIsNone(body.sync_properties.token_id)

    def test_plain_enum_valued_connection_state_offline_is_accepted(self):
        # Simulate a future SDK regen where ConnectionState is a plain Enum (not str-mixed);
        # equality with the raw string would fail without .value coercion.
        class _PlainConnectionState(enum.Enum):
            OFFLINE = 'Offline'

        cur = _fake_cr(auth_type=AUTH_TYPE_SYNC_TOKEN,
                       connection_state=_PlainConnectionState.OFFLINE)
        client = self._run_update(cur, auth_type=AUTH_TYPE_MANAGED_IDENTITY,
                                  identity=TEST_MSI_ID)
        self.assertTrue(client.begin_update.called)


# ---------------------------------------------------------------------------
# delete: MI-mode skips sync-token / scope-map cleanup
# ---------------------------------------------------------------------------


class TestConnectedRegistryDeleteMI(unittest.TestCase):

    def _invoke(self, cleanup):
        client = mock.MagicMock()
        client.begin_delete.return_value.result.return_value = None
        cr = _fake_cr(has_identity=True)
        cr.parent.id = None

        with mock.patch(UPDATE_MODULE + '.validate_managed_registry',
                        return_value=(None, TEST_RG)), \
             mock.patch(UPDATE_MODULE + '.acr_connected_registry_show',
                        return_value=cr), \
             mock.patch(UPDATE_MODULE + '.get_token_from_id') as p_get_tok, \
             mock.patch(UPDATE_MODULE + '.cf_acr_tokens') as p_tok_client, \
             mock.patch(UPDATE_MODULE + '.cf_acr_scope_maps') as p_sm_client, \
             mock.patch(UPDATE_MODULE + '._update_ancestor_permissions') as p_anc:
            acr_connected_registry_delete(
                cmd=_make_cmd(), client=client,
                connected_registry_name=TEST_CR, registry_name=TEST_REGISTRY,
                cleanup=cleanup, yes=True, resource_group_name=TEST_RG)

        return client, p_get_tok, p_tok_client, p_sm_client, p_anc

    def test_mi_mode_skips_token_and_scope_map_cleanup(self):
        # MI-mode must not resolve the sync token, instantiate token/scope-map
        # clients, walk ancestors, or list siblings for cleanup.
        client, p_get_tok, p_tok_client, p_sm_client, p_anc = self._invoke(cleanup=True)
        p_get_tok.assert_not_called()
        p_tok_client.assert_not_called()
        p_sm_client.assert_not_called()
        p_anc.assert_not_called()
        client.list.assert_not_called()

    def test_mi_mode_delete_without_cleanup_is_noop_beyond_begin_delete(self):
        client, p_get_tok, p_tok_client, p_sm_client, p_anc = self._invoke(cleanup=False)
        p_get_tok.assert_not_called()
        p_tok_client.assert_not_called()
        p_sm_client.assert_not_called()
        p_anc.assert_not_called()
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


if __name__ == '__main__':
    unittest.main()
