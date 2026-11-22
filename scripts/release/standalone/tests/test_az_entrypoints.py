# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import venv


REPO_ROOT = Path(__file__).resolve().parents[4]
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
SHADOW_MARKER = "AZ_LAUNCHER_LOCAL_IMPORT_SENTINEL"
SHADOW_CODE = f"print({SHADOW_MARKER!r})\nraise SystemExit(86)\n"
CLI_CODE = """
import json
import os
import sys
import launcher_dependency

# Mirror portalocker's optional redis import: an empty local namespace can
# import successfully even when the optional installed package is absent.
try:
    import redis
except ImportError:
    redis = None
if redis is not None:
    redis.client.PubSubWorkerThread

print(json.dumps({
    "argv": sys.argv,
    "installer": os.environ.get("AZ_INSTALLER"),
    "pythonpath": os.environ.get("PYTHONPATH"),
    "dependency": launcher_dependency.VALUE,
    "redis": redis.__file__ if redis is not None else None,
    "name": __name__,
    "package": __package__,
    "cwd": os.getcwd(),
    "user_site": not sys.flags.no_user_site,
}))
sys.exit(int(os.environ.get("CLI_EXIT_CODE", "0")))
"""


class TestAzEntrypoints(unittest.TestCase):

    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="az entrypoints ")
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name).resolve()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.tools = self.root / "tools"
        self.tools.mkdir()
        python_environment = self.root / "python environment"
        venv.EnvBuilder(with_pip=False).create(python_environment)
        self.python = python_environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.root),
            "LC_ALL": "C",
        }
        if "SYSTEMROOT" in os.environ:
            self.env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
        self.assertNotIn("PYTHONSAFEPATH", self.env)
        self.assertNotIn("PYTHONPATH", self.env)

    def _python(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"#!/bin/sh\nexec {shlex.quote(str(self.python))} \"$@\"\n", encoding="utf-8")
        path.chmod(0o755)

    def _packages(self, path):
        cli = path / "azure/cli"
        cli.mkdir(parents=True, exist_ok=True)
        (cli / "__init__.py").write_text("", encoding="utf-8")
        (cli / "__main__.py").write_text(CLI_CODE, encoding="utf-8")
        (path / "launcher_dependency.py").write_text("VALUE = 'installed'\n", encoding="utf-8")
        return path

    def _shadow_packages(self, other_packages=False):
        (self.project / "redis").mkdir(exist_ok=True)
        (self.project / "redis/__init__.py").write_text(SHADOW_CODE, encoding="utf-8")
        if other_packages:
            for name in ("runpy.py", "launcher_dependency.py"):
                (self.project / name).write_text(SHADOW_CODE, encoding="utf-8")
            (self.project / "azure").mkdir()
            (self.project / "azure/__init__.py").write_text(SHADOW_CODE, encoding="utf-8")

    def _installed_redis(self, packages):
        redis = packages / "redis"
        redis.mkdir()
        (redis / "__init__.py").write_text("from . import client\n", encoding="utf-8")
        (redis / "client.py").write_text("class PubSubWorkerThread:\n    pass\n", encoding="utf-8")
        return redis / "__init__.py"

    def _run(self, launcher, args=(), **environment):
        command = [str(launcher), *args]
        if launcher.suffix == ".bat":
            cmd = subprocess.list2cmdline([os.environ.get("COMSPEC", "cmd.exe")])
            # cmd.exe needs an outer quote pair around the entire /c command.
            command = f'{cmd} /d /s /c "{subprocess.list2cmdline(command)}"'
        return subprocess.run(
            command,
            cwd=self.project,
            env={**self.env, **environment},
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def _assert_cli(self, result, packages, installer, args, exit_code=0, user_site=False):
        self.assertNotIn(SHADOW_MARKER, result.stdout + result.stderr)
        self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)
        self.assertEqual(Path(output["argv"][0]).resolve(), packages / "azure/cli/__main__.py")
        self.assertEqual(output["argv"][1:], list(args))
        self.assertEqual(output["installer"], installer)
        self.assertIn(packages, [Path(path).resolve() for path in output["pythonpath"].split(os.pathsep)])
        self.assertEqual(output["dependency"], "installed")
        self.assertEqual(output["name"], "__main__")
        self.assertEqual(output["package"], "azure.cli")
        self.assertEqual(output["cwd"], str(self.project))
        self.assertEqual(output["user_site"], user_site)
        return output

    def _standalone(self, installer):
        if os.name != "posix":
            self.skipTest("The standalone launcher requires Bash.")
        spec = importlib.util.spec_from_file_location(
            "standalone_builder", REPO_ROOT / "scripts/release/standalone/build_binary_tar_gz.py"
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        prefix = self.root / installer
        install = prefix / "Caskroom/azure-cli/1.0" if installer == "HOMEBREW_CASK" else prefix / "tarball"
        packages = self._packages(install / f"libexec/lib/python{PYTHON_VERSION}/site-packages")
        bin_dir = install / "libexec/bin"
        bin_dir.mkdir(parents=True)
        with contextlib.redirect_stdout(io.StringIO()):
            builder._create_launcher_script(bin_dir, PYTHON_VERSION)
        launcher = install / "bin/az"
        launcher.parent.mkdir()
        launcher.symlink_to("../libexec/bin/az")
        if installer == "HOMEBREW_CASK":
            python = prefix / f"opt/python@{PYTHON_VERSION}/libexec/bin/python"
            self._python(python)
        else:
            self.env["AZ_PYTHON"] = str(self.python)
        return launcher, packages

    def _rpm(self, matching_python=True):
        if os.name != "posix":
            self.skipTest("The RPM launcher requires Bash.")
        install = self.root / ("rpm matching" if matching_python else "rpm fallback")
        packages = self._packages(install / f"lib64/az/lib/python{PYTHON_VERSION}/site-packages")
        (install / "bin").mkdir()
        spec = (REPO_ROOT / "scripts/release/rpm/azure-cli.spec").read_text(encoding="utf-8")
        # Execute the real printf expression, including its two levels of shell quoting.
        start = spec.index('printf "#!/usr/bin/env bash\n')
        end = spec.index('" > %{buildroot}%{_bindir}/az', start) + len('" > %{buildroot}%{_bindir}/az')
        command = spec[start:end]
        for macro, value in (("%{python_cmd}", "python3"), ("%{buildroot}", "."), ("%{_bindir}", "/bin")):
            command = command.replace(macro, value)
        result = subprocess.run(
            ["bash", "-c", command],
            cwd=install,
            env={**self.env, "python_version": f"python{PYTHON_VERSION}"},
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        launcher = install / "bin/az"
        launcher.chmod(0o755)
        for python in self.tools.glob("python*"):
            python.unlink()
        self._python(self.tools / "python3")
        if matching_python:
            self._python(self.tools / f"python{PYTHON_VERSION}")
            (self.tools / "python3").write_text("#!/bin/sh\nexit 85\n", encoding="utf-8")
            (self.tools / "python3").chmod(0o755)
        # Keep the tool path controlled so host interpreters cannot defeat the fallback case.
        for name in ("bash", "dirname"):
            if not (self.tools / name).exists():
                (self.tools / name).symlink_to(shutil.which(name))
        self.env["PATH"] = str(self.tools)
        return launcher, packages

    def test_standalone_ignores_empty_redis_directory(self):
        (self.project / "redis").mkdir()
        for installer in ("HOMEBREW_CASK", "TARBALL"):
            with self.subTest(installer=installer):
                launcher, packages = self._standalone(installer)
                for args in (("group", "list"), ("login",)):
                    output = self._assert_cli(self._run(launcher, args), packages, installer, args)
                    self.assertIsNone(output["redis"])

    def test_standalone_does_not_execute_local_packages(self):
        self._shadow_packages()
        for installer in ("HOMEBREW_CASK", "TARBALL"):
            with self.subTest(installer=installer):
                launcher, packages = self._standalone(installer)
                for args in (("login",), ("aks", "list"), ("account", "show")):
                    self._assert_cli(self._run(launcher, args), packages, installer, args)

    def test_standalone_prefers_installed_modules(self):
        self._shadow_packages(other_packages=True)
        for installer in ("HOMEBREW_CASK", "TARBALL"):
            with self.subTest(installer=installer):
                launcher, packages = self._standalone(installer)
                redis = self._installed_redis(packages)
                output = self._assert_cli(self._run(launcher, ("login",)), packages, installer, ("login",))
                self.assertEqual(Path(output["redis"]).resolve(), redis)

    def test_standalone_preserves_arguments_and_safe_path_environment(self):
        args = ("group", "list", "", "value with spaces", "'\"$HOME;`echo injected`", "*", "line\nbreak")
        for installer in ("HOMEBREW_CASK", "TARBALL"):
            launcher, packages = self._standalone(installer)
            for safe_path in ("", "1"):
                with self.subTest(installer=installer, safe_path=safe_path):
                    self._assert_cli(
                        self._run(launcher, args, PYTHONSAFEPATH=safe_path, CLI_EXIT_CODE="37"),
                        packages, installer, args, exit_code=37,
                    )

    def test_rpm_ignores_empty_redis_directory(self):
        (self.project / "redis").mkdir()
        for matching_python in (True, False):
            with self.subTest(matching_python=matching_python):
                launcher, packages = self._rpm(matching_python)
                for args in (("group", "list"), ("login",)):
                    output = self._assert_cli(self._run(launcher, args), packages, "RPM", args)
                    self.assertIsNone(output["redis"])

    def test_rpm_does_not_execute_local_packages(self):
        self._shadow_packages()
        launcher, packages = self._rpm()
        for args in (("login",), ("aks", "list"), ("account", "show")):
            with self.subTest(args=args):
                self._assert_cli(self._run(launcher, args), packages, "RPM", args)

    def test_rpm_prefers_installed_modules(self):
        self._shadow_packages(other_packages=True)
        launcher, packages = self._rpm()
        redis = self._installed_redis(packages)
        output = self._assert_cli(self._run(launcher, ("login",)), packages, "RPM", ("login",))
        self.assertEqual(Path(output["redis"]).resolve(), redis)

    def test_rpm_preserves_arguments_and_safe_path_environment(self):
        launcher, packages = self._rpm()
        args = ("group", "list", "", "value with spaces", "'\"$HOME;`echo injected`", "*", "line\nbreak")
        for safe_path in ("", "1"):
            with self.subTest(safe_path=safe_path):
                self._assert_cli(
                    self._run(launcher, args, PYTHONSAFEPATH=safe_path, CLI_EXIT_CODE="37"),
                    packages, "RPM", args, exit_code=37,
                )

    def test_rpm_replaces_launcher_process(self):
        launcher, packages = self._rpm()
        (packages / "azure/cli/__main__.py").write_text(
            "import os\nprint(os.getpid())\n", encoding="utf-8",
        )
        with subprocess.Popen(
            [str(launcher)], cwd=self.project, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ) as process:
            output, error = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, error)
            self.assertEqual(int(output), process.pid)

    @unittest.skipUnless(os.name == "posix", "The developer launcher requires a POSIX executable.")
    def test_developer_launcher_does_not_execute_local_packages(self):
        self._shadow_packages()
        launcher = self.tools / "az"
        shutil.copy2(REPO_ROOT / "src/azure-cli/az", launcher)
        launcher.chmod(0o755)
        self._python(self.tools / "python")
        self.env["PATH"] = str(self.tools)
        packages = self._packages(self.tools / "src")
        inherited = self._packages(self.root / "inherited packages")
        for pythonpath in (None, "", str(inherited)):
            with self.subTest(pythonpath=pythonpath):
                environment = {} if pythonpath is None else {"PYTHONPATH": pythonpath}
                args = ("group", "list", "", "value with spaces")
                output = self._assert_cli(
                    self._run(launcher, args, CLI_EXIT_CODE="37", **environment),
                    packages, "PIP", args, exit_code=37, user_site=True,
                )
                if pythonpath:
                    self.assertIn(pythonpath, output["pythonpath"].split(os.pathsep))
        self._assert_cli(
            self._run(launcher, ("login",), AZ_INSTALLER="CUSTOM"),
            packages, "CUSTOM", ("login",), user_site=True,
        )

    @unittest.skipUnless(os.name == "nt", "The batch launcher requires Windows cmd.exe.")
    def test_batch_launcher_does_not_execute_local_packages(self):
        self._shadow_packages()
        environment = self.root / "venv"
        venv.EnvBuilder(with_pip=False).create(environment)
        bin_dir = environment / "Scripts"
        launcher = bin_dir / "az.bat"
        shutil.copy2(REPO_ROOT / "src/azure-cli/az.bat", launcher)
        packages = self._packages(bin_dir / "src")
        fallback = self.root / "fallback venv"
        venv.EnvBuilder(with_pip=False).create(fallback)
        self.env["PATH"] = os.pathsep.join((str(bin_dir), self.env["PATH"]))
        for adjacent_python in (True, False):
            if not adjacent_python:
                (bin_dir / "python.exe").rename(bin_dir / "launcher-python.exe")
                self.env["PATH"] = os.pathsep.join((str(fallback / "Scripts"), self.env["PATH"]))
            for pythonpath in (None, "", str(self.root)):
                with self.subTest(adjacent_python=adjacent_python, pythonpath=pythonpath):
                    extra = {} if pythonpath is None else {"PYTHONPATH": pythonpath}
                    for args in (("login",), ("aks", "list"), ("group", "list", "value with spaces")):
                        self._assert_cli(
                            self._run(launcher, args, CLI_EXIT_CODE="37", **extra),
                            packages, "PIP", args, exit_code=37, user_site=True,
                        )


@unittest.skipUnless(os.environ.get("AZ_LAUNCHER_TEST_EXECUTABLE"), "Requires an installed CLI launcher.")
class TestInstalledAzEntrypoints(unittest.TestCase):
    """Run against release artifacts, without replacing Azure CLI or its dependencies."""

    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="az installed entrypoint ")
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name).resolve()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.config_dir = self.root / "config"
        self.config_dir.mkdir()
        self.config = self.config_dir / "config"
        self.config_content = "[core]\ncollect_telemetry = no\n\n[cloud]\nname = AzureCloud\n\n"
        self.config.write_text(self.config_content, encoding="utf-8")
        self.launcher = str(Path(os.environ["AZ_LAUNCHER_TEST_EXECUTABLE"]).absolute())
        self.env = os.environ.copy()
        for name in ("PYTHONSAFEPATH", "PYTHONPATH", "PYTHONHOME"):
            self.env.pop(name, None)
        self.env.update({
            "AZURE_CONFIG_DIR": str(self.config_dir),
            "AZURE_CORE_COLLECT_TELEMETRY": "false",
            "AZURE_CORE_ENABLE_BROKER_ON_MAC": "false",
            "AZURE_CORE_ENABLE_BROKER_ON_WINDOWS": "false",
            "PYTHONUNBUFFERED": "1",
            "LC_ALL": "C",
        })

    def _redis(self, shadow_package):
        redis = self.project / "redis"
        redis.mkdir()
        if shadow_package:
            (redis / "__init__.py").write_text(SHADOW_CODE, encoding="utf-8")
        return redis

    def _assert_no_shadowing(self, output):
        self.assertNotIn(SHADOW_MARKER, output)
        self.assertNotIn("module 'redis' has no attribute 'client'", output)

    def _run(self, args, **environment):
        return subprocess.run(
            [self.launcher, *args], cwd=self.project, env={**self.env, **environment},
            capture_output=True, text=True, check=False, timeout=60,
        )

    def test_login_imports_with_empty_redis_directory(self):
        self._assert_login_imports(shadow_package=False)

    def test_login_does_not_execute_local_redis_package(self):
        self._assert_login_imports(shadow_package=True)

    def _assert_login_imports(self, shadow_package):
        redis = self._redis(shadow_package)
        # This configuration error occurs after Identity imports msal_extensions
        # and portalocker, before any network request or credential acquisition.
        invalid_boolean = "az-launcher-invalid-boolean"
        result = self._run(("login",), AZURE_CORE_USE_MSAL_HTTP_CACHE=invalid_boolean)
        output = result.stdout + result.stderr
        self._assert_no_shadowing(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"Not a boolean: {invalid_boolean}", output)
        self.assertTrue(redis.is_dir())
        self.assertEqual(self.config.read_text(encoding="utf-8"), self.config_content)

    def test_commands_do_not_execute_local_redis_package(self):
        redis = self._redis(shadow_package=True)
        for args in (("aks", "list"), ("group", "list"), ("account", "show")):
            with self.subTest(command=args):
                result = self._run(args)
                output = result.stdout + result.stderr
                self._assert_no_shadowing(output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Please run 'az login'", output)
                self.assertTrue(redis.is_dir())

    @unittest.skipUnless(os.environ.get("AZ_LAUNCHER_TEST_DEVICE_LOGIN") == "1",
                         "Requires identity-service connectivity, but no credentials.")
    def test_empty_redis_reaches_device_login(self):
        self._redis(shadow_package=False)
        self._assert_device_login()

    @unittest.skipUnless(os.environ.get("AZ_LAUNCHER_TEST_DEVICE_LOGIN") == "1",
                         "Requires identity-service connectivity, but no credentials.")
    def test_local_redis_package_does_not_intercept_device_login(self):
        self._redis(shadow_package=True)
        self._assert_device_login()

    @unittest.skipUnless(os.environ.get("AZ_LAUNCHER_TEST_DEVICE_LOGIN") == "1",
                         "Requires identity-service connectivity, but no credentials.")
    def test_clean_directory_reaches_device_login(self):
        self._assert_device_login()

    def _assert_device_login(self):
        log = self.root / "device-login.log"
        with log.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(
                [self.launcher, "login", "--use-device-code"],
                cwd=self.project, env=self.env, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    content = log.read_text(encoding="utf-8")
                    # Never include the device code or service response in test output.
                    self.assertFalse(SHADOW_MARKER in content, "Local redis package was executed.")
                    self.assertFalse("module 'redis' has no attribute 'client'" in content,
                                     "Local redis directory shadowed the dependency.")
                    if "To sign in" in content and "enter the code" in content:
                        break
                    if process.poll() is not None:
                        self.fail("Installed CLI exited before reaching device-code sign-in.")
                    time.sleep(0.1)
                else:
                    self.fail("Installed CLI did not reach device-code sign-in within 90 seconds.")
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
        self.assertEqual(self.config.read_text(encoding="utf-8"), self.config_content)

    @unittest.skipUnless(os.environ.get("AZ_LAUNCHER_TEST_AUTHENTICATED_CONFIG_DIR"),
                         "Requires a configuration directory authenticated by the external login lane.")
    def test_signed_in_account_show(self):
        for shadow_package in (False, True):
            with self.subTest(shadow_package=shadow_package):
                if shadow_package:
                    self._redis(shadow_package=True)
                result = self._run(
                    ("account", "show", "--output", "json"),
                    AZURE_CONFIG_DIR=os.environ["AZ_LAUNCHER_TEST_AUTHENTICATED_CONFIG_DIR"],
                )
                self.assertFalse(SHADOW_MARKER in result.stdout + result.stderr,
                                 "Local redis package was executed.")
                self.assertEqual(result.returncode, 0, "Signed-in account show failed.")
                account = json.loads(result.stdout)
                self.assertTrue(account.get("id"), "Missing signed-in subscription information.")
                self.assertTrue(account.get("user"), "Missing signed-in account information.")


if __name__ == "__main__":
    unittest.main()
