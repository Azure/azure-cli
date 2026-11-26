# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("verify_crypto", Path(__file__).resolve().parents[1] / "verify_crypto.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class TestMacOSLibraries(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="crypto-linkage-test-", dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.packages = self.root / "site-packages"
        self.binary = self.packages / "cryptography" / "_rust.abi3.so"
        self.binary.parent.mkdir(parents=True)
        self.binary.touch()
        self.python = self.root / "python"
        self.openssl = self.root / "openssl"
        self.openssl.mkdir()
        self.library = self.openssl / "libcrypto.dylib"
        self.library.touch()

    def run_check(self, dependency):
        def command(*args):
            if args[:3] == ("brew", "deps", "--formula"):
                return "openssl@3"
            if args[:2] == ("brew", "--prefix"):
                return str(self.openssl if args[2] == "openssl@3" else self.python)
            if args[:2] == ("otool", "-L"):
                return f"{args[2]}:\n\t{dependency} (compatibility version 3.0.0)"
            return ""

        with mock.patch.object(verifier.platform, "machine", return_value="x86_64"), \
                mock.patch.object(verifier, "command", side_effect=command), \
                mock.patch.object(verifier.subprocess, "run") as run:
            verifier.verify_macos_libraries(self.packages, "x86_64", "python@3.14")
            return run

    def test_declared_python_dependency_is_allowed_and_architecture_checked(self):
        run = self.run_check(str(self.library))
        run.assert_any_call(["lipo", str(self.binary), "-verify_arch", "x86_64"], check=True)
        run.assert_any_call(["lipo", str(self.library), "-verify_arch", "x86_64"], check=True)

    def test_incidental_runner_library_is_rejected(self):
        library = self.root / "incidental.dylib"
        library.touch()
        with self.assertRaisesRegex(RuntimeError, "Undeclared native dependency"):
            self.run_check(str(library))

    def test_system_shared_cache_dependency_is_allowed(self):
        self.run_check("/usr/lib/libSystem.B.dylib")

    def test_missing_dependency_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.run_check(str(self.root / "missing.dylib"))

    def test_wrong_runner_architecture_is_rejected(self):
        with mock.patch.object(verifier.platform, "machine", return_value="arm64"):
            with self.assertRaisesRegex(RuntimeError, "Expected x86_64"):
                verifier.verify_macos_libraries(self.packages, "x86_64", "python@3.14")

    def test_loader_path_and_rpath_resolution(self):
        bundled = self.binary.parent / "libcrypto.dylib"
        bundled.touch()
        self.assertEqual(verifier.resolve_library("@loader_path/libcrypto.dylib", self.binary, []), bundled)
        self.assertEqual(verifier.resolve_library("@rpath/libcrypto.dylib", self.binary, ["@loader_path"]), bundled)
        with self.assertRaisesRegex(RuntimeError, "Unresolved library"):
            verifier.resolve_library("@rpath/missing.dylib", self.binary, ["@loader_path"])

    def test_pipeline_checks_downloaded_artifact_on_both_architectures(self):
        pipeline = (ROOT / ".azure-pipelines" / "templates" / "macos" / "macos-build-jobs.yml").read_text()
        verify_job = pipeline.split("- job: VerifyMacOSCli", 1)[1]
        for expected in (
                "Architecture: 'arm64'", "Architecture: 'x86_64'",
                "- checkout: self", '"$AZ_PYTHON" -S scripts/release/standalone/verify_crypto.py',
                '--packages "$EXTRACT_DIR/libexec/lib/python$RELEASE_PYTHON_VERSION/site-packages"',
                '--architecture "$ARCH"', '--python-formula "python@$RELEASE_PYTHON_VERSION"'):
            self.assertIn(expected, verify_job)
