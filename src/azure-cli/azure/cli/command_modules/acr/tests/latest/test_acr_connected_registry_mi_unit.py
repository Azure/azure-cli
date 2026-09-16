# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit tests for managed-identity connected registry creation and permissions."""

import unittest
from unittest import mock

from azure.cli.core.azclierror import ArgumentUsageError

from azure.mgmt.containerregistry.models import ManagedServiceIdentityType

from azure.cli.command_modules.acr._constants import ConnectedRegistryAuthType

from azure.cli.command_modules.acr.connected_registry import (
    _get_current_auth_type,
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
