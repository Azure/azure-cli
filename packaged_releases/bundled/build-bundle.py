# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Script to create a bundled archive that can be used to install a fully self-contained instance of the CLI.
"""

from __future__ import print_function

import os
import sys
import tarfile
import tempfile
import hashlib
import glob
import subprocess
import shutil
try:
    # Attempt to load python 3 module
    from urllib.request import urlretrieve
except ImportError:
    # Import python 2 version
    from urllib import urlretrieve

try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

CLI_VERSION = os.getenv('CLI_VERSION')
CLI_SOURCE_ARCHIVE_SHA256 = os.getenv('CLI_DOWNLOAD_SHA256')

assert CLI_VERSION and CLI_SOURCE_ARCHIVE_SHA256, 'Set env vars CLI_VERSION and CLI_DOWNLOAD_SHA256'

CLI_SOURCE_ARCHIVE_URL = 'https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_{}.tar.gz'.format(CLI_VERSION)
COMPLETION_FILE_NAME = 'az.completion'
ARCHIVE_FILE_TMPL = 'azure-cli_bundle_{}'
INSTALLER_FILE_NAME = 'installer'

VIRTUALENV_VERSION = '15.0.0'
VIRTUALENV_ARCHIVE = 'virtualenv-'+VIRTUALENV_VERSION+'.tar.gz'
VIRTUALENV_DOWNLOAD_URL = 'https://pypi.python.org/packages/source/v/virtualenv/'+VIRTUALENV_ARCHIVE
VIRTUALENV_ARCHIVE_SHA256 = '70d63fb7e949d07aeb37f6ecc94e8b60671edb15b890aa86dba5dfaf2225dc19'

PLATFORM_SPECIFIC_DEPENDENCIES = [
    ('cryptography', '1.8.1'),
    ('cffi', '1.10.0'),
    ('SecretStorage', '2.3.1'),
    ('pywin32-ctypes', '0.0.1'),
]

def _error_exit(msg):
    print('ERROR: '+msg, file=sys.stderr)
    sys.exit(1)

def _print_status(msg=''):
    print('-- '+msg)

def _get_tmp_dir():
    return tempfile.mkdtemp()

def _get_tmp_file():
    return tempfile.mkstemp()[1]

def _create_dir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)

def _is_valid_sha256sum(a_file, expected_sum):
    sha256 = hashlib.sha256()
    with open(a_file, 'rb') as f:
        sha256.update(f.read())
    computed_hash = sha256.hexdigest()
    return expected_sum == computed_hash

def _exec_command(command_list, cwd=None, stdout=None):
    """Returns True in the command was executed successfully"""
    try:
        _print_status('Executing {}'.format(command_list))
        subprocess.check_call(command_list, stdout=stdout, cwd=cwd)
        return True
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)
        return False

def _build_package(path_to_package, dist_dir):
    cmd_success = _exec_command(['python', 'setup.py', 'bdist_wheel', '-d', dist_dir], cwd=path_to_package)
    if not cmd_success:
        _error_exit('Error building {}.'.format(path_to_package))

def get_source():
    """ Download and extract the CLI source archive. """
    source_dir = _get_tmp_dir()
    downloaded_archive, _ = urlretrieve(CLI_SOURCE_ARCHIVE_URL, _get_tmp_file())
    if not _is_valid_sha256sum(downloaded_archive, CLI_SOURCE_ARCHIVE_SHA256):
        _error_exit("The checksum of {} does not match the expected {}.".format(CLI_SOURCE_ARCHIVE_URL, CLI_SOURCE_ARCHIVE_SHA256))
    package_tar = tarfile.open(downloaded_archive)
    package_tar.extractall(path=source_dir)
    package_tar.close()
    # The archive creates one wrapper directory so go one level deeper
    return os.path.join(source_dir, os.listdir(source_dir)[0])

def build_packages(source_dir):
    dist_dir = _get_tmp_dir()
    packages_to_build = [
        os.path.join(source_dir, 'src', 'azure-cli'),
        os.path.join(source_dir, 'src', 'azure-cli-core'),
        os.path.join(source_dir, 'src', 'azure-cli-nspkg'),
        os.path.join(source_dir, 'src', 'azure-cli-command_modules-nspkg')
    ]
    packages_to_build.extend(glob.glob(os.path.join(source_dir, 'src', 'command_modules', 'azure-cli-*')))
    for p in packages_to_build:
        _build_package(p, dist_dir)
    return dist_dir

def _add_platform_dep_packages(packages_dest):
    """ Install all platform specific dependencies. """
    for dep in PLATFORM_SPECIFIC_DEPENDENCIES:
        client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
        pypi_hits = client.release_urls(dep[0], dep[1])
        for h in pypi_hits:
            dest = os.path.join(packages_dest, h['filename'])
            if not os.path.isfile(dest):
                urlretrieve(h['url'], dest)
                _print_status('Downloaded {}'.format(h['filename']))

def _get_pip_args(python, cli_packages, cli_dist_dir, packages_dest):
    args = [python, '-m', 'pip', 'download']
    args.extend([os.path.join(cli_dist_dir, p) for p in cli_packages])
    args.extend(['--dest', packages_dest])
    return args

def add_packages_to_bundle(bundle_working_dir, cli_dist_dir):
    """ Add the CLI packages (and all dependencies) to bundle """
    cli_packages = os.listdir(cli_dist_dir)
    packages_dest = os.path.join(bundle_working_dir, 'packages')
    _exec_command(_get_pip_args('python', cli_packages, cli_dist_dir, packages_dest))
    _exec_command(_get_pip_args('python3', cli_packages, cli_dist_dir, packages_dest))
    # 'pip download' only downloads packages for current platform. But we need all..
    # There isn't a way to get pip to download the union of all dependencies required for all platforms.
    # So we do this instead.
    # see https://github.com/pypa/pip/pull/4423, https://github.com/pypa/pip/issues/4304
    # https://github.com/pypa/pip/issues/4289
    _add_platform_dep_packages(packages_dest)

def add_completion_to_bundle(bundle_working_dir, cli_source_dir):
    src = os.path.join(cli_source_dir, COMPLETION_FILE_NAME)
    dest = os.path.join(bundle_working_dir, COMPLETION_FILE_NAME)
    shutil.copy(src, dest)

def add_install_script_to_bundle(bundle_working_dir):
    src = os.path.join(os.path.dirname(os.path.realpath(__file__)), INSTALLER_FILE_NAME)
    dest = os.path.join(bundle_working_dir, INSTALLER_FILE_NAME)
    shutil.copy(src, dest)
    os.chmod(dest, 0o777)

def add_virtualenv_to_bundle(bundle_working_dir):
    dest = os.path.join(bundle_working_dir, 'virtualenv.tar.gz')
    downloaded_file, _ = urlretrieve(VIRTUALENV_DOWNLOAD_URL, dest)
    if not _is_valid_sha256sum(downloaded_file, VIRTUALENV_ARCHIVE_SHA256):
        _error_exit("The checksum of {} does not match the expected {}.".format(VIRTUALENV_DOWNLOAD_URL, VIRTUALENV_ARCHIVE_SHA256))

def archive_bundle(bundle_working_dir):
    archive_filename = ARCHIVE_FILE_TMPL.format(CLI_VERSION)
    archive_dest = _get_tmp_dir()
    archive_path = os.path.join(archive_dest, archive_filename+'.tar.gz')
    with tarfile.open(archive_path, 'w:gz') as tar:
        tar.add(bundle_working_dir, arcname=archive_filename)
    return archive_path

def build_bundle():
    bundle = _get_tmp_dir()
    _print_status('Bundle working dir is {}'.format(bundle))
    cli_source_dir = get_source()
    _print_status('Source downloaded to {}'.format(cli_source_dir))
    cli_dist_dir = build_packages(cli_source_dir)
    _print_status('Built CLI packages to {}'.format(cli_dist_dir))
    add_packages_to_bundle(bundle, cli_dist_dir)
    _print_status('Added CLI packages and dependencies to working dir {}'.format(bundle))
    add_completion_to_bundle(bundle, cli_source_dir)
    _print_status('Added completion file to working dir {}'.format(bundle))
    add_install_script_to_bundle(bundle)
    _print_status('Added install script file to working dir {}'.format(bundle))
    add_virtualenv_to_bundle(bundle)
    _print_status('Added virtualenv to working dir {}'.format(bundle))
    archived_bundle = archive_bundle(bundle)
    return archived_bundle

if __name__ == '__main__':
    archive = build_bundle()
    print("Archive saved to {}".format(archive))
    print("Done.")
