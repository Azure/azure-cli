# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import traceback
import json
import re
from distutils.sysconfig import get_python_lib

import pkginfo
from knack.config import CLIConfig
from knack.log import get_logger
from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX

az_config = CLIConfig(config_dir=GLOBAL_CONFIG_DIR, config_env_var_prefix=ENV_VAR_PREFIX)
_CUSTOM_EXT_DIR = az_config.get('extension', 'dir', None)
_DEV_EXTENSION_SOURCES = az_config.get('extension', 'dev_sources', None)
_CUSTOM_EXT_SYS_DIR = az_config.get('extension', 'sys_dir', None)
EXTENSIONS_DIR = os.path.expanduser(_CUSTOM_EXT_DIR) if _CUSTOM_EXT_DIR else os.path.join(GLOBAL_CONFIG_DIR,
                                                                                          'cliextensions')
DEV_EXTENSION_SOURCES = _DEV_EXTENSION_SOURCES.split(',') if _DEV_EXTENSION_SOURCES else []
EXTENSIONS_SYS_DIR = os.path.expanduser(_CUSTOM_EXT_SYS_DIR) if _CUSTOM_EXT_SYS_DIR else os.path.join(get_python_lib(), 'azure-cli-extensions')

EXTENSIONS_MOD_PREFIX = 'azext_'

AZEXT_METADATA_FILENAME = 'azext_metadata.json'

EXT_METADATA_MINCLICOREVERSION = 'azext.minCliCoreVersion'
EXT_METADATA_MAXCLICOREVERSION = 'azext.maxCliCoreVersion'
EXT_METADATA_ISPREVIEW = 'azext.isPreview'
EXT_METADATA_ISEXPERIMENTAL = 'azext.isExperimental'

# If this Azure CLI core version has breaking changes that do not support older versions of extensions,
# put the requirements of the minimum extension versions here.
# Example:
# {'azure-devops': {'minExtVersion': '1.0.0'}}
EXTENSION_VERSION_REQUIREMENTS = {}
MIN_EXT_VERSION = 'minExtVersion'

WHEEL_INFO_RE = re.compile(
    r"""^(?P<namever>(?P<name>.+?)(-(?P<ver>\d.+?))?)
    ((-(?P<build>\d.*?))?-(?P<pyver>.+?)-(?P<abi>.+?)-(?P<plat>.+?)
    \.whl|\.dist-info|\.egg-info)$""",
    re.VERBOSE).match

logger = get_logger(__name__)


class ExtensionNotInstalledException(Exception):
    def __init__(self, extension_name):
        super(ExtensionNotInstalledException, self).__init__(extension_name)
        self.extension_name = extension_name

    def __str__(self):
        return "The extension {} is not installed.".format(self.extension_name)


class Extension:

    def __init__(self, name, ext_type, path=None):
        self.name = name
        self.ext_type = ext_type
        self.path = path
        self._version = None
        self._metadata = None
        self._preview = None
        self._experimental = None

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

    @property
    def experimental(self):
        """
        Lazy load experimental status.
        Returns the experimental status of the extension.
        """
        try:
            if not isinstance(self._experimental, bool):
                self._experimental = bool(self.metadata.get(EXT_METADATA_ISEXPERIMENTAL))
        except Exception:  # pylint: disable=broad-except
            logger.debug("Unable to get extension experimental status: %s", traceback.format_exc())
        return self._experimental

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
        from glob import glob

        metadata = {}
        ext_dir = self.path or get_extension_path(self.name)
        if not ext_dir or not os.path.isdir(ext_dir):
            return None

        # include *.egg-info and *.dist-info
        info_dirs = glob(os.path.join(ext_dir, self.name.replace('-', '_') + '*.*-info'))
        if not info_dirs:
            return None

        azext_metadata = WheelExtension.get_azext_metadata(ext_dir)
        if azext_metadata:
            metadata.update(azext_metadata)

        for dist_info_dirname in info_dirs:
            try:
                if dist_info_dirname.endswith('.egg-info'):
                    ext_whl_metadata = pkginfo.Develop(dist_info_dirname)
                elif dist_info_dirname.endswith('.dist-info'):
                    ext_whl_metadata = pkginfo.Wheel(dist_info_dirname)
                else:
                    raise ValueError()

                if self.name == ext_whl_metadata.name:
                    metadata.update(vars(ext_whl_metadata))
            except ValueError:
                logger.warning('extension %s contains invalid metadata for Python Package', self.name)

        return metadata

    def __eq__(self, other):
        return other.name == self.name

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
    def get_metadata_extras(ext_file):
        metadata_extras = []
        extra_const = " extra == "
        try:
            if ext_file.endswith('.whl'):
                ext_whl_metadata = pkginfo.Wheel(ext_file)
            else:
                raise ValueError()
            # Parse out the extras for readability
            for ext in ext_whl_metadata.requires_dist:
                if extra_const in ext:
                    key = ext[ext.find(extra_const) + len(extra_const) + 1: ext.rfind("'")]
                    metadata_extras.append(key)
        except ValueError:
            logger.warning('Could not parse metadata to get setup extras. Will install without extras.')
        return metadata_extras

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
                pattern = os.path.join(ext_path, '*.*-info')    # include *.egg-info and *.dist-info
                if os.path.isdir(ext_path) and glob(pattern):
                    exts.append(WheelExtension(ext_name, ext_path))
        if os.path.isdir(EXTENSIONS_SYS_DIR):
            for ext_name in os.listdir(EXTENSIONS_SYS_DIR):
                ext_path = os.path.join(EXTENSIONS_SYS_DIR, ext_name)
                pattern = os.path.join(ext_path, '*.*-info')    # include *.egg-info and *.dist-info
                if os.path.isdir(ext_path) and glob(pattern):
                    ext = WheelExtension(ext_name, ext_path)
                    if ext not in exts:
                        exts.append(ext)
        return exts


