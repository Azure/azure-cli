# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

UPGRADE_MSG = 'Not able to upgrade automatically. Instructions can be found at https://aka.ms/doc/InstallAzureCli'
SECRET_STORE_DEMO = "secret_store_demo"

def rest_call(cmd, url, method=None, headers=None, uri_parameters=None,
              body=None, skip_authorization_header=False, resource=None, output_file=None):
    from azure.cli.core.commands.transform import unregister_global_transforms
    # No transform should be performed on `az rest`.
    unregister_global_transforms(cmd.cli_ctx)

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


def upgrade_version(cmd, update_all=None, yes=None):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches, no-member, unused-argument
    import platform
    import sys
    import subprocess
    from azure.cli.core import telemetry
    from azure.cli.core import __version__ as local_version
    from azure.cli.core._environment import _ENV_AZ_INSTALLER
    from azure.cli.core.extension import get_extensions, WheelExtension
    from packaging.version import parse

    update_cli = True
    from azure.cli.core.util import get_latest_from_github
    try:
        latest_version = get_latest_from_github()
        if latest_version and parse(latest_version) <= parse(local_version):
            logger.warning("You already have the latest azure-cli version: %s", local_version)
            update_cli = False
            if not update_all:
                return
    except Exception as ex:  # pylint: disable=broad-except
        logger.debug("Failed to get the latest version. %s", str(ex))
    exts = [ext.name for ext in get_extensions(ext_type=WheelExtension)] if update_all else []

    exit_code = 0
    installer = os.getenv(_ENV_AZ_INSTALLER) or ''
    installer = installer.upper()
    if update_cli:
        latest_version_msg = 'It will be updated to {}.'.format(latest_version) if yes \
            else 'Latest version available is {}.'.format(latest_version)
        logger.warning("Your current Azure CLI version is %s. %s", local_version, latest_version_msg)
        from knack.prompting import prompt_y_n, NoTTYException
        if not yes:
            logger.warning("Please check the release notes first: https://docs.microsoft.com/"
                           "cli/azure/release-notes-azure-cli")
            try:
                confirmation = prompt_y_n("Do you want to continue?", default='y')
            except NoTTYException:
                from azure.cli.core.azclierror import UnclassifiedUserFault
                raise UnclassifiedUserFault("No tty available.", "Please run command with --yes.")

            if not confirmation:
                telemetry.set_success("Upgrade stopped by user")
                return

        if installer == 'DEB':
            from azure.cli.core.util import in_cloud_console
            if in_cloud_console():
                raise CLIError("az upgrade is not supported in Cloud Shell.")
            apt_update_cmd = 'apt-get update'.split()
            az_update_cmd = 'apt-get install --only-upgrade -y azure-cli'.split()
            if os.geteuid() != 0:  # pylint: disable=no-member
                apt_update_cmd.insert(0, 'sudo')
                az_update_cmd.insert(0, 'sudo')
            exit_code = subprocess.call(apt_update_cmd)
            if exit_code == 0:
                logger.debug("Update azure cli with '%s'", " ".join(az_update_cmd))
                exit_code = subprocess.call(az_update_cmd)
        elif installer == 'RPM':
            from azure.cli.core.util import get_linux_distro
            distname, _ = get_linux_distro()
            if not distname:
                logger.warning(UPGRADE_MSG)
            else:
                distname = distname.lower().strip()
                if any(x in distname for x in ['centos', 'rhel', 'red hat', 'fedora']):
                    update_cmd = 'yum update -y azure-cli'.split()
                    if os.geteuid() != 0:  # pylint: disable=no-member
                        update_cmd.insert(0, 'sudo')
                    logger.debug("Update azure cli with '%s'", " ".join(update_cmd))
                    exit_code = subprocess.call(update_cmd)
                elif any(x in distname for x in ['opensuse', 'suse', 'sles']):
                    zypper_refresh_cmd = ['zypper', 'refresh']
                    az_update_cmd = 'zypper update -y azure-cli'.split()
                    if os.geteuid() != 0:  # pylint: disable=no-member
                        zypper_refresh_cmd.insert(0, 'sudo')
                        az_update_cmd.insert(0, 'sudo')
                    exit_code = subprocess.call(zypper_refresh_cmd)
                    if exit_code == 0:
                        logger.debug("Update azure cli with '%s'", " ".join(az_update_cmd))
                        exit_code = subprocess.call(az_update_cmd)
                else:
                    logger.warning(UPGRADE_MSG)
        elif installer == 'HOMEBREW':
            logger.debug("Update homebrew formulae")
            exit_code = subprocess.call(['brew', 'update'])
            if exit_code == 0:
                update_cmd = ['brew', 'upgrade', 'azure-cli']
                logger.debug("Update azure cli with '%s'", " ".join(update_cmd))
                exit_code = subprocess.call(update_cmd)
        elif installer == 'PIP':
            pip_args = [sys.executable, '-m', 'pip', 'install', '--upgrade', 'azure-cli', '-vv',
                        '--disable-pip-version-check', '--no-cache-dir']
            logger.debug("Update azure cli with '%s'", " ".join(pip_args))
            exit_code = subprocess.call(pip_args, shell=platform.system() == 'Windows')
        elif installer == 'DOCKER':
            logger.warning("Exit the container to pull latest image with 'docker pull mcr.microsoft.com/azure-cli' "
                           "or run 'pip install --upgrade azure-cli' in this container")
        elif installer == 'MSI':
            exit_code = _upgrade_on_windows()
        else:
            logger.warning(UPGRADE_MSG)
    if exit_code:
        err_msg = "CLI upgrade failed."
        logger.warning(err_msg)
        telemetry.set_failure(err_msg)
        sys.exit(exit_code)

    # Avoid using python modules directly as they may have been changed due to upgrade.
    # If you do need to use them, you may need to reload them and their dependent modules.
    # Otherwise you may have such issue https://github.com/Azure/azure-cli/issues/16952
    import importlib
    import json
    importlib.reload(subprocess)
    importlib.reload(json)

    version_result = subprocess.check_output(['az', 'version', '-o', 'json'], shell=platform.system() == 'Windows')
    version_json = json.loads(version_result)
    new_version = version_json['azure-cli-core']

    if update_cli and new_version == local_version:
        err_msg = "CLI upgrade failed or aborted."
        logger.warning(err_msg)
        telemetry.set_failure(err_msg)
        sys.exit(1)

    if exts:
        logger.warning("Upgrading extensions")
    for ext_name in exts:
        try:
            logger.warning("Checking update for %s", ext_name)
            subprocess.call(['az', 'extension', 'update', '-n', ext_name],
                            shell=platform.system() == 'Windows')
        except Exception as ex:  # pylint: disable=broad-except
            msg = "Extension {} update failed during az upgrade. {}".format(ext_name, str(ex))
            raise CLIError(msg)
    auto_upgrade_msg = "You can enable auto-upgrade with 'az config set auto-upgrade.enable=yes'. " \
        "More details in https://docs.microsoft.com/cli/azure/update-azure-cli#automatic-update"
    logger.warning("Upgrade finished.%s", "" if cmd.cli_ctx.config.getboolean('auto-upgrade', 'enable', False)
                   else auto_upgrade_msg)


