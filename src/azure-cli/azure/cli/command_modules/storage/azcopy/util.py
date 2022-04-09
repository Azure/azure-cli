# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
import json
import platform
import subprocess
import datetime
import sys
import zipfile
import stat
from urllib.parse import urlparse
from urllib.request import urlopen
from azure.cli.core._profile import Profile
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


STORAGE_RESOURCE_ENDPOINT = "https://storage.azure.com"
SERVICES = {'blob', 'file'}
AZCOPY_VERSION = '10.13.0'


class AzCopy:
    def __init__(self, creds=None):
        self.system = platform.system()
        install_location = _get_default_install_location()
        self.executable = install_location
        self.creds = creds
        if not os.path.isfile(install_location) or self.check_version() != AZCOPY_VERSION:
            self.install_azcopy(install_location)

    def install_azcopy(self, install_location):
        install_dir = os.path.dirname(install_location)
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
        base_url = 'https://azcopyvnext.azureedge.net/release20211027/azcopy_{}_{}_{}.{}'

        if self.system == 'Windows':
            if platform.machine().endswith('64'):
                file_url = base_url.format('windows', 'amd64', AZCOPY_VERSION, 'zip')
            else:
                file_url = base_url.format('windows', '386', AZCOPY_VERSION, 'zip')
        elif self.system == 'Linux':
            file_url = base_url.format('linux', 'amd64', AZCOPY_VERSION, 'tar.gz')
        elif self.system == 'Darwin':
            file_url = base_url.format('darwin', 'amd64', AZCOPY_VERSION, 'zip')
        else:
            raise CLIError('Azcopy ({}) does not exist.'.format(self.system))
        try:
            os.chmod(install_dir, os.stat(install_dir).st_mode | stat.S_IWUSR)
            _urlretrieve(file_url, install_location)
            os.chmod(install_location,
                     os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except IOError as err:
            raise CLIError('Connection error while attempting to download azcopy {}. You could also install the '
                           'specified azcopy version to {} manually. ({})'.format(AZCOPY_VERSION, install_dir, err))

    def check_version(self):
        try:
            import re
            args = [self.executable] + ["--version"]
            out_bytes = subprocess.check_output(args)
            out_text = out_bytes.decode('utf-8')
            version = re.findall(r"azcopy version (.+?)\n", out_text)[0]
            return version
        except subprocess.CalledProcessError:
            return ""

    def run_command(self, args):
        args = [self.executable] + args
        args_hides = args.copy()
        for i in range(len(args_hides)):
            if args_hides[i].find('sig') > 0:
                args_hides[i] = args_hides[i][0:args_hides[i].index('sig')+4]
        logger.warning("Azcopy command: %s", args_hides)
        env_kwargs = {}
        if self.creds and self.creds.token_info:
            env_kwargs = {'AZCOPY_OAUTH_TOKEN_INFO': json.dumps(self.creds.token_info)}
        result = subprocess.call(args, env=dict(os.environ, **env_kwargs))
        if result > 0:
            raise CLIError('Failed to perform {} operation.'.format(args[1]))

    def copy(self, source, destination, flags=None):
        flags = flags or []
        self.run_command(['copy', source, destination] + flags)

    def remove(self, target, flags=None):
        flags = flags or []
        self.run_command(['remove', target] + flags)

    def sync(self, source, destination, flags=None):
        flags = flags or []
        self.run_command(['sync', source, destination] + flags)


class AzCopyCredentials:  # pylint: disable=too-few-public-methods
    def __init__(self, sas_token=None, token_info=None):
        self.sas_token = sas_token
        self.token_info = token_info


def login_auth_for_azcopy(cmd):
    token_info = Profile(cli_ctx=cmd.cli_ctx).get_raw_token(resource=STORAGE_RESOURCE_ENDPOINT)[0][2]
    try:
        token_info = _unserialize_non_msi_token_payload(token_info)
    except KeyError:  # unserialized MSI token payload
        raise Exception('MSI auth not yet supported.')
    return AzCopyCredentials(token_info=token_info)


def client_auth_for_azcopy(cmd, client, service='blob'):
    azcopy_creds = storage_client_auth_for_azcopy(client, service)
    if azcopy_creds is not None:
        return azcopy_creds

    # oauth mode
    if client.token_credential:
        token_info = Profile(cli_ctx=cmd.cli_ctx).get_raw_token(resource=STORAGE_RESOURCE_ENDPOINT)[0][2]
        try:
            token_info = _unserialize_non_msi_token_payload(token_info)
        except KeyError as ex:  # unserialized token payload
            from azure.cli.core.azclierror import ValidationError
            raise ValidationError('No {}. MSI auth and service principal are not yet supported.'.format(ex))
        return AzCopyCredentials(token_info=token_info)

    return None


def storage_client_auth_for_azcopy(client, service):
    if service not in SERVICES:
        raise Exception('{} not one of: {}'.format(service, str(SERVICES)))

    if client.sas_token:
        return AzCopyCredentials(sas_token=client.sas_token)
    return None


def _unserialize_non_msi_token_payload(token_info):
    import jwt  # pylint: disable=import-error

    parsed_authority = urlparse(token_info['_authority'])
    decode = jwt.decode(token_info['accessToken'], algorithms=['RS256'], options={"verify_signature": False})
    return {
        'access_token': token_info['accessToken'],
        'refresh_token': token_info['refreshToken'],
        'expires_in': str(token_info['expiresIn']),
        'not_before': str(decode['nbf']),
        'expires_on': str(int((datetime.datetime.strptime(
            token_info['expiresOn'], "%Y-%m-%d %H:%M:%S.%f")).timestamp())),
        'resource': STORAGE_RESOURCE_ENDPOINT,
        'token_type': token_info['tokenType'],
        '_tenant': parsed_authority.path.strip('/'),
        '_client_id': token_info['_clientId'],
        '_ad_endpoint': '{uri.scheme}://{uri.netloc}'.format(uri=parsed_authority)
    }


def _generate_sas_token(cmd, account_name, account_key, service, resource_types='sco', permissions='rwdlacup'):
    from .._client_factory import cloud_storage_account_service_factory
    from .._validators import resource_type_type, services_type

    kwargs = {
        'account_name': account_name,
        'account_key': account_key
    }
    cloud_storage_client = cloud_storage_account_service_factory(cmd.cli_ctx, kwargs)
    t_account_permissions = cmd.loader.get_sdk('common.models#AccountPermissions')

    return cloud_storage_client.generate_shared_access_signature(
        services_type(cmd.loader)(service[0]),
        resource_type_type(cmd.loader)(resource_types),
        t_account_permissions(_str=permissions),
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    )


def _get_default_install_location():
    system = platform.system()
    if system == 'Windows':
        home_dir = os.environ.get('USERPROFILE')
        if not home_dir:
            raise CLIError('In the Windows platform, please specify the environment variable "USERPROFILE" '
                           'as the installation location.')
        install_location = os.path.join(home_dir, r'.azcopy\azcopy.exe')
    elif system in ('Linux', 'Darwin'):
        install_location = os.path.expanduser(os.path.join('~', 'bin/azcopy'))
    else:
        raise CLIError('The {} platform is not currently supported. If you want to know which platforms are supported, '
                       'please refer to the document for supported platforms: '
                       'https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10#download-azcopy'
                       .format(system))
    return install_location


def _urlretrieve(url, install_location):
    import io
    req = urlopen(url)
    compressedFile = io.BytesIO(req.read())
    if url.endswith('zip'):
        if sys.version_info.major >= 3:
            zip_file = zipfile.ZipFile(compressedFile)
        else:
            # If Python version is 2.X, use StringIO instead.
            import StringIO  # pylint: disable=import-error
            zip_file = zipfile.ZipFile(StringIO.StringIO(req.read()))
        for fileName in zip_file.namelist():
            if fileName.endswith('azcopy') or fileName.endswith('azcopy.exe'):
                with open(install_location, 'wb') as f:
                    f.write(zip_file.read(fileName))
    elif url.endswith('gz'):
        import tarfile
        with tarfile.open(fileobj=compressedFile, mode="r:gz") as tar:
            for tarinfo in tar:
                if tarinfo.isfile() and tarinfo.name.endswith('azcopy'):
                    with open(install_location, 'wb') as f:
                        f.write(tar.extractfile(tarinfo).read())
    else:
        raise CLIError('Invalid downloading url {}'.format(url))
