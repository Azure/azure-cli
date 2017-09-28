# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from base64 import b64encode
import requests
from requests.utils import to_native_string

from azure.cli.core.prompting import prompt, prompt_pass, NoTTYException, prompt_y_n
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError

from azure.mgmt.containerregistry.v2017_06_01_preview.models import SkuTier

from ._utils import get_registry_by_name, managed_registry_validation
from ._docker_utils import get_login_access_token
from .credential import acr_credential_show


logger = azlogging.get_az_logger(__name__)
DOCKER_MANIFEST_V2 = 'application/vnd.docker.distribution.manifest.v2+json'
DELETE_NOT_SUPPORTED = 'Delete is only supported for managed registries.'
LIST_MANIFESTS_NOT_SUPPORTED = 'List manifests is only supported for managed registries.'


class NotFound(Exception):
    pass


class Unauthorized(Exception):
    pass


def _basic_auth_str(username, password):
    return 'Basic ' + to_native_string(
        b64encode(('%s:%s' % (username, password)).encode('latin1')).strip()
    )


def _bearer_auth_str(token):
    return 'Bearer ' + token


def _headers(username, password, is_manifest=False):
    if username is None:
        auth = _bearer_auth_str(password)
    else:
        auth = _basic_auth_str(username, password)

    if is_manifest:
        return {'Authorization': auth,
                'Accept': DOCKER_MANIFEST_V2}
    return {'Authorization': auth}


def _params(count=20):
    return {'n': count}


def _delete_data_from_registry(login_server, path, username, password, **kwargs):
    retry_times = kwargs['retry_times'] if 'retry_times' in kwargs else 3
    retry_interval = kwargs['retry_interval'] if 'retry_interval' in kwargs else 5

    for i in range(0, retry_times):
        try:
            errorMessage = None
            response = requests.delete(
                'https://{}/{}'.format(login_server, path),
                headers=_headers(username, password)
            )

            if response.status_code == 200 or response.status_code == 202:
                return
            elif response.status_code == 401:
                raise Unauthorized(response.text)
            elif response.status_code == 404:
                raise NotFound(response.text)
            else:
                raise CLIError(response.text)
        except NotFound:
            raise
        except Unauthorized:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)

    if errorMessage:
        raise CLIError(errorMessage)


def _obtain_data_from_registry(login_server, path, username, password, **kwargs):
    result_index = kwargs['result_index'] if 'result_index' in kwargs else ''
    retry_times = kwargs['retry_times'] if 'retry_times' in kwargs else 3
    retry_interval = kwargs['retry_interval'] if 'retry_interval' in kwargs else 5

    registryEndpoint = 'https://' + login_server
    resultList = []
    executeNextHttpCall = True

    while executeNextHttpCall:
        executeNextHttpCall = False
        for i in range(0, retry_times):
            try:
                errorMessage = None
                response = requests.get(
                    registryEndpoint + path,
                    headers=_headers(username, password),
                    params=_params()
                )

                if response.status_code == 200:
                    result = response.json()[result_index]
                    if result:
                        resultList += response.json()[result_index]
                    if 'link' in response.headers and response.headers['link']:
                        linkHeader = response.headers['link']
                        # The registry is telling us there's more items in the list,
                        # and another call is needed. The link header looks something
                        # like `Link: </v2/_catalog?last=hello-world&n=1>; rel="next"`
                        # we should follow the next path indicated in the link header
                        path = linkHeader[(linkHeader.index('<') + 1):linkHeader.index('>')]
                        executeNextHttpCall = True
                    break
                elif response.status_code == 401:
                    raise Unauthorized(response.text)
                elif response.status_code == 404:
                    raise NotFound(response.text)
                else:
                    raise CLIError(response.text)
            except NotFound:
                raise
            except Unauthorized:
                raise
            except Exception as e:  # pylint: disable=broad-except
                errorMessage = str(e)
                logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
                time.sleep(retry_interval)

    if errorMessage:
        raise CLIError(errorMessage)

    return resultList


