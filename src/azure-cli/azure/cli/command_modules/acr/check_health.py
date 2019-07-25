# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import re
import sys
from knack.util import CLIError
from knack.log import get_logger
from .custom import get_docker_command
from ._docker_utils import _get_aad_token
from .helm import get_helm_command
from ._utils import get_registry_by_name
from ._errors import ErrorClass

logger = get_logger(__name__)

DOCKER_PULL_SUCCEEDED = "Downloaded newer image for {}"
DOCKER_IMAGE_UP_TO_DATE = "Image is up to date for {}"
IMAGE = "mcr.microsoft.com/mcr/hello-world:latest"
FAQ_MESSAGE = "\nPlease refer to https://aka.ms/acr/health-check for more information."
MIN_HELM_VERSION = "2.11.0"
HELM_VERSION_REGEX = re.compile(r'SemVer:"v([.\d]+)"', re.I)


# Utilities functions
def print_pass(message):
    from colorama import Fore, Style, init
    init()
    print(str(message) + " : " + Fore.GREEN + "OK" + Style.RESET_ALL, file=sys.stderr)


def _handle_error(error, ignore_errors):
    if ignore_errors:
        logger.error(error.get_error_message())
    else:
        raise CLIError(error.get_error_message(FAQ_MESSAGE))


def _subprocess_communicate(command_parts, shell=False):
    from subprocess import PIPE, Popen, CalledProcessError
    output, stderr = "", ""

    try:
        p = Popen(command_parts, stdout=PIPE, stderr=PIPE, shell=shell)
        output, stderr = p.communicate()
        output = output.decode('UTF-8').rstrip()
        stderr = stderr.decode('UTF-8').rstrip()
    except CalledProcessError as e:
        stderr = str(e)

    warning = None
    if stderr.lower().startswith("warning"):
        warning = stderr
        stderr = None

    if stderr:
        stderr = "Failed to run command '{}'. {}".format(
            ' '.join(command_parts),
            stderr
        )
    return output, warning, stderr


# Checks for the environment
# Checks docker command, docker daemon, docker version and docker pull
def _get_docker_status_and_version(ignore_errors, yes):
    from ._errors import DOCKER_DAEMON_ERROR, DOCKER_PULL_ERROR, DOCKER_VERSION_ERROR

    # Docker command and docker daemon check
    docker_command, error = get_docker_command(is_diagnostics_context=True)
    docker_daemon_available = True

    if error:
        _handle_error(error, ignore_errors)
        if error.error_title != DOCKER_DAEMON_ERROR.error_title:
            return  # We cannot proceed if the error is unexpected or with docker command
        docker_daemon_available = False

    if docker_daemon_available:
        print("Docker daemon status: available", file=sys.stderr)

    # Docker version check
    output, warning, stderr = _subprocess_communicate([docker_command, "--version"])
    if stderr:
        _handle_error(DOCKER_VERSION_ERROR.append_error_message(stderr), ignore_errors)
    else:
        if warning:
            logger.warning(warning)
        print("Docker version: {}".format(output), file=sys.stderr)

    # Docker pull check - only if docker daemon is available
    if docker_daemon_available:
        if not yes:
            from knack.prompting import prompt_y_n
            confirmation = prompt_y_n("This will pull the image {}. Proceed?".format(IMAGE))
            if not confirmation:
                logger.warning("Skipping pull check.")
                return

        output, warning, stderr = _subprocess_communicate([docker_command, "pull", IMAGE])

        if stderr:
            _handle_error(DOCKER_PULL_ERROR.append_error_message(stderr), ignore_errors)
        else:
            if warning:
                logger.warning(warning)
            if output.find(DOCKER_PULL_SUCCEEDED.format(IMAGE)) != -1 or \
               output.find(DOCKER_IMAGE_UP_TO_DATE.format(IMAGE)) != -1:
                print_pass("Docker pull of '{}'".format(IMAGE))
            else:
                _handle_error(DOCKER_PULL_ERROR, ignore_errors)


# Get current CLI version
def _get_cli_version():
    from pkg_resources import working_set

    # working_set.by_key is a dictionary with component names as key
    cli_component_name = "azure-cli"
    cli_version = "not found"

    if cli_component_name in working_set.by_key:
        cli_version = working_set.by_key[cli_component_name].version

    print('Azure CLI version: {}'.format(cli_version), file=sys.stderr)


