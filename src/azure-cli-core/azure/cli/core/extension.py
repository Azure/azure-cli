# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import traceback
import json

from knack.log import get_logger

from azure.cli.core._config import GLOBAL_CONFIG_DIR


_CUSTOM_EXT_DIR = os.environ.get('AZURE_EXTENSION_DIR')
EXTENSIONS_DIR = os.path.expanduser(_CUSTOM_EXT_DIR) if _CUSTOM_EXT_DIR else os.path.join(GLOBAL_CONFIG_DIR,
                                                                                          'cliextensions')
EXTENSIONS_MOD_PREFIX = 'azext_'

WHL_METADATA_FILENAME = 'metadata.json'
AZEXT_METADATA_FILENAME = 'azext_metadata.json'

EXT_METADATA_MINCLICOREVERSION = 'azext.minCliCoreVersion'
EXT_METADATA_MAXCLICOREVERSION = 'azext.maxCliCoreVersion'
EXT_METADATA_ISPREVIEW = 'azext.isPreview'

logger = get_logger(__name__)


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
        self._preview = None

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

    @property
    def preview(self):
        """
        Lazy load preview status.
        Returns the preview status of the extension.
        """
        try:
            if not isinstance(self._preview, bool):
                self._preview = bool(self.metadata.get(EXT_METADATA_ISPREVIEW))
        except Exception:  # pylint: disable=broad-except
            logger.debug("Unable to get extension preview status: %s", traceback.format_exc())
        return self._preview

    def get_version(self):
        raise NotImplementedError()

    def get_metadata(self):
        raise NotImplementedError()

    @staticmethod
    def get_all():
        raise NotImplementedError()


class WheelExtension(Extension):

    def __init__(self, name):
        super(WheelExtension, self).__init__(name, 'whl')

    def get_version(self):
        return self.metadata.get('version')

    def get_metadata(self):
        from wheel.install import WHEEL_INFO_RE
        if not extension_exists(self.name):
            return None
        metadata = {}
        ext_dir = get_extension_path(self.name)
        dist_info_dirs = [f for f in os.listdir(ext_dir) if f.endswith('.dist-info')]
        azext_metadata = WheelExtension.get_azext_metadata(ext_dir)
        if azext_metadata:
            metadata.update(azext_metadata)
        for dist_info_dirname in dist_info_dirs:
            parsed_dist_info_dir = WHEEL_INFO_RE(dist_info_dirname)
            if parsed_dist_info_dir and parsed_dist_info_dir.groupdict().get('name') == self.name.replace('-', '_'):
                whl_metadata_filepath = os.path.join(ext_dir, dist_info_dirname, WHL_METADATA_FILENAME)
                if os.path.isfile(whl_metadata_filepath):
                    with open(whl_metadata_filepath) as f:
                        metadata.update(json.load(f))
        return metadata

    @staticmethod
    def get_azext_metadata(ext_dir):
        azext_metadata = None
        ext_modname = get_extension_modname(ext_dir=ext_dir)
        azext_metadata_filepath = os.path.join(ext_dir, ext_modname, AZEXT_METADATA_FILENAME)
        if os.path.isfile(azext_metadata_filepath):
            with open(azext_metadata_filepath) as f:
                azext_metadata = json.load(f)
        return azext_metadata

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


def ext_compat_with_cli(azext_metadata):
    from azure.cli.core import __version__ as core_version
    from pkg_resources import parse_version
    is_compatible, min_required, max_required = (True, None, None)
    if azext_metadata:
        min_required = azext_metadata.get(EXT_METADATA_MINCLICOREVERSION)
        max_required = azext_metadata.get(EXT_METADATA_MAXCLICOREVERSION)
        parsed_cli_version = parse_version(core_version)
        if min_required and parsed_cli_version < parse_version(min_required):
            is_compatible = False
        elif max_required and parsed_cli_version > parse_version(max_required):
            is_compatible = False
    return is_compatible, core_version, min_required, max_required


def get_extension_modname(ext_name=None, ext_dir=None):
    ext_dir = ext_dir or get_extension_path(ext_name)
    pos_mods = [n for n in os.listdir(ext_dir)
                if n.startswith(EXTENSIONS_MOD_PREFIX) and os.path.isdir(os.path.join(ext_dir, n))]
    if len(pos_mods) != 1:
        raise AssertionError("Expected 1 module to load starting with "
                             "'{}': got {}".format(EXTENSIONS_MOD_PREFIX, pos_mods))
    return pos_mods[0]


def get_extension_path(ext_name):
    return os.path.join(EXTENSIONS_DIR, ext_name)


def get_extensions():
    logger.debug("Extensions directory: '%s'", EXTENSIONS_DIR)
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
