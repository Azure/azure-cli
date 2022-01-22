# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

from cmath import e
from operator import contains
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.util import user_confirmation
from azure.cli.core.azclierror import InvalidArgumentValueError
from .repository import (
    _parse_image_name,
    get_image_digest,
    _obtain_data_from_registry,
    _get_manifest_path,
    _acr_repository_attributes_helper
)
import json

from ._docker_utils import (
    request_data_from_registry,
    get_access_credentials,
    get_login_server_suffix,
    RegistryException,
    RepoAccessTokenPermission
)

from ._validators import (
    BAD_MANIFEST_FQDN,
    BAD_REPO_FQDN
)
logger = get_logger(__name__)

ORDERBY_PARAMS = {
    'time_asc': 'timeasc',
    'time_desc': 'timedesc'
}
DEFAULT_PAGINATION = 100

BAD_ARGS_ERROR_REPO = "Error: You must provide either a fully qualified repository specifier such as myreg.azurecr.io/myrepo as a positional parameter or provide -r myreg -n myrepo argument values."
BAD_ARGS_ERROR_MANIFEST ="Error: You must provide either a fully qualified manifest specifier such as myreg.azurecr.io/myrepo:mytag as a positional parameter or provide -r myreg -n myrepo:mytag argument values."

def _get_v2_manifest_path(repository, manifest):
    return '/v2/{}/manifests/{}'.format(repository, manifest)


def _get_references_path(repository, manifest, artifact_type=None):
    if(artifact_type):
        return '/oras/artifacts/v1/{}/manifests/{}/referrers?artifactType={}'.format(repository, manifest, artifact_type)
    else:
        return '/oras/artifacts/v1/{}/manifests/{}/referrers'.format(repository, manifest)


def _obtain_manifest_from_registry(login_server,
                               path,
                               username,
                               password,
                               raw=False):

    result, next_link = request_data_from_registry(
            http_method='get',
            login_server=login_server,
            path=path,
            raw=raw,
            username=username,
            password=password,
            result_index=None,
            manifest_headers=True)

    return result

def _parse_fqdn(cmd, id, is_manifest=True):
    try:
        id = id.lstrip('https://')
        reg_addr = id.split('/', 1)[0]
        registry_name = reg_addr.split('.', 1)[0]
        reg_suffix= '.' + reg_addr.split('.', 1)[1]
        manifest_id = id.split('/', 1)[1]
        _validate_login_server_suffix(cmd, reg_suffix)
        repository, tag, manifest = _parse_image_name(manifest_id, allow_digest=True)

    except IndexError as e:
        if is_manifest:
            raise InvalidArgumentValueError(BAD_MANIFEST_FQDN) from e
        else:
            raise InvalidArgumentValueError(BAD_REPO_FQDN) from e

    return registry_name, repository, tag, manifest

def _validate_login_server_suffix(cmd, reg_suffix):
    cli_ctx = cmd.cli_ctx
    login_server_suffix = get_login_server_suffix(cli_ctx)

    if(reg_suffix != login_server_suffix):
        raise InvalidArgumentValueError(f'Error: Provided registry suffix \'{reg_suffix}\' does not match the configured az cli acr login server suffix \'{login_server_suffix}\'. Check the \'acrLoginServerEndpoint\' value when running \'az cloud show\'.')

def acr_repository_list_manifests(cmd,
                                  registry_name=None,
                                  repository=None,
                                  id=None,
                                  top=None,
                                  orderby=None,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None
                                  ):
    if (id and repository) or (not id and not (registry_name and repository)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_REPO)

    if id:
        registry_name, repository, _, _ = _parse_fqdn(cmd, id[0], is_manifest=False)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL_META_READ.value)

    raw_result = _obtain_data_from_registry(
        login_server=login_server,
        path=_get_manifest_path(repository),
        top=top,
        username=username,
        password=password,
        result_index='manifests',
        orderby=orderby)


    digest_list = [x['digest'] for x in raw_result]
    manifest_list = []

    for digest in digest_list:
        manifest_list.append(_obtain_manifest_from_registry(
            login_server=login_server,
            path=_get_v2_manifest_path(repository, digest),
            username=username,
            password=password))

    return manifest_list


def acr_repository_list_manifest_metadata(cmd,
                                  registry_name=None,
                                  repository=None,
                                  id=None,
                                  top=None,
                                  orderby=None,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None
                                  ):
    if (id and repository) or (not id and not (registry_name and repository)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_REPO)

    if id:
        registry_name, repository, _, _ = _parse_fqdn(cmd, id[0], is_manifest=False)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.METADATA_READ.value)

    raw_result = _obtain_data_from_registry(
        login_server=login_server,
        path=_get_manifest_path(repository),
        username=username,
        password=password,
        result_index='manifests',
        top=top,
        orderby=orderby)

    return raw_result

