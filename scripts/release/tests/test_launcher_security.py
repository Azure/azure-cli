# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
MACOS_LAUNCHER = REPO_ROOT / 'scripts/release/macos/templates/az_launcher.sh.in'
CURL_INSTALLER = REPO_ROOT / 'scripts/curl_install_pypi/install.py'


class LauncherSecurityTest(unittest.TestCase):

    def _write_cli_package(self, site_packages, exit_code):
        cli_dir = site_packages / 'azure' / 'cli'
        cli_dir.mkdir(parents=True)
        (cli_dir.parent / '__init__.py').write_text('', encoding='utf-8')
        (cli_dir / '__init__.py').write_text('', encoding='utf-8')
        (cli_dir / '__main__.py').write_text(
            'import json, sys\n'
            'print(json.dumps(sys.argv[1:]))\n'
            f'raise SystemExit({exit_code})\n',
            encoding='utf-8',
        )

    def _write_attacker_module(self, attacker_dir):
        attacker_dir.mkdir()
        (attacker_dir / 'azure.py').write_text(
            'from pathlib import Path\n'
            'Path("PWNED").write_text("yes", encoding="utf-8")\n',
            encoding='utf-8',
        )

    def test_macos_launcher_ignores_cwd_module(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            install_dir = root / 'install'
            launcher_dir = install_dir / 'libexec' / 'bin'
            site_packages = install_dir / 'libexec' / 'lib' / \
                f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
            attacker_dir = root / 'attacker'
            launcher_dir.mkdir(parents=True)
            self._write_cli_package(site_packages, exit_code=23)
            self._write_attacker_module(attacker_dir)

            launcher = launcher_dir / 'az'
            launcher.write_text(
                MACOS_LAUNCHER.read_text(encoding='utf-8')
                .replace('{PYTHON_MAJOR_MINOR}', f'{sys.version_info.major}.{sys.version_info.minor}')
                .replace('{PYTHON_BIN}', f'python{sys.version_info.major}'),
                encoding='utf-8',
            )
            launcher.chmod(0o755)

            result = subprocess.run(
                [str(launcher), 'alpha', 'two words'],
                cwd=attacker_dir,
                env={**os.environ, 'AZ_PYTHON': sys.executable},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(23, result.returncode, result.stderr)
            self.assertEqual('["alpha", "two words"]', result.stdout.strip())
            self.assertFalse((attacker_dir / 'PWNED').exists())

    def test_curl_dispatch_ignores_cwd_module(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            install_dir = root / 'install'
            bin_dir = install_dir / 'bin'
            site_packages = install_dir / 'site-packages'
            attacker_dir = root / 'attacker'
            bin_dir.mkdir(parents=True)
            self._write_cli_package(site_packages, exit_code=31)
            self._write_attacker_module(attacker_dir)

            python_wrapper = bin_dir / 'python'
            python_wrapper.write_text(
                '#!/usr/bin/env bash\n'
                f'PYTHONPATH="{site_packages}" exec "{sys.executable}" "$@"\n',
                encoding='utf-8',
            )
            python_wrapper.chmod(0o755)

            dispatch_template = runpy.run_path(str(CURL_INSTALLER))['AZ_DISPATCH_TEMPLATE']
            launcher = root / 'az'
            launcher.write_text(dispatch_template.format(install_dir=install_dir), encoding='utf-8')
            launcher.chmod(0o755)

            result = subprocess.run(
                [str(launcher), 'alpha', 'two words'],
                cwd=attacker_dir,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(31, result.returncode, result.stderr)
            self.assertEqual('["alpha", "two words"]', result.stdout.strip())
            self.assertFalse((attacker_dir / 'PWNED').exists())

    def test_production_launchers_do_not_use_unsafe_module_entry(self):
        launcher_paths = [
            REPO_ROOT / 'src/azure-cli/az.bat',
            REPO_ROOT / 'src/azure-cli/azps.ps1',
            REPO_ROOT / 'scripts/curl_install_pypi/install.py',
            REPO_ROOT / 'scripts/release/macos/templates/az_launcher.sh.in',
            REPO_ROOT / 'scripts/release/rpm/azure-cli.spec',
            REPO_ROOT / 'src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py',
        ]

        for launcher_path in launcher_paths:
            with self.subTest(launcher_path=launcher_path):
                contents = launcher_path.read_text(encoding='utf-8')
                self.assertNotIn('-m azure.cli', contents)
                self.assertNotIn("'-m', 'azure.cli'", contents)


if __name__ == '__main__':
    unittest.main()