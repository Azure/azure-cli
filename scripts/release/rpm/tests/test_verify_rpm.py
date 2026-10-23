# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Shell-contract tests, not Fedora/RPM integration or publication verification."""

import os
from pathlib import Path
import shutil
import subprocess
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "verify_rpm_in_docker.sh"
VERSION = "2.86.0"
RELEASE = "1.fc44"
REPOSITORY = "maintainer-acceptance"
RPM_ROW = f"azure-cli|{VERSION}|{RELEASE}|x86_64"
REPO_ROW = f"{RPM_ROW}|{REPOSITORY}"

# Source the real script in a fresh Bash process. Function stubs, including the
# absolute az path, avoid writing executables, logs, repos or keys on the host.
HARNESS = r"""
trace() {
    printf '\036'
    printf '%s\037' "$@"
    printf '\036'
} >&2
reply() {
    if [[ "$STUB_FAIL" == "$1" ]]; then
        printf 'stub failure: %s\n' "$1" >&2
        return 41
    fi
    printf '%s\n' "$2"
}
installed=0
rpm() {
    trace rpm "$@"
    case "$1" in
        -qa) reply preflight "$STUB_PREINSTALLED" ;;
        --eval) reply arch "$STUB_ARCH" ;;
        -q)
            [[ "$installed" == 1 ]] || return 97
            reply rpm-query "$STUB_RPM"
            ;;
        -qf) reply owner "$STUB_OWNER" ;;
        --import) reply import "" ;;
        *) return 97 ;;
    esac
}
dnf5() {
    trace dnf5 "$@"
    case " $* " in
        *" --available "*) reply available "$STUB_AVAILABLE" ;;
        *" --installed "*) reply installed-origin "$STUB_ORIGIN" ;;
        *" install "*)
            if [[ "$STUB_FAIL" == signature ]]; then
                echo "signature verification failed" >&2
                return 42
            fi
            reply install ""
            installed=1
            if [[ "$STUB_SHADOW_AFTER" == 1 ]]; then
                az() { trace az "$@"; return 97; }
            fi
            ;;
        *) return 97 ;;
    esac
}
function /usr/bin/az() {
    trace /usr/bin/az "$@"
    case "$1" in
        version) reply cli-version "$STUB_CLI_VERSION" ;;
        --version) reply cli-banner "" ;;
        self-test) reply self-test "" ;;
        *) return 97 ;;
    esac
}
if [[ "$STUB_PATH_CLI" == 1 || ${RPM_REPOSITORY_ID+x} != x ]]; then
    az() {
        trace az "$@"
        printf '  "azure-cli": "%s",\n' "$STUB_CLI_VERSION"
    }
fi
yum() { trace yum "$@"; reply legacy-install ""; }
sh() { trace sh "$@"; }
sleep() { trace sleep "$@"; }
sed() { "$STUB_SED" "$@"; }
source "$1"
"""


