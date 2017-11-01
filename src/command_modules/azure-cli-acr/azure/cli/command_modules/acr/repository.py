# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from base64 import b64encode
import requests
from requests.utils import to_native_string

from knack.prompting import prompt, prompt_pass, NoTTYException, prompt_y_n
from knack.util import CLIError

from ._utils import validate_managed_registry
from ._docker_utils import get_access_credentials



DELETE_NOT_SUPPORTED = 'Delete is not supported for registries in Basic SKU.'
LIST_MANIFESTS_NOT_SUPPORTED = 'List manifests is not supported for registries in Basic SKU.'


def _get_basic_auth_str(username, password):
    return 'Basic ' + to_native_string(
        b64encode(('%s:%s' % (username, password)).encode('latin1')).strip()
    )


def _get_bearer_auth_str(token):
    return 'Bearer ' + token


def _get_manifest_v2_header():
    return {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}


def _get_authorization_header(username, password):
    if username is None:
        auth = _get_bearer_auth_str(password)
    else:
        auth = _get_basic_auth_str(username, password)

    return {'Authorization': auth}


def _get_pagination_params(count):
    return {'n': count}


def _delete_data_from_registry(login_server, path, username, password, retry_times=3, retry_interval=5):
    for i in range(0, retry_times):
        errorMessage = None
        try:
            response = requests.delete(
                'https://{}/{}'.format(login_server, path),
                headers=_get_authorization_header(username, password)
            )

            if response.status_code == 200 or response.status_code == 202:
                return
            elif response.status_code == 401 or response.status_code == 404:
                raise CLIError(response.text)
            else:
                raise Exception(response.text)
        except CLIError:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)
    if errorMessage:
        raise CLIError(errorMessage)


def _get_manifest_digest(login_server, path, username, password, retry_times=3, retry_interval=5):
    for i in range(0, retry_times):
        errorMessage = None
        try:
            headers = _get_authorization_header(username, password)
            headers.update(_get_manifest_v2_header())
            response = requests.get(
                'https://{}/{}'.format(login_server, path),
                headers=headers
            )

            if response.status_code == 200 and response.headers and 'Docker-Content-Digest' in response.headers:
                return response.headers['Docker-Content-Digest']
            elif response.status_code == 401 or response.status_code == 404:
                raise CLIError(response.text)
            else:
                raise Exception(response.text)
        except CLIError:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)
    if errorMessage:
        raise CLIError(errorMessage)


def _obtain_data_from_registry(login_server,
                               path,
                               username,
                               password,
                               result_index,
                               retry_times=3,
                               retry_interval=5,
                               pagination=20):
    resultList = []
    executeNextHttpCall = True

    while executeNextHttpCall:
        executeNextHttpCall = False
        for i in range(0, retry_times):
            errorMessage = None
            try:
                response = requests.get(
                    'https://{}/{}'.format(login_server, path),
                    headers=_get_authorization_header(username, password),
                    params=_get_pagination_params(pagination)
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
                elif response.status_code == 401 or response.status_code == 404:
                    raise CLIError(response.text)
                else:
                    raise Exception(response.text)
            except CLIError:
                raise
            except Exception as e:  # pylint: disable=broad-except
                errorMessage = str(e)
                logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
                time.sleep(retry_interval)
        if errorMessage:
            raise CLIError(errorMessage)

    return resultList


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
    login_server, username, password = get_access_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password)

    return _obtain_data_from_registry(
        login_server=login_server,
        path='/v2/_catalog',
        username=username,
        password=password,
        result_index='repositories')


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
    login_server, username, password = get_access_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        repository=repository,
        permission='pull')

    return _obtain_data_from_registry(
        login_server=login_server,
        path='/v2/{}/tags/list'.format(repository),
        username=username,
        password=password,
        result_index='tags')


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
    login_server, username, password = get_access_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        repository=repository,
        permission='pull')

    return _obtain_data_from_registry(
        login_server=login_server,
        path='/v2/_acr/{}/manifests/list'.format(repository),
        username=username,
        password=password,
        result_index='manifests')


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
    _, resource_group_name = validate_managed_registry(
        registry_name, resource_group_name, DELETE_NOT_SUPPORTED)

    login_server, username, password = get_access_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        repository=repository,
        permission='*')

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
            login_server=login_server,
            username=username,
            password=password,
            repository=repository,
            tag=tag,
            manifest=manifest,
            yes=yes)
        path = '/v2/{}/manifests/{}'.format(repository, manifest)
    # If --manifest is specified with a value
    else:
        # Raise if --tag is not empty
        if tag:
            raise CLIError(_INVALID)
        manifest = _delete_manifest_confirmation(
            login_server=login_server,
            username=username,
            password=password,
            repository=repository,
            tag=tag,
            manifest=manifest,
            yes=yes)
        path = '/v2/{}/manifests/{}'.format(repository, manifest)

    return _delete_data_from_registry(
        login_server=login_server,
        path=path,
        username=username,
        password=password)


def _delete_manifest_confirmation(login_server,
                                  username,
                                  password,
                                  repository,
                                  tag,
                                  manifest,
                                  yes):
    # Always query manifest if it is empty
    manifest = manifest or _get_manifest_digest(
        login_server=login_server,
        path='/v2/{}/manifests/{}'.format(repository, tag),
        username=username,
        password=password)

    if yes:
        return manifest

    manifests = _obtain_data_from_registry(
        login_server=login_server,
        path='/v2/_acr/{}/manifests/list'.format(repository),
        username=username,
        password=password,
        result_index='manifests',
        pagination=20
    )
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