class DevExtension(Extension):
    def __init__(self, name, path):
        super(DevExtension, self).__init__(name, 'dev', path)

    def get_version(self):
        return self.metadata.get('version')

    def get_metadata(self):
        metadata = {}
        ext_dir = self.path
        if not ext_dir or not os.path.isdir(ext_dir):
            return None

        egg_info_dirs = [f for f in os.listdir(ext_dir) if f.endswith('.egg-info')]
        if not egg_info_dirs:
            return None

        azext_metadata = DevExtension.get_azext_metadata(ext_dir)
        if azext_metadata:
            metadata.update(azext_metadata)

        for egg_info_dirname in egg_info_dirs:
            egg_metadata_path = os.path.join(ext_dir, egg_info_dirname, )
            try:
                ext_whl_metadata = pkginfo.Develop(egg_metadata_path)
                if self.name == ext_whl_metadata.name:
                    metadata.update(vars(ext_whl_metadata))
            except ValueError:
                logger.warning('extension % contains invalid metadata for Python Package', self.name)

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
    from packaging.version import parse
    is_compatible, min_required, max_required = (True, None, None)
    if azext_metadata:
        min_required = azext_metadata.get(EXT_METADATA_MINCLICOREVERSION)
        max_required = azext_metadata.get(EXT_METADATA_MAXCLICOREVERSION)
        parsed_cli_version = parse(core_version)
        if min_required and parsed_cli_version < parse(min_required):
            is_compatible = False
        elif max_required and parsed_cli_version > parse(max_required):
            is_compatible = False

    try:
        min_ext_required = EXTENSION_VERSION_REQUIREMENTS.get(azext_metadata.get('name')).get(MIN_EXT_VERSION)
        if parse(azext_metadata.get('version')) < parse(min_ext_required):
            is_compatible = False
    except AttributeError:
        min_ext_required = None
    return is_compatible, core_version, min_required, max_required, min_ext_required


def get_extension_modname(ext_name=None, ext_dir=None):
    ext_dir = ext_dir or get_extension_path(ext_name)
    pos_mods = [n for n in os.listdir(ext_dir)
                if n.startswith(EXTENSIONS_MOD_PREFIX) and os.path.isdir(os.path.join(ext_dir, n))]
    if len(pos_mods) != 1:
        raise AssertionError("Expected 1 module to load starting with "
                             "'{}': got {}".format(EXTENSIONS_MOD_PREFIX, pos_mods))
    return pos_mods[0]


def get_extension_path(ext_name):
    # This will return the path for a WHEEL extension if exists.
    ext_sys_path = os.path.join(EXTENSIONS_SYS_DIR, ext_name)
    ext_path = os.path.join(EXTENSIONS_DIR, ext_name)
    return ext_path if os.path.isdir(ext_path) else (
        ext_sys_path if os.path.isdir(ext_sys_path) else None)


def build_extension_path(ext_name, system=None):
    # This will simply form the path for a WHEEL extension.
    return os.path.join(EXTENSIONS_SYS_DIR, ext_name) if system else os.path.join(EXTENSIONS_DIR, ext_name)


def get_extensions(ext_type=None):
    extensions = []
    if not ext_type:
        ext_type = EXTENSION_TYPES
    elif not isinstance(ext_type, list):
        ext_type = [ext_type]
    for t in ext_type:
        extensions.extend(t.get_all())
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
