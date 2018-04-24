# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from base64 import b64encode
import requests
from requests.utils import to_native_string

from knack.prompting import prompt_y_n, NoTTYException
from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.util import should_disable_connection_verify

from ._utils import validate_managed_registry
from ._docker_utils import get_access_credentials, log_registry_response


logger = get_logger(__name__)


UNTAG_NOT_SUPPORTED = 'Untag is only supported for managed registries.'
DELETE_NOT_SUPPORTED = 'Delete is only supported for managed registries.'
LIST_MANIFESTS_NOT_SUPPORTED = 'List manifests is only supported for managed registries.'


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


def _parse_error_message(error_message, response):
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


def _delete_data_from_registry(login_server, path, username, password, retry_times=3, retry_interval=5):
    for i in range(0, retry_times):
        errorMessage = None
        try:
            response = requests.delete(
                'https://{}{}'.format(login_server, path),
                headers=_get_authorization_header(username, password),
                verify=(not should_disable_connection_verify())
            )
            log_registry_response(response)

            if response.status_code == 200 or response.status_code == 202:
                return
            elif response.status_code == 401:
                raise CLIError(_parse_error_message('Authentication required.', response))
            elif response.status_code == 404:
                raise CLIError(_parse_error_message('The requested data does not exist.', response))
            else:
                raise Exception(_parse_error_message('Could not delete the requested data.', response))
        except CLIError:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)
    if errorMessage:
        raise CLIError(errorMessage)


def _get_manifest_digest(login_server, path, username, password, retry_times=3, retry_interval=5):  # pylint: disable=inconsistent-return-statements
    for i in range(0, retry_times):
        errorMessage = None
        try:
            headers = _get_authorization_header(username, password)
            headers.update(_get_manifest_v2_header())
            response = requests.get(
                'https://{}{}'.format(login_server, path),
                headers=headers,
                verify=(not should_disable_connection_verify())
            )
            log_registry_response(response)

            if response.status_code == 200 and response.headers and 'Docker-Content-Digest' in response.headers:
                return response.headers['Docker-Content-Digest']
            elif response.status_code == 401:
                raise CLIError(_parse_error_message('Authentication required.', response))
            elif response.status_code == 404:
                raise CLIError(_parse_error_message('The manifest does not exist.', response))
            else:
                raise Exception(_parse_error_message('Could not get manifest digest.', response))
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
                    'https://{}{}'.format(login_server, path),
                    headers=_get_authorization_header(username, password),
                    params=_get_pagination_params(pagination),
                    verify=(not should_disable_connection_verify())
                )
                log_registry_response(response)

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
                    raise CLIError(_parse_error_message('Authentication required.', response))
                elif response.status_code == 404:
                    raise CLIError(_parse_error_message('The requested data does not exist.', response))
                else:
                    raise Exception(_parse_error_message('Could not get the requested data.', response))
            except CLIError:
                raise
            except Exception as e:  # pylint: disable=broad-except
                errorMessage = str(e)
                logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
                time.sleep(retry_interval)
        if errorMessage:
            raise CLIError(errorMessage)

    return resultList


def acr_repository_list(cmd,
                        registry_name,
                        resource_group_name=None,
                        username=None,
                        password=None):
    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
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


def acr_repository_show_tags(cmd,
                             registry_name,
                             repository,
                             resource_group_name=None,
                             username=None,
                             password=None):
    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
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


def acr_repository_show_manifests(cmd,
                                  registry_name,
                                  repository,
                                  resource_group_name=None,
                                  username=None,
                                  password=None):
    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
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


def acr_repository_untag(cmd,
                         registry_name,
                         image,
                         resource_group_name=None,
                         username=None,
                         password=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, UNTAG_NOT_SUPPORTED)

    repository, tag, _ = _parse_image_name(image)

    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        repository=repository,
        permission='*')

    return _delete_data_from_registry(
        login_server=login_server,
        path='/v2/_acr/{}/tags/{}'.format(repository, tag),
        username=username,
        password=password)


