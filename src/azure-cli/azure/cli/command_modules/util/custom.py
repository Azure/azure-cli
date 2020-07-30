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


def upgrade_version(cmd):
    from azure.cli.core._environment import _ENV_AZ_INSTALLER
    import subprocess
    # TODO check whether it's already the latest version
    try:
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
    except Exception:  # pylint: disable=broad-except
        pass
