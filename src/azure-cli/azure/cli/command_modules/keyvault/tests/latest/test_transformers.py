# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.keyvault.keys import JsonWebKey, KeyProperties, KeyVaultKey
from azure.keyvault.keys._models import DeletedKey

from azure.cli.command_modules.keyvault._transformers import (
    transform_key_list_output,
    transform_key_output,
)


class _Attrs:
    def __init__(self, key_size=None):
        self.enabled = True
        self.not_before = None
        self.expires = None
        self.created = None
        self.updated = None
        self.recovery_level = "Recoverable"
        self.recoverable_days = 7
        self.exportable = False
        self.hsm_platform = None
        self.key_size = key_size


def _kid(name):
    return "https://example.vault.azure.net/keys/{}/abc".format(name)


def _make_key_properties(name, key_size=None):
    return KeyProperties(key_id=_kid(name), attributes=_Attrs(key_size=key_size))


def _make_key(name, key_size=None, kty="oct"):
    key = KeyVaultKey.__new__(KeyVaultKey)
    key._properties = _make_key_properties(name, key_size=key_size)
    key._key_material = JsonWebKey(kty=kty, key_ops=["encrypt", "decrypt"])
    return key


def _make_deleted_key(name, key_size=None, kty="oct"):
    # DeletedKey.__init__ forwards to KeyVaultKey.__init__, which still
    # requires the positional key_id arg; bypass with __new__.
    deleted = DeletedKey.__new__(DeletedKey)
    deleted._properties = _make_key_properties(name, key_size=key_size)
    deleted._key_material = JsonWebKey(kty=kty)
    deleted._deleted_date = None
    deleted._recovery_id = "https://example.vault.azure.net/deletedkeys/{}".format(name)
    deleted._scheduled_purge_date = None
    return deleted


class KeyVaultTransformersTests(unittest.TestCase):

    def test_show_aes_key_surfaces_key_size(self):
        out = transform_key_output(_make_key("aes-256", key_size=256, kty="oct"))

        self.assertEqual(out["attributes"]["keySize"], 256)

    def test_show_aes_hsm_key_surfaces_key_size(self):
        out = transform_key_output(_make_key("aes-128", key_size=128, kty="oct-HSM"))

        self.assertEqual(out["attributes"]["keySize"], 128)

    def test_show_rsa_key_returns_none_key_size(self):
        out = transform_key_output(_make_key("rsa", key_size=None, kty="RSA"))

        self.assertIn("keySize", out["attributes"])
        self.assertIsNone(out["attributes"]["keySize"])

    def test_show_deleted_key_includes_key_size_and_deletion_fields(self):
        out = transform_key_output(_make_deleted_key("deleted-aes", key_size=256))

        self.assertEqual(out["attributes"]["keySize"], 256)
        self.assertIn("deletedDate", out)
        self.assertIn("scheduledPurgeDate", out)
        self.assertTrue(out["recoveryId"].endswith("/deletedkeys/deleted-aes"))

    def test_show_passes_through_unknown_types(self):
        sentinel = {"already": "transformed"}

        self.assertIs(transform_key_output(sentinel), sentinel)

    def test_list_surfaces_key_size_per_item(self):
        items = [
            _make_key_properties("aes-256", key_size=256),
            _make_key_properties("aes-128", key_size=128),
            _make_key_properties("rsa", key_size=None),
        ]

        out = transform_key_list_output(items)

        self.assertEqual([k["keySize"] for k in out], [256, 128, None])
        self.assertEqual([k["name"] for k in out], ["aes-256", "aes-128", "rsa"])

    def test_list_surfaces_key_size_for_deleted_entries(self):
        items = [
            _make_deleted_key("deleted-aes", key_size=256),
            _make_key_properties("live-aes", key_size=128),
        ]

        out = transform_key_list_output(items)

        self.assertEqual(out[0]["keySize"], 256)
        self.assertIn("deletedDate", out[0])
        self.assertIn("scheduledPurgeDate", out[0])
        self.assertEqual(out[1]["keySize"], 128)
        self.assertNotIn("deletedDate", out[1])

    def test_list_empty_returns_input(self):
        self.assertEqual(transform_key_list_output([]), [])
        self.assertIsNone(transform_key_list_output(None))

    def test_list_passes_through_non_key_properties(self):
        original = [{"not": "a key"}]

        self.assertIs(transform_key_list_output(original), original)


if __name__ == "__main__":
    unittest.main()