def _upgrade_on_windows():
    """Download MSI to a temp folder and install it with msiexec.exe.
    Directly installing from URL may be blocked by policy: https://github.com/Azure/azure-cli/issues/19171
    This also gives the user a chance to manually install the MSI in case of msiexec.exe failure.
    """
    logger.warning("Updating Azure CLI with MSI from https://aka.ms/installazurecliwindows")
    tmp_dir, msi_path = _download_from_url('https://aka.ms/installazurecliwindows')

    logger.warning("Installing MSI")
    import subprocess
    exit_code = subprocess.call(['msiexec.exe', '/i', msi_path])

    if exit_code:
        logger.warning("Installation Failed. You may manually install %s", msi_path)
    else:
        from azure.cli.core.util import rmtree_with_retry
        logger.warning("Succeeded. Deleting %s", tmp_dir)
        rmtree_with_retry(tmp_dir)
    return exit_code


def _download_from_url(url):
    import requests
    from azure.cli.core.util import should_disable_connection_verify
    r = requests.get(url, stream=True, verify=(not should_disable_connection_verify()))
    if r.status_code != 200:
        raise CLIError("Request to {} failed with {}".format(url, r.status_code))

    # r.url is the real path of the msi, like'https://azcliprod.blob.core.windows.net/msi/azure-cli-2.27.1.msi'
    file_name = r.url.rsplit('/')[-1]
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    msi_path = os.path.join(tmp_dir, file_name)
    logger.warning("Downloading MSI to %s", msi_path)

    with open(msi_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)

    # Return both the temp directory and MSI path, like
    # 'C:\Users\<name>\AppData\Local\Temp\tmpzv4pelsf',
    # 'C:\Users\<name>\AppData\Local\Temp\tmpzv4pelsf\azure-cli-2.27.1.msi'
    return tmp_dir, msi_path


