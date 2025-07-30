# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from enum import Enum
from knack.log import get_logger
from knack.util import CLIError
from ._docker_utils import (
    request_data_from_registry,
    get_access_credentials,
    RepoAccessTokenPermission,
    RegistryException
)
from .manifest import (
    _get_referrers_path,
    _obtain_referrers_from_registry
)
from .repository import get_image_digest

logger = get_logger(__name__)


class OperationActions(str, Enum):
    CANCEL = 'cancel'


class ArtifactStreamingStatus(str, Enum):
    NotStarted = 'NotStarted'
    Running = 'Running'
    Succeeded = 'Succeeded'
    Failed = 'Failed'
    Canceled = 'Canceled'


def _get_v1_artifact_streaming_path(repository):
    return '/acr/v1/{}/_streaming'.format(repository)


def _get_v1_artifact_streaming_image_path(repository, digest):
    return '/acr/v1/{}/_streaming/{}'.format(repository, digest)


def _get_v1_artifact_streaming_operation_path(repository, operation_id, operation_type=None):
    if operation_type:
        return '/acr/v1/{}/_operations/{}:{}'.format(repository, operation_id, operation_type)
    return '/acr/v1/{}/_operations/{}'.format(repository, operation_id)


def acr_artifact_streaming_create(cmd,
                                  registry_name,
                                  image,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None,
                                  no_wait=False):
    try:
        repository, digest = get_image_digest(cmd, registry_name, image)
    except CLIError as e:
        raise CLIError("Could not find image '{}'. {}".format(image, e))

    # Get read/write access credentials
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL_PUSH.value)

    # Check if streaming artifact already exists
    streaming_artifact_exists = _check_if_streaming_artifact_exists(
        repository,
        digest,
        login_server,
        username,
        password)
    if streaming_artifact_exists:
        logger.warning("The streaming artifact for image '%s' already exists. Skipping request.", image)
        return

    result = _get_last_streaming_operation(cmd=cmd,
                                           registry_name=registry_name,
                                           repository=repository,
                                           digest=digest,
                                           tenant_suffix=tenant_suffix,
                                           username=username,
                                           password=password)

    # Create the artifact streaming
    if result and _is_ongoing_streaming_status(result['status']):
        operation_id = result['id']
    else:
        path = _get_v1_artifact_streaming_image_path(repository, digest)
        json_payload = {"conversionFormat": "overlaybd", "conversionVersion": "v1"}
        result, _, response_status = request_data_from_registry(http_method='post',
                                                                login_server=login_server,
                                                                path=path,
                                                                username=username,
                                                                password=password,
                                                                json_payload=json_payload)
        if response_status != 202:
            return result
        operation_id = result['id']

    logger.warning("The operation is in progress. " +
                   "Use 'az acr artifact-streaming operation show -n %s --repository %s --id %s' to check the status.",
                   registry_name,
                   repository,
                   operation_id)
    if not no_wait:
        result = _create_streaming_artifact_poller(repository=repository,
                                                   operationId=operation_id,
                                                   create_response=result,
                                                   login_server=login_server,
                                                   username=username,
                                                   password=password)
    return result


def _check_if_streaming_artifact_exists(repository,
                                        digest,
                                        login_server,
                                        username,
                                        password):
    path = _get_referrers_path(repository, digest)
    referrers = _obtain_referrers_from_registry(
        login_server=login_server,
        path=path,
        username=username,
        password=password,
        artifact_type="application/vnd.azure.artifact.streaming.v1")
    manifest = referrers['manifests']
    return len(manifest) > 0


def _get_last_streaming_operation(cmd,
                                  registry_name,
                                  repository,
                                  digest,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):
    path = _get_v1_artifact_streaming_image_path(repository, digest)
    # Verify if the artifact streaming create operation is already in queue
    try:
        login_server, username, password = get_access_credentials(
            cmd=cmd,
            registry_name=registry_name,
            tenant_suffix=tenant_suffix,
            username=username,
            password=password,
            repository=repository,
            permission=RepoAccessTokenPermission.PULL.value)
        result, _, response_status = request_data_from_registry(http_method='get',
                                                                login_server=login_server,
                                                                path=path,
                                                                username=username,
                                                                password=password)
        if response_status == 200:
            return result
    except RegistryException as e:
        if e.status_code != 404:
            raise
    return None


def _is_ongoing_streaming_status(status):
    res = status == ArtifactStreamingStatus.Running.value or status == ArtifactStreamingStatus.NotStarted.value
    return res


