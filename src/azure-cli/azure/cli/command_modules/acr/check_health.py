# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from knack.util import CLIError
from knack.log import get_logger
from .custom import get_docker_command
from ._docker_utils import _get_aad_token
from .helm import get_helm_command
from ._utils import get_registry_by_name, resolve_identity_client_id
from ._errors import ErrorClass
from ._format import add_timestamp

logger = get_logger(__name__)

DOCKER_PULL_SUCCEEDED = "Downloaded newer image for {}"
DOCKER_IMAGE_UP_TO_DATE = "Image is up to date for {}"
IMAGE = "mcr.microsoft.com/mcr/hello-world:latest"
FAQ_MESSAGE = "\nPlease refer to https://aka.ms/acr/health-check for more information."
ERROR_MSG_DEEP_LINK = "\nPlease refer to https://aka.ms/acr/errors#{} for more information."
MIN_HELM_VERSION = "2.11.0"
HELM_VERSION_REGEX = re.compile(r'(SemVer|Version):"v([.\d]+)"')
ACR_CHECK_HEALTH_MSG = "Try running 'az acr check-health -n {} --yes' to diagnose this issue."
RECOMMENDED_NOTARY_VERSION = "0.6.0"
NOTARY_VERSION_REGEX = re.compile(r'Version:\s+([.\d]+)')
DOCKER_PULL_WRONG_PLATFORM = 'cannot be used on this platform'

# Utilities functions
def print_pass(message):
    logger.warning("%s : OK", str(message))


def _handle_error(error, ignore_errors):
    if ignore_errors:
        logger.error(error.get_error_message())
    else:
        error_msg = ERROR_MSG_DEEP_LINK.format(error.error_title.lower())
        raise CLIError(error.get_error_message(error_msg))


def _subprocess_communicate(command_parts, shell=False):
    from subprocess import PIPE, Popen, CalledProcessError
    output, stderr = "", ""
    succeeded = False

    try:
        p = Popen(command_parts, stdout=PIPE, stderr=PIPE, shell=shell)
        output, stderr = p.communicate()
        output = output.decode('UTF-8').rstrip()
        stderr = stderr.decode('UTF-8').rstrip()
        exit_code = p.returncode
    except CalledProcessError as e:
        stderr = str(e)

    warning = None
    if stderr.lower().startswith("warning"):
        warning = stderr
        stderr = None

    if exit_code == 0:
        succeeded = True
        stderr = None

    if stderr:
        stderr = "Failed to run command '{}'. {}".format(
            ' '.join(command_parts),
            stderr
        )
    return output, warning, stderr, succeeded


# Retrieve blob identified by digest - GET {url}/v2/{name}/blobs/{digest}
def _get_blob(login_server, repository_name, digest):
    return 'https://{}/v2/{}/blobs/{}'.format(login_server, repository_name, digest)

