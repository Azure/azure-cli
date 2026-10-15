# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Offline packaging regression tests; subprocesses and PyPI access are mocked."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from automation.utilities import packaging, path as package_paths
from automation.tests import verify_package_versions as versions
from automation.tests import verify_readme_history as readme
from automation.verify import default_modules


RUNTIME_PATHS = {
    'azure-cli': 'azure/cli/__main__.py',
    'azure-cli-core': 'azure/cli/core/__init__.py',
}


class PackageFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cli packaging tests ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, relative_path, text):
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        return target

    def package(self, name, version='1.2.3', parent='src'):
        folder = Path(parent) / name
        self.write(folder / 'pyproject.toml',
                   '[project]\nname = "{}"\nversion = "{}"\n'.format(name, version))
        if name in RUNTIME_PATHS:
            self.write(folder / RUNTIME_PATHS[name],
                       'raise AssertionError("Runtime must not be imported")\n'
                       '__version__ = "{}"\n'.format(version))
        return self.root / folder


class PackageVersionTests(PackageFixture):
    def test_static_metadata_for_all_four_distributions_without_execution(self):
        with mock.patch.object(packaging.subprocess, 'check_output') as execute:
            for name in ('azure-cli', 'azure-cli-core', 'azure-cli-telemetry', 'azure-cli-testsdk'):
                with self.subTest(name=name):
                    folder = self.package(name)
                    self.write(folder / 'setup.py', 'raise AssertionError("Do not execute")\n')
                    self.assertEqual(packaging.get_package_version(folder), '1.2.3')
            execute.assert_not_called()

    def test_metadata_read_uses_toml_not_text_matching(self):
        folder = self.package('azure-cli-telemetry')
        self.write(folder / 'pyproject.toml',
                   '# version = "wrong"\n[tool.example]\nversion = "also-wrong"\n'
                   "[project]\nname = 'azure-cli-telemetry'\nversion = '1.2.3' # comment\n")
        self.assertEqual(packaging.get_package_version(folder), '1.2.3')

    def test_tomli_fallback_when_tomllib_is_unavailable(self):
        spec = importlib.util.spec_from_file_location('packaging_fallback', packaging.__file__)
        module = importlib.util.module_from_spec(spec)
        # Exercise the import fallback without requiring both parsers installed.
        with mock.patch.dict(sys.modules, {'tomllib': None, 'tomli': packaging.tomllib}):
            spec.loader.exec_module(module)
        self.assertEqual(module.get_package_version(self.package('azure-cli-testsdk')), '1.2.3')

    def test_invalid_modern_metadata_never_falls_back_to_setup(self):
        folder = self.package('azure-cli-testsdk')
        self.write(folder / 'setup.py', '# legacy metadata must not hide invalid TOML\n')
        cases = (
            ('[project\n', 'Invalid TOML'),
            ('[project]\nname = "azure-cli-testsdk"\n', 'static'),
            ('[project]\nname = "azure-cli-testsdk"\nversion = 123\n', 'static'),
            ('[project]\nname = "azure-cli-testsdk"\nversion = ""\n', 'static'),
            ('[project]\nname = "azure-cli-testsdk"\ndynamic = ["version"]\n', 'static'),
            ('[project]\nname = "azure-cli-testsdk"\nversion = "1.2.3"\n'
             'dynamic = ["version"]\n', 'static'),
            ('[project]\nversion = "1.2.3"\n', 'name'),
        )
        with mock.patch.object(packaging.subprocess, 'check_output') as execute:
            for content, message in cases:
                with self.subTest(content=content):
                    self.write(folder / 'pyproject.toml', content)
                    with self.assertRaisesRegex(ValueError, message):
                        packaging.get_package_version(folder)
            execute.assert_not_called()

    def test_runtime_mismatch_reports_both_versions_and_paths(self):
        for name, runtime_file in RUNTIME_PATHS.items():
            with self.subTest(name=name):
                folder = self.package(name)
                self.write(folder / runtime_file, '__version__ = "9.8.7"\n')
                with self.assertRaises(ValueError) as caught:
                    packaging.get_package_version(folder)
                for detail in (name, '1.2.3', '9.8.7', str(folder / 'pyproject.toml'),
                               str(folder / runtime_file)):
                    self.assertIn(detail, str(caught.exception))

    def test_runtime_must_be_one_top_level_literal(self):
        folder = self.package('azure-cli-core')
        for content in (
                '# __version__ = "1.2.3"\n',
                '__version__ = get_version()\n',
                '__version__ = 123\n',
                '__version__: str\n',
                '__version__ = "1.2.3"\n__version__ = "1.2.3"\n',
                'def nested():\n    __version__ = "1.2.3"\n'):
            with self.subTest(content=content):
                self.write(folder / RUNTIME_PATHS['azure-cli-core'], content)
                with self.assertRaisesRegex(ValueError, 'top-level string literal __version__'):
                    packaging.get_package_version(folder)

    def test_annotated_runtime_literal_is_supported(self):
        folder = self.package('azure-cli-core')
        self.write(folder / RUNTIME_PATHS['azure-cli-core'], '__version__: str = "1.2.3"\n')
        self.assertEqual(packaging.get_package_version(folder), '1.2.3')

    def test_missing_or_invalid_runtime_source_is_not_silently_skipped(self):
        folder = self.package('azure-cli')
        runtime_file = folder / RUNTIME_PATHS['azure-cli']
        runtime_file.unlink()
        with self.assertRaisesRegex(ValueError, 'Unable to read runtime __version__'):
            packaging.get_package_version(folder)
        self.write(runtime_file, '__version__ = (\n')
        with self.assertRaisesRegex(ValueError, 'Unable to read runtime __version__'):
            packaging.get_package_version(folder)

    def test_legacy_fallback_uses_current_interpreter_and_package_directory(self):
        folder = self.root / 'legacy package'
        self.write(folder / 'setup.py', '# historical setup\n')
        with mock.patch.object(packaging.subprocess, 'check_output', return_value='1.2.3\n') as execute:
            self.assertEqual(packaging.get_package_version(folder), '1.2.3')
        execute.assert_called_once_with(
            [sys.executable, 'setup.py', '--version'], cwd=str(folder), universal_newlines=True)

    def test_missing_package_has_useful_error(self):
        with self.assertRaisesRegex(FileNotFoundError, 'No pyproject.toml or setup.py'):
            packaging.get_package_version(self.root)

    def test_historical_base_repo_comparison_retains_legacy_fallback(self):
        current = self.root / 'current'
        base = self.root / 'historical'
        relative = Path('src') / 'azure-cli'
        self.write(base / relative / 'setup.py', '# historical setup\n')
        with mock.patch.object(versions, 'get_repo_root', return_value=str(current)), \
                mock.patch.object(packaging.subprocess, 'check_output', return_value='1.2.3\n') as execute:
            self.assertTrue(versions.version_in_base_repo(
                str(base), str(current / relative), 'azure-cli', '1.2.3'))
        execute.assert_called_once_with(
            [sys.executable, 'setup.py', '--version'], cwd=str(base / relative), universal_newlines=True)

    def test_version_validator_checks_runtime_before_contacting_pypi(self):
        folder = self.package('azure-cli')
        self.write(folder / RUNTIME_PATHS['azure-cli'], '__version__ = "9.8.7"\n')
        with mock.patch.object(versions, 'is_available_on_pypi') as pypi:
            with self.assertRaisesRegex(ValueError, 'Version mismatch'):
                versions.check_package_version('azure-cli', str(folder))
            pypi.assert_not_called()


