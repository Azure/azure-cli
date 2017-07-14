# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import shutil
import logging

import requests
from wheel.install import WHEEL_INFO_RE

from six import StringIO
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

from azure.cli.core.util import CLIError
from azure.cli.core.extension import (extension_exists, get_extension_path, get_extensions,
                                      get_extension, ExtensionNotInstalledException)

import azure.cli.core.azlogging as azlogging


logger = azlogging.get_az_logger(__name__)

OUT_KEY_NAME = 'name'
OUT_KEY_VERSION = 'version'
OUT_KEY_TYPE = 'extensionType'
OUT_KEY_METADATA = 'metadata'


def _run_pip(pip, pip_exec_args):
    log_stream = StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_handler.setFormatter(logging.Formatter('%(name)s : %(message)s'))
    pip.logger.handlers = []
    pip.logger.addHandler(log_handler)
    # Don't propagate to root logger as we catch the pip logs in our own log stream
    pip.logger.propagate = False
    logger.debug('Running pip: %s %s', pip, pip_exec_args)
    status_code = pip.main(pip_exec_args)
    log_output = log_stream.getvalue()
    logger.debug(log_output)
    log_stream.close()
    if status_code > 0:
        raise CLIError('An error occurred. Use --debug for more information.')


def _whl_download_from_url(url_parse_result, ext_file):
    url = url_parse_result.geturl()
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        raise CLIError("Request to {} failed with {}".format(url, r.status_code))
    with open(ext_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # ignore keep-alive new chunks
                f.write(chunk)


def _add_whl_ext(source):
    import pip
    url_parse_result = urlparse(source)
    is_url = (url_parse_result.scheme == 'http' or url_parse_result.scheme == 'https')
    logger.debug('Extension source is url? %s', is_url)
    whl_filename = os.path.basename(url_parse_result.path) if is_url else os.path.basename(source)
    parsed_filename = WHEEL_INFO_RE(whl_filename)
    extension_name = parsed_filename.groupdict().get('name') if parsed_filename else None
    if not extension_name:
        raise CLIError('Unable to determine extension name from {}'.format(source))
    if extension_exists(extension_name):
        raise CLIError('The extension {} already exists.'.format(extension_name))
    ext_file = None
    if is_url:
        # Download from URL
        tmp_dir = tempfile.mkdtemp()
        ext_file = os.path.join(tmp_dir, whl_filename)
        logger.debug('Downloading %s to %s', source, ext_file)
        _whl_download_from_url(url_parse_result, ext_file)
        logger.debug('Downloaded to %s', ext_file)
    else:
        # Get file path
        ext_file = os.path.realpath(os.path.expanduser(source))
        if not os.path.isfile(ext_file):
            raise CLIError("File {} not found.".format(source))
    # Install with pip
    pip_args = ['install', '--target', get_extension_path(extension_name), ext_file]
    logger.debug('Executing pip with args: %s', pip_args)
    _run_pip(pip, pip_args)
    # Save the whl we used to install the extension in the extension dir.
    dst = os.path.join(get_extension_path(extension_name), whl_filename)
    shutil.copyfile(ext_file, dst)
    logger.debug('Saved the whl to %s', dst)


def add_extension(source):
    if source.endswith('.whl'):
        _add_whl_ext(source)
    else:
        raise CLIError('Unknown extension type. Only Python wheels are supported.')


def remove_extension(extension_name):
    try:
        get_extension(extension_name)
        shutil.rmtree(get_extension_path(extension_name))
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def list_extensions():
    extensions = []
    for ext in get_extensions():
        extensions.append({OUT_KEY_NAME: ext.name,
                           OUT_KEY_VERSION: ext.version,
                           OUT_KEY_TYPE: ext.ext_type})
    return extensions


def show_extension(extension_name):
    try:
        extension = get_extension(extension_name)
        return {OUT_KEY_NAME: extension.name,
                OUT_KEY_VERSION: extension.version,
                OUT_KEY_TYPE: extension.ext_type,
                OUT_KEY_METADATA: extension.metadata}
    except ExtensionNotInstalledException as e:
        raise CLIError(e)
