# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys
import os
import tempfile
import shutil
import zipfile
import traceback
import hashlib
from subprocess import check_output, STDOUT, CalledProcessError
import requests
from wheel.install import WHEEL_INFO_RE
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

from knack.log import get_logger

from azure.cli.core.util import CLIError
from azure.cli.core.extension import (extension_exists, get_extension_path, get_extensions,
                                      get_extension, ext_compat_with_cli,
                                      WheelExtension, ExtensionNotInstalledException)
from azure.cli.core.telemetry import set_extension_management_detail

from ._homebrew_patch import HomebrewPipPatch
from ._index import get_index_extensions
from ._resolve import resolve_from_index, NoExtensionCandidatesError

logger = get_logger(__name__)

OUT_KEY_NAME = 'name'
OUT_KEY_VERSION = 'version'
OUT_KEY_TYPE = 'extensionType'
OUT_KEY_METADATA = 'metadata'

IS_WINDOWS = sys.platform.lower() in ['windows', 'win32']
LIST_FILE_PATH = os.path.join(os.sep, 'etc', 'apt', 'sources.list.d', 'azure-cli.list')
LSB_RELEASE_FILE = os.path.join(os.sep, 'etc', 'lsb-release')


def _run_pip(pip_exec_args):
    cmd = [sys.executable, '-m', 'pip'] + pip_exec_args + ['-vv', '--disable-pip-version-check', '--no-cache-dir']
    logger.debug('Running: %s', cmd)
    try:
        log_output = check_output(cmd, stderr=STDOUT, universal_newlines=True)
        logger.debug(log_output)
        returncode = 0
    except CalledProcessError as e:
        logger.debug(e.output)
        logger.debug(e)
        returncode = e.returncode
    return returncode