class VerifyRpmTests(unittest.TestCase):
    def run_script(self, success=True, **overrides):
        bash = shutil.which("bash")
        sed = shutil.which("sed")
        self.assertIsNotNone(bash, "These shell tests require Bash.")
        self.assertIsNotNone(sed, "The legacy verifier requires sed.")
        env = {
            # No real package command or az can be found through PATH.
            "PATH": os.devnull,
            "LC_ALL": "C",
            "RPM_REPOSITORY_ID": REPOSITORY,
            "CLI_VERSION": VERSION,
            "RPM_RELEASE": RELEASE,
            "STUB_ARCH": "x86_64",
            "STUB_PREINSTALLED": "",
            "STUB_AVAILABLE": REPO_ROW,
            "STUB_RPM": RPM_ROW,
            "STUB_ORIGIN": REPO_ROW,
            "STUB_OWNER": RPM_ROW,
            "STUB_CLI_VERSION": VERSION,
            "STUB_FAIL": "",
            "STUB_PATH_CLI": "0",
            "STUB_SHADOW_AFTER": "0",
            "STUB_SED": sed,
        }
        for key, value in overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        result = subprocess.run(
            [bash, "--noprofile", "--norc", "-c", HARNESS, "verify-rpm-test", str(SCRIPT)],
            cwd=os.environ.get("TMPDIR", SCRIPT.parent),
            env=env, capture_output=True, text=True, timeout=10, check=False,
        )
        commands = [
            tuple(record.split("\x1f")[:-1])
            for record in result.stderr.split("\x1e")[1::2]
        ]
        diagnostic = (result.stdout + result.stderr).replace("\x1e", "\n").replace("\x1f", " ")
        self.assertEqual(result.returncode == 0, success, diagnostic)
        return result, commands

    def test_selected_repository_and_native_architecture(self):
        for arch in ("x86_64", "aarch64"):
            with self.subTest(arch=arch):
                row = f"azure-cli|{VERSION}|{RELEASE}|{arch}"
                result, commands = self.run_script(
                    STUB_ARCH=arch, STUB_AVAILABLE=f"{row}|{REPOSITORY}",
                    STUB_RPM=row, STUB_ORIGIN=f"{row}|{REPOSITORY}", STUB_OWNER=row,
                )
                package = f"azure-cli-{VERSION}-{RELEASE}.{arch}"
                self.assertIn(f"Verified {package}", result.stdout)
                self.assertEqual(commands[0], ("rpm", "-qa", "azure-cli", "--queryformat", "%{NAME}\\n"))
                self.assertEqual(commands[1], ("rpm", "--eval", "%{_arch}"))
                queries = [cmd for cmd in commands if cmd[0] == "dnf5"]
                self.assertEqual(len(queries), 3)
                available, install, installed = queries
                self.assertIn("--refresh", available)
                self.assertIn(f"--repo={REPOSITORY}", available)
                self.assertIn("--available", available)
                self.assertEqual(available[-1], package)
                self.assertEqual(available[available.index("--queryformat") + 1],
                                 "%{name}|%{version}|%{release}|%{arch}|%{repoid}\\n")
                self.assertIn(f"--from-repo={REPOSITORY}", install)
                self.assertIn("--assumeyes", install)
                self.assertEqual(install[-1], package)
                self.assertFalse(any(arg.startswith(("--repo=", "--enable-repo=", "--disable-repo="))
                                     for arg in install))
                self.assertIn("--installed", installed)
                self.assertEqual(installed[installed.index("--queryformat") + 1],
                                 "%{name}|%{version}|%{release}|%{arch}|%{from_repo}\\n")
                gpg_options = {"--setopt=gpgcheck=1", "--setopt=*.gpgcheck=1",
                               f"--setopt={REPOSITORY}.gpgcheck=1"}
                for command in queries:
                    self.assertTrue(gpg_options.issubset(command))
                    self.assertFalse({"--nogpgcheck", "--no-gpgchecks"}.intersection(command))
                    self.assertFalse(any("repo_gpgcheck=" in arg for arg in command))
                self.assertEqual(commands[-4],
                                 ("rpm", "-qf", "--queryformat", "%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}\\n",
                                  "/usr/bin/az"))
                self.assertEqual(commands[-3:], [
                    ("/usr/bin/az", "version", "--query", '"azure-cli"', "-o", "tsv"),
                    ("/usr/bin/az", "--version"), ("/usr/bin/az", "self-test"),
                ])
                self.assertFalse(any(cmd[0] in ("yum", "sh", "sleep", "az") for cmd in commands))

    def test_missing_or_wrong_available_package(self):
        rows = ("", REPO_ROW.replace(VERSION, "2.0.0"), REPO_ROW.replace(RELEASE, "1.fc43"),
                REPO_ROW.replace("x86_64", "noarch"), REPO_ROW.replace("azure-cli", "other-cli"),
                REPO_ROW.replace(REPOSITORY, "fedora"), REPO_ROW.replace(REPOSITORY, "other-feed"),
                REPO_ROW + "\n" + REPO_ROW)
        for row in rows:
            with self.subTest(row=row):
                result, commands = self.run_script(success=False, STUB_AVAILABLE=row)
                self.assertIn("not available", result.stderr)
                self.assertEqual(len(commands), 3)
                self.assertIn("--available", commands[-1])

    def test_preinstalled_rpm_or_path_cli_is_rejected(self):
        for override in ({"STUB_PREINSTALLED": "azure-cli"}, {"STUB_PATH_CLI": "1"}):
            with self.subTest(override=override):
                result, commands = self.run_script(success=False, **override)
                self.assertIn("clean container", result.stderr)
                self.assertEqual(len(commands), 1)
                self.assertEqual(commands[0][0], "rpm")

    def test_installed_rpm_origin_and_owner_must_match(self):
        for key, expected in (("STUB_RPM", RPM_ROW), ("STUB_ORIGIN", REPO_ROW), ("STUB_OWNER", RPM_ROW)):
            rows = ("", expected.replace("azure-cli", "other-cli"), expected.replace(VERSION, "2.0.0"),
                    expected.replace(RELEASE, "1.el9"), expected.replace("x86_64", "aarch64"),
                    expected + "\n" + expected)
            if key == "STUB_ORIGIN":
                rows += (expected.replace(REPOSITORY, "fedora"), expected.replace(REPOSITORY, "@System"))
            for row in rows:
                with self.subTest(key=key, row=row):
                    _, commands = self.run_script(success=False, **{key: row})
                    self.assertFalse(any(cmd[0] == "/usr/bin/az" for cmd in commands))

    def test_cli_version_must_match(self):
        for version in ("", "2.0.0", VERSION + "\n" + VERSION):
            with self.subTest(version=version):
                result, commands = self.run_script(success=False, STUB_CLI_VERSION=version)
                self.assertIn("different CLI version", result.stderr)
                self.assertEqual(commands[-1],
                                 ("/usr/bin/az", "version", "--query", '"azure-cli"', "-o", "tsv"))

    def test_command_and_signature_failures_stop_immediately(self):
        _, successful_commands = self.run_script()
        stages = ("preflight", "arch", "available", "install", "rpm-query", "installed-origin",
                  "owner", "cli-version", "cli-banner", "self-test")
        self.assertEqual(len(successful_commands), len(stages))
        for index, stage in enumerate(stages):
            with self.subTest(stage=stage):
                result, commands = self.run_script(success=False, STUB_FAIL=stage)
                self.assertEqual(result.returncode, 41)
                self.assertEqual(commands, successful_commands[:index + 1])
        result, commands = self.run_script(success=False, STUB_FAIL="signature")
        self.assertEqual(result.returncode, 42)
        self.assertIn("signature verification failed", result.stderr)
        self.assertEqual(commands, successful_commands[:4])

    def test_invalid_inputs_fail_before_any_commands(self):
        for key, valid in (("RPM_REPOSITORY_ID", REPOSITORY), ("CLI_VERSION", VERSION), ("RPM_RELEASE", RELEASE)):
            values = ("", "-option", valid + "*", valid + "?", "[" + valid + "]", valid + ",other",
                      valid + "\n", valid + "\r", valid + "\tother", valid + " other", valid + "/other",
                      valid + ";false")
            if key != "RPM_REPOSITORY_ID":
                values += (None,)
            for value in values:
                with self.subTest(key=key, value=value):
                    result, commands = self.run_script(success=False, **{key: value})
                    self.assertIn(key, result.stderr)
                    self.assertEqual(commands, [])
        for release in ("1.fc43", "1.el9"):
            with self.subTest(release=release):
                _, commands = self.run_script(success=False, RPM_RELEASE=release)
                self.assertEqual(commands, [])

    def test_invalid_native_architecture(self):
        for arch in ("", "%{_arch}", "*", "x86_64\naarch64"):
            with self.subTest(arch=arch):
                _, commands = self.run_script(success=False, STUB_ARCH=arch)
                self.assertEqual(len(commands), 2)
                self.assertEqual(commands[-1][0], "rpm")

    def test_postinstall_path_shadow_cannot_satisfy_verification(self):
        _, commands = self.run_script(STUB_SHADOW_AFTER="1")
        self.assertFalse(any(cmd[0] == "az" for cmd in commands))

    def test_legacy_interface_when_selector_is_unset(self):
        result, commands = self.run_script(RPM_REPOSITORY_ID=None, RPM_RELEASE=None)
        self.assertIn("Latest package is verified.", result.stdout)
        self.assertEqual(commands[0], ("rpm", "--import", "https://packages.microsoft.com/keys/microsoft.asc"))
        self.assertEqual(commands[1][:2], ("sh", "-c"))
        self.assertIn("gpgcheck=1", commands[1][2])
        self.assertIn("> /etc/yum.repos.d/azure-cli.repo", commands[1][2])
        self.assertEqual(commands[2:], [("yum", "install", "azure-cli", "-y"), ("az", "version")])

    def test_legacy_retry_and_failure_behavior(self):
        for version, attempts in (("", 4), ("2.0.0", 1)):
            with self.subTest(version=version):
                _, commands = self.run_script(success=False, RPM_REPOSITORY_ID=None, STUB_CLI_VERSION=version)
                self.assertEqual(commands.count(("yum", "install", "azure-cli", "-y")), attempts)
                self.assertEqual(commands.count(("sleep", "300")), 4 if version == "" else 0)
        self.run_script(RPM_REPOSITORY_ID=None, STUB_FAIL="legacy-install")


if __name__ == "__main__":
    unittest.main()
