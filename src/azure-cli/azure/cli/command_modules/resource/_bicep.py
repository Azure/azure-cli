# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import stat
import platform
import subprocess
import json
import certifi

from json.decoder import JSONDecodeError
from contextlib import suppress
from datetime import datetime, timedelta

import requests
import semver

from urllib.request import urlopen
from knack.log import get_logger
from azure.cli.core.api import get_config_dir
from azure.cli.core.azclierror import (
    FileOperationError,
    ValidationError,
    UnclassifiedUserFault,
    ClientRequestError,
    InvalidTemplateError,
)
from azure.cli.core.util import should_disable_connection_verify

from ._bicep_config import (
    get_check_version_config,
    get_use_binary_from_path_config,
    remove_use_binary_from_path_config,
    set_use_binary_from_path_config
)

# See: https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
_semver_pattern = r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"  # pylint: disable=line-too-long

# See: https://learn.microsoft.com/azure/azure-resource-manager/templates/template-syntax#template-format
_template_schema_pattern = r"https?://schema\.management\.azure\.com/schemas/[0-9a-zA-Z-]+/(?P<templateType>[a-zA-Z]+)Template\.json#?"  # pylint: disable=line-too-long

_bicep_diagnostic_warning_pattern = r"^([^\s].*)\((\d+)(?:,\d+|,\d+,\d+)?\)\s+:\s+(Warning)\s+([a-zA-Z-\d]+):\s*(.*?)\s+\[(.*?)\]$"  # pylint: disable=line-too-long

_config_dir = get_config_dir()
_bicep_installation_dir = os.path.join(_config_dir, "bin")
_bicep_version_check_file_path = os.path.join(_config_dir, "bicepVersionCheck.json")
_bicep_version_check_cache_ttl = timedelta(minutes=10)
_bicep_version_check_time_format = "%Y-%m-%dT%H:%M:%S.%f"

_logger = get_logger(__name__)

_requests_verify = not should_disable_connection_verify()


def validate_bicep_target_scope(template_schema, deployment_scope):
    target_scope = _template_schema_to_target_scope(template_schema)
    if target_scope != deployment_scope:
        raise InvalidTemplateError(
            f'The target scope "{target_scope}" does not match the deployment scope "{deployment_scope}".'
        )


def run_bicep_command(cli_ctx, args, auto_install=True, custom_env=None):
    if _use_binary_from_path(cli_ctx):
        from shutil import which

        if which("bicep") is None:
            raise ValidationError(
                'Could not find the "bicep" executable on PATH. To install Bicep via Azure CLI, set the "bicep.use_binary_from_path" configuration to False and run "az bicep install".'  # pylint: disable=line-too-long
            )

        bicep_version_message = _run_command("bicep", ["--version"])

        _logger.debug("Using Bicep CLI from PATH. %s", bicep_version_message)

        return _run_command("bicep", args, custom_env)

    installation_path = _get_bicep_installation_path(platform.system())
    _logger.debug("Bicep CLI installation path: %s", installation_path)

    installed = os.path.isfile(installation_path)
    _logger.debug("Bicep CLI installed: %s.", installed)

    check_version = get_check_version_config(cli_ctx)

    if not installed:
        if auto_install:
            ensure_bicep_installation(cli_ctx, stdout=False)
        else:
            raise FileOperationError('Bicep CLI not found. Install it now by running "az bicep install".')
    elif check_version:
        latest_release_tag, cache_expired = _load_bicep_version_check_result_from_cache()

        with suppress(ClientRequestError):
            # Checking upgrade should ignore connection issues.
            # Users may continue using the current installed version.
            installed_version = _get_bicep_installed_version(installation_path)
            latest_release_tag = get_bicep_latest_release_tag() if cache_expired else latest_release_tag
            latest_version = _extract_version(latest_release_tag)

            if installed_version and latest_version and installed_version < latest_version:
                _logger.warning(
                    'A new Bicep release is available: %s. Upgrade now by running "az bicep upgrade".',
                    latest_release_tag,
                )

            if cache_expired:
                _refresh_bicep_version_check_cache(latest_release_tag)

    return _run_command(installation_path, args, custom_env)


