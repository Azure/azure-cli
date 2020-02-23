# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform

from knack.util import CLIError
from knack.log import get_logger
from six.moves.urllib.request import urlopen  # pylint: disable=import-error
from six.moves.urllib.error import URLError  # pylint: disable=import-error

from azure.cli.core.util import in_cloud_console
from ._utils import user_confirmation

from ._docker_utils import (
    get_access_credentials,
    request_data_from_registry,
    RegistryException,
    HelmAccessTokenPermission
)


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
        permission=HelmAccessTokenPermission.PULL.value)

    return request_data_from_registry(
        http_method='get',
        login_server=login_server,
        path=_get_charts_path(repository),
        username=username,
        password=password)[0]


def acr_helm_show(cmd,
                  registry_name,
                  chart,
                  client_version=None,
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
        permission=HelmAccessTokenPermission.PULL.value)

    return request_data_from_registry(
        http_method='get',
        login_server=login_server,
        path=_get_charts_path(repository, chart, client_version),
        username=username,
        password=password)[0]


def acr_helm_delete(cmd,
                    registry_name,
                    chart,
                    client_version=None,
                    repository='repo',
                    resource_group_name=None,  # pylint: disable=unused-argument
                    tenant_suffix=None,
                    username=None,
                    password=None,
                    prov=False,
                    yes=False):
    if client_version:
        message = "This operation will delete the chart package '{}'".format(
            _get_chart_package_name(chart, client_version, prov))
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
        permission=HelmAccessTokenPermission.DELETE.value)

    return request_data_from_registry(
        http_method='delete',
        login_server=login_server,
        path=_get_blobs_path(repository, chart, client_version, prov) if client_version else _get_charts_path(repository, chart),
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
        permission=HelmAccessTokenPermission.PUSH_PULL.value)

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
        permission=HelmAccessTokenPermission.PULL.value)

    from subprocess import Popen
    p = Popen([helm_command, 'repo', 'add', registry_name,
               'https://{}/helm/v1/{}'.format(login_server, repository),
               '--username', username, '--password', password])
    p.wait()


def acr_helm_install_cli(cmd, client_version='2.16.3', install_location=None, yes=False):
    """Install Helm command-line interface."""

    if client_version >= '3':
        raise CLIError('Helm v3 is not supported yet.')

    if not install_location:
        raise CLIError('Invalid install location.')

    # ensure installation directory exists
    install_dir, cli = os.path.dirname(install_location), os.path.basename(install_location)
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    client_version = "v%s" % client_version
    # source_url = 'https://get.helm.sh/{}'
    source_url = 'http://localhost:8000/{}'
    package, folder = _get_helm_package_name(client_version)
    download_path = '' # path to downloaded file

    if not package:
        raise CLIError("Current system is not supported.")

    # TODO: sha verification

    system = platform.system()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Download
        download_path = os.path.join(tmp_dir, package)
        _urlretrieve(source_url.format(package), download_path)

        # Unzip
        try:
            if system == 'Windows':
                import zipfile
                with zipfile.ZipFile(download_path, 'r') as zipObj:
                    zipObj.extractall(tmp_dir)
            elif system in ('Linux', 'Darwin'):
                import tarfile
                with tarfile.open(download_path, 'r') as tarObj:
                    tarObj.extractall(tmp_dir)
            else:
                raise CLIError('This system is not supported yet.')

            sub_dir = os.path.join(tmp_dir, folder)
            # Show license
            if not yes:
                with open(os.path.join(sub_dir, 'LICENSE')) as f:
                    text = f.read()
                    logger.warning(text)
                user_confirmation('Before proceeding with the installation, '
                                  'please confirm that you have read and agreed the above license.')

            # Move files from temporary location to specified location
            import shutil
            for f in os.scandir(sub_dir):
                # Rename helm to specified name
                if os.path.splitext(f.name)[0] == 'helm':
                    shutil.move(f.path, install_location)
                else:
                    shutil.move(f.path, install_dir)

            import stat
            os.chmod(install_location, os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except IOError as e:
            raise CLIError('Error while installing {}: {}'.format(package, e))

    # Remind user to add to path
    if system == 'Windows':  # be verbose, as the install_location likely not in Windows's search PATHs
        env_paths = os.environ['PATH'].split(';')
        found = next((x for x in env_paths if x.lower().rstrip('\\') == install_dir.lower()), None)
        if not found:
            # pylint: disable=logging-format-interpolation
            logger.warning('Please add "{0}" to your search PATH so the `{1}` can be found. 2 options: \n'
                           '    1. Run "set PATH=%PATH%;{0}" or "$env:path += \'{0}\'" for PowerShell. '
                           'This is good for the current command session.\n'
                           '    2. Update system PATH environment variable by following '
                           '"Control Panel->System->Advanced->Environment Variables", and re-open the command window. '
                           'You only need to do it once'.format(install_dir, cli))
    else:
        logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                       install_dir, cli)


def _ssl_context():
    import sys
    import ssl

    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


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


def _get_charts_path(repository, chart=None, client_version=None):
    if chart and client_version:
        return '/helm/v1/{}/_charts/{}/{}'.format(repository, chart, client_version)

    if chart:
        return '/helm/v1/{}/_charts/{}'.format(repository, chart)

    return '/helm/v1/{}/_charts'.format(repository)


def _get_blobs_path(repository, chart, client_version=None, prov=False):
    path = '/helm/v1/{}/_blobs'.format(repository)

    if client_version:
        return '{}/{}'.format(path, _get_chart_package_name(chart, client_version, prov))

    return '{}/{}'.format(path, chart)


def _get_chart_package_name(chart, client_version, prov=False):
    chart_package_name = '{}-{}.tgz'.format(chart, client_version)

    if prov:
        return '{}.prov'.format(chart_package_name)

    return chart_package_name


def _get_helm_package_name(client_version):
    package_template = 'helm-{}-{}-{}.{}'
    folder_template = '{}-{}'
    package = ''
    folder = ''

    archs = {
        'armv5*': 'armv5',
        'armv6*': 'armv6',
        'armv7*': 'arm',
        'aarch64': 'arm64',
        'x86': '386',
        'x86_64': 'amd64',
        'i686': '386',
        'i386': '386',
        'AMD64': 'amd64',
        'ppc64le': 'ppc64le',
        's390x': 's390x'
    }
    machine = platform.machine()
    if machine not in archs:
        return None, None
    arch = archs[machine]

    system = platform.system().lower()
    if system == 'windows':
        package = package_template.format(client_version, system, arch, 'zip')
    elif system in ('linux', 'darwin'):
        package = package_template.format(client_version, system, arch, 'tar.gz')
    else:
        return None, None

    folder = folder_template.format(system, arch)
    return package, folder


def _urlretrieve(url, path):
    logger.warning('Requesting %s, it may take a long time...', url)
    with urlopen(url, context=_ssl_context()) as response:
        logger.debug('Start downloading from %s to %s', url, path)
        # Open for writing in binary mode
        with open(path, "wb") as f:
            f.write(response.read())
    logger.debug('Successfully downloaded from %s to %s', url, path)
