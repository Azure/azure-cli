# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from azure.cli.command_modules.storage.azcopy import util


class TestAzCopyExecutableResolution(unittest.TestCase):

    def setUp(self):
        platform_patcher = mock.patch.object(util.platform, "system", return_value="Windows")
        platform_patcher.start()
        self.addCleanup(platform_patcher.stop)

    def _make_directory_link(self, target, link):
        if sys.platform == "win32":
            subprocess.run(["cmd", "/c", "mklink", "/J", link, target], check=True, capture_output=True)
        else:
            os.symlink(target, link)

    def test_cwd_executable_is_not_probed_or_reused(self):
        with tempfile.TemporaryDirectory() as cwd:
            managed_executable = os.path.realpath(os.path.join(cwd, "managed", "azcopy.exe"))
            cwd_executable = os.path.join(cwd, "azcopy.exe")

            with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                    mock.patch.object(util.os, "getcwd", return_value=cwd), \
                    mock.patch.object(util.shutil, "which", return_value=cwd_executable), \
                    mock.patch.object(util.subprocess, "check_output") as check_output, \
                    mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                azcopy = util.AzCopy()

        check_output.assert_not_called()
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_relative_path_executable_is_not_probed_or_reused(self):
        managed_executable = os.path.abspath(os.path.join("managed", "azcopy.exe"))
        relative_executable = os.path.join("bin", "azcopy.exe")

        with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                mock.patch.object(util.shutil, "which", return_value=relative_executable), \
                mock.patch.object(util.subprocess, "check_output") as check_output, \
                mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
            azcopy = util.AzCopy()

        check_output.assert_not_called()
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_windows_lookup_uses_exe_name(self):
        managed_executable = os.path.abspath(os.path.join("managed", "azcopy.exe"))

        with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                mock.patch.object(util.shutil, "which", return_value=None) as which, \
                mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
            azcopy = util.AzCopy()

        which.assert_called_once_with("azcopy.exe")
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_windows_lookup_rejects_script_result(self):
        managed_executable = os.path.abspath(os.path.join("managed", "azcopy.exe"))
        script_executable = os.path.abspath(os.path.join("system", "azcopy.exe.cmd"))

        with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                mock.patch.object(util.shutil, "which", return_value=script_executable), \
                mock.patch.object(util.subprocess, "check_output") as check_output, \
                mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
            azcopy = util.AzCopy()

        check_output.assert_not_called()
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_non_windows_lookup_uses_bare_name(self):
        managed_executable = os.path.abspath(os.path.join("managed", "azcopy"))

        with mock.patch.object(util.platform, "system", return_value="Linux"), \
                mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                mock.patch.object(util.shutil, "which", return_value=None) as which, \
                mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
            azcopy = util.AzCopy()

        which.assert_called_once_with("azcopy")
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_system_executable_is_probed_and_reused_by_absolute_path(self):
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as system_dir:
            managed_executable = os.path.join(cwd, "managed", "azcopy.exe")
            system_executable = os.path.join(system_dir, "azcopy.exe")

            with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                    mock.patch.object(util.os, "getcwd", return_value=cwd), \
                    mock.patch.object(util.shutil, "which", return_value=system_executable), \
                    mock.patch.object(util.subprocess, "check_output",
                                      return_value=b"azcopy version 10.13.0\n") as check_output, \
                    mock.patch.object(util.subprocess, "call", return_value=0) as call, \
                    mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                azcopy = util.AzCopy()
                azcopy.copy("source", "destination")

        check_output.assert_called_once_with([os.path.abspath(system_executable), "--version"])
        call.assert_called_once_with(
            [os.path.abspath(system_executable), "copy", "source", "destination"],
            env=mock.ANY)
        install_azcopy.assert_not_called()
        self.assertEqual(os.path.abspath(system_executable), azcopy.executable)

    def test_relative_managed_executable_is_normalized_for_probe_and_operation(self):
        relative_executable = os.path.join("managed", "azcopy.exe")
        absolute_executable = os.path.abspath(relative_executable)

        with mock.patch.object(util, "_get_default_install_location", return_value=relative_executable), \
                mock.patch.object(util.os.path, "isfile", return_value=True), \
                mock.patch.object(util.subprocess, "check_output",
                                  return_value=b"azcopy version 10.13.0\n") as check_output, \
                mock.patch.object(util.subprocess, "call", return_value=0) as call:
            azcopy = util.AzCopy()
            azcopy.sync("source", "destination")

        check_output.assert_called_once_with([absolute_executable, "--version"])
        call.assert_called_once_with(
            [absolute_executable, "sync", "source", "destination"],
            env=mock.ANY)
        self.assertEqual(absolute_executable, azcopy.executable)

    @unittest.skipIf(sys.platform == "win32", "POSIX symlink resolution semantics")
    def test_managed_path_resolves_symlink_before_parent_component(self):
        with tempfile.TemporaryDirectory() as root:
            config_dir = os.path.join(root, "config")
            profile_dir = os.path.join(root, "data", "profile")
            os.makedirs(config_dir)
            os.makedirs(profile_dir)
            self._make_directory_link(profile_dir, os.path.join(config_dir, "link"))

            configured_executable = os.path.join(config_dir, "link", "..", "bin", "azcopy.exe")
            expected_executable = os.path.join(os.path.realpath(root), "data", "bin", "azcopy.exe")

            with mock.patch.object(util, "_get_default_install_location", return_value=configured_executable), \
                    mock.patch.object(util.shutil, "which", return_value=None), \
                    mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                azcopy = util.AzCopy()

        install_azcopy.assert_called_once_with(expected_executable)
        self.assertEqual(expected_executable, azcopy.executable)

    def test_system_path_preserves_symlink_and_parent_component(self):
        with tempfile.TemporaryDirectory() as root:
            config_dir = os.path.join(root, "config")
            profile_dir = os.path.join(root, "data", "profile")
            system_dir = os.path.join(root, "data", "bin")
            cwd = os.path.join(root, "work")
            os.makedirs(config_dir)
            os.makedirs(profile_dir)
            os.makedirs(system_dir)
            os.makedirs(cwd)
            self._make_directory_link(profile_dir, os.path.join(config_dir, "link"))

            managed_executable = os.path.join(root, "managed", "azcopy.exe")
            discovered_executable = os.path.join(config_dir, "link", "..", "bin", "azcopy.exe")

            with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                    mock.patch.object(util.os, "getcwd", return_value=cwd), \
                    mock.patch.object(util.shutil, "which", return_value=discovered_executable), \
                    mock.patch.object(util.subprocess, "check_output",
                                      return_value=b"azcopy version 10.13.0\n") as check_output, \
                    mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                azcopy = util.AzCopy()

        check_output.assert_called_once_with([discovered_executable, "--version"])
        install_azcopy.assert_not_called()
        self.assertEqual(discovered_executable, azcopy.executable)

    def test_system_path_resolving_to_cwd_is_not_probed_or_reused(self):
        with tempfile.TemporaryDirectory() as root:
            cwd = os.path.join(root, "work")
            os.makedirs(cwd)
            cwd_link = os.path.join(root, "work-link")
            self._make_directory_link(cwd, cwd_link)

            managed_executable = os.path.realpath(os.path.join(root, "managed", "azcopy.exe"))
            discovered_executable = os.path.join(cwd_link, "azcopy.exe")

            with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                    mock.patch.object(util.os, "getcwd", return_value=cwd), \
                    mock.patch.object(util.shutil, "which", return_value=discovered_executable), \
                    mock.patch.object(util.subprocess, "check_output") as check_output, \
                    mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                azcopy = util.AzCopy()

        check_output.assert_not_called()
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_system_probe_failure_falls_back_to_managed_executable(self):
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as system_dir:
            managed_executable = os.path.realpath(os.path.join(cwd, "managed", "azcopy.exe"))
            system_executable = os.path.join(system_dir, "azcopy.exe")

            with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                    mock.patch.object(util.os, "getcwd", return_value=cwd), \
                    mock.patch.object(util.shutil, "which", return_value=system_executable), \
                    mock.patch.object(util.subprocess, "check_output", side_effect=OSError), \
                    mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                azcopy = util.AzCopy()

        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)

    def test_unusable_system_version_falls_back_to_managed_executable(self):
        unusable_outputs = (
            b"\xff",
            b"unexpected output\n",
            b"azcopy version not-a-version\n",
        )

        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as system_dir:
            managed_executable = os.path.realpath(os.path.join(cwd, "managed", "azcopy.exe"))
            system_executable = os.path.join(system_dir, "azcopy.exe")

            for output in unusable_outputs:
                with self.subTest(output=output), \
                        mock.patch.object(util, "_get_default_install_location",
                                          return_value=managed_executable), \
                        mock.patch.object(util.os, "getcwd", return_value=cwd), \
                        mock.patch.object(util.shutil, "which", return_value=system_executable), \
                        mock.patch.object(util.subprocess, "check_output", return_value=output), \
                        mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
                    azcopy = util.AzCopy()

                install_azcopy.assert_called_once_with(managed_executable)
                self.assertEqual(managed_executable, azcopy.executable)

    def test_path_validation_failure_falls_back_without_probing(self):
        managed_executable = os.path.abspath(os.path.join("managed", "azcopy.exe"))
        system_executable = os.path.abspath(os.path.join("system", "azcopy.exe"))

        with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                mock.patch.object(util.os.path, "realpath", return_value=managed_executable), \
                mock.patch.object(util.shutil, "which", return_value=system_executable), \
                mock.patch.object(util.os, "getcwd", side_effect=OSError) as getcwd, \
                mock.patch.object(util.subprocess, "check_output") as check_output, \
                mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
            azcopy = util.AzCopy()

        getcwd.assert_called_once_with()
        check_output.assert_not_called()
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)


