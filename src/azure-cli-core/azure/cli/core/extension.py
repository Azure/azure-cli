# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import traceback
import json

from wheel.install import WHEEL_INFO_RE

import azure.cli.core.azlogging as azlogging

from azure.cli.core._config import GLOBAL_CONFIG_DIR


_CUSTOM_EXT_DIR = os.environ.get('AZURE_EXTENSION_DIR')
EXTENSIONS_DIR = os.path.expanduser(_CUSTOM_EXT_DIR) if _CUSTOM_EXT_DIR \
                    else os.path.join(GLOBAL_CONFIG_DIR, 'cliextensions')
EXTENSIONS_MOD_PREFIX = 'azext_'

logger = azlogging.get_az_logger(__name__)

logger.debug("Extension directory: '%s'", EXTENSIONS_DIR)


class ExtensionNotInstalledException(Exception):
    def __init__(self, extension_name):
        super(ExtensionNotInstalledException, self).__init__(extension_name)
        self.extension_name = extension_name

    def __str__(self):
        return "The extension {} is not installed.".format(self.extension_name)


class Extension(object):

    def __init__(self, name, ext_type):
        self.name = name
        self.ext_type = ext_type
        self._version = None
        self._metadata = None

    @property
    def version(self):
        """
        Lazy load version.
        Returns the version as a string or None if not available.
        """
        try:
            self._version = self._version or self.get_version()
        except Exception:  # pylint: disable=broad-except
            logger.debug("Unable to get extension version: %s", traceback.format_exc())
        return self._version

    @property
    def metadata(self):
        """
        Lazy load metadata.
        Returns the metadata as a dictionary or None if not available.
        """
        try:
            self._metadata = self._metadata or self.get_metadata()
        except Exception:  # pylint: disable=broad-except
            logger.debug("Unable to get extension metadata: %s", traceback.format_exc())
        return self._metadata

    def get_version(self):
        raise NotImplementedError()

    def get_metadata(self):
        raise NotImplementedError()

    @staticmethod
    def get_all():
        raise NotImplementedError()


class WheelExtension(Extension):

    EXT_TYPE = 'whl'

    def __init__(self, name):
        super(WheelExtension, self).__init__(name, WheelExtension.EXT_TYPE)

    def get_version(self):
        return self.metadata.get('version')

    def get_metadata(self):
        if not extension_exists(self.name):
            return None
        ext_dir = get_extension_path(self.name)
        dist_info_dirs = [f for f in os.listdir(ext_dir) if f.endswith('.dist-info')]
        for dist_info_dirname in dist_info_dirs:
            parsed_dist_info_dir = WHEEL_INFO_RE(dist_info_dirname)
            if parsed_dist_info_dir and parsed_dist_info_dir.groupdict().get('name') == self.name:
                metadata_filepath = os.path.join(ext_dir, dist_info_dirname, 'metadata.json')
                metadata = None
                if os.path.isfile(metadata_filepath):
                    with open(metadata_filepath) as f:
                        metadata = json.load(f)
                return metadata

    @staticmethod
    def get_all():
        """
        Returns all wheel-based extensions.
        """
        exts = []
        if os.path.isdir(EXTENSIONS_DIR):
            for ext_name in os.listdir(EXTENSIONS_DIR):
                ext_path = get_extension_path(ext_name)
                if os.path.isdir(ext_path) and \
                        next((f for f in os.listdir(ext_path) if f.endswith(('.dist-info', '.egg-info'))), None):
                    exts.append(WheelExtension(ext_name))
        return exts


EXTENSION_TYPES = [WheelExtension]


def get_extension_path(ext_name):
    return os.path.join(EXTENSIONS_DIR, ext_name)


def get_extensions():
    extensions = []
    for ext_type in EXTENSION_TYPES:
        extensions.extend([ext for ext in ext_type.get_all()])
    return extensions


def get_extension(ext_name):
    ext = next((ext for ext in get_extensions() if ext.name == ext_name), None)
    if ext is None:
        raise ExtensionNotInstalledException(ext_name)
    return ext


def extension_exists(ext_name):
    ext = next((ext for ext in get_extensions() if ext.name == ext_name), None)
    return ext is not None


def get_extension_names():
    """
    Helper method to only get extension names.
    Returns the extension names of extensions installed in the extensions directory.
    """
    return [ext.name for ext in get_extensions()]