def ensure_bicep_installation(cli_ctx, release_tag=None, target_platform=None, stdout=True):
    if _use_binary_from_path(cli_ctx) and release_tag is None:
        # Only use the Bicep executable from PATH when no specific version is requested.
        from shutil import which

        if which("bicep") is None:
            raise ValidationError(
                'Could not find the "bicep" executable on PATH. To install Bicep via Azure CLI, set the "bicep.use_binary_from_path" configuration to False and run "az bicep install".'  # pylint: disable=line-too-long
            )

        _logger.debug("Using Bicep CLI from PATH.")

        return

    system = platform.system()
    machine = platform.machine()
    installation_path = _get_bicep_installation_path(system)

    if os.path.isfile(installation_path):
        if not release_tag:
            print(f"Bicep CLI is already installed at '{installation_path}'. Skipping installation as no specific version was requested.")  # pylint: disable=line-too-long
            return

        installed_version = _get_bicep_installed_version(installation_path)
        target_version = _extract_version(release_tag)
        if installed_version and target_version and installed_version == target_version:
            print(f"Bicep CLI {installed_version} is already installed at '{installation_path}'.")
            return

    installation_dir = os.path.dirname(installation_path)
    os.makedirs(installation_dir, exist_ok=True)

    try:
        release_tag = release_tag if release_tag else get_bicep_latest_release_tag()
        if stdout:
            if release_tag:
                print(f"Installing Bicep CLI {release_tag}...")
            else:
                print("Installing Bicep CLI...")
        os.environ.setdefault("CURL_CA_BUNDLE", certifi.where())

        download_url = _get_bicep_download_url(system, machine, release_tag, target_platform=target_platform)
        _logger.debug(
            "Generated download URL %s. from system %s, machine %s, release tag %s and target platform %s.",
            download_url, system, machine, release_tag, target_platform,
        )

        request = urlopen(download_url)
        with open(installation_path, "wb") as f:
            f.write(request.read())

        os.chmod(installation_path, os.stat(installation_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        use_binary_from_path = get_use_binary_from_path_config(cli_ctx)
        if use_binary_from_path not in ["0", "no", "false", "off"]:
            _logger.warning("The configuration value of bicep.use_binary_from_path has been set to 'false'.")
            set_use_binary_from_path_config(cli_ctx, "false")

        if stdout:
            print(f'Successfully installed Bicep CLI to "{installation_path}".')
        else:
            _logger.info(
                "Successfully installed Bicep CLI to %s",
                installation_path,
            )
    except OSError as err:
        raise ClientRequestError(f"Error while attempting to download Bicep CLI: {err}")


def remove_bicep_installation(cli_ctx):
    system = platform.system()
    installation_path = _get_bicep_installation_path(system)

    if os.path.exists(installation_path):
        os.remove(installation_path)
    if os.path.exists(_bicep_version_check_file_path):
        os.remove(_bicep_version_check_file_path)

    use_binary_from_path = get_use_binary_from_path_config(cli_ctx)
    if use_binary_from_path in ["0", "no", "false", "off"]:
        _logger.warning("The configuration value of bicep.use_binary_from_path has been reset")
        remove_use_binary_from_path_config(cli_ctx)


def is_bicep_file(file_path):
    return file_path.lower().endswith(".bicep") if file_path else False


def is_bicepparam_file(file_path):
    return file_path.lower().endswith(".bicepparam") if file_path else False


def get_bicep_available_release_tags():
    try:
        os.environ.setdefault("CURL_CA_BUNDLE", certifi.where())
        response = requests.get("https://aka.ms/BicepReleases", verify=_requests_verify)
        return [release["tag_name"] for release in response.json()]
    except OSError as err:
        raise ClientRequestError(f"Error while attempting to retrieve available Bicep versions: {err}.")


def get_bicep_latest_release_tag():
    try:
        os.environ.setdefault("CURL_CA_BUNDLE", certifi.where())
        response = requests.get("https://aka.ms/BicepLatestRelease", verify=_requests_verify)
        response.raise_for_status()
        return response.json()["tag_name"]
    except requests.RequestException as err:
        raise ClientRequestError(f"Error while attempting to retrieve the latest Bicep version: {err}.")


def bicep_version_greater_than_or_equal_to(cli_ctx, version):
    if _use_binary_from_path(cli_ctx):
        installed_version = _get_bicep_installed_version("bicep")
    else:
        system = platform.system()
        installation_path = _get_bicep_installation_path(system)
        installed_version = _get_bicep_installed_version(installation_path)

    parsed_version = semver.VersionInfo.parse(version)
    return installed_version >= parsed_version


def _bicep_installed_in_ci():
    if "GITHUB_ACTIONS" in os.environ or "TF_BUILD" in os.environ:
        from shutil import which
        installed = which("bicep") is not None

        _logger.debug("Running in a CI environment. Bicep CLI available on PATH: %s.", installed)

        return installed
    return False


def _use_binary_from_path(cli_ctx):
    use_binary_from_path = get_use_binary_from_path_config(cli_ctx)

    _logger.debug('Current value of "use_binary_from_path": %s.', use_binary_from_path)

    if use_binary_from_path == "if_found_in_ci":
        # With if_found_in_ci, GitHub Actions and Azure Pipeline users may expect some delay (usually a few days)
        # in getting the latest version of Bicep CLI, since the az bicep commands will use the pre-installed Bicep CLI
        # on the build agents, but the build agents has a different release cycle. The benefit is that the az bicep
        # commands will not download the Bicep CLI on each pipeline run.
        return _bicep_installed_in_ci()
    if use_binary_from_path in ["1", "yes", "true", "on"]:
        # Setting the config True forces the az bicep commands to use the Bicep executable added to PATH, which
        # indicates that the user is intended to manage the Bicep CLI, and version checks will be disabled.
        return True
    if use_binary_from_path in ["0", "no", "false", "off"]:
        return False

    _logger.warning(
        'The configuration value of bicep.use_binary_from_path is invalid: "%s". Possible values include "if_found_in_ci" (default) and Booleans.',  # pylint: disable=line-too-long
        use_binary_from_path,
    )

    return False


def _load_bicep_version_check_result_from_cache():
    try:
        with open(_bicep_version_check_file_path, "r") as version_check_file:
            version_check_data = json.load(version_check_file)
            latest_release_tag = version_check_data["latestReleaseTag"]
            last_check_time = datetime.strptime(version_check_data["lastCheckTime"], _bicep_version_check_time_format)
            cache_expired = datetime.now() - last_check_time > _bicep_version_check_cache_ttl

            return latest_release_tag, cache_expired
    except (OSError, JSONDecodeError):
        return None, True


def _refresh_bicep_version_check_cache(latest_release_tag):
    with open(_bicep_version_check_file_path, "w+") as version_check_file:
        version_check_data = {
            "lastCheckTime": datetime.now().strftime(_bicep_version_check_time_format),
            "latestReleaseTag": latest_release_tag,
        }
        json.dump(version_check_data, version_check_file)


def _get_bicep_installed_version(bicep_executable_path):
    installed_version_output = _run_command(bicep_executable_path, ["--version"])
    return _extract_version(installed_version_output)


def _is_arm_architecture(machine):
    return machine in ("arm64", "aarch64", "aarch64_be", "armv8b", "armv8l")


def _has_musl_library_only():
    return os.path.exists("/lib/ld-musl-x86_64.so.1") and not os.path.exists("/lib/x86_64-linux-gnu/libc.so.6")


def _get_bicep_download_url(system, machine, release_tag, target_platform=None):
    if not target_platform:
        if system == "Windows" and _is_arm_architecture(machine):
            target_platform = "win-arm64"
        elif system == "Windows":
            # default to x64
            target_platform = "win-x64"
        elif system == "Linux" and _is_arm_architecture(machine):
            target_platform = "linux-arm64"
        elif system == "Linux" and _has_musl_library_only():
            # check for alpine linux
            target_platform = "linux-musl-x64"
        elif system == "Linux":
            # default to x64
            target_platform = "linux-x64"
        elif system == "Darwin" and _is_arm_architecture(machine):
            target_platform = "osx-arm64"
        elif system == "Darwin":
            # default to x64
            target_platform = "osx-x64"
        else:
            raise ValidationError(f'The platform "{system}" is not supported.')

    extension = ".exe" if target_platform.startswith("win-") else ""
    asset_name = f"bicep-{target_platform}{extension}"

    return f"https://downloads.bicep.azure.com/{release_tag}/{asset_name}"


def _get_bicep_installation_path(system):
    if system == "Windows":
        return os.path.join(_bicep_installation_dir, "bicep.exe")
    if system in ("Linux", "Darwin"):
        return os.path.join(_bicep_installation_dir, "bicep")

    raise ValidationError(f'The platform "{system}" is not supported.')


def _extract_version(text):
    semver_match = re.search(_semver_pattern, text)
    return semver.VersionInfo.parse(semver_match.group(0)) if semver_match else None


def _get_bicep_env_vars(custom_env=None):
    env_vars = (custom_env or os.environ).copy()

    # See https://github.com/Azure/azure-cli/issues/29828 for background on this
    from azure.cli.core._environment import _ENV_AZ_BICEP_GLOBALIZATION_INVARIANT
    env_bicep_globalization_invariant = os.getenv(_ENV_AZ_BICEP_GLOBALIZATION_INVARIANT, 'False')

    if env_bicep_globalization_invariant.lower() in ('true', '1'):
        env_vars['DOTNET_SYSTEM_GLOBALIZATION_INVARIANT'] = '1'

    return env_vars


def _run_command(bicep_installation_path, args, custom_env=None):
    process = subprocess.run(
        [rf"{bicep_installation_path}"] + args,
        capture_output=True,
        env=_get_bicep_env_vars(custom_env))

    try:
        process.check_returncode()
        command_warnings = process.stderr.decode("utf-8")
        if command_warnings:
            _logger.warning(command_warnings)
        return process.stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        stderr_output = process.stderr.decode("utf-8")
        errors = []

        for line in stderr_output.splitlines():
            if re.match(_bicep_diagnostic_warning_pattern, line):
                _logger.warning(line)
            else:
                errors.append(line)

        error_msg = os.linesep.join(errors)
        raise UnclassifiedUserFault(error_msg)


def _template_schema_to_target_scope(template_schema):
    template_schema_match = re.search(_template_schema_pattern, template_schema)
    template_type = template_schema_match.group("templateType") if template_schema_match else None
    template_type_lower = template_type.lower() if template_type else None

    if template_type_lower == "deployment":
        return "resourceGroup"
    if template_type_lower == "subscriptiondeployment":
        return "subscription"
    if template_type_lower == "managementgroupdeployment":
        return "managementGroup"
    if template_type_lower == "tenantdeployment":
        return "tenant"
    return None
