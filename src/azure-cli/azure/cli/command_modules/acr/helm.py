# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
from urllib.request import urlopen

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.util import in_cloud_console, user_confirmation

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
        permission=HelmAccessTokenPermission.PULL.value)

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
        permission=HelmAccessTokenPermission.DELETE.value)

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


def acr_helm_install_cli(client_version='2.16.3', install_location=None, yes=False):
    """Install Helm command-line tool."""

    if client_version >= '3':
        logger.warning('Please note that "az acr helm" commands do not work with Helm 3, '
                       'but you can still push Helm chart to ACR using a different command flow. '
                       'For more information, please check out '
                       'https://docs.microsoft.com/azure/container-registry/container-registry-helm-repos')

    install_location, install_dir, cli = _process_helm_install_location_info(install_location)

    client_version = "v%s" % client_version
    source_url = 'https://get.helm.sh/{}'
    package, folder = _get_helm_package_name(client_version)
    download_path = ''

    if not package:
        raise CLIError('No prebuilt binary for current system.')

    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            download_path = os.path.join(tmp_dir, package)
            _urlretrieve(source_url.format(package), download_path)
            _unzip(download_path, tmp_dir)

            sub_dir = os.path.join(tmp_dir, folder)
            # Ask user to check license
            if not yes:
                with open(os.path.join(sub_dir, 'LICENSE')) as f:
                    text = f.read()
                    logger.warning(text)
                user_confirmation('Before proceeding with the installation, '
                                  'please confirm that you have read and agreed the above license.')

            # Move files from temporary location to specified location
            import shutil
            import stat
            for f in os.scandir(sub_dir):
                # Rename helm to specified name
                target_path = install_location if os.path.splitext(f.name)[0] == 'helm' \
                    else os.path.join(install_dir, f.name)
                logger.debug('Moving %s to %s', f.path, target_path)
                shutil.move(f.path, target_path)

                if os.path.splitext(f.name)[0] in ('helm', 'tiller'):
                    os.chmod(target_path, os.stat(target_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except IOError as e:
        import traceback
        logger.debug(traceback.format_exc())
        raise CLIError('Error while installing {} to {}: {}'.format(cli, install_dir, e))

    logger.warning('Successfully installed %s to %s.', cli, install_dir)
    # Remind user to add to path
    system = platform.system()
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


def _process_helm_install_location_info(install_location):
    if not install_location or install_location.isspace():
        raise CLIError('Invalid install location.')

    install_dir, cli = os.path.dirname(install_location), os.path.basename(install_location)
    if not install_dir:
        # Use current working directory
        install_dir = os.getcwd()
        install_location = os.path.join(install_dir, cli)
    # Ensure installation directory exists
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
    if not cli:
        system = platform.system()
        cli = 'helm.exe' if system == 'Windows' else 'helm'
        install_location = os.path.join(install_dir, cli)

    return install_location, install_dir, cli


def _get_helm_package_name(client_version):
    package_template = 'helm-{}-{}-{}.{}'
    folder_template = '{}-{}'
    package = ''
    folder = ''

    # Reference: https://github.com/helm/helm/blob/master/scripts/get
    archs = {
        'armv5': 'armv5',
        'armv6': 'armv6',
        'armv7': 'arm',
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


def _ssl_context():
    import sys
    import ssl

    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url, path):
    logger.warning('Downloading client from %s, it may take a long time...', url)
    with urlopen(url, context=_ssl_context()) as response:
        logger.debug('Start downloading from %s to %s', url, path)
        # Open for writing in binary mode
        with open(path, "wb") as f:
            f.write(response.read())
    logger.debug('Successfully downloaded from %s to %s', url, path)


def _unzip(src, dest):
    logger.debug('Extracting %s to %s.', src, dest)
    system = platform.system()
    if system == 'Windows':
        import zipfile
        with zipfile.ZipFile(src, 'r') as zipObj:
            zipObj.extractall(dest)
    elif system in ('Linux', 'Darwin'):
        import tarfile
        with tarfile.open(src, 'r') as tarObj:
            tarObj.extractall(dest)
    else:
        raise CLIError('The current system is not supported.')
