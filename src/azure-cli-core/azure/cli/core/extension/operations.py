# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from collections import OrderedDict
import sys
import os
import tempfile
import shutil
import zipfile
import traceback
import hashlib
from subprocess import check_output, STDOUT, CalledProcessError
from urllib.parse import urlparse

from packaging.version import parse

from azure.cli.core import CommandIndex
from azure.cli.core.util import CLIError, reload_module, rmtree_with_retry
from azure.cli.core.extension import (extension_exists, build_extension_path, get_extensions, get_extension_modname,
                                      get_extension, ext_compat_with_cli,
                                      EXT_METADATA_ISPREVIEW, EXT_METADATA_ISEXPERIMENTAL,
                                      WheelExtension, DevExtension, ExtensionNotInstalledException, WHEEL_INFO_RE)
from azure.cli.core.telemetry import set_extension_management_detail

from knack.log import get_logger

from ._homebrew_patch import HomebrewPipPatch
from ._index import get_index_extensions
from ._resolve import resolve_from_index, NoExtensionCandidatesError

logger = get_logger(__name__)

OUT_KEY_NAME = 'name'
OUT_KEY_VERSION = 'version'
OUT_KEY_TYPE = 'extensionType'
OUT_KEY_METADATA = 'metadata'
OUT_KEY_PREVIEW = 'preview'
OUT_KEY_EXPERIMENTAL = 'experimental'
OUT_KEY_PATH = 'path'

IS_WINDOWS = sys.platform.lower() in ['windows', 'win32']
LIST_FILE_PATH = os.path.join(os.sep, 'etc', 'apt', 'sources.list.d', 'azure-cli.list')
LSB_RELEASE_FILE = os.path.join(os.sep, 'etc', 'lsb-release')


def _run_pip(pip_exec_args, extension_path=None):
    cmd = [sys.executable, '-m', 'pip'] + pip_exec_args + ['-vv', '--disable-pip-version-check', '--no-cache-dir']
    logger.debug('Running: %s', cmd)
    try:
        log_output = check_output(cmd, stderr=STDOUT, universal_newlines=True)
        logger.debug(log_output)
        returncode = 0
    except CalledProcessError as e:
        logger.debug(e.output)
        logger.debug(e)
        if "PermissionError: [WinError 5]" in e.output:
            logger.warning("You do not have the permission to add extensions in the target directory%s. You may need to rerun on a shell as administrator.", ': ' + os.path.split(extension_path)[0] if extension_path else '')
        returncode = e.returncode
    return returncode


