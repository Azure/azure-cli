# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import stat
import platform
import subprocess

from pathlib import Path
from contextlib import suppress

import requests
import semver

from six.moves.urllib.request import urlopen
from knack.log import get_logger
from azure.cli.core.azclierror import (
    FileOperationError,
    ValidationError,
    UnclassifiedUserFault,
    ClientRequestError,
    InvalidTemplateError,
)

# See: https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
_semver_pattern = r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"  # pylint: disable=line-too-long

# See: https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/template-syntax#template-format
_template_schema_pattern = r"https?://schema\.management\.azure\.com/schemas/[0-9a-zA-Z-]+/(?P<templateType>[a-zA-Z]+)Template\.json#?"  # pylint: disable=line-too-long

_logger = get_logger(__name__)


def validate_bicep_target_scope(template_schema, deployment_scope):
    target_scope = _template_schema_to_target_scope(template_schema)
    if target_scope != deployment_scope:
        raise InvalidTemplateError(
            f'The target scope "{target_scope}" does not match the deployment scope "{deployment_scope}".'
        )


def run_bicep_command(args, auto_install=True, check_upgrade=True):
    installation_path = _get_bicep_installation_path(platform.system())
    installed = os.path.isfile(installation_path)

    if not installed:
        if auto_install:
            ensure_bicep_installation(stdout=False)
        else:
            raise FileOperationError('Bicep CLI not found. Install it now by running "az bicep install".')
    elif check_upgrade:
        with suppress(ClientRequestError):
            # Checking upgrade should ignore connection issues.
            # Users may continue using the current installed version.
            installed_version = _get_bicep_installed_version(installation_path)
            latest_release_tag = get_bicep_latest_release_tag()
            latest_version = _extract_semver(latest_release_tag)
            if installed_version and latest_version and semver.compare(installed_version, latest_version) < 0:
                _logger.warning(
                    'A new Bicep release is available: %s. Upgrade now by running "az bicep upgrade".',
                    latest_release_tag,
                )

    return _run_command(installation_path, args)


def ensure_bicep_installation(release_tag=None, stdout=True):
    system = platform.system()
    installation_path = _get_bicep_installation_path(system)

    if os.path.isfile(installation_path):
        if not release_tag:
            return

        installed_version = _get_bicep_installed_version(installation_path)
        target_version = _extract_semver(release_tag)
        if installed_version and target_version and semver.compare(installed_version, target_version) == 0:
            return

    installation_dir = os.path.dirname(installation_path)
    if not os.path.exists(installation_dir):
        os.makedirs(installation_dir)

    try:
        release_tag = release_tag if release_tag else get_bicep_latest_release_tag()
        if stdout:
            if release_tag:
                print(f"Installing Bicep CLI {release_tag}...")
            else:
                print("Installing Bicep CLI...")

        request = urlopen(_get_bicep_download_url(system, release_tag))
        with open(installation_path, "wb") as f:
            f.write(request.read())

        os.chmod(installation_path, os.stat(installation_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if stdout:
            print(f'Successfully installed Bicep CLI to "{installation_path}".')
        else:
            _logger.info(
                "Successfully installed Bicep CLI to %s",
                installation_path,
            )
    except IOError as err:
        raise ClientRequestError(f"Error while attempting to download Bicep CLI: {err}")


def is_bicep_file(file_path):
    return file_path.lower().endswith(".bicep")


def get_bicep_available_release_tags():
    try:
        response = requests.get("https://api.github.com/repos/Azure/bicep/releases")
        return [release["tag_name"] for release in response.json()]
    except IOError as err:
        raise ClientRequestError(f"Error while attempting to retrieve available Bicep versions: {err}.")


def get_bicep_latest_release_tag():
    try:
        response = requests.get("https://api.github.com/repos/Azure/bicep/releases/latest")
        return response.json()["tag_name"]
    except IOError as err:
        raise ClientRequestError(f"Error while attempting to retrieve the latest Bicep version: {err}.")


def _get_bicep_installed_version(bicep_executable_path):
    installed_version_output = _run_command(bicep_executable_path, ["--version"])
    return _extract_semver(installed_version_output)


def _get_bicep_download_url(system, release_tag):
    download_url = f"https://github.com/Azure/bicep/releases/download/{release_tag}/{{}}"

    if system == "Windows":
        return download_url.format("bicep-win-x64.exe")
    if system == "Linux":
        if os.path.exists("/lib/ld-musl-x86_64.so.1"):
            return download_url.format("bicep-linux-musl-x64")
        return download_url.format("bicep-linux-x64")
    if system == "Darwin":
        return download_url.format("bicep-osx-x64")

    raise ValidationError(f'The platform "{format(system)}" is not supported.')


def _get_bicep_installation_path(system):
    installation_folder = os.path.join(str(Path.home()), ".azure", "bin")

    if system == "Windows":
        return os.path.join(installation_folder, "bicep.exe")
    if system in ("Linux", "Darwin"):
        return os.path.join(installation_folder, "bicep")

    raise ValidationError(f'The platform "{format(system)}" is not supported.')


def _extract_semver(text):
    semver_match = re.search(_semver_pattern, text)
    return semver_match.group(0) if semver_match else None


def _run_command(bicep_installation_path, args):
    process = subprocess.run([rf"{bicep_installation_path}"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        process.check_returncode()
        command_warnings = process.stderr.decode("utf-8")
        if command_warnings:
            _logger.warning(command_warnings)
        return process.stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        raise UnclassifiedUserFault(process.stderr.decode("utf-8"))


def _template_schema_to_target_scope(template_schema):
    template_schema_match = re.search(_template_schema_pattern, template_schema)
    template_type = template_schema_match.group('templateType') if template_schema_match else None
    template_type_lower = template_type.lower() if template_type else None
    print(template_type)

    if template_type_lower == "deployment":
        return "resourceGroup"
    if template_type_lower == "subscriptiondeployment":
        return "subscription"
    if template_type_lower == "managementgroupdeployment":
        return "managementGroup"
    if template_type_lower == "tenantdeployment":
        return "tenant"
    return None
