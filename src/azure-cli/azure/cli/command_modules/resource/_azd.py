# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
import subprocess
import sys
import re

from knack.log import get_logger
from azure.cli.core.azclierror import (
    ValidationError,
    UnclassifiedUserFault
)
_logger = get_logger(__name__)
_azd_diagnostic_warning_pattern = r"^([^\s].*)\((\d+)(?:,\d+|,\d+,\d+)?\)\s+:\s+(Warning)\s+([a-zA-Z-\d]+):\s*(.*?)\s+\[(.*?)\]$"


def ensure_azd_installation(stdout=True):
    system = platform.system()
    installation_path = _get_azd_installation_path(system)

    if os.path.isfile(installation_path):
        if stdout:
            print("Azure Developer CLI already installed")
        return

    installation_dir = os.path.dirname(installation_path)
    if not os.path.exists(installation_dir):
        os.makedirs(installation_dir)

    try:
        if stdout:
            print("Installing Azure Developer CLI...")
        # os.chmod(installation_path, os.stat(installation_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        _install_azd(system)

        if stdout:
            print(f'Successfully installed Azure Developer CLI to "{installation_path}".')
        else:
            _logger.info(
                "Successfully installed Azure Developer CLI to %s",
                installation_path,
            )
    except IOError as err:
        raise ClientRequestError(f"Error while attempting to download Azure Developer CLI: {err}")

def _get_azd_installation_path(system):
    _azd_installation_dir = os.getenv('LOCALAPPDATA')
    if system == "Windows":
        return os.path.join(_azd_installation_dir, "Programs\\Azure Dev CLI\\azd.exe")

    raise ValidationError(f'The platform "{system}" is not supported.')

def _install_azd(system):

    if system == "Windows":
        subprocess.run(
            'powershell -ex AllSigned -c "Invoke-RestMethod https://aka.ms/install-azd.ps1 | Invoke-Expression"',
            stdout=sys.stdout)
        return

    raise ValidationError(f'The platform "{system}" is not supported.')

def run_azd_command(args, auto_install=True, **kwargs):
    installation_path = _get_azd_installation_path(platform.system())
    installed = os.path.isfile(installation_path)

    if not installed:
        if auto_install:
            ensure_azd_installation(stdout=False)
        else:
            raise FileOperationError('Azure Developer CLI not found. Install it now by running "az dev install".')

    command = [rf"{installation_path}"] + args
    for k,v in kwargs.items():
        if v is not None:
            command += ['--'+k, v]
    return _run_command(command)

def _run_command(command):
    try:
        subprocess.run(command)
    except Exception as ex:
        raise(ex)