def _whl_download_from_url(url_parse_result, ext_file):
    import requests
    from azure.cli.core.util import should_disable_connection_verify
    url = url_parse_result.geturl()
    r = requests.get(url, stream=True, verify=(not should_disable_connection_verify()))
    if r.status_code != 200:
        raise CLIError("Request to {} failed with {}".format(url, r.status_code))
    with open(ext_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # ignore keep-alive new chunks
                f.write(chunk)


def _validate_whl_extension(ext_file):
    tmp_dir = tempfile.mkdtemp()
    zip_ref = zipfile.ZipFile(ext_file, 'r')
    zip_ref.extractall(tmp_dir)
    zip_ref.close()
    azext_metadata = WheelExtension.get_azext_metadata(tmp_dir)
    rmtree_with_retry(tmp_dir)
    check_version_compatibility(azext_metadata)


def _get_extension_info_from_source(source):
    url_parse_result = urlparse(source)
    is_url = (url_parse_result.scheme == 'http' or url_parse_result.scheme == 'https')
    whl_filename = os.path.basename(url_parse_result.path) if is_url else os.path.basename(source)
    parsed_filename = WHEEL_INFO_RE(whl_filename)
    # Extension names can have - but .whl format changes it to _ (PEP 0427). Undo this.
    extension_name = parsed_filename.groupdict().get('name').replace('_', '-') if parsed_filename else None
    extension_version = parsed_filename.groupdict().get('ver') if parsed_filename else None
    return extension_name, extension_version


def _add_whl_ext(cli_ctx, source, ext_sha256=None, pip_extra_index_urls=None, pip_proxy=None, system=None):  # pylint: disable=too-many-statements
    cli_ctx.get_progress_controller().add(message='Analyzing')
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
    if extension_exists(extension_name, ext_type=WheelExtension):
        raise CLIError('The extension {} already exists.'.format(extension_name))
    if extension_name == 'rdbms-connect':
        _install_deps_for_psycopg2()
    ext_file = None
    if is_url:
        # Download from URL
        tmp_dir = tempfile.mkdtemp()
        ext_file = os.path.join(tmp_dir, whl_filename)
        logger.debug('Downloading %s to %s', source, ext_file)
        import requests
        try:
            cli_ctx.get_progress_controller().add(message='Downloading')
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
        cli_ctx.get_progress_controller().add(message='Validating')
        _validate_whl_extension(ext_file)
    except AssertionError:
        logger.debug(traceback.format_exc())
        raise CLIError('The extension is invalid. Use --debug for more information.')
    except CLIError as e:
        raise e
    logger.debug('Validation successful on %s', ext_file)
    # Check for distro consistency
    check_distro_consistency()
    cli_ctx.get_progress_controller().add(message='Installing')
    # Install with pip
    extension_path = build_extension_path(extension_name, system)
    pip_args = ['install', '--target', extension_path, ext_file]

    if pip_proxy:
        pip_args = pip_args + ['--proxy', pip_proxy]
    if pip_extra_index_urls:
        for extra_index_url in pip_extra_index_urls:
            pip_args = pip_args + ['--extra-index-url', extra_index_url]

    logger.debug('Executing pip with args: %s', pip_args)
    with HomebrewPipPatch():
        pip_status_code = _run_pip(pip_args, extension_path)
    if pip_status_code > 0:
        logger.debug('Pip failed so deleting anything we might have installed at %s', extension_path)
        rmtree_with_retry(extension_path)
        raise CLIError('An error occurred. Pip failed with status code {}. '
                       'Use --debug for more information.'.format(pip_status_code))
    # Save the whl we used to install the extension in the extension dir.
    dst = os.path.join(extension_path, whl_filename)
    shutil.copyfile(ext_file, dst)
    logger.debug('Saved the whl to %s', dst)

    return extension_name


def _install_deps_for_psycopg2():  # pylint: disable=too-many-statements
    # Below system dependencies are required to install the psycopg2 dependency for Linux and macOS
    import platform
    import subprocess
    from azure.cli.core.util import get_linux_distro
    from azure.cli.core._environment import _ENV_AZ_INSTALLER
    installer = os.getenv(_ENV_AZ_INSTALLER)
    system = platform.system()
    if system == 'Darwin':
        subprocess.call(['xcode-select', '--install'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if installer != 'HOMEBREW':
            from shutil import which
            if which('brew') is None:
                logger.warning('You may need to install postgresql with homebrew first before you install this extension.')
                return
        exit_code = subprocess.call(['brew', 'list', 'postgresql'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if exit_code != 0:
            update_cmd = ['brew', 'install', 'postgresql']
            logger.warning('This extension depends on postgresql and it will be installed first.')
            logger.debug("Install dependencies with '%s'", " ".join(update_cmd))
            subprocess.call(update_cmd)
        # Fix the issue of -lssl not found during building psycopg2
        if os.environ.get('LIBRARY_PATH') is None:
            os.environ['LIBRARY_PATH'] = '/usr/local/opt/openssl/lib/'
        else:
            os.environ['LIBRARY_PATH'] = os.pathsep.join([
                os.environ.get('LIBRARY_PATH'),
                '/usr/local/opt/openssl/lib/'
            ])
    elif system == 'Linux':
        distname, _ = get_linux_distro()
        distname = distname.lower().strip()
        if installer == 'RPM' or any(x in distname for x in ['centos', 'rhel', 'red hat', 'fedora', 'opensuse', 'suse', 'sles']):
            if any(x in distname for x in ['centos', 'rhel', 'red hat', 'fedora']):
                yum_install_cmd = 'yum install -y gcc postgresql-devel python3-devel'.split()
                if os.geteuid() != 0:  # pylint: disable=no-member
                    yum_install_cmd.insert(0, 'sudo')
                logger.debug("Install dependencies with '%s'", " ".join(yum_install_cmd))
                logger.warning('This extension depends on gcc, postgresql-devel, python3-devel and they will be installed first if not exist.')
                subprocess.call(yum_install_cmd)
            elif any(x in distname for x in ['opensuse', 'suse', 'sles']):
                zypper_refresh_cmd = ['zypper', 'refresh']
                zypper_install_cmd = 'zypper install -y gcc postgresql-devel python3-devel'.split()
                logger.warning('This extension depends on gcc postgresql-devel, python3-devel and they will be installed first if not exist.')
                if os.geteuid() != 0:  # pylint: disable=no-member
                    zypper_refresh_cmd.insert(0, 'sudo')
                    zypper_install_cmd.insert(0, 'sudo')
                exit_code = subprocess.call(zypper_refresh_cmd)
                if exit_code == 0:
                    logger.debug("Install dependencies with '%s'", " ".join(zypper_install_cmd))
                    subprocess.call(zypper_install_cmd)


def is_valid_sha256sum(a_file, expected_sum):
    sha256 = hashlib.sha256()
    with open(a_file, 'rb') as f:
        sha256.update(f.read())
    computed_hash = sha256.hexdigest()
    return expected_sum == computed_hash, computed_hash


def _augment_telemetry_with_ext_info(extension_name, ext=None):
    # The extension must be available before calling this otherwise we can't get the version from metadata
    if not extension_name:
        return
    try:
        ext = ext or get_extension(extension_name)
        ext_version = ext.version
        set_extension_management_detail(extension_name, ext_version)
    except Exception:  # nopa pylint: disable=broad-except
        # Don't error on telemetry
        pass


def check_version_compatibility(azext_metadata):
    is_compatible, cli_core_version, min_required, max_required, min_ext_required = ext_compat_with_cli(azext_metadata)
    # logger.debug("Extension compatibility result: is_compatible=%s cli_core_version=%s min_required=%s "
    #              "max_required=%s", is_compatible, cli_core_version, min_required, max_required)
    if not is_compatible:
        ext_name = azext_metadata.get('name')
        ext_version = azext_metadata.get('version')
        min_max_msgs = [
            f"The '{ext_name}' extension version {ext_version} is not compatible with your current CLI core version {cli_core_version}."
        ]
        if min_ext_required:
            min_max_msgs.append(f"This CLI core requires a min of {min_ext_required} for the '{ext_name}' extension.")
            min_max_msgs.append(f"Please run 'az extension update -n {ext_name}' to update it.")
        elif min_required and max_required:
            min_max_msgs.append(f'This extension requires a min of {min_required} and max of {max_required} CLI core.')
            min_max_msgs.append("Please run 'az upgrade' to upgrade to a compatible version.")
        elif min_required:
            min_max_msgs.append(f'This extension requires a min of {min_required} CLI core.')
            min_max_msgs.append("Please run 'az upgrade' to upgrade to a compatible version.")
        elif max_required:
            min_max_msgs.append(f'This extension requires a max of {max_required} CLI core.')
            # we do not want users to downgrade CLI core version, so we suggest updating the extension in this case
            min_max_msgs.append(f"Please run 'az extension update -n {ext_name}' to update the extension.")

        raise CLIError("\n".join(min_max_msgs))


def add_extension(cmd=None, source=None, extension_name=None, index_url=None, yes=None,  # pylint: disable=unused-argument, too-many-statements
                  pip_extra_index_urls=None, pip_proxy=None, system=None,
                  version=None, cli_ctx=None, upgrade=None):
    ext_sha256 = None

    version = None if version == 'latest' else version
    cmd_cli_ctx = cli_ctx or cmd.cli_ctx
    if extension_name:
        cmd_cli_ctx.get_progress_controller().add(message='Searching')
        ext = None
        set_extension_management_detail(extension_name, version)
        try:
            ext = get_extension(extension_name)
        except ExtensionNotInstalledException:
            pass
        if ext:
            if isinstance(ext, WheelExtension):
                if not upgrade:
                    logger.warning("Extension '%s' is already installed.", extension_name)
                    return
                logger.warning("Extension '%s' %s is already installed.", extension_name, ext.get_version())
                if version and version == ext.get_version():
                    return
                logger.warning("It will be overridden with version {}.".format(version) if version else "It will be updated if available.")
                update_extension(cmd=cmd, extension_name=extension_name, index_url=index_url, pip_extra_index_urls=pip_extra_index_urls, pip_proxy=pip_proxy, cli_ctx=cli_ctx, version=version)
                return
            logger.warning("Overriding development version of '%s' with production version.", extension_name)
        try:
            source, ext_sha256 = resolve_from_index(extension_name, index_url=index_url, target_version=version, cli_ctx=cmd_cli_ctx)
        except NoExtensionCandidatesError as err:
            logger.debug(err)

            if version:
                err = "No matching extensions for '{} ({})'. Use --debug for more information.".format(extension_name, version)
            else:
                err = "No matching extensions for '{}'. Use --debug for more information.".format(extension_name)
            raise CLIError(err)
    ext_name, ext_version = _get_extension_info_from_source(source)
    set_extension_management_detail(extension_name if extension_name else ext_name, ext_version)
    extension_name = _add_whl_ext(cli_ctx=cmd_cli_ctx, source=source, ext_sha256=ext_sha256,
                                  pip_extra_index_urls=pip_extra_index_urls, pip_proxy=pip_proxy, system=system)
    try:
        ext = get_extension(extension_name)
        if extension_name and ext.experimental:
            logger.warning("The installed extension '%s' is experimental and not covered by customer support. "
                           "Please use with discretion.", extension_name)
        elif extension_name and ext.preview:
            logger.warning("The installed extension '%s' is in preview.", extension_name)
        CommandIndex().invalidate()
    except ExtensionNotInstalledException:
        pass


def remove_extension(extension_name):
    try:
        # Get the extension and it will raise an error if it doesn't exist
        ext = get_extension(extension_name)
        if ext and isinstance(ext, DevExtension):
            raise CLIError(
                "Extension '{name}' was installed in development mode. Remove using "
                "`azdev extension remove {name}`".format(name=extension_name))
        # We call this just before we remove the extension so we can get the metadata before it is gone
        _augment_telemetry_with_ext_info(extension_name, ext)
        rmtree_with_retry(ext.path)
        CommandIndex().invalidate()
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def list_extensions():
    return [{OUT_KEY_NAME: ext.name, OUT_KEY_VERSION: ext.version, OUT_KEY_TYPE: ext.ext_type,
             OUT_KEY_PREVIEW: ext.preview, OUT_KEY_EXPERIMENTAL: ext.experimental, OUT_KEY_PATH: ext.path}
            for ext in get_extensions()]


def show_extension(extension_name):
    try:
        extension = get_extension(extension_name)
        return {OUT_KEY_NAME: extension.name,
                OUT_KEY_VERSION: extension.version,
                OUT_KEY_TYPE: extension.ext_type,
                OUT_KEY_METADATA: extension.metadata,
                OUT_KEY_PATH: extension.path}
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def update_extension(cmd=None, extension_name=None, index_url=None, pip_extra_index_urls=None, pip_proxy=None, cli_ctx=None, version=None):
    try:
        cmd_cli_ctx = cli_ctx or cmd.cli_ctx
        ext = get_extension(extension_name, ext_type=WheelExtension)
        cur_version = ext.get_version()
        try:
            download_url, ext_sha256 = resolve_from_index(extension_name, cur_version=cur_version, index_url=index_url, target_version=version, cli_ctx=cmd_cli_ctx)
            _, ext_version = _get_extension_info_from_source(download_url)
            set_extension_management_detail(extension_name, ext_version)
        except NoExtensionCandidatesError as err:
            logger.debug(err)
            msg = "Extension {} with version {} not found.".format(extension_name, version) if version else "No updates available for '{}'. Use --debug for more information.".format(extension_name)
            logger.warning(msg)
            return
        # Copy current version of extension to tmp directory in case we need to restore it after a failed install.
        backup_dir = os.path.join(tempfile.mkdtemp(), extension_name)
        extension_path = ext.path
        logger.debug('Backing up the current extension: %s to %s', extension_path, backup_dir)
        shutil.copytree(extension_path, backup_dir)
        # Remove current version of the extension
        rmtree_with_retry(extension_path)
        # Install newer version
        try:
            _add_whl_ext(cli_ctx=cmd_cli_ctx, source=download_url, ext_sha256=ext_sha256,
                         pip_extra_index_urls=pip_extra_index_urls, pip_proxy=pip_proxy)
            logger.debug('Deleting backup of old extension at %s', backup_dir)
            rmtree_with_retry(backup_dir)
        except Exception as err:
            logger.error('An error occurred whilst updating.')
            logger.error(err)
            logger.debug('Copying %s to %s', backup_dir, extension_path)
            shutil.copytree(backup_dir, extension_path)
            raise CLIError('Failed to update. Rolled {} back to {}.'.format(extension_name, cur_version))
        CommandIndex().invalidate()
    except ExtensionNotInstalledException as e:
        raise CLIError(e)


def list_available_extensions(index_url=None, show_details=False, cli_ctx=None):
    index_data = get_index_extensions(index_url=index_url, cli_ctx=cli_ctx)
    if show_details:
        return index_data
    installed_extensions = get_extensions(ext_type=WheelExtension)
    installed_extension_names = [e.name for e in installed_extensions]
    results = []
    for name, items in OrderedDict(sorted(index_data.items())).items():
        # exclude extensions/versions incompatible with current CLI version
        items = [item for item in items if ext_compat_with_cli(item['metadata'])[0]]
        if not items:
            continue

        latest = max(items, key=lambda c: parse(c['metadata']['version']))
        installed = False
        if name in installed_extension_names:
            installed = True
            ext_version = get_extension(name).version
            if ext_version and parse(latest['metadata']['version']) > parse(ext_version):
                installed = str(True) + ' (upgrade available)'
        results.append({
            'name': name,
            'version': latest['metadata']['version'],
            'summary': latest['metadata']['summary'],
            'preview': latest['metadata'].get(EXT_METADATA_ISPREVIEW, False),
            'experimental': latest['metadata'].get(EXT_METADATA_ISEXPERIMENTAL, False),
            'installed': installed
        })
    return results


def list_versions(extension_name, index_url=None, cli_ctx=None):
    index_data = get_index_extensions(index_url=index_url, cli_ctx=cli_ctx)

    try:
        exts = index_data[extension_name]
    except Exception:
        raise CLIError('Extension {} not found.'.format(extension_name))

    try:
        installed_ext = get_extension(extension_name, ext_type=WheelExtension)
    except ExtensionNotInstalledException:
        installed_ext = None

    results = []
    latest_compatible_version = None

    for ext in sorted(exts, key=lambda c: parse(c['metadata']['version']), reverse=True):
        compatible = ext_compat_with_cli(ext['metadata'])[0]
        ext_version = ext['metadata']['version']
        if latest_compatible_version is None and compatible:
            latest_compatible_version = ext_version
        installed = ext_version == installed_ext.version if installed_ext else False
        if installed and parse(latest_compatible_version) > parse(installed_ext.version):
            installed = str(True) + ' (upgrade available)'
        version = ext['metadata']['version']
        if latest_compatible_version == ext_version:
            version = version + ' (max compatible version)'
        results.append({
            'name': extension_name,
            'version': version,
            'preview': ext['metadata'].get(EXT_METADATA_ISPREVIEW, False),
            'experimental': ext['metadata'].get(EXT_METADATA_ISEXPERIMENTAL, False),
            'installed': installed,
            'compatible': compatible
        })
    results.reverse()
    return results


def reload_extension(extension_name, extension_module=None):
    return reload_module(extension_module if extension_module else get_extension_modname(ext_name=extension_name))


def add_extension_to_path(extension_name, ext_dir=None):
    ext_dir = ext_dir or get_extension(extension_name).path
    sys.path.append(ext_dir)
    # If this path update should have made a new "azure" module available,
    # extend the existing module with its path. This allows extensions to
    # include (or depend on) Azure SDK modules that are not yet part of
    # the CLI. This applies to both the "azure" and "azure.mgmt" namespaces,
    # but ensures that modules installed by the CLI take priority.
    azure_dir = os.path.join(ext_dir, "azure")
    if os.path.isdir(azure_dir):
        import azure
        azure.__path__.append(azure_dir)
        azure_mgmt_dir = os.path.join(azure_dir, "mgmt")
        if os.path.isdir(azure_mgmt_dir):
            try:
                # Should have been imported already, so this will be quick
                import azure.mgmt
            except ImportError:
                pass
            else:
                azure.mgmt.__path__.append(azure_mgmt_dir)


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
        logger.debug('Linux distro check: An error occurred while checking '
                     'linux distribution version source list consistency.')
        logger.debug(err)

    if current_linux_dist_name != stored_linux_dist_name:
        logger.debug("Linux distro check: Mismatch distribution "
                     "name in %s file", LIST_FILE_PATH)
        logger.debug("Linux distro check: If command fails, install the appropriate package "
                     "for your distribution or change the above file accordingly.")
        logger.debug("Linux distro check: %s has '%s', current distro is '%s'",
                     LIST_FILE_PATH, stored_linux_dist_name, current_linux_dist_name)