class PackageDiscoveryTests(PackageFixture):
    def test_core_discovery_includes_four_pyprojects_legacy_and_deduplicates(self):
        names = ('azure-cli', 'azure-cli-core', 'azure-cli-telemetry', 'azure-cli-testsdk')
        expected = [(name, str(self.package(name))) for name in names]
        self.write('src/azure-cli/setup.py', '# transitional package\n')
        self.write('src/legacy/setup.py', '# legacy\n')
        expected.append(('legacy', str(self.root / 'src' / 'legacy')))
        self.write('src/not-a-package/README.rst', 'Not a package\n')
        (self.root / 'src' / 'not-a-package' / 'pyproject.toml').mkdir()
        with mock.patch.object(package_paths, 'get_repo_root', return_value=str(self.root)):
            self.assertEqual(sorted(package_paths.get_core_modules_paths()), sorted(expected))

    def test_command_discovery_preserves_prefix_option_and_combined_paths(self):
        core = self.package('azure-cli-core')
        command = self.package('azure-cli-modern', parent='src/command_modules')
        self.write(command / 'setup.py', '# transitional package\n')
        legacy = self.root / 'src' / 'command_modules' / 'azure-cli-legacy'
        self.write(legacy / 'setup.py', '# legacy\n')
        self.package('not-a-command', parent='src/command_modules')
        with mock.patch.object(package_paths, 'get_repo_root', return_value=str(self.root)):
            self.assertEqual(list(package_paths.get_command_modules_paths()),
                             [('legacy', str(legacy)), ('modern', str(command))])
            prefixed = [('azure-cli-legacy', str(legacy)), ('azure-cli-modern', str(command))]
            self.assertEqual(list(package_paths.get_command_modules_paths(include_prefix=True)), prefixed)
            self.assertEqual(package_paths.get_all_module_paths(), [('azure-cli-core', str(core))] + prefixed)

    def test_default_modules_points_to_main_pyproject(self):
        self.assertEqual(Path(default_modules.AZURE_CLI_PYPROJECT),
                         Path(default_modules.AZURE_CLI_PATH) / 'pyproject.toml')


