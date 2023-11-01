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
from .manifest import(
    _get_referrers_path,
    _obtain_referrers_from_registry
)

logger = get_logger(__name__)

class ArtifactStreamingOperation(Enum):
    CANCEL = 'cancel'

def _get_v1_artifact_streaming_path(repository):
    return '/acr/v1/{}/_streaming'.format(repository)


def _get_v1_artifact_streaming_image_path(repository, digest):
    return '/acr/v1/{}/_streaming/{}'.format(repository, digest)


def _get_v1_artifact_streaming_operation_path(repository, operation_id, operation_type=None):
    if operation_type:
        return '/acr/v1/{}/_operations/{}:{}'.format(repository, operation_id, operation_type)
    return '/acr/v1/{}/_operations/{}'.format(repository, operation_id)


def acr_artifact_streaming_update(cmd,
                                  registry_name,
                                  repository,
                                  enable_streaming,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):

    path = _get_v1_artifact_streaming_path(repository)
    json_payload = {"convertPushedImages": enable_streaming, "conversionFormat":"overlaybd", "conversionVersion": "v1"}

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


def acr_artifact_streaming_create(cmd,
                                  registry_name,
                                  image,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None,
                                  no_wait=False):
    from .repository import get_image_digest
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
        permission=RepoAccessTokenPermission.PULL_PUSH.value)#RepoAccessTokenPermission.META_WRITE_META_READ.value)

    # Check if streaming artifact already exists
    streaming_artifact_exists = _check_if_streaming_artifact_exists(
        repository,
        digest,
        login_server,
        username,
        password)
    if streaming_artifact_exists:
        logger.warning("The streaming artifact for image '{}' already exists. Skipping request.".format(image))
        return

    path = _get_v1_artifact_streaming_image_path(repository, digest)
    # Verify if the artifact streaming create operation is already in queue
    skip_create = False
    try: 
        result, _, response_status = request_data_from_registry(http_method='get',
                                                                login_server=login_server,
                                                                path=path,
                                                                username=username,
                                                                password=password)
        if response_status == 200:
            status = result['status']
            if status == 'Running' or status == 'NotStarted':
                operation_id = result['id']
                skip_create = True
    except RegistryException as e:
        if e.status_code != 404:
            raise

    # Create the artifact streaming
    if not skip_create:
        json_payload = {"conversionFormat":"overlaybd", "conversionVersion": "v1"}
        result, _, response_status = request_data_from_registry(http_method='post',
                                                                login_server=login_server,
                                                                path=path,
                                                                username=username,
                                                                password=password,
                                                                json_payload=json_payload)
        if response_status != 202:
            return result
        operation_id = result['id']

    logger.warning("The operation is in progress. Use 'az acr artifact-streaming operation show -n {} --repository {} --id {}' to check the status.".format(registry_name, repository, operation_id))
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
    status = 'NotStarted'
    while status == 'Running' or status == 'NotStarted':
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
            logger.info("Status: {} ran for approximately {} seconds".format(status, time_count))
            status = poller['status']
            timmer = 5
            time_count = 0
            if status == 'Running':
                logger.warn("{}...".format(status))
                progress = poller['progress']
                logger.info("{}: {}".format(status,progress))
            else:
                logger.info("Status: {}".format(status))
        if status == 'Running' and progress != poller['progress']:
            timmer = 5
            progress = poller['progress']
            logger.info("{}: {}".format(status,progress))

    create_response['status'] = status
    return create_response

def acr_artifact_streaming_operation_show(cmd,
                                          registry_name,
                                          repository,
                                          operation_id,
                                          tenant_suffix=None,
                                          username=None,
                                          password=None):

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
                                            repository,
                                            operation_id,
                                            tenant_suffix=None,
                                            username=None,
                                            password=None):

    path = _get_v1_artifact_streaming_operation_path(repository, operation_id, ArtifactStreamingOperation.CANCEL.value)

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
                                              raw=True)
    return result


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
