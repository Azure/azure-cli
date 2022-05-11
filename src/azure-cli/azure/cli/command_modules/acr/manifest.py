# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

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

from ._docker_utils import (
    request_data_from_registry,
    get_access_credentials,
    get_login_server_suffix,
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

BAD_ARGS_ERROR_REPO = "You must provide either a fully qualified repository specifier such as"\
                      " 'MyRegistry.azurecr.io/hello-world' as a positional parameter or"\
                      " provide '-r MyRegistry -n hello-world' argument values."
BAD_ARGS_ERROR_MANIFEST = "You must provide either a fully qualified manifest specifier such as"\
                          " 'MyRegistry.azurecr.io/hello-world:latest' as a positional parameter or provide"\
                          " '-r MyRegistry -n hello-world:latest' argument values."


def _get_v2_manifest_path(repository, manifest):
    return '/v2/{}/manifests/{}'.format(repository, manifest)


def _get_referrers_path(repository, manifest):
    return '/oras/artifacts/v1/{}/manifests/{}/referrers'.format(repository, manifest)


def _obtain_manifest_from_registry(login_server,
                                   path,
                                   username,
                                   password,
                                   raw=False):

    result, _ = request_data_from_registry(http_method='get',
                                           login_server=login_server,
                                           path=path,
                                           raw=raw,
                                           username=username,
                                           password=password,
                                           result_index=None,
                                           manifest_headers=True)

    return result


def _obtain_referrers_from_registry(login_server,
                                    path,
                                    username,
                                    password,
                                    artifact_type=None):

    result_list = {'references': []}
    execute_next_http_call = True

    params = {
        'artifactType': artifact_type
    }

    while execute_next_http_call:
        execute_next_http_call = False

        result, next_link = request_data_from_registry(
            http_method='get',
            login_server=login_server,
            path=path,
            username=username,
            password=password,
            result_index=None,
            params=params)

        if result:
            result_list['references'].extend(result['references'])

        if next_link:
            # The registry is telling us there's more items in the list,
            # and another call is needed. The link header looks something
            # like `Link: </v2/_catalog?last=hello-world&n=1>; rel="next"`
            # we should follow the next path indicated in the link header
            next_link_path = next_link[(next_link.index('<') + 1):next_link.index('>')]
            tokens = next_link_path.split('?', 1)
            params = {y[0]: unquote(y[1]) for y in (x.split('=', 1) for x in tokens[1].split('&'))}

            execute_next_http_call = True

    return result_list


def _parse_fqdn(cmd, fqdn, is_manifest=True):
    try:
        if fqdn.startswith('https://'):
            fqdn = fqdn[len('https://'):]
        reg_addr = fqdn.split('/', 1)[0]
        registry_name = reg_addr.split('.', 1)[0]
        reg_suffix = '.' + reg_addr.split('.', 1)[1]
        manifest_spec = fqdn.split('/', 1)[1]

        _validate_login_server_suffix(cmd, reg_suffix)

        # We must check for this here as the default tag 'latest' gets added in _parse_image_name
        if not is_manifest and ':' in manifest_spec:
            raise InvalidArgumentValueError("The positional parameter 'repo_id'"
                                            " should not include a tag or digest.")

        repository, tag, manifest = _parse_image_name(manifest_spec, allow_digest=True)

    except IndexError as e:
        if is_manifest:
            raise InvalidArgumentValueError(BAD_MANIFEST_FQDN) from e

        raise InvalidArgumentValueError(BAD_REPO_FQDN) from e

    return registry_name, repository, tag, manifest


def _validate_login_server_suffix(cmd, reg_suffix):
    cli_ctx = cmd.cli_ctx
    login_server_suffix = get_login_server_suffix(cli_ctx)

    if reg_suffix != login_server_suffix:
        raise InvalidArgumentValueError(f'Provided registry suffix \'{reg_suffix}\' does not match the configured az'
                                        f' cli acr login server suffix \'{login_server_suffix}\'. Check the'
                                        ' \'acrLoginServerEndpoint\' value when running \'az cloud show\'.')


def acr_manifest_list(cmd,
                      registry_name=None,
                      repository=None,
                      repo_id=None,
                      top=None,
                      orderby=None,
                      tenant_suffix=None,
                      username=None,
                      password=None):
    if (repo_id and repository) or (not repo_id and not (registry_name and repository)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_REPO)

    if repo_id:
        registry_name, repository, _, _ = _parse_fqdn(cmd, repo_id[0], is_manifest=False)

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


def acr_manifest_metadata_list(cmd,
                               registry_name=None,
                               repository=None,
                               repo_id=None,
                               top=None,
                               orderby=None,
                               tenant_suffix=None,
                               username=None,
                               password=None):
    if (repo_id and repository) or (not repo_id and not (registry_name and repository)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_REPO)

    if repo_id:
        registry_name, repository, _, _ = _parse_fqdn(cmd, repo_id[0], is_manifest=False)

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


def acr_manifest_list_referrers(cmd,
                                registry_name=None,
                                manifest_spec=None,
                                artifact_type=None,
                                manifest_id=None,
                                recursive=False,
                                tenant_suffix=None,
                                username=None,
                                password=None):
    if (manifest_id and manifest_spec) or (not manifest_id and not (registry_name and manifest_spec)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if manifest_id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, manifest_id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_spec, allow_digest=True)

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

    raw_result = _obtain_referrers_from_registry(
        login_server=login_server,
        path=_get_referrers_path(repository, manifest),
        username=username,
        password=password,
        artifact_type=artifact_type)

    ref_key = "references"
    if recursive:
        for referrers_obj in raw_result[ref_key]:
            internal_referrers_obj = _obtain_referrers_from_registry(
                login_server=login_server,
                path=_get_referrers_path(repository, referrers_obj["digest"]),
                username=username,
                password=password)

            for ref in internal_referrers_obj[ref_key]:
                raw_result[ref_key].append(ref)

    return raw_result


def acr_manifest_show(cmd,
                      registry_name=None,
                      manifest_spec=None,
                      manifest_id=None,
                      raw_output=None,
                      tenant_suffix=None,
                      username=None,
                      password=None):
    if (manifest_id and manifest_spec) or (not manifest_id and not (registry_name and manifest_spec)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if manifest_id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, manifest_id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_spec, allow_digest=True)

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

    # We are forced to print directly here in order to preserve bit for bit integrity and
    # avoid any formatting so that the output can successfully be hashed. Customer will expect that
    # 'az acr manifest show myreg.azurecr.io/myrepo@sha256:abc123 --raw | shasum -a 256' will result in 'abc123'
    if raw_output:
        print(raw_result, end='')
        return

    return raw_result


def acr_manifest_metadata_show(cmd,
                               registry_name=None,
                               manifest_spec=None,
                               manifest_id=None,
                               tenant_suffix=None,
                               username=None,
                               password=None):
    if (manifest_id and manifest_spec) or (not manifest_id and not (registry_name and manifest_spec)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if manifest_id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, manifest_id[0])
        manifest_spec = repository + ':' + tag if tag else repository + '@' + manifest

    return _acr_repository_attributes_helper(
        cmd=cmd,
        registry_name=registry_name,
        http_method='get',
        json_payload=None,
        permission=RepoAccessTokenPermission.METADATA_READ.value,
        repository=None,
        image=manifest_spec,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)


def acr_manifest_metadata_update(cmd,
                                 registry_name=None,
                                 manifest_spec=None,
                                 manifest_id=None,
                                 tenant_suffix=None,
                                 username=None,
                                 password=None,
                                 delete_enabled=None,
                                 list_enabled=None,
                                 read_enabled=None,
                                 write_enabled=None):
    if (manifest_id and manifest_spec) or (not manifest_id and not (registry_name and manifest_spec)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if manifest_id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, manifest_id[0])
        manifest_spec = repository + ':' + tag if tag else repository + '@' + manifest

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
        image=manifest_spec,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)


def acr_manifest_delete(cmd,
                        registry_name=None,
                        manifest_spec=None,
                        manifest_id=None,
                        tenant_suffix=None,
                        username=None,
                        password=None,
                        yes=False):
    if (manifest_id and manifest_spec) or (not manifest_id and not (registry_name and manifest_spec)):
        raise InvalidArgumentValueError(BAD_ARGS_ERROR_MANIFEST)

    if manifest_id:
        registry_name, repository, tag, manifest = _parse_fqdn(cmd, manifest_id[0])

    else:
        repository, tag, manifest = _parse_image_name(manifest_spec, allow_digest=True)

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

    user_confirmation("Are you sure you want to delete the artifact '{}'"
                      " and all manifests that refer to it?".format(manifest), yes)

    return request_data_from_registry(
        http_method='delete',
        login_server=login_server,
        path=_get_v2_manifest_path(repository, manifest),
        username=username,
        password=password)[0]