def _get_manifest_digest(login_server, path, username, password, **kwargs):
    retry_times = kwargs['retry_times'] if 'retry_times' in kwargs else 3
    retry_interval = kwargs['retry_interval'] if 'retry_interval' in kwargs else 5

    for i in range(0, retry_times):
        try:
            errorMessage = None
            response = requests.get(
                'https://{}/{}'.format(login_server, path),
                headers=_headers(username, password, is_manifest=True)
            )

            if response.status_code == 200 and response.headers and 'Docker-Content-Digest' in response.headers:
                return response.headers['Docker-Content-Digest']
            elif response.status_code == 401:
                raise Unauthorized(response.text)
            elif response.status_code == 404:
                raise NotFound(response.text)
            else:
                raise CLIError(response.text)
        except NotFound:
            raise
        except Unauthorized:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)

    if errorMessage:
        raise CLIError(errorMessage)


def _validate_user_credentials(registry_name,
                               resource_group_name,
                               path,
                               permission,
                               username=None,
                               password=None,
                               repository=None,
                               result_index=None,
                               request_method=None):
    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    sku_tier = registry.sku.tier
    login_server = registry.login_server

    # 1. if username was specified, verify that password was also specified
    if username:
        if not password:
            try:
                password = prompt_pass(msg='Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')
        return request_method(login_server, path, username, password, result_index=result_index)

    if sku_tier == SkuTier.managed.value:
        # 2. if we don't yet have credentials, attempt to get an access token
        try:
            managed_registry_validation(registry_name, resource_group_name)
            access_token = get_login_access_token(login_server, permission, repository)
            return request_method(login_server, path, None, access_token, result_index=result_index)
        except NotFound as e:
            raise CLIError(str(e))
        except Unauthorized as e:
            logger.warning("Unable to authenticate using AAD tokens: %s", str(e))
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("AAD authentication failed with message: %s", str(e))

    # 3. if we still don't have credentials, attempt to get the admin credentials (if enabled)
    try:
        cred = acr_credential_show(registry_name)
        username = cred.username
        password = cred.passwords[0].value
        return request_method(login_server, path, username, password, result_index=result_index)
    except NotFound as e:
        raise CLIError(str(e))
    except Unauthorized as e:
        logger.warning("Unable to authenticate using admin login credentials: %s", str(e))
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Admin user authentication failed with message: %s", str(e))

    # 4. if we still don't have credentials, prompt the user
    try:
        username = prompt('Username: ')
        password = prompt_pass(msg='Password: ')
    except NoTTYException:
        raise CLIError(
            'Unable to authenticate using AAD tokens or admin login credentials. ' +
            'Please specify both username and password in non-interactive mode.')
    return request_method(login_server, path, username, password, result_index=result_index)


def acr_repository_list(registry_name,
                        resource_group_name=None,
                        username=None,
                        password=None):
    """Lists repositories in the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    return _validate_user_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        path='/v2/_catalog',
        permission='*',
        username=username,
        password=password,
        result_index='repositories',
        request_method=_obtain_data_from_registry
    )


def acr_repository_show_tags(registry_name,
                             repository,
                             resource_group_name=None,
                             username=None,
                             password=None):
    """Shows tags of a given repository in the specified container registry.
    :param str registry_name: The name of container registry
    :param str repository: The repository to obtain tags from
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    return _validate_user_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        path='/v2/{}/tags/list'.format(repository),
        permission='pull',
        username=username,
        password=password,
        repository=repository,
        result_index='tags',
        request_method=_obtain_data_from_registry
    )


