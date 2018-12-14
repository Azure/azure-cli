# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import traceback
import json

from knack.config import CLIConfig
from knack.log import get_logger

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX

az_config = CLIConfig(config_dir=GLOBAL_CONFIG_DIR, config_env_var_prefix=ENV_VAR_PREFIX)
_CUSTOM_EXT_DIR = az_config.get('extension', 'dir', None)
_DEV_EXTENSION_SOURCES = az_config.get('extension', 'dev_sources', None)
EXTENSIONS_DIR = os.path.expanduser(_CUSTOM_EXT_DIR) if _CUSTOM_EXT_DIR else os.path.join(GLOBAL_CONFIG_DIR,
                                                                                          'cliextensions')
DEV_EXTENSION_SOURCES = _DEV_EXTENSION_SOURCES.split(',') if _DEV_EXTENSION_SOURCES else []

EXTENSIONS_MOD_PREFIX = 'azext_'

WHL_METADATA_FILENAME = 'metadata.json'
EGG_INFO_METADATA_FILE_NAME = 'PKG-INFO'  # used for dev packages
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

    def __init__(self, name, ext_type, path=None):
        self.name = name
        self.ext_type = ext_type
        self.path = path
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

    def __init__(self, name, path=None):
        super(WheelExtension, self).__init__(name, 'whl', path)

    def get_version(self):
        return self.metadata.get('version')

    def get_metadata(self):
        from wheel.install import WHEEL_INFO_RE
        from glob import glob
        if not extension_exists(self.name):
            return None
        metadata = {}
        ext_dir = self.path or get_extension_path(self.name)
        info_dirs = glob(os.path.join(ext_dir, '*.*-info'))
        azext_metadata = WheelExtension.get_azext_metadata(ext_dir)
        if azext_metadata:
            metadata.update(azext_metadata)

        for dist_info_dirname in info_dirs:
            parsed_dist_info_dir = WHEEL_INFO_RE(dist_info_dirname)
            if parsed_dist_info_dir:
                parsed_dist_info_dir = parsed_dist_info_dir.groupdict().get('name')

            if os.path.split(parsed_dist_info_dir)[-1] == self.name.replace('-', '_'):
                whl_metadata_filepath = os.path.join(dist_info_dirname, WHL_METADATA_FILENAME)
                if os.path.isfile(whl_metadata_filepath):
                    with open(whl_metadata_filepath) as f:
                        metadata.update(json.loads(f.read()))

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
        from glob import glob
        exts = []
        if os.path.isdir(EXTENSIONS_DIR):
            for ext_name in os.listdir(EXTENSIONS_DIR):
                ext_path = os.path.join(EXTENSIONS_DIR, ext_name)
                pattern = os.path.join(ext_path, '*.*-info')
                if os.path.isdir(ext_path) and glob(pattern):
                    exts.append(WheelExtension(ext_name, ext_path))
        return exts


class DevExtension(Extension):
    def __init__(self, name, path):
        super(DevExtension, self).__init__(name, 'dev', path)

    def get_version(self):
        return self.metadata.get('version')

    def get_metadata(self):

        if not extension_exists(self.name):
            return None
        metadata = {}
        ext_dir = self.path
        egg_info_dirs = [f for f in os.listdir(ext_dir) if f.endswith('.egg-info')]
        azext_metadata = DevExtension.get_azext_metadata(ext_dir)
        if azext_metadata:
            metadata.update(azext_metadata)

        def _apply_egginfo_metadata(filename):
            # extract version info for dev extensions from PKG-INFO
            if os.path.isfile(filename):
                with open(filename) as f:
                    for line in f.readlines():
                        try:
                            key, val = line.split(':', 1)
                            key = key.lower()
                            if key == 'version':
                                metadata[key] = '{}'.format(val.strip())
                        except ValueError:
                            continue

        for egg_info_dirname in egg_info_dirs:
            egg_metadata_filepath = os.path.join(ext_dir, egg_info_dirname, EGG_INFO_METADATA_FILE_NAME)
            _apply_egginfo_metadata(egg_metadata_filepath)

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
        Returns all dev extensions.
        """
        from glob import glob
        exts = []

        def _collect(path, depth=0, max_depth=3):
            if not os.path.isdir(path) or depth == max_depth or os.path.split(path)[-1].startswith('.'):
                return
            pattern = os.path.join(path, '*.egg-info')
            match = glob(pattern)
            if match:
                ext_path = os.path.dirname(match[0])
                ext_name = os.path.split(ext_path)[-1]
                exts.append(DevExtension(ext_name, ext_path))
            else:
                for item in os.listdir(path):
                    _collect(os.path.join(path, item), depth + 1, max_depth)
        for source in DEV_EXTENSION_SOURCES:
            _collect(source)
        return exts


EXTENSION_TYPES = [WheelExtension, DevExtension]


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


def get_extensions(ext_type=None):
    logger.debug("Extensions directory: '%s'", EXTENSIONS_DIR)
    extensions = []
    if not ext_type:
        ext_type = EXTENSION_TYPES
    elif not isinstance(ext_type, list):
        ext_type = [ext_type]
    for t in ext_type:
        extensions.extend([ext for ext in t.get_all()])
    return extensions


def get_extension(ext_name, ext_type=None):
    ext = next((ext for ext in get_extensions(ext_type=ext_type) if ext.name == ext_name), None)
    if ext is None:
        raise ExtensionNotInstalledException(ext_name)
    return ext


def extension_exists(ext_name, ext_type=None):
    exts = get_extensions(ext_type=ext_type)
    ext = next((ext for ext in exts if ext.name == ext_name), None)
    return ext is not None


def get_extension_names(ext_type=None):
    """
    Helper method to only get extension names.
    Returns the extension names of extensions installed in the extensions directory.
    """
    return [ext.name for ext in get_extensions(ext_type=ext_type)]
