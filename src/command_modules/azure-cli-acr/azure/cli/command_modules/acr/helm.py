# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from os.path import isdir, basename

from knack.util import CLIError
from knack.log import get_logger

from ._utils import user_confirmation
from ._docker_utils import get_access_credentials, request_data_from_registry


logger = get_logger(__name__)


# https://github.com/kubernetes/helm/blob/b6660cd5c9a9ee35ff24034fcc223b7eaeed3ee2/pkg/tiller/release_server.go#L80
VALID_NAME = '^(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])+(.tgz)(.prov)?$'


def acr_helm_list(cmd,
                  registry_name,
                  repository='repo',
                  resource_group_name=None,
                  username=None,
                  password=None):
    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
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
                  resource_group_name=None,
                  username=None,
                  password=None):
    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
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
                    resource_group_name=None,
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
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='*')

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
                  resource_group_name=None,
                  username=None,
                  password=None):
    if isdir(chart_package):
        raise CLIError("Please run 'helm package {}' to generate a chart package first.".format(chart_package))

    chart_name = basename(chart_package)
    if not re.match(VALID_NAME, chart_name):
        raise CLIError("Invalid helm package name '{}'. Is it a '*.tgz' or '*.tgz.prov' file?".format(chart_package))

    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='*')

    try:
        with open(chart_package, 'rb') as input_file:
            return request_data_from_registry(
                http_method='patch' if force else 'put',
                login_server=login_server,
                path=_get_blobs_path(repository, chart_name),
                username=username,
                password=password,
                data_payload=input_file,
                retry_times=1)[0]
    except OSError as e:
        raise CLIError(e)


def acr_helm_repo_add(cmd,
                      registry_name,
                      repository='repo',
                      resource_group_name=None,
                      username=None,
                      password=None):
    helm_command = _get_helm_command()

    login_server, username, password = get_access_credentials(
        cli_ctx=cmd.cli_ctx,
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password,
        artifact_repository=repository,
        permission='pull')

    from subprocess import Popen
    p = Popen([helm_command, 'repo', 'add', registry_name,
               'https://{}/helm/v1/{}'.format(login_server, repository),
               '--username', username, '--password', password])
    p.wait()


def _get_helm_command():
    helm_not_installed = "Please verify if helm is installed."
    helm_command = 'helm'

    from subprocess import PIPE, Popen
    try:
        p = Popen([helm_command, "--help"], stdout=PIPE, stderr=PIPE)
        _, stderr = p.communicate()
    except OSError:
        # The executable may not be discoverable in WSL so retry *.exe once
        try:
            helm_command = 'helm.exe'
            p = Popen([helm_command, "--help"], stdout=PIPE, stderr=PIPE)
            _, stderr = p.communicate()
        except OSError:
            raise CLIError(helm_not_installed)

    if stderr:
        raise CLIError(stderr.decode())

    return helm_command


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