def acr_repository_show_manifests(registry_name,
                                  repository,
                                  resource_group_name=None,
                                  username=None,
                                  password=None):
    """Shows manifests of a given repository in the specified container registry.
    :param str registry_name: The name of container registry
    :param str repository: The repository to obtain manifests from
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    _, resource_group_name = managed_registry_validation(
        registry_name, resource_group_name, LIST_MANIFESTS_NOT_SUPPORTED)
    return _validate_user_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        path='/v2/_acr/{}/manifests/list'.format(repository),
        permission='pull',
        username=username,
        password=password,
        repository=repository,
        result_index='manifests',
        request_method=_obtain_data_from_registry
    )


def acr_repository_delete(registry_name,
                          repository,
                          tag=None,
                          manifest=None,
                          resource_group_name=None,
                          username=None,
                          password=None,
                          yes=False):
    """Deletes a repository or a manifest/tag from the given repository in the specified container registry.
    :param str registry_name: The name of container registry
    :param str repository: The name of repository to delete
    :param str tag: The name of tag to delete
    :param str manifest: The sha256 based digest of manifest to delete
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    _, resource_group_name = managed_registry_validation(
        registry_name, resource_group_name, DELETE_NOT_SUPPORTED)
    _INVALID = "Please specify either a tag name with --tag or a manifest digest with --manifest."

    # If manifest is not specified
    if manifest is None:
        if not tag:
            _user_confirmation("Are you sure you want to delete the repository '{}' "
                               "and all images under it?".format(repository), yes)
            path = '/v2/_acr/{}/repository'.format(repository)
        else:
            _user_confirmation("Are you sure you want to delete the tag '{}:{}'?".format(repository, tag), yes)
            path = '/v2/_acr/{}/tags/{}'.format(repository, tag)
    # If --manifest is specified as a flag
    elif not manifest:
        # Raise if --tag is empty
        if not tag:
            raise CLIError(_INVALID)
        manifest = _delete_manifest_confirmation(
            registry_name=registry_name,
            resource_group_name=resource_group_name,
            repository=repository,
            tag=tag,
            manifest=manifest,
            username=username,
            password=password,
            yes=yes)
        path = '/v2/{}/manifests/{}'.format(repository, manifest)
    # If --manifest is specified with a value
    else:
        # Raise if --tag is not empty
        if tag:
            raise CLIError(_INVALID)
        manifest = _delete_manifest_confirmation(
            registry_name=registry_name,
            resource_group_name=resource_group_name,
            repository=repository,
            tag=tag,
            manifest=manifest,
            username=username,
            password=password,
            yes=yes)
        path = '/v2/{}/manifests/{}'.format(repository, manifest)
    return _validate_user_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        path=path,
        permission='*',
        username=username,
        password=password,
        repository=repository,
        request_method=_delete_data_from_registry
    )


def _delete_manifest_confirmation(registry_name,
                                  resource_group_name,
                                  repository,
                                  tag,
                                  manifest,
                                  username,
                                  password,
                                  yes):
    # All tags that are referencing the manifest, this can be empty.
    tags = []
    # Always query manifest if it is None
    if not manifest:
        manifest = _validate_user_credentials(
            registry_name=registry_name,
            resource_group_name=resource_group_name,
            path='/v2/{}/manifests/{}'.format(repository, tag),
            permission='pull',
            username=username,
            password=password,
            repository=repository,
            request_method=_get_manifest_digest
        )

    if yes:
        return manifest

    if not tags:
        manifests = acr_repository_show_manifests(registry_name, repository)
        filter_by_manifest = [x for x in manifests if manifest == x['digest']]

        if not filter_by_manifest:
            raise CLIError("No manifest can be found with digest '{}'.".format(manifest))
        elif len(filter_by_manifest) == 1:
            manifest = filter_by_manifest[0]['digest']
            tags = filter_by_manifest[0]['tags']
        else:
            raise CLIError("More than one manifests can be found with digest '{}'.".format(manifest))

    message = "This operation will delete the manifest '{}'".format(manifest)
    images = ", ".join(["'{}:{}'".format(repository, str(x)) for x in tags])
    if images:
        message += " and all the following images: {}".format(images)
    _user_confirmation("{}.\nAre you sure you want to continue?".format(message))

    return manifest


def _user_confirmation(message, yes=False):
    if yes:
        return
    try:
        if not prompt_y_n(message):
            raise CLIError('Operation cancelled.')
    except NoTTYException:
        raise CLIError('Unable to prompt for confirmation as no tty available. Use --yes.')