def _whl_download_from_url(url_parse_result, ext_file):
    from azure.cli.core.util import should_disable_connection_verify
    url = url_parse_result.geturl()
    r = requests.get(url, stream=True, verify=(not should_disable_connection_verify()))
    if r.status_code != 200:
        raise CLIError("Request to {} failed with {}".format(url, r.status_code))
    with open(ext_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # ignore keep-alive new chunks
                f.write(chunk)


def _validate_whl_cli_compat(azext_metadata):
    is_compatible, cli_core_version, min_required, max_required = ext_compat_with_cli(azext_metadata)
    logger.debug("Extension compatibility result: is_compatible=%s cli_core_version=%s min_required=%s "
                 "max_required=%s", is_compatible, cli_core_version, min_required, max_required)
    if not is_compatible:
        min_max_msg_fmt = "The extension is not compatible with this version of the CLI.\n" \
                          "You have CLI core version {} and this extension " \
                          "requires ".format(cli_core_version)
        if min_required and max_required:
            min_max_msg_fmt += 'a min of {} and max of {}.'.format(min_required, max_required)
        elif min_required:
            min_max_msg_fmt += 'a min of {}.'.format(min_required)
        elif max_required:
            min_max_msg_fmt += 'a max of {}.'.format(max_required)
        raise CLIError(min_max_msg_fmt)


def _validate_whl_extension(ext_file):
    tmp_dir = tempfile.mkdtemp()
    zip_ref = zipfile.ZipFile(ext_file, 'r')
    zip_ref.extractall(tmp_dir)
    zip_ref.close()
    azext_metadata = WheelExtension.get_azext_metadata(tmp_dir)
    shutil.rmtree(tmp_dir)
    _validate_whl_cli_compat(azext_metadata)


def _add_whl_ext(source, ext_sha256=None, pip_extra_index_urls=None, pip_proxy=None):  # pylint: disable=too-many-statements
    if not source.endswith('.whl'):
        raise ValueError('Unknown extension type. Only Python wheels are supported.')
    url_parse_result = urlparse(source)
    is_url = (url_parse_result.scheme == 'http' or url_parse_result.scheme == 'https')
    logger.debug('Extension source is url? %s', is_url)
    whl_filename = os.path.basename(url_parse_result.path) if is_url else os.path.basename(source)
    parsed_filename = WHEEL_INFO_RE(whl_filename)
    # Extension names can have - but .whl format changes it to _ (PEP 0427). Undo this.
    extension_name = parsed_filename.groupdict().get('name').replace('_', '-') if parsed_filename else None
    if not extension_name:
        raise CLIError('Unable to determine extension name from {}. Is the file name correct?'.format(source))
    if extension_exists(extension_name):
        raise CLIError('The extension {} already exists.'.format(extension_name))
    ext_file = None
    if is_url:
        # Download from URL
        tmp_dir = tempfile.mkdtemp()
        ext_file = os.path.join(tmp_dir, whl_filename)
        logger.debug('Downloading %s to %s', source, ext_file)
        try:
            _whl_download_from_url(url_parse_result, ext_file)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            raise CLIError('Please ensure you have network connection. Error detail: {}'.format(str(err)))
        logger.debug('Downloaded to %s', ext_file)
    else:
        # Get file path
        ext_file = os.path.realpath(os.path.expanduser(source))
        if not os.path.isfile(ext_file):
            raise CLIError("File {} not found.".format(source))
    # Validate the extension
    logger.debug('Validating the extension %s', ext_file)
    if ext_sha256:
        valid_checksum, computed_checksum = is_valid_sha256sum(ext_file, ext_sha256)
        if valid_checksum:
            logger.debug("Checksum of %s is OK", ext_file)
        else:
            logger.debug("Invalid checksum for %s. Expected '%s', computed '%s'.",
                         ext_file, ext_sha256, computed_checksum)
            raise CLIError("The checksum of the extension does not match the expected value. "
                           "Use --debug for more information.")
    try:
        _validate_whl_extension(ext_file)
    except AssertionError:
        logger.debug(traceback.format_exc())
        raise CLIError('The extension is invalid. Use --debug for more information.')
    except CLIError as e:
        raise e
    logger.debug('Validation successful on %s', ext_file)
    # Check for distro consistency
    check_distro_consistency()
    # Install with pip
    extension_path = get_extension_path(extension_name)
    pip_args = ['install', '--target', extension_path, ext_file]

    if pip_proxy:
        pip_args = pip_args + ['--proxy', pip_proxy]
    if pip_extra_index_urls:
        for extra_index_url in pip_extra_index_urls:
            pip_args = pip_args + ['--extra-index-url', extra_index_url]

    logger.debug('Executing pip with args: %s', pip_args)
    with HomebrewPipPatch():
        pip_status_code = _run_pip(pip_args)
    if pip_status_code > 0:
        logger.debug('Pip failed so deleting anything we might have installed at %s', extension_path)
        shutil.rmtree(extension_path, ignore_errors=True)
        raise CLIError('An error occurred. Pip failed with status code {}. '
                       'Use --debug for more information.'.format(pip_status_code))
    # Save the whl we used to install the extension in the extension dir.
    dst = os.path.join(extension_path, whl_filename)
    shutil.copyfile(ext_file, dst)
    logger.debug('Saved the whl to %s', dst)


def is_valid_sha256sum(a_file, expected_sum):
    sha256 = hashlib.sha256()
    with open(a_file, 'rb') as f:
        sha256.update(f.read())
    computed_hash = sha256.hexdigest()
    return expected_sum == computed_hash, computed_hash


def _augment_telemetry_with_ext_info(extension_name):
    # The extension must be available before calling this otherwise we can't get the version from metadata
    if not extension_name:
        return
    try:
        ext = get_extension(extension_name)
        ext_version = ext.version
        set_extension_management_detail(extension_name, ext_version)
    except Exception:  # nopa pylint: disable=broad-except
        # Don't error on telemetry
        pass


def add_extension(source=None, extension_name=None, index_url=None, yes=None,  # pylint: disable=unused-argument
                  pip_extra_index_urls=None, pip_proxy=None):
    ext_sha256 = None
    if extension_name:
        if extension_exists(extension_name):
            raise CLIError('The extension {} already exists.'.format(extension_name))
        try:
            source, ext_sha256 = resolve_from_index(extension_name, index_url=index_url)
        except NoExtensionCandidatesError as err:
            logger.debug(err)
            raise CLIError("No matching extensions for '{}'. Use --debug for more information.".format(extension_name))
    _add_whl_ext(source, ext_sha256=ext_sha256, pip_extra_index_urls=pip_extra_index_urls, pip_proxy=pip_proxy)
    _augment_telemetry_with_ext_info(extension_name)


def remove_extension(extension_name):
    try:
        # Get the extension and it will raise an error if it doesn't exist
        get_extension(extension_name)
        # We call this just before we remove the extension so we can get the metadata before it is gone
        _augment_telemetry_with_ext_info(extension_name)
        shutil.rmtree(get_extension_path(extension_name))
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def list_extensions():
    return [{OUT_KEY_NAME: ext.name, OUT_KEY_VERSION: ext.version, OUT_KEY_TYPE: ext.ext_type}
            for ext in get_extensions()]


def show_extension(extension_name):
    try:
        extension = get_extension(extension_name)
        return {OUT_KEY_NAME: extension.name,
                OUT_KEY_VERSION: extension.version,
                OUT_KEY_TYPE: extension.ext_type,
                OUT_KEY_METADATA: extension.metadata}
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def update_extension(extension_name, index_url=None, pip_extra_index_urls=None, pip_proxy=None):
    try:
        ext = get_extension(extension_name)
        cur_version = ext.get_version()
        try:
            download_url, ext_sha256 = resolve_from_index(extension_name, cur_version=cur_version, index_url=index_url)
        except NoExtensionCandidatesError as err:
            logger.debug(err)
            raise CLIError("No updates available for '{}'. Use --debug for more information.".format(extension_name))
        # Copy current version of extension to tmp directory in case we need to restore it after a failed install.
        backup_dir = os.path.join(tempfile.mkdtemp(), extension_name)
        extension_path = get_extension_path(extension_name)
        logger.debug('Backing up the current extension: %s to %s', extension_path, backup_dir)
        shutil.copytree(extension_path, backup_dir)
        # Remove current version of the extension
        shutil.rmtree(extension_path)
        # Install newer version
        try:
            _add_whl_ext(download_url, ext_sha256=ext_sha256,
                         pip_extra_index_urls=pip_extra_index_urls, pip_proxy=pip_proxy)
            logger.debug('Deleting backup of old extension at %s', backup_dir)
            shutil.rmtree(backup_dir)
            # This gets the metadata for the extension *after* the update
            _augment_telemetry_with_ext_info(extension_name)
        except Exception as err:
            logger.error('An error occurred whilst updating.')
            logger.error(err)
            logger.debug('Copying %s to %s', backup_dir, extension_path)
            shutil.copytree(backup_dir, extension_path)
            raise CLIError('Failed to update. Rolled {} back to {}.'.format(extension_name, cur_version))
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def list_available_extensions(index_url=None):
    return get_index_extensions(index_url=index_url)


def get_lsb_release():
    try:
        with open(LSB_RELEASE_FILE, 'r') as lr:
            lsb = lr.readlines()
            desc = lsb[2]
            desc_split = desc.split('=')
            rel = desc_split[1]
            return rel.strip()
    except Exception:  # pylint: disable=broad-except
        return None


def check_distro_consistency():
    if IS_WINDOWS:
        return

    try:
        logger.debug('Linux distro check: Reading from: %s', LIST_FILE_PATH)

        with open(LIST_FILE_PATH, 'r') as list_file:
            package_source = list_file.read()
            stored_linux_dist_name = package_source.split(" ")[3]
            logger.debug('Linux distro check: Found in list file: %s', stored_linux_dist_name)
            current_linux_dist_name = get_lsb_release()
            logger.debug('Linux distro check: Reported by API: %s', current_linux_dist_name)

    except Exception as err:  # pylint: disable=broad-except
        current_linux_dist_name = None
        stored_linux_dist_name = None
        logger.debug('Linux distro check: An error occurred while checking \
linux distribution version source list consistency.')
        logger.debug(err)

    if current_linux_dist_name != stored_linux_dist_name:
        logger.warning("Linux distro check: Mismatch distribution \
name in %s file", LIST_FILE_PATH)
        logger.warning("Linux distro check: If command fails, install the appropriate package \
for your distribution or change the above file accordingly.")
        logger.warning("Linux distro check: %s has '%s', current distro is '%s'",
                       LIST_FILE_PATH, stored_linux_dist_name, current_linux_dist_name)
