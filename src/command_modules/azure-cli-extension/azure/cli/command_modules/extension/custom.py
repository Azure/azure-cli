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
from subprocess import check_output, STDOUT, CalledProcessError

import requests
from wheel.install import WHEEL_INFO_RE

from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

from azure.cli.core.util import CLIError
from azure.cli.core.extension import (extension_exists, get_extension_path, get_extensions,
                                      get_extension, ext_compat_with_cli,
                                      WheelExtension, ExtensionNotInstalledException)
import azure.cli.core.azlogging as azlogging

from ._homebrew_patch import HomebrewPipPatch


logger = azlogging.get_az_logger(__name__)

OUT_KEY_NAME = 'name'
OUT_KEY_VERSION = 'version'
OUT_KEY_TYPE = 'extensionType'
OUT_KEY_METADATA = 'metadata'


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
    url = url_parse_result.geturl()
    r = requests.get(url, stream=True)
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


def _add_whl_ext(source):  # pylint: disable=too-many-statements
    url_parse_result = urlparse(source)
    is_url = (url_parse_result.scheme == 'http' or url_parse_result.scheme == 'https')
    logger.debug('Extension source is url? %s', is_url)
    whl_filename = os.path.basename(url_parse_result.path) if is_url else os.path.basename(source)
    parsed_filename = WHEEL_INFO_RE(whl_filename)
    extension_name = parsed_filename.groupdict().get('name') if parsed_filename else None
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
    logger.debug('Validating the extension {}'.format(ext_file))
    try:
        _validate_whl_extension(ext_file)
    except AssertionError:
        logger.debug(traceback.format_exc())
        raise CLIError('The extension is invalid. Use --debug for more information.')
    except CLIError as e:
        raise e
    logger.debug('Validation successful on {}'.format(ext_file))
    # Install with pip
    extension_path = get_extension_path(extension_name)
    pip_args = ['install', '--target', extension_path, ext_file]
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


def add_extension(source):
    if source.endswith('.whl'):
        _add_whl_ext(source)
    else:
        raise ValueError('Unknown extension type. Only Python wheels are supported.')


def remove_extension(extension_name):
    try:
        get_extension(extension_name)
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
