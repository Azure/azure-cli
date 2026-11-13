# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest import mock

import requests
import semver

from azure.cli.core.azclierror import (
    ClientRequestError, FileOperationError, UnclassifiedUserFault, ValidationError,
)
from azure.cli.command_modules.resource._bicep import (
    _get_bicep_download_url,
    ensure_bicep_version_installation,
)
from azure.cli.command_modules.resource._bicep_version import parse_bicep_version_constraint


class TestBicepInstallation(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.addCleanup(directory.cleanup)
        self.bin_dir = os.path.join(directory.name, "bin")
        os.makedirs(self.bin_dir)
        self.legacy_path = os.path.join(self.bin_dir, "bicep.exe")
        with open(self.legacy_path, "wb") as file:
            file.write(b"legacy compiler")
        self.patch("_bicep_installation_dir", self.bin_dir)
        self.system = self.patch("platform.system", return_value="Windows")
        self.machine = self.patch("platform.machine", return_value="AMD64")
        self.musl = self.patch("_has_musl_library_only", return_value=False)
        self.logger = self.patch("_logger")
        self.set_config = self.patch("set_use_binary_from_path_config")
        self.get_version = self.patch(
            "_get_bicep_installed_version",
            side_effect=lambda path: semver.VersionInfo.parse(os.path.basename(os.path.dirname(os.path.dirname(path))))
        )
        self.catalog = self.response(payload=[{"tag_name": "v0.31.92"}])
        self.binary = self.response(chunks=(b"downloaded ", b"compiler"))
        self.get = self.patch("requests.get", side_effect=[self.catalog, self.binary])

    def patch(self, name, *args, **kwargs):
        patcher = mock.patch(f"azure.cli.command_modules.resource._bicep.{name}", *args, **kwargs)
        patched = patcher.start()
        self.addCleanup(patcher.stop)
        return patched

    @staticmethod
    def response(payload=None, chunks=()):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.json.return_value = payload
        response.iter_content.return_value = iter(chunks)
        return response

    def cache_path(self, version="0.31.92", target_platform="win-x64"):
        filename = "bicep.exe" if target_platform.startswith("win-") else "bicep"
        return os.path.join(self.bin_dir, "bicep-versions", version, target_platform, filename)

    def cache(self, version, target_platform="win-x64"):
        path = self.cache_path(version, target_platform)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            file.write(b"cached compiler")
        return path

    def acquire(self, constraint=">=0.31, <0.32"):
        return ensure_bicep_version_installation(parse_bicep_version_constraint(constraint))

    def assert_no_published_download(self, version="0.31.92", target_platform="win-x64"):
        path = self.cache_path(version, target_platform)
        self.assertFalse(os.path.exists(path))
        if os.path.isdir(os.path.dirname(path)):
            self.assertEqual([], os.listdir(os.path.dirname(path)))

    def test_highest_compatible_cached_version_is_reused_without_network(self):
        self.cache("0.31.1")
        expected = self.cache("0.31.92")
        self.cache("0.32.0")
        installation = self.acquire()
        self.assertEqual(semver.VersionInfo(0, 31, 92), installation.version)
        self.assertEqual(expected, installation.executable_path)
        self.get.assert_not_called()
        self.get_version.assert_called_once_with(expected)
        self.set_config.assert_not_called()

    def test_compatible_cache_is_used_even_if_newer_releases_exist(self):
        expected = self.cache("0.31.1")
        self.assertEqual(expected, self.acquire().executable_path)
        self.get.assert_not_called()

    def test_exact_constraint_reuses_only_that_cached_version(self):
        expected = self.cache("0.31.1")
        self.cache("0.31.92")
        self.assertEqual(expected, self.acquire("0.31.1").executable_path)
        self.get.assert_not_called()

    def test_cache_miss_selects_highest_stable_matching_release_numerically(self):
        self.cache("0.30.0")
        self.catalog.json.return_value = [
            {"tag_name": tag} for tag in (
                "v0.31.9", "v0.32.0", "v0.31.92-preview", "v0.31.01", "v0.31.91+metadata",
                "v0.31.2147483648", "v0.31", "=0.31.99", "nightly", "v0.31.92", "v0.31.10")
        ] + [
            {"tag_name": "v0.31.99", "prerelease": True},
            {"tag_name": "v0.31.98", "draft": True},
        ]
        installation = self.acquire()
        self.assertEqual(semver.VersionInfo(0, 31, 92), installation.version)
        self.assertEqual(self.cache_path(), installation.executable_path)
        self.assertEqual(
            "https://downloads.bicep.azure.com/v0.31.92/bicep-win-x64.exe",
            self.get.call_args_list[1].args[0],
        )

    def test_missing_executable_and_other_platform_cache_do_not_count_as_installed(self):
        os.makedirs(os.path.dirname(self.cache_path("0.31.99")))
        self.cache("0.31.98", "win-arm64")
        os.makedirs(os.path.join(self.bin_dir, "bicep-versions", "not-a-version"))
        self.assertEqual(semver.VersionInfo(0, 31, 92), self.acquire().version)
        self.assertEqual(2, self.get.call_count)

    def test_invalid_cached_binary_is_reported_and_lower_valid_cache_is_reused(self):
        self.cache("0.31.92")
        expected = self.cache("0.31.1")
        self.get_version.side_effect = [OSError("cannot execute"), semver.VersionInfo(0, 31, 1)]
        self.assertEqual(expected, self.acquire().executable_path)
        self.logger.warning.assert_called_once()
        self.get.assert_not_called()

    def test_wrong_version_in_cache_is_reported_and_replaced_after_validation(self):
        self.cache("0.31.92")
        self.get_version.side_effect = [semver.VersionInfo(0, 30, 0), semver.VersionInfo(0, 31, 92)]
        installation = self.acquire()
        self.logger.warning.assert_called_once()
        with open(installation.executable_path, "rb") as file:
            self.assertEqual(b"downloaded compiler", file.read())

    def test_unsatisfiable_range_fails_before_network_or_cache_access(self):
        with self.assertRaisesRegex(ValidationError, "cannot be satisfied"):
            self.acquire(">=2, <1")
        self.get.assert_not_called()
        self.get_version.assert_not_called()

    def test_no_matching_release_is_a_clear_error_without_downloading(self):
        self.catalog.json.return_value = [{"tag_name": "v0.30.0"}, {"tag_name": "v0.32.0"}]
        with self.assertRaisesRegex(ValidationError, "No published stable Bicep release satisfies"):
            self.acquire()
        self.assertEqual(1, self.get.call_count)
        self.assert_no_published_download()

    def test_malformed_catalog_is_not_treated_as_no_matching_release(self):
        for payload in (None, {}, [None], [{}], [{"tag_name": 42}], [{"tag_name": ""}],
                        [{"tag_name": "v0.31.92", "draft": "false"}],
                        [{"tag_name": "v0.31.92", "prerelease": None}]):
            with self.subTest(payload=payload):
                self.get.side_effect = None
                self.get.return_value = self.response(payload=payload)
                with self.assertRaisesRegex(ClientRequestError, "response"):
                    self.acquire()

    def test_catalog_network_http_and_json_errors_are_actionable(self):
        for failure in ("network", "http", "json"):
            with self.subTest(failure=failure):
                response = self.response()
                self.get.side_effect = None
                self.get.return_value = response
                if failure == "network":
                    self.get.side_effect = requests.Timeout("offline")
                elif failure == "http":
                    response.raise_for_status.side_effect = requests.HTTPError("503")
                else:
                    response.json.side_effect = ValueError("invalid JSON")
                with self.assertRaisesRegex(ClientRequestError, "Unable to retrieve Bicep releases"):
                    self.acquire()
                self.assert_no_published_download()

    def test_download_is_verified_before_atomic_publication_and_default_is_unchanged(self):
        def verify_temporary(path):
            self.assertNotEqual(self.cache_path(), path)
            self.assertFalse(os.path.exists(self.cache_path()))
            with open(path, "rb") as file:
                self.assertEqual(b"downloaded compiler", file.read())
            return semver.VersionInfo(0, 31, 92)

        self.get_version.side_effect = verify_temporary
        installation = self.acquire()
        self.assertEqual(["bicep.exe"], os.listdir(os.path.dirname(installation.executable_path)))
        with open(self.legacy_path, "rb") as file:
            self.assertEqual(b"legacy compiler", file.read())
        self.set_config.assert_not_called()
        self.catalog.__exit__.assert_called_once()
        self.binary.__exit__.assert_called_once()

    def test_requests_respect_tls_setting(self):
        self.patch("_requests_verify", False)
        self.acquire()
        self.get.assert_has_calls([
            mock.call("https://downloads.bicep.azure.com/releases", verify=False),
            mock.call("https://downloads.bicep.azure.com/v0.31.92/bicep-win-x64.exe",
                      stream=True, verify=False),
        ])

    def test_interrupted_download_cleans_temporary_file_without_publishing(self):
        def interrupted():
            yield b"partial"
            raise requests.ConnectionError("connection lost")

        self.binary.iter_content.return_value = interrupted()
        with self.assertRaisesRegex(ClientRequestError, "Unable to download Bicep CLI"):
            self.acquire()
        self.assert_no_published_download()
        self.get_version.assert_not_called()

    def test_empty_and_http_error_downloads_are_not_published(self):
        for failure in ("empty", "http"):
            with self.subTest(failure=failure):
                binary = self.response()
                if failure == "http":
                    binary.raise_for_status.side_effect = requests.HTTPError("404")
                self.get.side_effect = [self.catalog, binary]
                with self.assertRaises(ClientRequestError):
                    self.acquire()
                self.assert_no_published_download()
                self.get_version.assert_not_called()

    def test_wrong_or_unrunnable_download_is_not_published(self):
        for reported in (None, semver.VersionInfo(0, 30, 0), semver.VersionInfo.parse("0.31.92+metadata"),
                         OSError("bad executable"), UnclassifiedUserFault("failed to run")):
            with self.subTest(reported=reported):
                self.get.side_effect = [self.catalog, self.response(chunks=(b"compiler",))]
                self.get_version.side_effect = [reported]
                with self.assertRaises(ValidationError):
                    self.acquire()
                self.assert_no_published_download()

    def test_cache_permission_failure_is_not_treated_as_a_cache_miss(self):
        self.patch("os.scandir", side_effect=PermissionError("denied"))
        with self.assertRaisesRegex(FileOperationError, "Unable to read the Bicep version cache"):
            self.acquire()
        self.get.assert_not_called()

    def test_publication_failure_cleans_temporary_file(self):
        self.patch("os.replace", side_effect=PermissionError("denied"))
        with self.assertRaisesRegex(FileOperationError, "Unable to install Bicep CLI"):
            self.acquire()
        self.assert_no_published_download()

    def test_concurrent_publication_reuses_valid_executable_and_cleans_own_download(self):
        def competing_install(source, destination):
            self.assertNotEqual(source, destination)
            with open(destination, "wb") as file:
                file.write(b"concurrently installed compiler")
            raise PermissionError("another invocation installed it")

        self.patch("os.replace", side_effect=competing_install)
        installation = self.acquire()
        self.assertEqual(["bicep.exe"], os.listdir(os.path.dirname(installation.executable_path)))
        with open(installation.executable_path, "rb") as file:
            self.assertEqual(b"concurrently installed compiler", file.read())

    def test_platform_cache_and_download_url_use_the_same_platform_mapping(self):
        cases = (
            ("Windows", "AMD64", False, "win-x64"),
            ("Windows", "arm64", False, "win-arm64"),
            ("Linux", "x86_64", False, "linux-x64"),
            ("Linux", "aarch64", True, "linux-arm64"),
            ("Linux", "x86_64", True, "linux-musl-x64"),
            ("Darwin", "x86_64", False, "osx-x64"),
            ("Darwin", "arm64", False, "osx-arm64"),
        )
        for system, machine, musl, target in cases:
            with self.subTest(system=system, machine=machine, musl=musl):
                self.system.return_value = system
                self.machine.return_value = machine
                self.musl.return_value = musl
                expected = self.cache("0.31.92", target)
                self.assertEqual(expected, self.acquire().executable_path)
                extension = ".exe" if system == "Windows" else ""
                self.assertEqual(
                    f"https://downloads.bicep.azure.com/v0.31.92/bicep-{target}{extension}",
                    _get_bicep_download_url(system, machine, "v0.31.92"),
                )
        self.get.assert_not_called()

    def test_explicit_download_target_override_is_preserved(self):
        self.assertEqual(
            "https://downloads.bicep.azure.com/v0.31.92/bicep-win-arm64.exe",
            _get_bicep_download_url("Darwin", "x86_64", "v0.31.92", target_platform="win-arm64"),
        )

    def test_unsupported_host_fails_without_network_access(self):
        self.system.return_value = "unsupported"
        with self.assertRaisesRegex(ValidationError, "not supported"):
            self.acquire()
        self.get.assert_not_called()