# Checks inputted image or tag for possible matches
def _check_image_match(cmd,
                       registry_name,
                       repository_name,
                       login_server,
                       username,
                       password,
                       image):
    from difflib import get_close_matches
    from .manifest import _get_manifest_path
    from .repository import(
        acr_repository_show_tags,
        _obtain_data_from_registry)

    if 'sha256' not in image:
        tags = acr_repository_show_tags(
            cmd,
            registry_name=registry_name,
            repository=repository_name,
            orderby=None,
            username=username,
            password=password)
        # Get a list of tags that have at least 80% similarity with the inputted image name
        matches = get_close_matches(image, tags, n=1, cutoff=0.8)

        if matches:
            raise CLIError("Tag '{}' not found. Did you mean to input '{}'?".format(image, matches[0]))
        return

    # If digest is used, get all digests
    image_digest_list = _obtain_data_from_registry(
        login_server=login_server,
        path=_get_manifest_path(repository_name),
        username=username,
        password=password,
        result_index='manifests',
        orderby=None)

    # Get a list of digests that have at least 80% similarity with the inputted image name
    digests = [item['digest'] for item in image_digest_list]
    matches = get_close_matches(image, digests, n=1, cutoff=0.8)

    if matches:
        raise CLIError("Image '{}' not found. Did you mean to input '{}'?".format(image, matches[0]))
    return

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
        logger.warning("Docker daemon status: available")

    # Docker version check
    output, warning, stderr, succeeded = _subprocess_communicate(
        [docker_command, "version", "--format", "'Docker version {{.Server.Version}}, "
         "build {{.Server.GitCommit}}, platform {{.Server.Os}}/{{.Server.Arch}}'"])
    if not succeeded:
        _handle_error(DOCKER_VERSION_ERROR.append_error_message(stderr), ignore_errors)
    else:
        if warning:
            logger.warning(warning)
        logger.warning("Docker version: %s", output)

    # Docker pull check - only if docker daemon is available
    if docker_daemon_available:
        if not yes:
            from knack.prompting import prompt_y_n
            confirmation = prompt_y_n("This will pull the image {}. Proceed?".format(IMAGE))
            if not confirmation:
                logger.warning("Skipping pull check.")
                return

        output, warning, stderr, succeeded = _subprocess_communicate([docker_command, "pull", IMAGE])

        if not succeeded:
            if stderr and DOCKER_PULL_WRONG_PLATFORM in stderr:
                print_pass("Docker pull of '{}'".format(IMAGE))
                logger.warning("Image '%s' can be pulled but cannot be used on this platform", IMAGE)
                return
            _handle_error(DOCKER_PULL_ERROR.append_error_message(stderr), ignore_errors)
        else:
            if warning:
                logger.warning(warning)
            print_pass("Docker pull of '{}'".format(IMAGE))


# Get current CLI version
def _get_cli_version():
    from azure.cli.core import __version__ as core_version
    logger.warning('Azure CLI version: %s', core_version)

# Get helm versions
def _get_helm_version(ignore_errors):
    from ._errors import HELM_VERSION_ERROR
    from packaging.version import parse  # pylint: disable=import-error,no-name-in-module

    # Helm command check
    helm_command, error = get_helm_command(is_diagnostics_context=True)

    if error:
        _handle_error(error, ignore_errors)
        return

    # Helm version check
    output, warning, stderr, succeeded = _subprocess_communicate([helm_command, "version", "--client"])

    if not succeeded:
        _handle_error(HELM_VERSION_ERROR.append_error_message(stderr), ignore_errors)
        return

    if warning:
        logger.warning(warning)

    # Retrieve the helm version if regex pattern is found
    match_obj = HELM_VERSION_REGEX.search(output)
    if match_obj:
        output = match_obj.group(2)

    logger.warning("Helm version: %s", output)

    # Display an error message if the current helm version < min required version
    if match_obj and parse(output) < parse(MIN_HELM_VERSION):
        obsolete_ver_error = HELM_VERSION_ERROR.set_error_message(
            "Current Helm client version is not recommended. Please upgrade your Helm client to at least version {}."
            .format(MIN_HELM_VERSION))
        _handle_error(obsolete_ver_error, ignore_errors)


def _get_notary_version(ignore_errors):
    from ._errors import NOTARY_VERSION_ERROR
    from .notary import get_notary_command
    from packaging.version import parse  # pylint: disable=import-error,no-name-in-module

    # Notary command check
    notary_command, error = get_notary_command(is_diagnostics_context=True)

    if error:
        _handle_error(error, ignore_errors)
        return

    # Notary version check
    output, warning, stderr, succeeded = _subprocess_communicate([notary_command, "version"])

    if not succeeded:
        _handle_error(NOTARY_VERSION_ERROR.append_error_message(stderr), ignore_errors)
        return

    if warning:
        logger.warning(warning)

    # Retrieve the notary version if regex pattern is found
    match_obj = NOTARY_VERSION_REGEX.search(output)
    if match_obj:
        output = match_obj.group(1)

    logger.warning("Notary version: %s", output)

    # Display error if the current version does not match the recommended version
    if match_obj and parse(output) != parse(RECOMMENDED_NOTARY_VERSION):
        version_msg = "upgrade"
        if parse(output) > parse(RECOMMENDED_NOTARY_VERSION):
            version_msg = "downgrade"
        obsolete_ver_error = NOTARY_VERSION_ERROR.set_error_message(
            "Current notary version is not recommended. Please {} your notary client to version {}."
            .format(version_msg, RECOMMENDED_NOTARY_VERSION))
        _handle_error(obsolete_ver_error, ignore_errors)


