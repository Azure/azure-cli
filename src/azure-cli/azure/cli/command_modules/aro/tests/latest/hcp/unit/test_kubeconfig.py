# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import base64
import errno
import io
import os
import stat
import tempfile
import unittest
from unittest import mock

import yaml
from azure.cli.core.azclierror import FileOperationError
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from knack.util import CLIError

from azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig import (
    _embed_private_key,
    _generate_admin_credential_request,
    _handle_merge,
    load_kubernetes_configuration,
    merge_kubernetes_configurations,
    print_or_merge_credentials,
)


def _config(name="admin", server="https://api.example.invalid"):
    return {
        "apiVersion": "v1",
        "clusters": [{"name": name, "cluster": {"server": server}}],
        "contexts": [{"name": name, "context": {"cluster": name, "user": "admin"}}],
        "current-context": name,
        "kind": "Config",
        "users": [{"name": "admin", "user": {"client-certificate-data": "certificate"}}],
    }


class CredentialHelperTest(unittest.TestCase):

    def test_generate_admin_credential_request(self):
        private_key_pem, csr_pem = _generate_admin_credential_request()

        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        csr = x509.load_pem_x509_csr(csr_pem.encode("ascii"))

        self.assertEqual(4096, private_key.key_size)
        self.assertEqual(
            [
                (x509.NameOID.COMMON_NAME, "system:customer-break-glass:system-admin"),
                (x509.NameOID.ORGANIZATION_NAME, "system:masters"),
            ],
            [(attribute.oid, attribute.value) for attribute in csr.subject],
        )
        self.assertTrue(csr.is_signature_valid)
        self.assertEqual(csr.public_key().public_numbers(), private_key.public_key().public_numbers())

    def test_embed_private_key_in_admin_user(self):
        private_key_pem, _ = _generate_admin_credential_request()
        kubeconfig = yaml.safe_dump({
            "apiVersion": "v1",
            "current-context": "other-context",
            "contexts": [
                {"name": "other-context", "context": {"cluster": "other", "user": "other"}},
                {"name": "admin-context", "context": {"cluster": "cluster", "user": "admin"}},
            ],
            "clusters": [{"name": "cluster", "cluster": {"server": "https://example.invalid"}}],
            "users": [
                {"name": "other", "user": {"client-key-data": "unchanged"}},
                {"name": "admin", "user": {"client-certificate-data": "certificate", "client-key": "admin.key"}},
            ],
        })

        config = yaml.safe_load(_embed_private_key(kubeconfig, private_key_pem))

        self.assertEqual("unchanged", config["users"][0]["user"]["client-key-data"])
        admin_credentials = config["users"][1]["user"]
        self.assertNotIn("client-key", admin_credentials)
        self.assertEqual(private_key_pem, base64.b64decode(admin_credentials["client-key-data"]))


class LoadKubernetesConfigurationTest(unittest.TestCase):

    def test_loads_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as stream:
            yaml.safe_dump(_config(), stream)
            stream.flush()
            self.assertEqual(_config(), load_kubernetes_configuration(stream.name))

    def test_missing_file_raises_cli_error(self):
        with self.assertRaisesRegex(CLIError, "does not exist"):
            load_kubernetes_configuration("/path/that/does/not/exist")

    @mock.patch(
        "azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig.open",
        side_effect=PermissionError(errno.EACCES, "Permission denied"),
    )
    def test_permission_error_is_actionable(self, _):
        with self.assertRaisesRegex(FileOperationError, "Permission denied"):
            load_kubernetes_configuration("config")


class HandleMergeTest(unittest.TestCase):

    def test_adds_new_entry(self):
        existing = {"clusters": [{"name": "one"}]}
        _handle_merge(existing, {"clusters": [{"name": "two"}]}, "clusters", replace=False)
        self.assertEqual([{"name": "one"}, {"name": "two"}], existing["clusters"])

    def test_replaces_duplicate_when_requested(self):
        existing = {"clusters": [{"name": "one", "value": "old"}]}
        addition = {"clusters": [{"name": "one", "value": "new"}]}
        _handle_merge(existing, addition, "clusters", replace=True)
        self.assertEqual(addition["clusters"], existing["clusters"])

    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig.prompt_y_n", return_value=False)
    def test_rejects_conflicting_entry(self, _):
        existing = {"users": [{"name": "admin", "user": {"token": "old"}}]}
        addition = {"users": [{"name": "admin", "user": {"token": "new"}}]}
        with self.assertRaisesRegex(CLIError, "already exists"):
            _handle_merge(existing, addition, "users", replace=False)

    def test_missing_existing_section_raises_file_error(self):
        with self.assertRaisesRegex(FileOperationError, "No such key 'clusters'"):
            _handle_merge({}, {"clusters": [{"name": "one"}]}, "clusters", replace=False)


class MergeKubernetesConfigurationsTest(unittest.TestCase):

    def test_merges_and_renames_context_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            existing_path = os.path.join(directory, "config")
            addition_path = os.path.join(directory, "addition")
            with open(existing_path, "w", encoding="utf-8") as stream:
                yaml.safe_dump(_config("existing"), stream)
            with open(addition_path, "w", encoding="utf-8") as stream:
                yaml.safe_dump(_config("new"), stream)
            os.chmod(existing_path, 0o600)

            merge_kubernetes_configurations(
                existing_path, addition_path, replace=True, context_name="renamed"
            )

            merged = load_kubernetes_configuration(existing_path)
            self.assertEqual("renamed", merged["current-context"])
            self.assertIn("renamed", [item["name"] for item in merged["clusters"]])
            self.assertIn("renamed", [item["name"] for item in merged["contexts"]])
            self.assertEqual(0o600, stat.S_IMODE(os.stat(existing_path).st_mode))

    def test_refuses_to_replace_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            target_path = os.path.join(directory, "target")
            link_path = os.path.join(directory, "config")
            addition_path = os.path.join(directory, "addition")
            for path in (target_path, addition_path):
                with open(path, "w", encoding="utf-8") as stream:
                    yaml.safe_dump(_config(), stream)
            os.symlink(target_path, link_path)

            with self.assertRaisesRegex(CLIError, "symbolic link"):
                merge_kubernetes_configurations(link_path, addition_path, replace=True)


class PrintOrMergeCredentialsTest(unittest.TestCase):

    def test_dash_prints_kubeconfig(self):
        kubeconfig = yaml.safe_dump(_config())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_or_merge_credentials("-", kubeconfig, False, None)
        self.assertEqual(kubeconfig + "\n", output.getvalue())

    def test_creates_parent_and_secure_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, ".kube", "config")
            print_or_merge_credentials(path, yaml.safe_dump(_config()), False, None)

            self.assertEqual(_config(), load_kubernetes_configuration(path))
            self.assertEqual(0o600, stat.S_IMODE(os.stat(path).st_mode))


if __name__ == "__main__":
    unittest.main()