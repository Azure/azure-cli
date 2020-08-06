# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def rest_call(cmd, url, method=None, headers=None, uri_parameters=None,
              body=None, skip_authorization_header=False, resource=None, output_file=None):
    from azure.cli.core.util import send_raw_request
    r = send_raw_request(cmd.cli_ctx, method, url, headers, uri_parameters, body,
                         skip_authorization_header, resource, output_file)
    if not output_file and r.content:
        try:
            return r.json()
        except ValueError:
            logger.warning('Not a json response, outputting to stdout. For binary data '
                           'suggest use "--output-file" to write to a file')
            print(r.text)
    return None


def show_version(cmd):  # pylint: disable=unused-argument
    from azure.cli.core.util import get_az_version_json
    versions = get_az_version_json()
    return versions


def upgrade_version(cmd, all=None):
    import subprocess
    from azure.cli.core._environment import _ENV_AZ_INSTALLER
    from azure.cli.core.util import CLI_PACKAGE_NAME, _get_local_versions, _update_latest_from_pypi
    from distutils.version import LooseVersion
    from knack.util import CLIError

    update_cli = True
    versions = _get_local_versions()
    local = versions[CLI_PACKAGE_NAME]['local']
    versions, success = _update_latest_from_pypi(versions)
    if not success:
        raise CLIError("Failed to fetch the latest version. Please check your network connectivity.")

    pypi = versions[CLI_PACKAGE_NAME].get('pypi', None)
    latest_version = pypi
    if pypi and LooseVersion(pypi) <= LooseVersion(local):
        logger.warning("You already have the latest %s: %s", CLI_PACKAGE_NAME, local)
        update_cli = False
        if not all:
            return
    ext_sources = []
    if all:
        from azure.cli.core.extension import get_extensions, WheelExtension
        from azure.cli.core.extension._resolve import resolve_from_index, NoExtensionCandidatesError
        from azure.cli.core.extension.operations import update_extension
        extensions = get_extensions(ext_type=WheelExtension)
        if extensions:
            for ext in extensions:
                try:
                    download_url, _ = resolve_from_index(ext.name, cur_version=ext.version)
                    ext_sources.append((ext.name, download_url))
                except NoExtensionCandidatesError:
                    pass
    if update_cli:
        import os
        installer = os.getenv(_ENV_AZ_INSTALLER)
        if installer == 'DEB':
            subprocess.call('sudo apt-get update && sudo apt-get install --only-upgrade -y azure-cli', shell=True)
        elif installer == 'RPM':
            subprocess.call('sudo yum update -y azure-cli', shell=True)
        elif installer == 'HOMEBREW':
            subprocess.call('brew update && brew upgrade -y azure-cli', shell=True)
        elif installer == 'PIP':
            subprocess.call('pip install --upgrade azure-cli', shell=True)
        elif installer == 'DOCKER':
            logger.warning('Exit the container to pull latest image with docker pull mcr.microsoft.com/azure-cli or pip install --upgrade azure-cli in this container')
        elif installer == 'MSI':
            # TODO put the script in a storage account, download it and store in a tmp dir
            subprocess.call('powershell.exe "C:\\upgrade.ps1"', shell=True)
            # logger.warning('Update with the latest MSI https://aka.ms/installazurecliwindows')
        else:
            logger.warning('Not able to upgrade automatically. Instructions can be found at https://docs.microsoft.com/en-us/cli/azure/install-azure-cli')
    
    for name, download_url in ext_sources:
        logger.warning("Update extension: {}".format(name))
        update_extension(cli_ctx=cmd.cli_ctx, extension_name=name, source=download_url)
