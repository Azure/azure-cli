# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlencode, urlparse, urlunparse
except ImportError:
    from urllib import urlencode
    from urlparse import urlparse, urlunparse

import time
from json import loads
from base64 import b64encode
import requests
from requests import RequestException
from requests.utils import to_native_string
from msrest.http_logger import log_request, log_response

from knack.util import CLIError
from knack.prompting import prompt, prompt_pass, NoTTYException
from knack.log import get_logger

from azure.cli.core.util import should_disable_connection_verify
from azure.cli.core.cloud import CloudSuffixNotSetException
from azure.cli.core._profile import _AZ_LOGIN_MESSAGE

from ._client_factory import cf_acr_registries
from ._constants import get_managed_sku
from ._utils import get_registry_by_name, ResourceNotFound


logger = get_logger(__name__)


EMPTY_GUID = '00000000-0000-0000-0000-000000000000'
ALLOWED_HTTP_METHOD = ['get', 'patch', 'put', 'delete']
ACCESS_TOKEN_PERMISSION = ['pull', 'push', 'delete', 'push,pull', 'delete,pull']

AAD_TOKEN_BASE_ERROR_MESSAGE = "Unable to get AAD authorization tokens with message"
ADMIN_USER_BASE_ERROR_MESSAGE = "Unable to get admin user credentials with message"


def _get_aad_token(cli_ctx,
                   login_server,
                   only_refresh_token,
                   repository=None,
                   artifact_repository=None,
                   permission=None):
    """Obtains refresh and access tokens for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    :param bool only_refresh_token: Whether to ask for only refresh token, or for both refresh and access tokens
    :param str repository: Repository for which the access token is requested
    :param str artifact_repository: Artifact repository for which the access token is requested
    :param str permission: The requested permission on the repository, '*' or 'pull'
    """
    if repository and artifact_repository:
        raise ValueError("Only one of repository and artifact_repository can be provided.")

    if (repository or artifact_repository) and permission not in ACCESS_TOKEN_PERMISSION:
        raise ValueError(
            "Permission is required for a repository or artifact_repository. Allowed access token permission: {}"
            .format(ACCESS_TOKEN_PERMISSION))

    login_server = login_server.rstrip('/')

    challenge = requests.get('https://' + login_server + '/v2/', verify=(not should_disable_connection_verify()))
    if challenge.status_code not in [401] or 'WWW-Authenticate' not in challenge.headers:
        raise CLIError("Registry '{}' did not issue a challenge.".format(login_server))

    authenticate = challenge.headers['WWW-Authenticate']

    tokens = authenticate.split(' ', 2)
    if len(tokens) < 2 or tokens[0].lower() != 'bearer':
        raise CLIError("Registry '{}' does not support AAD login.".format(login_server))

    params = {y[0]: y[1].strip('"') for y in
              (x.strip().split('=', 2) for x in tokens[1].split(','))}
    if 'realm' not in params or 'service' not in params:
        raise CLIError("Registry '{}' does not support AAD login.".format(login_server))

    authurl = urlparse(params['realm'])
    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/exchange', '', '', ''))

    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    creds, _, tenant = profile.get_raw_token()

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    content = {
        'grant_type': 'access_token',
        'service': params['service'],
        'tenant': tenant,
        'access_token': creds[1]
    }

    response = requests.post(authhost, urlencode(content), headers=headers,
                             verify=(not should_disable_connection_verify()))

    if response.status_code not in [200]:
        raise CLIError("Access to registry '{}' was denied. Response code: {}.".format(
            login_server, response.status_code))

    refresh_token = loads(response.content.decode("utf-8"))["refresh_token"]
    if only_refresh_token:
        return refresh_token

    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/token', '', '', ''))

    if repository:
        scope = 'repository:{}:{}'.format(repository, permission)
    elif artifact_repository:
        scope = 'artifact-repository:{}:{}'.format(artifact_repository, permission)
    else:
        # catalog only has * as permission, even for a read operation
        scope = 'registry:catalog:*'

    content = {
        'grant_type': 'refresh_token',
        'service': login_server,
        'scope': scope,
        'refresh_token': refresh_token
    }
    response = requests.post(authhost, urlencode(content), headers=headers,
                             verify=(not should_disable_connection_verify()))

    if response.status_code not in [200]:
        raise CLIError("Access to registry '{}' was denied. Response code: {}.".format(
            login_server, response.status_code))

    return loads(response.content.decode("utf-8"))["access_token"]