class TestClientAuthForAzcopy(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.Mock()

    def _assert_not_oauth(self, client):
        with mock.patch.object(util, "Profile") as profile_mock:
            result = util.client_auth_for_azcopy(self.cmd, client)
        profile_mock.assert_not_called()
        self.assertIsNone(result)

    def test_account_key_dict_credential_skips_oauth(self):
        client = mock.Mock(credential={"account_key": "fake_key"}, url="https://foo.blob.core.windows.net/c")
        self._assert_not_oauth(client)

    def test_account_key_object_credential_skips_oauth(self):
        credential = mock.Mock(spec=["account_key"], account_key="fake_key")
        client = mock.Mock(credential=credential, url="https://foo.blob.core.windows.net/c")
        self._assert_not_oauth(client)

    def test_sas_token_credential_string_skips_oauth(self):
        client = mock.Mock(credential="sv=2021-01-01&sig=abc", url="https://foo.blob.core.windows.net/c")
        self._assert_not_oauth(client)

    def test_sas_token_embedded_in_url_skips_oauth(self):
        # Reproduces #32284: azure-storage-blob SDK sets credential to None and appends the
        # SAS token to the client URL's query string instead of keeping it as client.credential.
        client = mock.Mock(
            credential=None,
            url="https://foo.blob.core.windows.net/c?sv=2021-01-01&sig=abc&se=2024-01-01")
        self._assert_not_oauth(client)

    def test_no_credential_and_no_sas_uses_oauth(self):
        client = mock.Mock(credential=None, url="https://foo.blob.core.windows.net/c")
        with mock.patch.object(util, "Profile") as profile_mock:
            profile_instance = profile_mock.return_value
            profile_instance.get_raw_token.return_value = (
                ("bearer", "token", {"_authority": "https://login.microsoftonline.com/tenant",
                                     "accessToken": "token",
                                     "userId": "user"}),
                None,
                "tenant-id",
            )
            with mock.patch.object(util, "_unserialize_non_msi_token_payload",
                                   return_value={"access_token": "token"}):
                result = util.client_auth_for_azcopy(self.cmd, client)
        profile_instance.get_raw_token.assert_called_once()
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
