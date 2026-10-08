# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


_builder_spec = importlib.util.spec_from_file_location(
    "standalone_build_binary_tar_gz",
    Path(__file__).resolve().parents[1] / "build_binary_tar_gz.py",
)
builder = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(builder)

PYTHON_VERSION = "3.14"
CASK_INSTALL_PATH = Path("Caskroom/azure-cli/2.85.0")
SITE_PACKAGES_PATH = Path(f"libexec/lib/python{PYTHON_VERSION}/site-packages")
PYTHON_CANDIDATES = (
    f"opt/python@{PYTHON_VERSION}/libexec/bin/python",
    f"opt/python@{PYTHON_VERSION}/libexec/bin/python3",
    f"opt/python@{PYTHON_VERSION}/bin/python{PYTHON_VERSION}",
    f"bin/python{PYTHON_VERSION}",
)
MISSING_CASK_PYTHON = (
    f"Error: Python {PYTHON_VERSION} not found.\n"
    f"Install via Homebrew: brew install python@{PYTHON_VERSION}\n"
)


@unittest.skipUnless(os.name == "posix", "The launcher requires Bash and POSIX symlinks.")
class TestAzLauncher(unittest.TestCase):

    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="az launcher ")
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name).resolve()
        self.tools = self.root / "tools"
        self.tools.mkdir()
        for name in ("bash", "dirname", "readlink"):
            executable = shutil.which(name)
            if executable is None:
                self.skipTest(f"The launcher requires {name}.")
            try:
                (self.tools / name).symlink_to(Path(executable).resolve())
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"Symlinks are unavailable: {error}")
        self.env = {
            "PATH": str(self.tools),
            "HOME": str(self.root),
            "LC_ALL": "C",
            "PYTHONPATH": "inherited python path",
            "AZ_INSTALLER": "inherited installer",
        }

    def _install(self, install_dir):
        bin_dir = install_dir / "libexec/bin"
        bin_dir.mkdir(parents=True)
        (install_dir / SITE_PACKAGES_PATH).mkdir(parents=True)
        with contextlib.redirect_stdout(io.StringIO()):
            builder._create_launcher_script(bin_dir=bin_dir, python_version=PYTHON_VERSION)
        launcher = install_dir / "bin/az"
        launcher.parent.mkdir()
        launcher.symlink_to("../libexec/bin/az")
        return launcher

    def _python(self, path, executable=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/bin/sh\n"
            "printf '%s\\0' \"$0\" \"${AZ_INSTALLER-}\" \"${PYTHONPATH-}\" \"$@\"\n"
            "exit \"${STUB_EXIT_CODE:-0}\"\n",
            encoding="utf-8",
        )
        path.chmod(0o755 if executable else 0o644)
        return path

    def _run(self, launcher, args=(), **environment):
        return subprocess.run(
            [str(launcher), *args],
            cwd=self.root,
            env={**self.env, **environment},
            capture_output=True,
            check=False,
            timeout=10,
        )

    def _assert_python(self, result, python, install_dir, installer="HOMEBREW_CASK", args=(), exit_code=0):
        self.assertEqual(result.returncode, exit_code, result.stderr)
        self.assertEqual(result.stderr, b"")
        expected = (str(python), installer, str(install_dir / SITE_PACKAGES_PATH), "-sm", "azure.cli", *args)
        self.assertEqual(result.stdout, b"".join(os.fsencode(value) + b"\0" for value in expected))

    def _assert_error(self, result, message):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, message.encode("utf-8"))

    def test_cask_prefix_layouts(self):
        # Virtualize standard prefixes beneath the fixture root, without rewriting the template.
        for layout in ("custom prefix", "opt/homebrew", "usr/local", "home/linuxbrew/.linuxbrew"):
            with self.subTest(prefix=layout):
                prefix = self.root / layout
                install_dir = prefix / CASK_INSTALL_PATH
                launcher = self._install(install_dir)
                python = self._python(prefix / PYTHON_CANDIDATES[0])
                self._assert_python(self._run(launcher), python, install_dir)

    def test_relocated_cask_resolves_directory_and_launcher_symlinks(self):
        for absolute in (False, True):
            fixture = self.root / ("absolute links" if absolute else "relative links")
            prefix = fixture / "relocated Homebrew prefix with spaces"
            install_dir = prefix / CASK_INSTALL_PATH
            self._install(install_dir)
            cellar = prefix / f"Cellar/python@{PYTHON_VERSION}/3.14.0"
            self._python(cellar / "libexec/bin/python")
            formula = prefix / f"opt/python@{PYTHON_VERSION}"
            formula.parent.mkdir()
            formula.symlink_to(os.path.relpath(cellar, formula.parent), target_is_directory=True)
            python = prefix / PYTHON_CANDIDATES[0]

            alias = fixture / "opt/homebrew"
            alias.parent.mkdir(parents=True)
            alias.symlink_to(
                prefix if absolute else os.path.relpath(prefix, alias.parent),
                target_is_directory=True,
            )
            homebrew_launcher = prefix / "bin/az"
            homebrew_launcher.parent.mkdir()
            homebrew_launcher.symlink_to(
                alias / CASK_INSTALL_PATH / "bin/az" if absolute else Path("..") / CASK_INSTALL_PATH / "bin/az"
            )

            for entry in ("bin/az", CASK_INSTALL_PATH / "libexec/bin/az"):
                with self.subTest(absolute=absolute, entry=str(entry)):
                    self._assert_python(
                        self._run(alias / entry, args=("version",)), python, install_dir, args=("version",)
                    )

    def test_cask_python_candidate_precedence(self):
        prefix = self.root / "brew"
        install_dir = prefix / CASK_INSTALL_PATH
        launcher = self._install(install_dir)
        candidates = [self._python(prefix / candidate) for candidate in PYTHON_CANDIDATES]
        for python in candidates:
            with self.subTest(candidate=python.relative_to(prefix)):
                self._assert_python(self._run(launcher), python, install_dir)
            python.unlink()

    def test_cask_skips_non_executable_python_candidates(self):
        prefix = self.root / "brew"
        install_dir = prefix / CASK_INSTALL_PATH
        launcher = self._install(install_dir)
        candidates = [self._python(prefix / candidate) for candidate in PYTHON_CANDIDATES]
        for previous, python in zip(candidates, candidates[1:]):
            previous.chmod(0o644)
            with self.subTest(candidate=python.relative_to(prefix)):
                self._assert_python(self._run(launcher), python, install_dir)

    def test_cask_requires_executable_python(self):
        prefix = self.root / "brew"
        launcher = self._install(prefix / CASK_INSTALL_PATH)
        for state in ("missing", "non-executable"):
            with self.subTest(python=state):
                if state == "non-executable":
                    for candidate in PYTHON_CANDIDATES:
                        self._python(prefix / candidate, executable=False)
                self._assert_error(self._run(launcher), MISSING_CASK_PYTHON)

    def test_cask_ignores_other_installations(self):
        prefix = self.root / "own brew"
        install_dir = prefix / CASK_INSTALL_PATH
        launcher = self._install(install_dir)
        python = self._python(prefix / PYTHON_CANDIDATES[0])
        unrelated = self.root / "opt/homebrew"
        for candidate in PYTHON_CANDIDATES:
            self._python(unrelated / candidate)
        for name in ("python", "python3"):
            self._python(unrelated / "bin" / name)
        brew_log = self.root / "brew calls"
        brew = unrelated / "bin/brew"
        brew.write_text(
            "#!/bin/sh\n"
            "printf '%s\\0' \"$@\" >> \"$BREW_CALL_LOG\"\n"
            f"printf '%s\\n' \"$HOMEBREW_PREFIX/opt/python@{PYTHON_VERSION}\"\n",
            encoding="utf-8",
        )
        brew.chmod(0o755)
        environment = {
            "PATH": os.pathsep.join((str(unrelated / "bin"), str(self.tools))),
            "HOMEBREW_PREFIX": str(unrelated),
            "AZ_PYTHON": str(unrelated / "bin/python3"),
            "BREW_CALL_LOG": str(brew_log),
        }
        for available in (True, False):
            with self.subTest(own_python_available=available):
                if not available:
                    python.unlink()
                result = self._run(launcher, **environment)
                self.assertFalse(brew_log.exists(), "The launcher must not invoke brew from PATH.")
                if available:
                    self._assert_python(result, python, install_dir)
                else:
                    self._assert_error(result, MISSING_CASK_PYTHON)

    def test_tarball_requires_az_python(self):
        launcher = self._install(self.root / "tarball with spaces")
        for environment in ({}, {"AZ_PYTHON": ""}):
            with self.subTest(environment=environment):
                self._assert_error(
                    self._run(launcher, **environment),
                    "Error: AZ_PYTHON not set.\n"
                    f"For offline/tarball installs, set AZ_PYTHON to a Python {PYTHON_VERSION} path.\n",
                )

    def test_tarball_rejects_invalid_az_python(self):
        launcher = self._install(self.root / "tarball")
        for state in ("missing", "non-executable"):
            with self.subTest(python=state):
                python = self.root / f"{state} python"
                if state == "non-executable":
                    self._python(python, executable=False)
                self._assert_error(
                    self._run(launcher, AZ_PYTHON=str(python)),
                    f"Error: Python not found at {python}\n",
                )

    def test_tarball_paths_are_not_casks(self):
        python = self._python(self.root / "explicit interpreter with spaces/python")
        for layout in (
            "tarball with spaces",
            "Caskroom/azure-cli-preview/2.85.0",
            "not-Caskroom/azure-cli/2.85.0",
            "Caskroom/azure-cli/2.85.0/nested",
            "Caskroom/azure-cli",
        ):
            with self.subTest(install=layout):
                install_dir = self.root / layout
                launcher = self._install(install_dir)
                result = self._run(launcher, AZ_PYTHON=str(python))
                self._assert_python(result, python, install_dir, installer="TARBALL")

    def test_execution_preserves_arguments_environment_and_exit_status(self):
        args = (
            "group", "show", "--name", "value with spaces", "",
            "'\"$HOME;`printf injected`", "$(printf injected)", "*", "a|b&c>d<e", "line\nbreak", "",
        )
        for inherited in (True, False):
            if not inherited:
                self.env.pop("PYTHONPATH")
                self.env.pop("AZ_INSTALLER")
            for installer in ("HOMEBREW_CASK", "TARBALL"):
                with self.subTest(installer=installer, inherited_environment=inherited):
                    prefix = self.root / ("inherited" if inherited else "unset") / installer
                    install_dir = prefix / CASK_INSTALL_PATH if installer == "HOMEBREW_CASK" else prefix / "tarball"
                    launcher = self._install(install_dir)
                    python = self._python(prefix / PYTHON_CANDIDATES[0])
                    environment = {"AZ_PYTHON": str(python)} if installer == "TARBALL" else {}
                    result = self._run(launcher, args=args, STUB_EXIT_CODE="37", **environment)
                    self._assert_python(result, python, install_dir, installer=installer, args=args, exit_code=37)

    def test_package_directory_is_required(self):
        for installer in ("HOMEBREW_CASK", "TARBALL"):
            prefix = self.root / installer
            install_dir = prefix / CASK_INSTALL_PATH if installer == "HOMEBREW_CASK" else prefix / "tarball"
            launcher = self._install(install_dir)
            python = self._python(prefix / PYTHON_CANDIDATES[0])
            environment = {"AZ_PYTHON": str(python)} if installer == "TARBALL" else {}
            packages = install_dir / SITE_PACKAGES_PATH
            packages.rmdir()
            for state in ("missing", "regular file"):
                with self.subTest(installer=installer, packages=state):
                    if state == "regular file":
                        packages.write_text("not a directory", encoding="utf-8")
                    self._assert_error(
                        self._run(launcher, **environment),
                        f"Error: Azure CLI packages not found at {packages}\n",
                    )


if __name__ == "__main__":
    unittest.main()