def _get_credentials(cmd,  # pylint: disable=too-many-statements
                     registry_name,
                     tenant_suffix,
                     username,
                     password,
                     only_refresh_token,
                     repository=None,
                     artifact_repository=None,
                     permission=None):
    """Try to get AAD authorization tokens or admin user credentials.
    :param str registry_name: The name of container registry
    :param str tenant_suffix: The registry login server tenant suffix
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    :param bool only_refresh_token: Whether to ask for only refresh token, or for both refresh and access tokens
    :param str repository: Repository for which the access token is requested
    :param str artifact_repository: Artifact repository for which the access token is requested
    :param str permission: The requested permission on the repository, '*' or 'pull'
    """
    # Raise an error if password is specified but username isn't
    if not username and password:
        raise CLIError('Please also specify username if password is specified.')

    cli_ctx = cmd.cli_ctx
    resource_not_found, registry = None, None
    try:
        registry, resource_group_name = get_registry_by_name(cli_ctx, registry_name)
        login_server = registry.login_server
        if tenant_suffix:
            logger.warning(
                "Obtained registry login server '%s' from service. The specified suffix '%s' is ignored.",
                login_server, tenant_suffix)
    except (ResourceNotFound, CLIError) as e:
        resource_not_found = str(e)
        logger.debug("Could not get registry from service. Exception: %s", resource_not_found)
        if not isinstance(e, ResourceNotFound) and _AZ_LOGIN_MESSAGE not in resource_not_found:
            raise
        # Try to use the pre-defined login server suffix to construct login server from registry name.
        login_server_suffix = get_login_server_suffix(cli_ctx)
        if not login_server_suffix:
            raise
        login_server = '{}{}{}'.format(
            registry_name, '-{}'.format(tenant_suffix) if tenant_suffix else '', login_server_suffix).lower()

    # Validate the login server is reachable
    url = 'https://' + login_server + '/v2/'
    try:
        challenge = requests.get(url, verify=(not should_disable_connection_verify()))
        if challenge.status_code in [403]:
            raise CLIError("Looks like you don't have access to registry '{}'. "
                           "Are firewalls and virtual networks enabled?".format(login_server))
    except RequestException as e:
        logger.debug("Could not connect to registry login server. Exception: %s", str(e))
        if resource_not_found:
            logger.warning("%s\nUsing '%s' as the default registry login server.", resource_not_found, login_server)
        raise CLIError("Could not connect to the registry login server '{}'. ".format(login_server) +
                       "Please verify that the registry exists and " +
                       "the URL '{}' is reachable from your environment.".format(url))

    # 1. if username was specified, verify that password was also specified
    if username:
        if not password:
            try:
                password = prompt_pass(msg='Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')

        return login_server, username, password

    # 2. if we don't yet have credentials, attempt to get a refresh token
    if not registry or registry.sku.name in get_managed_sku(cmd):
        try:
            return login_server, EMPTY_GUID, _get_aad_token(
                cli_ctx, login_server, only_refresh_token, repository, artifact_repository, permission)
        except CLIError as e:
            logger.warning("%s: %s", AAD_TOKEN_BASE_ERROR_MESSAGE, str(e))

    # 3. if we still don't have credentials, attempt to get the admin credentials (if enabled)
    if registry:
        if registry.admin_user_enabled:
            try:
                cred = cf_acr_registries(cli_ctx).list_credentials(resource_group_name, registry_name)
                return login_server, cred.username, cred.passwords[0].value
            except CLIError as e:
                logger.warning("%s: %s", ADMIN_USER_BASE_ERROR_MESSAGE, str(e))
        else:
            logger.warning("%s: %s", ADMIN_USER_BASE_ERROR_MESSAGE, "Admin user is disabled.")
    else:
        logger.warning("%s: %s", ADMIN_USER_BASE_ERROR_MESSAGE, resource_not_found)

    # 4. if we still don't have credentials, prompt the user
    try:
        username = prompt('Username: ')
        password = prompt_pass(msg='Password: ')
        return login_server, username, password
    except NoTTYException:
        raise CLIError(
            'Unable to authenticate using AAD or admin login credentials. ' +
            'Please specify both username and password in non-interactive mode.')

    return login_server, None, None