# Get helm versions
def _get_helm_version(ignore_errors):
    from ._errors import HELM_VERSION_ERROR
    from distutils.version import LooseVersion  # pylint: disable=import-error,no-name-in-module

    # Helm command check
    helm_command, error = get_helm_command(is_diagnostics_context=True)

    if error:
        _handle_error(error, ignore_errors)
        return

    # Helm version check
    output, warning, stderr = _subprocess_communicate([helm_command, "version", "--client"])

    if stderr:
        _handle_error(HELM_VERSION_ERROR.append_error_message(stderr), ignore_errors)
        return

    if warning:
        logger.warning(warning)

    # Retrieve the helm version if regex pattern is found
    match_obj = HELM_VERSION_REGEX.search(output)
    if match_obj:
        output = match_obj.group(1)

    print("Helm version: {}".format(output), file=sys.stderr)

    # Display an error message if the current helm version < min required version
    if match_obj and LooseVersion(output) < LooseVersion(MIN_HELM_VERSION):
        obsolete_ver_error = HELM_VERSION_ERROR.set_error_message(
            "Current Helm client version is not recommended. Please upgrade your Helm client to at least version {}."
            .format(MIN_HELM_VERSION))
        _handle_error(obsolete_ver_error, ignore_errors)


def _check_health_environment(ignore_errors, yes):
    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        logger.warning("Environment checks are not supported in Azure Cloud Shell.")
        return

    _get_docker_status_and_version(ignore_errors, yes)
    _get_cli_version()
    _get_helm_version(ignore_errors)


# Checks for the connectivity
# Check DNS lookup and access to challenge endpoint
def _get_registry_status(login_server, registry_name, ignore_errors):
    import socket

    registry_ip = ""

    try:
        registry_ip = socket.gethostbyname(login_server)
    except socket.gaierror:
        pass

    if not registry_ip:
        from ._errors import CONNECTIVITY_DNS_ERROR
        _handle_error(CONNECTIVITY_DNS_ERROR.format_error_message(login_server), ignore_errors)
        return False

    print_pass("DNS lookup to {} at IP {}".format(login_server, registry_ip))

    import requests
    from azure.cli.core.util import should_disable_connection_verify
    challenge = requests.get('https://' + login_server + '/v2/', verify=(not should_disable_connection_verify()))

    if challenge.status_code == 403:
        from ._errors import CONNECTIVITY_FORBIDDEN_ERROR
        _handle_error(CONNECTIVITY_FORBIDDEN_ERROR.format_error_message(login_server, registry_name), ignore_errors)
        return False
    return True


def _get_endpoint_and_token_status(cmd, login_server, ignore_errors):
    from ._errors import CONNECTIVITY_CHALLENGE_ERROR, CONNECTIVITY_AAD_LOGIN_ERROR, \
        CONNECTIVITY_REFRESH_TOKEN_ERROR, CONNECTIVITY_ACCESS_TOKEN_ERROR

    # Check access to login endpoint
    url = 'https://' + login_server + '/v2/'
    result_from_token = _get_aad_token(cmd.cli_ctx, login_server, False, is_diagnostics_context=True)

    if isinstance(result_from_token, ErrorClass):
        if result_from_token.error_title == CONNECTIVITY_CHALLENGE_ERROR.error_title:
            _handle_error(result_from_token, ignore_errors)
            return

        print_pass("Challenge endpoint {}".format(url))

        if result_from_token.error_title == CONNECTIVITY_AAD_LOGIN_ERROR.error_title:
            _handle_error(result_from_token, ignore_errors)
            return

        if result_from_token.error_title == CONNECTIVITY_REFRESH_TOKEN_ERROR.error_title:
            _handle_error(result_from_token, ignore_errors)
            return

        print_pass("Fetch refresh token for registry '{}'".format(login_server))

        if result_from_token.error_title == CONNECTIVITY_ACCESS_TOKEN_ERROR.error_title:
            _handle_error(result_from_token, ignore_errors)
            return

        print_pass("Fetch access token for registry '{}'".format(login_server))

        return

    # If return is not of type ErrorClass, then it is the token
    print_pass("Challenge endpoint {}".format(url))
    print_pass("Fetch refresh token for registry '{}'".format(login_server))
    print_pass("Fetch access token for registry '{}'".format(login_server))


def _check_health_connectivity(cmd, registry_name, ignore_errors):
    if registry_name is None:
        logger.warning("Registry name must be provided to check connectivity.")
        return

    try:
        registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name)
        login_server = registry.login_server.rstrip('/')
    except CLIError:
        from ._docker_utils import get_login_server_suffix
        suffix = get_login_server_suffix(cmd.cli_ctx)

        if not suffix:
            from ._errors import LOGIN_SERVER_ERROR
            _handle_error(LOGIN_SERVER_ERROR.format_error_message(registry_name), ignore_errors)
            return

        login_server = registry_name + suffix

    status_validated = _get_registry_status(login_server, registry_name, ignore_errors)
    if status_validated:
        _get_endpoint_and_token_status(cmd, login_server, ignore_errors)


# General command
def acr_check_health(cmd,  # pylint: disable useless-return
                     ignore_errors=False,
                     yes=False,
                     registry_name=None):

    _check_health_environment(ignore_errors, yes)
    _check_health_connectivity(cmd, registry_name, ignore_errors)
    print(FAQ_MESSAGE, file=sys.stderr)