# Checks for the connectivity
# Check DNS lookup and access to challenge endpoint
def _get_registry_status(login_server, registry_name, ignore_errors):
    import socket

    registry_ip = None

    try:
        registry_ip = socket.gethostbyname(login_server)
    except (socket.gaierror, UnicodeError):
        # capture UnicodeError for https://github.com/Azure/azure-cli/issues/12936
        pass

    if not registry_ip:
        from ._errors import CONNECTIVITY_DNS_ERROR
        _handle_error(CONNECTIVITY_DNS_ERROR.format_error_message(login_server), ignore_errors)
        return False

    print_pass("DNS lookup to {} at IP {}".format(login_server, registry_ip))

    import requests
    from requests.exceptions import SSLError, RequestException
    from azure.cli.core.util import should_disable_connection_verify

    try:
        request_url = 'https://' + login_server + '/v2/'
        logger.debug(add_timestamp("Sending a HTTP GET request to {}".format(request_url)))
        challenge = requests.get(request_url, verify=(not should_disable_connection_verify()))
    except SSLError:
        from ._errors import CONNECTIVITY_SSL_ERROR
        _handle_error(CONNECTIVITY_SSL_ERROR.format_error_message(login_server), ignore_errors)
        return False
    except RequestException:
        from ._errors import CONNECTIVITY_CHALLENGE_ERROR
        _handle_error(CONNECTIVITY_CHALLENGE_ERROR.format_error_message(login_server), ignore_errors)
        return False

    if challenge.status_code == 403:
        from ._errors import CONNECTIVITY_FORBIDDEN_ERROR
        _handle_error(CONNECTIVITY_FORBIDDEN_ERROR.format_error_message(login_server, registry_name), ignore_errors)
        return False
    return True


def _get_endpoint_and_token_status(cmd, login_server, ignore_errors):
    from ._errors import CONNECTIVITY_CHALLENGE_ERROR, CONNECTIVITY_AAD_LOGIN_ERROR, \
        CONNECTIVITY_REFRESH_TOKEN_ERROR, CONNECTIVITY_ACCESS_TOKEN_ERROR, \
        CONNECTIVITY_TOOMANYREQUESTS_ERROR

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

        if result_from_token.error_title == CONNECTIVITY_TOOMANYREQUESTS_ERROR.error_title:
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

def _check_registry_health(cmd,
                           registry_name,
                           registry,
                           login_server,
                           ignore_errors):
    from azure.cli.core.profiles import ResourceType

    status_validated = _get_registry_status(login_server, registry_name, ignore_errors)
    if status_validated:
        _get_endpoint_and_token_status(cmd, login_server, ignore_errors)

    if cmd.supported_api_version(min_api='2020-11-01-preview', resource_type=ResourceType.MGMT_CONTAINERREGISTRY):  # pylint: disable=too-many-nested-blocks
        # CMK settings
        if registry and registry.encryption and registry.encryption.key_vault_properties:  # pylint: disable=too-many-nested-blocks
            client_id = registry.encryption.key_vault_properties.identity
            valid_identity = False
            if registry.identity:
                valid_identity = ((client_id == 'system') and
                                  bool(registry.identity.principal_id))  # use system identity?
                if not valid_identity and registry.identity.user_assigned_identities:
                    for k, v in registry.identity.user_assigned_identities.items():
                        if v.client_id == client_id:
                            from msrestazure.azure_exceptions import CloudError
                            try:
                                valid_identity = (resolve_identity_client_id(cmd.cli_ctx, k) == client_id)
                            except CloudError:
                                pass
            if not valid_identity:
                from ._errors import CMK_MANAGED_IDENTITY_ERROR
                _handle_error(CMK_MANAGED_IDENTITY_ERROR.format_error_message(registry_name), ignore_errors)