def _create_streaming_artifact_poller(repository,
                                      operationId,
                                      create_response,
                                      login_server,
                                      username,
                                      password):
    path = _get_v1_artifact_streaming_operation_path(repository, operationId)
    timmer = 5
    time_count = 0
    progress = "0%"
    status = ArtifactStreamingStatus.NotStarted.value
    while _is_ongoing_streaming_status(status):
        time.sleep(timmer)
        time_count += timmer
        if timmer < 21:
            timmer += 1
        poller, _, _ = request_data_from_registry(http_method='get',
                                                  login_server=login_server,
                                                  path=path,
                                                  username=username,
                                                  password=password)

        if poller['status'] != status:
            logger.info("Status: %s ran for approximately %i seconds", status, time_count)
            status = poller['status']
            timmer = 5
            time_count = 0
            if status == ArtifactStreamingStatus.Running.value:
                logger.warning("%s...", status)
                progress = poller['progress']
                logger.info("%s: %s", status, progress)
            else:
                logger.info("Status: %s", status)
        if status == ArtifactStreamingStatus.Running.value and progress != poller['progress']:
            timmer = 5
            progress = poller['progress']
            logger.info("%s: %s", status, progress)

    create_response['status'] = status
    return create_response


def acr_artifact_streaming_show(cmd,
                                registry_name,
                                repository=None,
                                tenant_suffix=None,
                                username=None,
                                password=None):

    path = _get_v1_artifact_streaming_path(repository)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL.value)

    result, _, _ = request_data_from_registry(http_method='get',
                                              login_server=login_server,
                                              path=path,
                                              username=username,
                                              password=password)
    return result


def acr_artifact_streaming_update(cmd,
                                  registry_name,
                                  repository,
                                  enable_streaming,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):

    path = _get_v1_artifact_streaming_path(repository)
    json_payload = {"convertPushedImages": enable_streaming, "conversionFormat": "overlaybd", "conversionVersion": "v1"}

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL_PUSH.value)

    result, _, _ = request_data_from_registry(http_method='post',
                                              login_server=login_server,
                                              path=path,
                                              username=username,
                                              password=password,
                                              json_payload=json_payload,
                                              raw=True)
    return result


def _get_streaming_operation_info_from_image(cmd,
                                             registry_name,
                                             image,
                                             tenant_suffix,
                                             username,
                                             password):
    repository, digest = get_image_digest(cmd=cmd,
                                          registry_name=registry_name,
                                          image=image,
                                          tenant_suffix=tenant_suffix,
                                          username=username,
                                          password=password)
    response = _get_last_streaming_operation(cmd=cmd,
                                             registry_name=registry_name,
                                             repository=repository,
                                             digest=digest,
                                             tenant_suffix=tenant_suffix,
                                             username=username,
                                             password=password)
    return repository, response


# OPEERATION GROUP COMMANDS
def acr_artifact_streaming_operation_show(cmd,
                                          registry_name,
                                          repository=None,
                                          operation_id=None,
                                          image=None,
                                          tenant_suffix=None,
                                          username=None,
                                          password=None):
    _validate_operation_parameters(repository, operation_id, image)

    if image:
        repository, stream_response = _get_streaming_operation_info_from_image(cmd=cmd,
                                                                               registry_name=registry_name,
                                                                               image=image,
                                                                               tenant_suffix=tenant_suffix,
                                                                               username=username,
                                                                               password=password)
        if not stream_response:
            raise CLIError("No operation found for image '{}'".format(image))
        operation_id = stream_response['id']

    path = _get_v1_artifact_streaming_operation_path(repository, operation_id)
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL.value)

    result, _, _ = request_data_from_registry(http_method='get',
                                              login_server=login_server,
                                              path=path,
                                              username=username,
                                              password=password,
                                              raw=True)
    return result


def acr_artifact_streaming_operation_cancel(cmd,
                                            registry_name,
                                            repository=None,
                                            operation_id=None,
                                            image=None,
                                            tenant_suffix=None,
                                            username=None,
                                            password=None):
    _validate_operation_parameters(repository, operation_id, image)

    if image:
        repository, stream_response = _get_streaming_operation_info_from_image(cmd=cmd,
                                                                               registry_name=registry_name,
                                                                               image=image,
                                                                               tenant_suffix=tenant_suffix,
                                                                               username=username,
                                                                               password=password)
        if not stream_response:
            raise CLIError("No operation found for image '{}'".format(image))
        if not _is_ongoing_streaming_status(stream_response['status']):
            raise CLIError("The image '{}' does not have any ongoing operation. Operation ID: {}".
                           format(image, stream_response['id']))
        operation_id = stream_response['id']

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL_PUSH.value)
    path = _get_v1_artifact_streaming_operation_path(repository, operation_id, OperationActions.CANCEL.value)
    result, _, _ = request_data_from_registry(http_method='post',
                                              login_server=login_server,
                                              path=path,
                                              username=username,
                                              password=password,
                                              raw=True)
    return result


def _validate_operation_parameters(repository, operation_id, image):
    repo = bool(repository)
    op_id = bool(operation_id)
    img = bool(image)
    if (not repo and op_id) or not (op_id or img) or (repo and img):
        raise CLIError('Usage error: You need to provide either --repository MyRepo --id MyId | --image MyImage')
