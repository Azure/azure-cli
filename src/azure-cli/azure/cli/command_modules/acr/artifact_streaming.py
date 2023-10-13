# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from knack.log import get_logger
from knack.util import CLIError
from ._docker_utils import (
    request_data_from_registry,
    get_access_credentials,
    RepoAccessTokenPermission
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


def acr_streaming_artifact_update(cmd,
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
        permission=RepoAccessTokenPermission.METADATA_WRITE.value)

    result, _ = request_data_from_registry(http_method='post',
                                           login_server=login_server,
                                           path=path,
                                           username=username,
                                           password=password,
                                           json_payload=json_payload,
                                           raw=True)
    return result


def acr_streaming_artifact_create(cmd,
                                  registry_name,
                                  image,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):
    from .repository import get_image_digest
    try:
        repository, digest = get_image_digest(cmd, registry_name, image)
    except CLIError as e:
        raise CLIError("Could not find image '{}'. {}".format(image, e))
    path = _get_v1_artifact_streaming_image_path(repository, digest)
    json_payload = {"conversionFormat":"overlaybd", "conversionVersion": "v1"}

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.METADATA_WRITE.value)

    result, _ = request_data_from_registry(http_method='post',
                                           login_server=login_server,
                                           path=path,
                                           username=username,
                                           password=password,
                                           json_payload=json_payload,
                                           raw=True)
    return result


def acr_streaming_artifact_operation_show(cmd,
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
        permission=RepoAccessTokenPermission.METADATA_READ.value)

    result, _ = request_data_from_registry(http_method='get',
                                           login_server=login_server,
                                           path=path,
                                           username=username,
                                           password=password,
                                           raw=True)
    return result


def acr_streaming_artifact_operation_cancel(cmd,
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
        permission=RepoAccessTokenPermission.METADATA_WRITE.value)

    result, _ = request_data_from_registry(http_method='post',
                                           login_server=login_server,
                                           path=path,
                                           username=username,
                                           password=password,
                                           raw=True)
    return result


def acr_streaming_artifact_show(cmd,
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
        permission=RepoAccessTokenPermission.PULL_META_READ.value)

    result, _ = request_data_from_registry(http_method='get',
                                           login_server=login_server,
                                           path=path,
                                           username=username,
                                           password=password)
    return result
