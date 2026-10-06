# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest import mock

from azure.cli.command_modules.storage.azcopy import util


class TestAzCopyExecutableResolution(unittest.TestCase):

    def test_cwd_executable_is_not_probed_or_reused(self):
        with tempfile.TemporaryDirectory() as cwd:
            managed_executable = os.path.join(cwd, "managed", "azcopy.exe")
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

    def test_system_probe_failure_falls_back_to_managed_executable(self):
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as system_dir:
            managed_executable = os.path.join(cwd, "managed", "azcopy.exe")
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
            managed_executable = os.path.join(cwd, "managed", "azcopy.exe")
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

        with mock.patch.object(util, "_get_default_install_location", return_value=managed_executable), \
                mock.patch.object(util.shutil, "which", return_value="azcopy.exe"), \
                mock.patch.object(util.os, "getcwd", side_effect=OSError), \
                mock.patch.object(util.subprocess, "check_output") as check_output, \
                mock.patch.object(util.AzCopy, "install_azcopy") as install_azcopy:
            azcopy = util.AzCopy()

        check_output.assert_not_called()
        install_azcopy.assert_called_once_with(managed_executable)
        self.assertEqual(managed_executable, azcopy.executable)


if __name__ == "__main__":
    unittest.main()