def demo_style(cmd, theme=None):  # pylint: disable=unused-argument
    from azure.cli.core.style import Style, print_styled_text, format_styled_text
    if theme:
        format_styled_text.theme = theme
    print_styled_text("[How to call print_styled_text]")
    # Print an empty line
    print_styled_text()
    # Various methods to print
    print_styled_text("- Print using a str")
    print_styled_text("- Print using multiple", "strs")
    print_styled_text((Style.PRIMARY, "- Print using a tuple"))
    print_styled_text((Style.PRIMARY, "- Print using multiple"), (Style.IMPORTANT, "tuples"))
    print_styled_text([(Style.PRIMARY, "- Print using a "), (Style.IMPORTANT, "list")])
    print_styled_text([(Style.PRIMARY, "- Print using multiple")], [(Style.IMPORTANT, "lists")])
    print_styled_text()

    print_styled_text("[Available styles]\n")
    placeholder = '████ {:8s}: {}\n'
    styled_text = [
        (Style.PRIMARY, placeholder.format("White", "Primary text color")),
        (Style.SECONDARY, placeholder.format("Grey", "Secondary text color")),
        (Style.IMPORTANT, placeholder.format("Magenta", "Important text color")),
        (Style.ACTION, placeholder.format(
            "Blue", "Commands, parameters, and system inputs (White in legacy powershell terminal)")),
        (Style.HYPERLINK, placeholder.format("Cyan", "Hyperlink")),
        (Style.ERROR, placeholder.format("Red", "Error message indicator")),
        (Style.SUCCESS, placeholder.format("Green", "Success message indicator")),
        (Style.WARNING, placeholder.format("Yellow", "Warning message indicator")),
    ]
    print_styled_text(styled_text)

    print_styled_text("[interactive]\n")
    # NOTE! Unicode character ⦾ ⦿ will most likely not be displayed correctly
    styled_text = [
        (Style.ACTION, "?"),
        (Style.PRIMARY, " Select a SKU for your app:\n"),
        (Style.PRIMARY, "⦾ Free            "),
        (Style.SECONDARY, "Dev/Test workloads: 1 GB memory, 60 minutes/day compute\n"),
        (Style.PRIMARY, "⦾ Basic           "),
        (Style.SECONDARY, "Dev/Test workloads: 1.75 GB memory, monthly charges apply\n"),
        (Style.PRIMARY, "⦾ Standard        "),
        (Style.SECONDARY, "Production workloads: 1.75 GB memory, monthly charges apply\n"),
        (Style.ACTION, "⦿ Premium         "),
        (Style.SECONDARY, "Production workloads: 3.5 GB memory, monthly charges apply\n"),
    ]
    print_styled_text(styled_text)

    print_styled_text("[progress report]\n")
    # NOTE! Unicode character ✓ will most likely not be displayed correctly
    styled_text = [
        (Style.SUCCESS, '(✓) Done: '),
        (Style.PRIMARY, "Creating a resource group for myfancyapp\n"),
        (Style.SUCCESS, '(✓) Done: '),
        (Style.PRIMARY, "Creating an App Service Plan for myfancyappplan on a "),
        (Style.IMPORTANT, "premium instance"),
        (Style.PRIMARY, " that has a "),
        (Style.IMPORTANT, "monthly charge"),
        (Style.PRIMARY, "\n"),
        (Style.SUCCESS, '(✓) Done: '),
        (Style.PRIMARY, "Creating a webapp named myfancyapp\n"),
    ]
    print_styled_text(styled_text)

    print_styled_text("[error handing]\n")
    styled_text = [
        (Style.ERROR, "ERROR: Command not found: az storage create\n"),
        (Style.PRIMARY, "TRY\n"),
        (Style.ACTION, "az storage account create --name"),
        (Style.PRIMARY, " mystorageaccount "),
        (Style.ACTION, "--resource-group"),
        (Style.PRIMARY, " MyResourceGroup\n"),
        (Style.SECONDARY, "Create a storage account. For more detail, see "),
        (Style.HYPERLINK, "https://docs.microsoft.com/azure/storage/common/storage-account-create?"
                          "tabs=azure-cli#create-a-storage-account-1"),
        (Style.SECONDARY, "\n"),
    ]
    print_styled_text(styled_text)

    print_styled_text("[post-output hint]\n")
    styled_text = [
        (Style.PRIMARY, "The default subscription is "),
        (Style.IMPORTANT, "AzureSDKTest (0b1f6471-1bf0-4dda-aec3-cb9272f09590)"),
        (Style.PRIMARY, ". To switch to another subscription, run "),
        (Style.ACTION, "az account set --subscription"),
        (Style.PRIMARY, " <subscription ID>\n"),
        (Style.WARNING, "WARNING: The subscription has been disabled!\n")
    ]
    print_styled_text(styled_text)

    print_styled_text("[logs]\n")

    # Print logs
    logger.debug("This is a debug log entry.")
    logger.info("This is a info log entry.")
    logger.warning("This is a warning log entry.")
    logger.error("This is a error log entry.")
    logger.critical("This is a critical log entry.")


def secret_store_save(cmd, key_value):
    data = dict(kv.split('=', 1) for kv in key_value)
    from azure.cli.core.util import get_secret_store
    store = get_secret_store(cmd.cli_ctx, SECRET_STORE_DEMO)
    store.save(data)
    logger.warning("Data written to %s: %s",
                   store._persistence.get_location(), data)  # pylint: disable=protected-access


def secret_store_load(cmd):
    from azure.cli.core.util import get_secret_store
    store = get_secret_store(cmd.cli_ctx, SECRET_STORE_DEMO)
    return store.load()