def acr_repository_list_manifest_referrers(cmd,
                                  registry_name=None,
                                  manifest_id=None,
                                  artifact_type=None,
                                  id=None,
                                  recurse=False,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):
    if (id and manifest_id) or (not id and not (registry_name and manifest_id)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_id, allow_digest=True)

    if not manifest:
        image = repository + ':' + tag
        repository, tag, manifest = get_image_digest(cmd, registry_name, image)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL.value)

    raw_result = _obtain_manifest_from_registry(
        login_server=login_server,
        path=_get_references_path(repository, manifest, artifact_type),
        username=username,
        password=password)

    ref_key = "references"
    if recurse:
        #checking for ref_key only necessary because of backend bug when manifest has no referrers
        if ref_key in raw_result:
            for referrers_obj in raw_result[ref_key]:
                internal_referrers_obj = _obtain_manifest_from_registry(
                                login_server=login_server,
                                path=_get_references_path(repository, referrers_obj["digest"]),
                                username=username,
                                password=password)

                if ref_key in internal_referrers_obj:
                    for ref in internal_referrers_obj[ref_key]:
                        raw_result[ref_key].append(ref)

    return raw_result


def acr_repository_show_manifest(cmd,
                                  registry_name=None,
                                  manifest_id=None,
                                  id=None,
                                  raw_output=None,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):
    if (id and manifest_id) or (not id and not (registry_name and manifest_id)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_id, allow_digest=True)

    if not manifest:
        image = repository + ':' + tag
        repository, tag, manifest = get_image_digest(cmd, registry_name, image)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL.value)

    raw_result = _obtain_manifest_from_registry(
        login_server=login_server,
        path=_get_v2_manifest_path(repository, manifest),
        raw=raw_output,
        username=username,
        password=password)

    if raw_output:
        print(raw_result, end='')
        return

    return raw_result


def acr_repository_show_manifest_metadata(cmd,
                                  registry_name=None,
                                  manifest_id=None,
                                  id=None,
                                  tenant_suffix=None,
                                  username=None,
                                  password=None):
    if (id and manifest_id) or (not id and not (registry_name and manifest_id)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_id, allow_digest=True)

    if not manifest:
        image = repository + ':' + tag
        repository, tag, manifest = get_image_digest(cmd, registry_name, image)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.PULL.value)

    raw_result = _obtain_manifest_from_registry(
        login_server=login_server,
        path=_get_manifest_path(repository, manifest),
        username=username,
        password=password)

    return raw_result


def acr_repository_update_manifest_metadata(cmd,
                          registry_name=None,
                          manifest_id=None,
                          id=None,
                          tenant_suffix=None,
                          username=None,
                          password=None,
                          delete_enabled=None,
                          list_enabled=None,
                          read_enabled=None,
                          write_enabled=None):
    if (id and manifest_id) or (not id and not (registry_name and manifest_id)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_id, allow_digest=True)

    if not manifest:
        image = repository + ':' + tag
        repository, tag, manifest = get_image_digest(cmd, registry_name, image)

    if not manifest_id:
        manifest_id = repository + '@' + manifest

    json_payload = {}

    if delete_enabled is not None:
        json_payload.update({
            'deleteEnabled': delete_enabled
        })
    if list_enabled is not None:
        json_payload.update({
            'listEnabled': list_enabled
        })
    if read_enabled is not None:
        json_payload.update({
            'readEnabled': read_enabled
        })
    if write_enabled is not None:
        json_payload.update({
            'writeEnabled': write_enabled
        })

    permission = RepoAccessTokenPermission.META_WRITE_META_READ.value if json_payload \
        else RepoAccessTokenPermission.METADATA_READ.value
    return _acr_repository_attributes_helper(
        cmd=cmd,
        registry_name=registry_name,
        http_method='patch' if json_payload else 'get',
        json_payload=json_payload,
        permission=permission,
        repository=None,
        image=manifest_id,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)


def acr_repository_delete_manifests(cmd,
                                    registry_name=None,
                                    manifest_id=None,
                                    id=None,
                                    tenant_suffix=None,
                                    username=None,
                                    password=None,
                                    yes=False):
    if (id and manifest_id) or (not id and not (registry_name and manifest_id)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_id, allow_digest=True)

    if not manifest:
        image = repository + ':' + tag
        repository, tag, manifest = get_image_digest(cmd, registry_name, image)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=RepoAccessTokenPermission.DELETE.value)

    user_confirmation("Are you sure you want to delete the artifact '{}' "
                          "and all manifests that refer to it?".format(manifest), yes)

    path = _get_v2_manifest_path(repository, manifest)
    request_data_from_registry(
        http_method='delete',
        login_server=login_server,
        path=path,
        username=username,
        password=password)[0]