class ReleaseVersionTests(PackageFixture):
    def setUp(self):
        super().setUp()
        script = Path(__file__).resolve().parents[3] / 'scripts/ci/check_package_versions.py'
        spec = importlib.util.spec_from_file_location('check_package_versions', script)
        self.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.checker)
        self.checker.ROOT = self.root
        for name in self.checker.PACKAGES:
            self.package(name)
        with (self.root / 'src/azure-cli/pyproject.toml').open('a', encoding='utf-8') as stream:
            stream.write('dependencies = ["azure-cli-core==1.2.3"]\n')

    def test_matching_versions_pass(self):
        self.checker.main()

    def test_missing_distribution_fails(self):
        (self.root / 'src/azure-cli-testsdk/pyproject.toml').unlink()
        with self.assertRaises(FileNotFoundError):
            self.checker.main()

    def test_mismatched_core_dependency_fails(self):
        self.package('azure-cli-core', version='1.2.4')
        with self.assertRaisesRegex(ValueError, 'including the dependency'):
            self.checker.main()

    def test_nightly_versions_and_dependency_are_synchronized(self):
        for name in self.checker.PACKAGES:
            self.package(name, version='1.2.3.dev20260918000000')
        with (self.root / 'src/azure-cli/pyproject.toml').open('a', encoding='utf-8') as stream:
            stream.write('dependencies = ["azure-cli-core==1.2.3.dev20260918000000"]\n')
        self.checker.main()


class ReadmeValidationTests(PackageFixture):
    def history(self, folder, version='1.2.3'):
        self.write(folder / 'HISTORY.rst',
                   'Release History\n===============\n\n{}\n{}\n\n* Changes.\n\n'
                   '0.0.1\n-----\n\n* Initial release.\n'.format(
                       version, '-' * len(version)))

    def test_history_uses_static_source_version(self):
        folder = self.package('azure-cli-telemetry')
        self.history(folder)
        with mock.patch.object(packaging.subprocess, 'check_output') as execute:
            self.assertTrue(readme.check_history_headings(str(folder)))
            self.history(folder, '9.8.7')
            self.assertFalse(readme.check_history_headings(str(folder)))
            execute.assert_not_called()

    def test_history_retains_runtime_mismatch_validation(self):
        folder = self.package('azure-cli-core')
        self.history(folder)
        self.write(folder / RUNTIME_PATHS['azure-cli-core'], '__version__ = "9.8.7"\n')
        with self.assertRaisesRegex(ValueError, 'Version mismatch'):
            readme.check_history_headings(str(folder))

    def test_build_and_twine_use_clean_temporary_copy_and_leave_source_untouched(self):
        folder = self.package('azure-cli-telemetry')
        self.history(folder)
        self.write(folder / 'README.rst', 'Original readme\n')
        self.write(folder / 'azure/cli/telemetry/__init__.py', '# package\n')
        ignored = ('tests/recordings/large.yaml', 'build/stale.txt', 'dist/stale.tar.gz',
                   '__pycache__/stale.pyc', 'old.egg-info/PKG-INFO', '.venv/large.txt')
        for relative in ignored:
            self.write(folder / relative, 'stale\n')
        before = {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        commands = []
        working_dirs = []

        def execute(command, **kwargs):
            commands.append(command)
            source = Path(kwargs['cwd'])
            working_dirs.append(source)
            self.assertNotEqual(source, folder)
            self.assertTrue((source / 'pyproject.toml').is_file())
            if command[2] == 'build':
                self.assertEqual(command[:5], [sys.executable, '-m', 'build', '--sdist', '--outdir'])
                self.assertTrue((source / 'azure/cli/telemetry/__init__.py').is_file())
                for relative in ignored:
                    self.assertFalse((source / relative).exists())
                (source / 'README.rst').write_text('Backend changed the copy\n', encoding='utf-8')
                output = Path(command[5])
                output.mkdir()
                (output / 'azure_cli_telemetry-1.2.3.tar.gz').write_bytes(b'mocked sdist')
            else:
                self.assertEqual(command[:5], [sys.executable, '-m', 'twine', 'check', '--strict'])
                self.assertEqual(len(command), 6)
                self.assertTrue(Path(command[5]).is_file())

        with mock.patch.object(readme.subprocess, 'check_call', side_effect=execute):
            self.assertTrue(readme.check_readme_render(str(folder)))
        self.assertEqual(len(commands), 2)
        self.assertEqual(working_dirs[0], working_dirs[1])
        self.assertFalse(working_dirs[0].parent.exists())
        after = {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_failed_build_missing_sdist_and_twine_failure_are_reported_and_cleaned(self):
        folder = self.package('azure-cli-testsdk')
        for failure in ('build', 'missing-sdist', 'twine'):
            with self.subTest(failure=failure):
                working_dirs = []

                def execute(command, **kwargs):
                    working_dirs.append(Path(kwargs['cwd']))
                    if command[2] == failure:
                        raise subprocess.CalledProcessError(1, command)
                    if command[2] == 'build' and failure != 'missing-sdist':
                        output = Path(command[5])
                        output.mkdir()
                        (output / 'package-1.2.3.tar.gz').write_bytes(b'mocked sdist')

                with mock.patch.object(readme.subprocess, 'check_call', side_effect=execute) as call:
                    self.assertFalse(readme._check_sdist_render(str(folder)))
                self.assertEqual(call.call_count, 2 if failure == 'twine' else 1)
                self.assertFalse(working_dirs[0].parent.exists())


if __name__ == '__main__':
    unittest.main()