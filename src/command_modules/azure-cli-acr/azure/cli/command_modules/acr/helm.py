# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

from ._utils import user_confirmation
from ._docker_utils import get_access_credentials, request_data_from_registry, RegistryException


logger = get_logger(__name__)


def acr_helm_list(cmd,
                  registry_name,
                  repository='repo',
                  resource_group_name=None,  # pylint: disable=unused-argument
                  tenant_suffix=None,
                  username=None,
                  password=None):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='pull')

    return request_data_from_registry(
        http_method='get',
        login_server=login_server,
        path=_get_charts_path(repository),
        username=username,
        password=password)[0]


def acr_helm_show(cmd,
                  registry_name,
                  chart,
                  version=None,
                  repository='repo',
                  resource_group_name=None,  # pylint: disable=unused-argument
                  tenant_suffix=None,
                  username=None,
                  password=None):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='pull')

    return request_data_from_registry(
        http_method='get',
        login_server=login_server,
        path=_get_charts_path(repository, chart, version),
        username=username,
        password=password)[0]


def acr_helm_delete(cmd,
                    registry_name,
                    chart,
                    version=None,
                    repository='repo',
                    resource_group_name=None,  # pylint: disable=unused-argument
                    tenant_suffix=None,
                    username=None,
                    password=None,
                    prov=False,
                    yes=False):
    if version:
        message = "This operation will delete the chart package '{}'".format(
            _get_chart_package_name(chart, version, prov))
    else:
        message = "This operation will delete all versions of the chart '{}'".format(chart)
    user_confirmation("{}.\nAre you sure you want to continue?".format(message), yes)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='delete')

    return request_data_from_registry(
        http_method='delete',
        login_server=login_server,
        path=_get_blobs_path(repository, chart, version, prov) if version else _get_charts_path(repository, chart),
        username=username,
        password=password)[0]


def acr_helm_push(cmd,
                  registry_name,
                  chart_package,
                  repository='repo',
                  force=False,
                  resource_group_name=None,  # pylint: disable=unused-argument
                  tenant_suffix=None,
                  username=None,
                  password=None):
    from os.path import isdir, basename

    if isdir(chart_package):
        raise CLIError("Please run 'helm package {}' to generate a chart package first.".format(chart_package))

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='push,pull')

    path = _get_blobs_path(repository, basename(chart_package))

    try:
        result = request_data_from_registry(
            http_method='patch' if force else 'put',
            login_server=login_server,
            path=path,
            username=username,
            password=password,
            file_payload=chart_package)[0]
        return result
    except RegistryException as e:
        # Fallback using PUT if the chart doesn't exist
        if e.status_code == 404 and force:
            return request_data_from_registry(
                http_method='put',
                login_server=login_server,
                path=path,
                username=username,
                password=password,
                file_payload=chart_package)[0]
        raise


def acr_helm_repo_add(cmd,
                      registry_name,
                      repository='repo',
                      resource_group_name=None,  # pylint: disable=unused-argument
                      tenant_suffix=None,
                      username=None,
                      password=None):
    helm_command, _ = get_helm_command()

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='pull')

    from subprocess import Popen
    p = Popen([helm_command, 'repo', 'add', registry_name,
               'https://{}/helm/v1/{}'.format(login_server, repository),
               '--username', username, '--password', password])
    p.wait()


def get_helm_command(is_diagnostics_context=False):
    from ._errors import HELM_COMMAND_ERROR
    helm_command = 'helm'

    from subprocess import PIPE, Popen
    try:
        p = Popen([helm_command, "--help"], stdout=PIPE, stderr=PIPE)
        _, stderr = p.communicate()
    except OSError as e:
        logger.debug("Could not run '%s' command. Exception: %s", helm_command, str(e))
        # The executable may not be discoverable in WSL so retry *.exe once
        try:
            helm_command = 'helm.exe'
            p = Popen([helm_command, "--help"], stdout=PIPE, stderr=PIPE)
            _, stderr = p.communicate()
        except OSError as inner:
            logger.debug("Could not run '%s' command. Exception: %s", helm_command, str(inner))
            if is_diagnostics_context:
                return None, HELM_COMMAND_ERROR
            raise CLIError(HELM_COMMAND_ERROR.get_error_message())

    if stderr:
        if is_diagnostics_context:
            return None, HELM_COMMAND_ERROR.append_error_message(stderr.decode())
        raise CLIError(HELM_COMMAND_ERROR.append_error_message(stderr.decode()).get_error_message())

    return helm_command, None


def _get_charts_path(repository, chart=None, version=None):
    if chart and version:
        return '/helm/v1/{}/_charts/{}/{}'.format(repository, chart, version)

    if chart:
        return '/helm/v1/{}/_charts/{}'.format(repository, chart)

    return '/helm/v1/{}/_charts'.format(repository)


def _get_blobs_path(repository, chart, version=None, prov=False):
    path = '/helm/v1/{}/_blobs'.format(repository)

    if version:
        return '{}/{}'.format(path, _get_chart_package_name(chart, version, prov))

    return '{}/{}'.format(path, chart)


def _get_chart_package_name(chart, version, prov=False):
    chart_package_name = '{}-{}.tgz'.format(chart, version)

    if prov:
        return '{}.prov'.format(chart_package_name)

    return chart_package_name