def get_login_credentials(cmd,
                          registry_name,
                          tenant_suffix=None,
                          username=None,
                          password=None):
    """Try to get AAD authorization tokens or admin user credentials to log into a registry.
    :param str registry_name: The name of container registry
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    return _get_credentials(cmd,
                            registry_name,
                            tenant_suffix,
                            username,
                            password,
                            only_refresh_token=True)


def get_access_credentials(cmd,
                           registry_name,
                           tenant_suffix=None,
                           username=None,
                           password=None,
                           repository=None,
                           artifact_repository=None,
                           permission=None):
    """Try to get AAD authorization tokens or admin user credentials to access a registry.
    :param str registry_name: The name of container registry
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    :param str repository: Repository for which the access token is requested
    :param str artifact_repository: Artifact repository for which the access token is requested
    :param str permission: The requested permission on the repository
    """
    return _get_credentials(cmd,
                            registry_name,
                            tenant_suffix,
                            username,
                            password,
                            only_refresh_token=False,
                            repository=repository,
                            artifact_repository=artifact_repository,
                            permission=permission)


def log_registry_response(response):
    """Log the HTTP request and response of a registry API call.
    :param Response response: The response object
    """
    log_request(None, response.request)
    log_response(None, response.request, RegistryResponse(response.request, response))


def get_login_server_suffix(cli_ctx):
    """Get the Azure Container Registry login server suffix in the current cloud."""
    try:
        return cli_ctx.cloud.suffixes.acr_login_server_endpoint
    except CloudSuffixNotSetException as e:
        logger.debug("Could not get login server endpoint suffix. Exception: %s", str(e))
        # Ignore the error if the suffix is not set, the caller should then try to get login server from server.
        return None


def _get_basic_auth_str(username, password):
    return 'Basic ' + to_native_string(
        b64encode(('%s:%s' % (username, password)).encode('latin1')).strip()
    )


def _get_bearer_auth_str(token):
    return 'Bearer ' + token


def get_authorization_header(username, password):
    """Get the authorization header as Basic auth if username is provided, or Bearer auth otherwise
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    if username == EMPTY_GUID:
        auth = _get_bearer_auth_str(password)
    else:
        auth = _get_basic_auth_str(username, password)
    return {'Authorization': auth}


def request_data_from_registry(http_method,
                               login_server,
                               path,
                               username,
                               password,
                               result_index=None,
                               json_payload=None,
                               file_payload=None,
                               params=None,
                               retry_times=3,
                               retry_interval=5):
    if http_method not in ALLOWED_HTTP_METHOD:
        raise ValueError("Allowed http method: {}".format(ALLOWED_HTTP_METHOD))

    if json_payload and file_payload:
        raise ValueError("One of json_payload and file_payload can be specified.")

    if http_method in ['get', 'delete'] and (json_payload or file_payload):
        raise ValueError("Empty payload is required for http method: {}".format(http_method))

    if http_method in ['patch', 'put'] and not (json_payload or file_payload):
        raise ValueError("Non-empty payload is required for http method: {}".format(http_method))

    url = 'https://{}{}'.format(login_server, path)
    headers = get_authorization_header(username, password)

    for i in range(0, retry_times):
        errorMessage = None
        try:
            if file_payload:
                with open(file_payload, 'rb') as data_payload:
                    response = requests.request(
                        method=http_method,
                        url=url,
                        headers=headers,
                        params=params,
                        data=data_payload,
                        verify=(not should_disable_connection_verify())
                    )
            else:
                response = requests.request(
                    method=http_method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_payload,
                    verify=(not should_disable_connection_verify())
                )

            log_registry_response(response)

            if response.status_code == 200:
                result = response.json()[result_index] if result_index else response.json()
                next_link = response.headers['link'] if 'link' in response.headers else None
                return result, next_link
            elif response.status_code == 201 or response.status_code == 202:
                result = None
                try:
                    result = response.json()[result_index] if result_index else response.json()
                except ValueError as e:
                    logger.debug('Response is empty or is not a valid json. Exception: %s', str(e))
                return result, None
            elif response.status_code == 204:
                return None, None
            elif response.status_code == 401:
                raise RegistryException(
                    parse_error_message('Authentication required.', response),
                    response.status_code)
            elif response.status_code == 404:
                raise RegistryException(
                    parse_error_message('The requested data does not exist.', response),
                    response.status_code)
            elif response.status_code == 405:
                raise RegistryException(
                    parse_error_message('This operation is not supported.', response),
                    response.status_code)
            elif response.status_code == 409:
                raise RegistryException(
                    parse_error_message('Failed to request data due to a conflict.', response),
                    response.status_code)
            else:
                raise Exception(parse_error_message('Could not {} the requested data.'.format(http_method), response))
        except CLIError:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)

    raise CLIError(errorMessage)


def parse_error_message(error_message, response):
    import json
    try:
        server_message = json.loads(response.text)['errors'][0]['message']
        error_message = 'Error: {}'.format(server_message) if server_message else error_message
    except (ValueError, KeyError, TypeError, IndexError):
        pass

    if not error_message.endswith('.'):
        error_message = '{}.'.format(error_message)

    try:
        correlation_id = response.headers['x-ms-correlation-request-id']
        return '{} Correlation ID: {}.'.format(error_message, correlation_id)
    except (KeyError, TypeError, AttributeError):
        return error_message


class RegistryException(CLIError):
    def __init__(self, message, status_code):
        super(RegistryException, self).__init__(message)
        self.status_code = status_code


class RegistryResponse(object):  # pylint: disable=too-few-public-methods
    def __init__(self, request, internal_response):
        self.request = request
        self.internal_response = internal_response
        self.status_code = internal_response.status_code
        self.headers = internal_response.headers
        self.encoding = internal_response.encoding
        self.reason = internal_response.reason
        self.content = internal_response.content

    def text(self):
        return self.content.decode(self.encoding or "utf-8")
