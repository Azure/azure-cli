# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit tests for managed-identity connected registry creation and permissions."""

import unittest
from unittest import mock

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
    acr_connected_registry_permissions_show,
    acr_connected_registry_permissions_update,
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
