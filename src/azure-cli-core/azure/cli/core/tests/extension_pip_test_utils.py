# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Small, generated distributions for exercising extension installation with offline pip."""

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import zipfile
from unittest import mock

from azure.cli.core import _session, extension


EXTENSION_NAME = 'azcli-extension-pip-test'
EXTENSION_MODULE = 'azext_pip_test'
DEPENDENCY_NAME = 'azcli-extension-test-dependency'
DEPENDENCY_MODULE = 'azcli_extension_test_dependency'
BACKEND_NAME = 'azcli-extension-test-backend'
BACKEND_MODULE = 'azcli_extension_test_backend'
BUILD_LOG_ENV = 'AZCLI_EXTENSION_TEST_BUILD_LOG'
SENTINEL_ENV = 'AZCLI_EXTENSION_TEST_SENTINEL'

# This backend is installed only as a build requirement, never alongside the extension.
_BACKEND_SOURCE = '''
import json
import os
from pathlib import Path
import sys
import zipfile


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    fixture = json.loads(Path('fixture.json').read_text(encoding='utf-8'))
    observation = {
        'backend_file': __file__,
        'executable': sys.executable,
        'path': sys.path,
        'pythonpath': os.environ.get('PYTHONPATH'),
        'sentinel': os.environ.get('AZCLI_EXTENSION_TEST_SENTINEL'),
        'http_proxy': os.environ.get('HTTP_PROXY'),
        'https_proxy': os.environ.get('HTTPS_PROXY'),
    }
    Path(os.environ['AZCLI_EXTENSION_TEST_BUILD_LOG']).write_text(
        json.dumps(observation), encoding='utf-8')
    if fixture['unsupported']:
        raise RuntimeError('Synthetic source build is unsupported')
    with zipfile.ZipFile(Path(wheel_directory) / fixture['wheel'], 'w') as wheel:
        for path in sorted(Path('wheel').rglob('*')):
            if path.is_file():
                wheel.writestr(path.relative_to('wheel').as_posix(), path.read_bytes())
    return fixture['wheel']
'''


def _wheel_files(name, version, files, requirements=()):
    dist_info = '{}-{}.dist-info'.format(name.replace('-', '_'), version)
    contents = {path: text.encode('utf-8') for path, text in files.items()}
    contents[dist_info + '/METADATA'] = (
        'Metadata-Version: 2.1\nName: {}\nVersion: {}\n'.format(name, version) +
        ''.join('Requires-Dist: {}\n'.format(requirement) for requirement in requirements) + '\n'
    ).encode('utf-8')
    contents[dist_info + '/WHEEL'] = (
        b'Wheel-Version: 1.0\nGenerator: extension-pip-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n'
    )
    record = io.StringIO()
    writer = csv.writer(record, lineterminator='\n')
    for path, data in contents.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode('ascii')
        writer.writerow((path, 'sha256=' + digest, len(data)))
    writer.writerow((dist_info + '/RECORD', '', ''))
    contents[dist_info + '/RECORD'] = record.getvalue().encode('utf-8')
    return contents


def _write_wheel(directory, name, version, files, requirements=()):
    path = directory / '{}-{}-py3-none-any.whl'.format(name.replace('-', '_'), version)
    with zipfile.ZipFile(path, 'w') as wheel:
        for filename, data in _wheel_files(name, version, files, requirements).items():
            wheel.writestr(filename, data)
    return path


class ExtensionPipFixture:
    """Own the local packages, extension targets and restored environment for one test."""

    def __init__(self, testcase):
        directory = tempfile.TemporaryDirectory(prefix='azure-cli-extension-pip-')
        testcase.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.links = self.root / 'links'
        self.links.mkdir()
        self.user_dir = self.root / 'user'
        self.system_dir = self.root / 'system'
        self.build_log = self.root / 'build.json'
        scratch = self.root / 'scratch'
        scratch.mkdir()

        # Ignore caller pip configuration (including constraints and binary policy), not other environment.
        environment = {key: value for key, value in os.environ.items() if not key.startswith('PIP_')}
        environment.update({
            'PIP_NO_INDEX': '1',
            'PIP_FIND_LINKS': self.links.as_uri(),
            'PIP_CONFIG_FILE': os.devnull,
            'PIP_NO_INPUT': '1',
            'PIP_PROGRESS_BAR': 'off',
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONNOUSERSITE': '1',
            'TMPDIR': str(scratch),
            'TEMP': str(scratch),
            'TMP': str(scratch),
            'AZURE_CONFIG_DIR': str(self.root / 'config'),
            BUILD_LOG_ENV: str(self.build_log),
            SENTINEL_ENV: 'inherited-by-pip-and-build-backend',
        })
        for patcher in (
            mock.patch.dict(os.environ, environment, clear=True),
            mock.patch.object(tempfile, 'tempdir', str(scratch)),
            mock.patch.object(extension, 'EXTENSIONS_DIR', str(self.user_dir)),
            mock.patch.object(extension, 'EXTENSIONS_SYS_DIR', str(self.system_dir)),
            mock.patch.object(extension, 'DEV_EXTENSION_SOURCES', []),
            mock.patch('azure.cli.core.util.handle_version_update'),
            mock.patch('azure.cli.core.extension._homebrew_patch.is_homebrew', return_value=False),
        ):
            patcher.start()
            testcase.addCleanup(patcher.stop)
        for session in vars(_session).values():
            if isinstance(session, _session.Session):
                for attribute, value in (('filename', None), ('data', {})):
                    patcher = mock.patch.object(session, attribute, value)
                    patcher.start()
                    testcase.addCleanup(patcher.stop)

        _write_wheel(self.links, BACKEND_NAME, '1.0', {BACKEND_MODULE + '.py': _BACKEND_SOURCE})
        self.dependency_wheel = _write_wheel(
            self.links, DEPENDENCY_NAME, '1.0', {DEPENDENCY_MODULE + '/__init__.py': "__version__ = '1.0'\n"})
        self.make_sdist()
        self.extension_wheel = self.make_extension()

    def make_extension(self, requirement='>=1.0'):
        return _write_wheel(self.links, EXTENSION_NAME, '1.0', {
            EXTENSION_MODULE + '/__init__.py': '',
            EXTENSION_MODULE + '/azext_metadata.json': '{"azext.isPreview": false}',
        }, [DEPENDENCY_NAME + requirement])

    def make_sdist(self, unsupported=False):
        name = DEPENDENCY_NAME.replace('-', '_')
        files = {
            'wheel/' + path: data for path, data in _wheel_files(
                DEPENDENCY_NAME, '2.0', {DEPENDENCY_MODULE + '/__init__.py': "__version__ = '2.0'\n"}
            ).items()
        }
        files['pyproject.toml'] = (
            '[build-system]\nrequires = ["{}==1.0"]\nbuild-backend = "{}"\n'.format(BACKEND_NAME, BACKEND_MODULE)
        ).encode('utf-8')
        files['fixture.json'] = json.dumps({
            'wheel': name + '-2.0-py3-none-any.whl',
            'unsupported': unsupported,
        }).encode('utf-8')
        path = self.links / (name + '-2.0.tar.gz')
        with tarfile.open(path, 'w:gz') as sdist:
            for filename, data in files.items():
                info = tarfile.TarInfo(name + '-2.0/' + filename)
                info.size = len(data)
                sdist.addfile(info, io.BytesIO(data))
        return path

    def target(self, system=False):
        return (self.system_dir if system else self.user_dir) / EXTENSION_NAME