def acr_repository_delete(cmd,
                          registry_name,
                          repository=None,
                          image=None,
                          tag=None,
                          manifest=None,
                          resource_group_name=None,
                          username=None,
                          password=None,
                          yes=False):
    if bool(repository) == bool(image):
        raise CLIError('Usage error: --image IMAGE | --repository REPOSITORY')

    # Check if this is a legacy command. --manifest can be used as a flag so None is checked.
    if repository and (tag or manifest is not None):
        return _legacy_delete(cmd=cmd,
                              registry_name=registry_name,
                              repository=repository,
                              tag=tag,
                              manifest=manifest,
                              resource_group_name=resource_group_name,
                              username=username,
                              password=password,
                              yes=yes)

    # At this point the specified command must not be a legacy command so we process it as a new command.
    # If --tag/--manifest are specified with --repository, it's a legacy command handled above.
    # If --tag/--manifest are specified with --image, error out here.
    if tag:
        raise CLIError("The parameter --tag is redundant and deprecated. Please use --image to delete an image.")
    if manifest is not None:
        raise CLIError("The parameter --manifest is redundant and deprecated. Please use --image to delete an image.")

    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, DELETE_NOT_SUPPORTED)

    if image:
        # If --image is specified, repository/tag/manifest must be empty.
        repository, tag, manifest = _parse_image_name(image, allow_digest=True)

    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        repository=repository,
        permission='*')

    if tag or manifest:
        manifest = _delete_manifest_confirmation(
            login_server=login_server,
            username=username,
            password=password,
            repository=repository,
            tag=tag,
            manifest=manifest,
            yes=yes)
        path = '/v2/{}/manifests/{}'.format(repository, manifest)
    else:
        _user_confirmation("Are you sure you want to delete the repository '{}' "
                           "and all images under it?".format(repository), yes)
        path = '/v2/_acr/{}/repository'.format(repository)

    return _delete_data_from_registry(
        login_server=login_server,
        path=path,
        username=username,
        password=password)


def _parse_image_name(image, allow_digest=False):
    if allow_digest and '@' in image:
        # This is probably an image name by manifest digest
        tokens = image.split('@')
        if len(tokens) == 2:
            return tokens[0], None, tokens[1]

    if ':' in image:
        # This is probably an image name by tag
        tokens = image.split(':')
        if len(tokens) == 2:
            return tokens[0], tokens[1], None
    else:
        # This is probably an image with implicit latest tag
        return image, 'latest', None

    if allow_digest:
        raise CLIError("The name of the image to delete may include a tag in the"
                       " format 'name:tag' or digest in the format 'name@digest'.")
    else:
        raise CLIError("The name of the image may include a tag in the format 'name:tag'.")


def _legacy_delete(cmd,
                   registry_name,
                   repository,
                   tag=None,
                   manifest=None,
                   resource_group_name=None,
                   username=None,
                   password=None,
                   yes=False):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, DELETE_NOT_SUPPORTED)

    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
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
            logger.warning(
                "This command is deprecated. The new command for this operation "
                "is 'az acr repository untag --name %s --image %s:%s'.",
                registry_name, repository, tag)
            _user_confirmation("Are you sure you want to delete the tag '{}:{}'?".format(repository, tag), yes)
            path = '/v2/_acr/{}/tags/{}'.format(repository, tag)
    # If --manifest is specified as a flag
    elif not manifest:
        # Raise if --tag is empty
        if not tag:
            raise CLIError(_INVALID)
        logger.warning(
            "This command is deprecated. The new command for this operation "
            "is 'az acr repository delete --name %s --image %s:%s'.",
            registry_name, repository, tag)
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
        logger.warning(
            "This command is deprecated. The new command for this operation "
            "is 'az acr repository delete --name %s --image %s@%s'.",
            registry_name, repository, manifest)
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
