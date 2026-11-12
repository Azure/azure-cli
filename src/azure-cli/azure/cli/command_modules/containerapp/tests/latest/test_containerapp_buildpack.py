# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import os
import tarfile
import unittest
import zipfile
from unittest.mock import MagicMock, Mock, mock_open, patch

from azure.cli.command_modules.containerapp import _utils
from azure.cli.command_modules.containerapp._up_utils import ContainerApp
from azure.cli.core.azclierror import CLIError, ValidationError


class ContainerAppBuildpackTests(unittest.TestCase):
    def test_pack_versioned_cache(self):
        for platform, executable in (("Linux", "pack"), ("Darwin", "pack"), ("Windows", "pack.exe")):
            with self.subTest(platform=platform):
                with patch.object(_utils.platform, "system", return_value=platform), \
                        patch.object(_utils.os.path, "exists", return_value=True), \
                        patch.object(_utils, "urlopen") as download:
                    path = _utils.get_pack_exec_path()

                self.assertEqual(os.path.basename(path), executable)
                self.assertEqual(os.path.basename(os.path.dirname(path)), "v0.40.10")
                download.assert_not_called()

    def test_pack_download(self):
        for platform, suffix, executable in (
                ("Linux", "linux.tgz", "pack"),
                ("Darwin", "macos.tgz", "pack"),
                ("Windows", "windows.zip", "pack.exe")):
            with self.subTest(platform=platform):
                archive = io.BytesIO()
                if platform == "Windows":
                    with zipfile.ZipFile(archive, "w") as compressed:
                        compressed.writestr(executable, b"pack executable")
                else:
                    with tarfile.open(fileobj=archive, mode="w:gz") as compressed:
                        entry = tarfile.TarInfo(executable)
                        entry.size = len(b"pack executable")
                        compressed.addfile(entry, io.BytesIO(b"pack executable"))
                archive.seek(0)
                output = mock_open()
                with patch.object(_utils.platform, "system", return_value=platform), \
                        patch.object(_utils.os.path, "exists", return_value=False), \
                        patch.object(_utils.os, "makedirs") as mkdir, \
                        patch.object(_utils.os, "access", return_value=True), \
                        patch.object(_utils, "urlopen", return_value=archive) as download, \
                        patch("builtins.open", output):
                    path = _utils.get_pack_exec_path()

                self.assertIsNotNone(path)
                self.assertEqual(os.path.basename(os.path.dirname(path)), "v0.40.10")
                mkdir.assert_called_once_with(os.path.dirname(path))
                download.assert_called_once_with(
                    f"https://github.com/buildpacks/pack/releases/download/v0.40.10/pack-v0.40.10-{suffix}")
                output.assert_called_once_with(path, "wb")
                output().write.assert_called_once_with(b"pack executable")

    @patch("azure.cli.command_modules.containerapp._up_utils.is_docker_running", return_value=True)
    @patch("azure.cli.command_modules.containerapp._up_utils.get_pack_exec_path", return_value="pack")
    @patch("azure.cli.command_modules.containerapp._up_utils.get_latest_buildpack_run_tag")
    @patch("azure.cli.command_modules.containerapp._up_utils.subprocess.Popen")
    def test_buildpack_command(self, popen, run_tag, pack_path, docker):
        for tag in (None, "run-dotnet-aspnet-7.0.9-cbl-mariner2.0"):
            for port in (None, 8080):
                with self.subTest(tag=tag, port=port):
                    popen.reset_mock()
                    run_tag.return_value = tag
                    process = popen.return_value.__enter__.return_value
                    process.returncode = 0
                    process.communicate.return_value = (b"", b"")
                    process.stdout.readline.return_value = b""
                    app = Mock(spec=ContainerApp)
                    app.registry_server = "registry.azurecr.io"
                    app.target_port = port

                    ContainerApp.build_container_from_source_with_buildpack(app, "app:tag", "source")

                    expected = [
                        "pack", "build", "registry.azurecr.io/app:tag",
                        "--builder", "mcr.microsoft.com/oryx/builder:builder-dotnet-7.0",
                        "--path", "source", "--lifecycle-image", "buildpacksio/lifecycle:0.21.28",
                    ]
                    if tag:
                        expected.extend(["--run-image", f"mcr.microsoft.com/oryx/builder:{tag}"])
                    if port:
                        expected.extend(["--env", f"PORT={port}"])
                    self.assertEqual(popen.call_count, 2)
                    self.assertEqual(popen.call_args_list[1].args[0], expected)
                    self.assertEqual(popen.call_args_list[0].args[0], [
                        "pack", "config", "default-builder", "mcr.microsoft.com/oryx/builder:builder-dotnet-7.0"])
                    app._docker_push_to_container_registry.assert_called_once_with(
                        "registry.azurecr.io/app:tag", False)

    @patch("azure.cli.command_modules.containerapp._up_utils.is_docker_running", return_value=True)
    @patch("azure.cli.command_modules.containerapp._up_utils.get_pack_exec_path", return_value="pack")
    @patch("azure.cli.command_modules.containerapp._up_utils.get_latest_buildpack_run_tag", return_value=None)
    @patch("azure.cli.command_modules.containerapp._up_utils.subprocess.Popen")
    def test_buildpack_failure_does_not_push(self, popen, run_tag, pack_path, docker):
        config = MagicMock()
        config.communicate.return_value = (b"", b"")
        config.returncode = 0
        build = MagicMock()
        build.communicate.return_value = (b"", b"")
        build.returncode = 1
        build.stdout.readline.return_value = b""
        popen.side_effect = [
            MagicMock(__enter__=Mock(return_value=config)),
            MagicMock(__enter__=Mock(return_value=build)),
        ]
        app = Mock(spec=ContainerApp)
        app.registry_server = "registry.azurecr.io"
        app.target_port = 8080

        with self.assertRaisesRegex(CLIError, "Non-zero exit code"):
            ContainerApp.build_container_from_source_with_buildpack(app, "app:tag", "source")

        app._docker_push_to_container_registry.assert_not_called()

    @patch("azure.cli.command_modules.containerapp._up_utils.is_docker_running", return_value=False)
    @patch("azure.cli.command_modules.containerapp._up_utils.subprocess.Popen")
    def test_buildpack_requires_docker(self, popen, docker):
        with self.assertRaisesRegex(ValidationError, "Docker is not running"):
            ContainerApp.build_container_from_source_with_buildpack(Mock(spec=ContainerApp), "app:tag", "source")
        popen.assert_not_called()

    @patch("azure.cli.command_modules.acr.custom.acr_login")
    @patch("azure.cli.command_modules.containerapp._up_utils.subprocess.Popen")
    def test_push_authentication_retry(self, popen, login):
        for error in (
                "unauthorized: authentication required",
                "error from registry: authentication required, visit https://aka.ms/acr/authorization"):
            for retry_succeeds in (True, False):
                with self.subTest(error=error, retry_succeeds=retry_succeeds):
                    popen.reset_mock()
                    login.reset_mock()
                    app = ContainerApp.__new__(ContainerApp)
                    app.cmd = Mock()
                    app.cmd.command_kwargs = {"resource_type": "original-type", "operation_group": "original-group"}
                    app.acr = Mock()
                    app.acr.name = "registry"
                    denied = MagicMock()
                    denied.returncode = 1
                    denied.communicate.return_value = (b"", error.encode())
                    retried = MagicMock()
                    retried.returncode = 0 if retry_succeeds else 1
                    retried.communicate.return_value = (b"", error.encode())
                    popen.side_effect = [
                        MagicMock(__enter__=Mock(return_value=denied)),
                        MagicMock(__enter__=Mock(return_value=retried)),
                    ]

                    if retry_succeeds:
                        app._docker_push_to_container_registry("registry.azurecr.io/app:tag")
                    else:
                        with self.assertRaisesRegex(CLIError, "authentication required"):
                            app._docker_push_to_container_registry("registry.azurecr.io/app:tag")

                    login.assert_called_once_with(app.cmd, "registry")
                    self.assertEqual(popen.call_count, 2)
                    self.assertEqual(app.cmd.command_kwargs, {
                        "resource_type": "original-type", "operation_group": "original-group"})

    @patch("azure.cli.command_modules.acr.custom.acr_login")
    @patch("azure.cli.command_modules.containerapp._up_utils.subprocess.Popen")
    def test_push_other_failures_do_not_login(self, popen, login):
        for image, error in (
                ("registry.azurecr.io/app:tag", "network connection failed"),
                ("registry.example.com/app:tag", "error from registry: authentication required")):
            with self.subTest(image=image, error=error):
                popen.reset_mock()
                process = popen.return_value.__enter__.return_value
                process.returncode = 1
                process.communicate.return_value = (b"", error.encode())
                app = ContainerApp.__new__(ContainerApp)

                with self.assertRaisesRegex(CLIError, error):
                    app._docker_push_to_container_registry(image)

                login.assert_not_called()
                self.assertEqual(popen.call_count, 1)