def _check_private_endpoint(cmd,
                            registry_name,
                            registry,
                            vnet_of_private_endpoint):  # pylint: disable=too-many-locals, too-many-statements
    import socket
    from msrestazure.tools import parse_resource_id, is_valid_resource_id, resource_id

    if registry_name is None:
        raise CLIError("Registry name must be provided to verify DNS routings of its private endpoints")

    if not registry.private_endpoint_connections:
        raise CLIError('Registry "{}" doesn\'t have private endpoints to verify DNS routings.'.format(registry_name))

    if is_valid_resource_id(vnet_of_private_endpoint):
        res = parse_resource_id(vnet_of_private_endpoint)
        if not res.get("type") or res.get("type").lower() != 'virtualnetworks' or not res.get('name'):
            raise CLIError('"{}" is not a valid resource id of a virtual network'.format(vnet_of_private_endpoint))
    else:
        res = parse_resource_id(registry.id)
        vnet_of_private_endpoint = resource_id(name=vnet_of_private_endpoint, resource_group=res['resource_group'],
                                               namespace='Microsoft.Network', type='virtualNetworks',
                                               subscription=res['subscription'])

    # retrieve FQDNs for registry and its data endpoint
    from .aaz.latest.network.nic import Show as NICShow
    from .aaz.latest.network.private_endpoint import Show as PEShow

    pe_ids = [e.private_endpoint.id for e in registry.private_endpoint_connections if e.private_endpoint]
    dns_mappings = {}

    for pe_id in pe_ids:
        res = parse_resource_id(pe_id)
        pe = PEShow(cli_ctx=cmd.cli_ctx)(command_args={
            "name": res['name'],
            "subscription": res['subscription'],
            "resource_group": res['resource_group']
        })
        if pe["subnet"]["id"].lower().startswith(vnet_of_private_endpoint.lower()):
            nic_id = pe["networkInterfaces"][0]["id"]
            nic_res = parse_resource_id(nic_id)
            nic = NICShow(cli_ctx=cmd.cli_ctx)(command_args={
                "name": nic_res['name'],
                "subscription": nic_res['subscription'],
                "resource_group": nic_res['resource_group']
            })
            for dns_config in nic["ipConfigurations"]:
                if dns_config["privateLinkConnectionProperties"]["fqdns"][0] in dns_mappings:
                    err = ('Registry "{}" has more than one private endpoint in the vnet of "{}".'
                           ' DNS routing will be unreliable')
                    raise CLIError(err.format(registry_name, vnet_of_private_endpoint))
                dns_mappings[dns_config["privateLinkConnectionProperties"]["fqdns"][0]] = dns_config["privateIPAddress"]

    dns_ok = True
    if not dns_mappings:
        err = ('Registry "{}" doesn\'t have private endpoints in the vnet of "{}".'
               ' Please make sure you provided correct vnet')
        raise CLIError(err.format(registry_name, vnet_of_private_endpoint))

    for fqdn in dns_mappings:
        try:
            result = socket.gethostbyname(fqdn)
            if result != dns_mappings[fqdn]:
                err = 'DNS routing to registry "%s" through private IP is incorrect. Expect: %s, Actual: %s'
                logger.warning(err, registry_name, dns_mappings[fqdn], result)
                dns_ok = False
        except Exception as e:  # pylint: disable=broad-except
            logger.warning('Error resolving DNS for %s. Ex: %s', fqdn, e)
            dns_ok = False

    if dns_ok:
        print_pass('DNS routing to private endpoint')
    else:
        raise CLIError('DNS routing verification failed')

