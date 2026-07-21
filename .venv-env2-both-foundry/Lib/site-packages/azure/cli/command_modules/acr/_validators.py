# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.azclierror import FileOperationError, InvalidArgumentValueError
from ._constants import ACR_NAME_VALIDATION_REGEX

BAD_REPO_FQDN = "The positional parameter 'repo_id' must be a fully qualified repository specifier such"\
                " as 'myregistry.azurecr.io/hello-world'."
BAD_PERM_REPO_FQDN = "The positional parameter 'perm_repo_id' must be a fully qualified repository specifier such"\
                     " as 'myregistry.azurecr.io/hello-world'. It may optionally specify a"\
                     " tag such as 'myregistry.azurecr.io/hello-world:latest'."
BAD_MANIFEST_FQDN = "The positional parameter 'manifest_id' must be a fully qualified"\
                    " manifest specifier such as 'myregistry.azurecr.io/hello-world:latest' or"\
                    " 'myregistry.azurecr.io/hello-world@sha256:abc123'."
BAD_REGISTRY_NAME = "Registry names may contain only alpha numeric characters and must be between 5 and 50 characters"
INVALID_LOGIN_SERVER_SUFFIX = "The login server suffix is not valid for the current cloud. Please try again using"\
                              " '{}'."

logger = get_logger(__name__)


def validate_headers(namespace):
    """Extracts multiple space-separated headers in key[=value] format. """
    if isinstance(namespace.headers, list):
        headers_dict = {}
        for item in namespace.headers:
            headers_dict.update(validate_header(item))
        namespace.headers = headers_dict


def validate_header(string):
    """Extracts a single header in key[=value] format. """
    result = {}
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result


def validate_arg(namespace):
    if isinstance(namespace.arg, list):
        arguments_list = []
        for item in namespace.arg:
            arguments_list.append(validate_task_argument(item, False))
        namespace.arg = arguments_list


def validate_secret_arg(namespace):
    if isinstance(namespace.secret_arg, list):
        secret_arguments_list = []
        for item in namespace.secret_arg:
            secret_arguments_list.append(validate_task_argument(item, True))
        namespace.secret_arg = secret_arguments_list


def validate_set(namespace):
    if isinstance(namespace.set_value, list):
        set_list = []
        for item in namespace.set_value:
            set_list.append(validate_task_value(item, False))
        namespace.set_value = set_list


def validate_set_secret(namespace):
    if isinstance(namespace.set_secret, list):
        set_secret_list = []
        for item in namespace.set_secret:
            set_secret_list.append(validate_task_value(item, True))
        namespace.set_secret = set_secret_list


def validate_task_value(string, is_secret):
    """Extracts a single SetValue in key[=value] format. """
    if string:
        comps = string.split('=', 1)
        if len(comps) > 1:
            return {'type': 'SetValue', 'name': comps[0], 'value': comps[1], 'isSecret': is_secret}
        return {'type': 'SetValue', 'name': comps[0], 'value': '', 'isSecret': is_secret}
    return None


def validate_task_argument(string, is_secret):
    """Extracts a single argument in key[=value] format. """
    if string:
        comps = string.split('=', 1)
        if len(comps) > 1:
            return {'type': 'Argument', 'name': comps[0], 'value': comps[1], 'isSecret': is_secret}
        # If no value, check if the argument exists as an environment variable
        local_value = os.environ.get(comps[0])
        if local_value is not None:
            return {'type': 'Argument', 'name': comps[0], 'value': local_value, 'isSecret': is_secret}
        return {'type': 'Argument', 'name': comps[0], 'value': '', 'isSecret': is_secret}
    return None


def validate_retention_days(namespace):
    days = namespace.days
    if days and (days < 0 or days > 365):
        raise CLIError("Invalid value for days: should be from 0 to 365")


def validate_registry_name(cmd, namespace):
    """Omit login server endpoint suffix and domain name label (DNL) hash if given."""
    registry = namespace.registry_name
    if registry is None:
        return
    suffixes = cmd.cli_ctx.cloud.suffixes

    # Split registry login server into components ['myregistry-dnlhash', '.azurecr.io']
    registry_parts = registry.split('.', 1)
    trimmed_registry_name = registry_parts[0]
    registry_login_server_suffix = '.' + registry_parts[1] if len(registry_parts) > 1 else ''

    dnl_hash_index = trimmed_registry_name.find("-")

    # Registry name has hyphen but no login server endpoint suffix
    if registry_login_server_suffix == '' and dnl_hash_index != -1:
        raise InvalidArgumentValueError(BAD_REGISTRY_NAME)

    # Some clouds do not define 'acr_login_server_endpoint' (e.g. AzureGermanCloud)
    if hasattr(suffixes, 'acr_login_server_endpoint'):
        acr_suffix = suffixes.acr_login_server_endpoint
        if registry_login_server_suffix.lower() == acr_suffix and registry_login_server_suffix != '':
            if dnl_hash_index != -1:
                removed_suffix = trimmed_registry_name[dnl_hash_index:] + registry_login_server_suffix
                registry_name = trimmed_registry_name[:dnl_hash_index]
            else:
                removed_suffix = registry_login_server_suffix
                registry_name = trimmed_registry_name
            logger.warning("Registry name is '%s'. The following suffix '%s' is automatically omitted.",
                           registry_name,
                           removed_suffix)
        else:
            if registry_login_server_suffix != '':
                raise InvalidArgumentValueError(INVALID_LOGIN_SERVER_SUFFIX.format(acr_suffix))
            registry_name = trimmed_registry_name
        namespace.registry_name = registry_name
        registry = registry_name

    registry = namespace.registry_name
    if not re.match(ACR_NAME_VALIDATION_REGEX, registry):
        raise InvalidArgumentValueError(BAD_REGISTRY_NAME)


def validate_expiration_time(namespace):
    import datetime
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    if namespace.expiration:
        try:
            namespace.expiration = datetime.datetime.strptime(namespace.expiration, DATE_TIME_FORMAT)
        except ValueError:
            raise CLIError("Input '{}' is not valid datetime. Valid example: 2025-12-31T12:59:59Z".format(
                namespace.expiration))


def validate_repo_id(namespace):
    if namespace.repo_id:
        repo_id = namespace.repo_id[0]
        if '.' not in repo_id or '/' not in repo_id:
            raise InvalidArgumentValueError(BAD_REPO_FQDN)


def validate_permissive_repo_id(namespace):
    if namespace.perm_repo_id:
        perm_repo_id = namespace.perm_repo_id[0]
        if '.' not in perm_repo_id or '/' not in perm_repo_id:
            raise InvalidArgumentValueError(BAD_PERM_REPO_FQDN)
        if '@' in perm_repo_id:
            raise InvalidArgumentValueError(BAD_PERM_REPO_FQDN)


def validate_manifest_id(namespace):
    if namespace.manifest_id:
        manifest_id = namespace.manifest_id[0]
        if '.' not in manifest_id or '/' not in manifest_id:
            raise InvalidArgumentValueError(BAD_MANIFEST_FQDN)


def validate_repository(namespace):
    if namespace.repository:
        if ':' in namespace.repository:
            raise InvalidArgumentValueError("Parameter 'name' refers to a repository and"
                                            " should not include a tag or digest.")


def validate_docker_file_path(docker_file_path):
    if not os.path.isfile(docker_file_path):
        raise FileOperationError("Unable to find '{}'.".format(docker_file_path))