# Validate --image input
def validate_image(cmd,
                   registry_name,
                   repository_name,
                   login_server,
                   username,
                   password,
                   image):
    from .manifest import _get_v2_manifest_path

    from ._docker_utils import (
        request_data_from_registry,
        get_manifest_authorization_header,
        RegistryException
    )

    try:
        request_data_from_registry(
            http_method='get',
            login_server=login_server,
            path=_get_v2_manifest_path(repository_name, image),
            username=username,
            password=password,
            json_payload=None,
            file_payload=None,
            manifest_headers=get_manifest_authorization_header(username, password),
            params=image)

    except RegistryException as e:
        if e.status_code == 404:
            _check_image_match(cmd,
                               registry_name,
                               repository_name,
                               login_server,
                               username,
                               password,
                               image)
        raise CLIError("{} Please check if image/tag was inputted correctly.".format(str(e)))

# Validate if blob layer can be pulled
def _check_blob(repository_name,
                login_server,
                username,
                password,
                image):

    import requests
    from ._docker_utils import get_manifest_authorization_header, parse_error_message

    # Get manifest
    # GET {url}/v2/{name}/manifests/{reference}
    manifest_url = 'https://{}/v2/{}/manifests/{}'.format(login_server, repository_name, image)

    manifest_response = requests.get(
        manifest_url,
        headers=get_manifest_authorization_header(username, password))

    manifest = manifest_response.json()

    # Get the digest of the smallest blob for performance purposes
    smallest_blob = min(manifest['layers'], key=lambda layer: layer['size'])
    digest = smallest_blob['digest']

    # Get blob
    request_url = _get_blob(login_server, repository_name, digest)
    logger.debug(add_timestamp("Sending a HTTP GET request to {}".format(request_url)))

    res = requests.get(request_url, auth=(username, password))

    # Return server error message; if server error not available, will return error message below
    if res.status_code >= 400:
        raise CLIError(parse_error_message('Could not get the requested data.', res), res.status_code)
    # Check if image or tag was inputted and return appropriate message
    if res.status_code < 400 and 'sha256' not in image:
        print_pass("Blobs referenced by tag '{}' can be pulled from registry '{}'".format(image, login_server))
    else:
        print_pass("Blobs in image '{}' can be pulled from registry '{}'".format(image, login_server))

# General command
def acr_check_health(cmd,  # pylint: disable useless-return
                     vnet=None,
                     ignore_errors=False,
                     yes=False,
                     registry_name=None,
                     repository_name=None,
                     image=None,
                     resource_group_name=None):
    from azure.cli.core.util import in_cloud_console
    from .repository import get_access_credentials
    from ._utils import get_resource_group_name_by_registry_name

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    registry = None

    # Connectivity
    try:
        registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name, rg)
        login_server = registry.login_server.rstrip('/')
    except CLIError:
        from ._docker_utils import get_login_server_suffix
        suffix = get_login_server_suffix(cmd.cli_ctx)

        if not suffix:
            from ._errors import LOGIN_SERVER_ERROR
            _handle_error(LOGIN_SERVER_ERROR.format_error_message(registry_name), ignore_errors)
            return

    # Get the access credentials for the registry
    login_server, username, password = get_access_credentials(
        cmd,
        registry_name=registry_name,
        tenant_suffix=None,
        username=None,
        password=None,
        repository=repository_name,
        permission='pull')

    in_cloud_console = in_cloud_console()
    if in_cloud_console:
        logger.warning("Environment checks are not supported in Azure Cloud Shell.")
    else:
        _get_docker_status_and_version(ignore_errors, yes)
        _get_cli_version()

    _check_registry_health(cmd,
                           registry_name,
                           registry,
                           login_server,
                           ignore_errors)

    # If repository and image are provided, validate image input
    # Then check if blob layer can be pulled
    if (image and repository_name):
        validate_image(cmd,
                       registry_name,
                       repository_name,
                       login_server,
                       username,
                       password,
                       image)
        _check_blob(repository_name,
                    login_server,
                    username,
                    password,
                    image)

    if vnet:
        _check_private_endpoint(cmd, registry_name, vnet)

    if not in_cloud_console:
        _get_helm_version(ignore_errors)
        _get_notary_version(ignore_errors)
    logger.warning(FAQ_MESSAGE)
