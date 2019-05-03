# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
import json
import platform
import subprocess
import datetime
import ssl
import sys
import zipfile
from six.moves.urllib.parse import urlparse
from six.moves.urllib.request import urlopen  # pylint: disable=import-error
from azure.cli.core._profile import Profile
from azure.cli.core.util import in_cloud_console
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


STORAGE_RESOURCE_ENDPOINT = "https://storage.azure.com"
SERVICES = {'blob', 'file'}
AZCOPY_VERSION = '10.1.0'


class AzCopy(object):
    def __init__(self, creds=None):
        self.system = platform.system()
        install_location = _get_default_install_location()
        if not os.path.isfile(install_location):
            install_dir = os.path.dirname(install_location)
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)
            base_url = 'https://azcopyvnext.azureedge.net/release20190423/azcopy_{}_amd64_10.1.0.{}'
            if self.system == 'Windows':
                file_url = base_url.format('windows', 'zip')
            elif self.system == 'Linux':
                file_url = base_url.format('linux', 'tar.gz')
            elif self.system == 'Darwin':
                file_url = base_url.format('darwin', 'zip')
            else:
                raise CLIError('Azcopy ({}) does not exist.'.format(self.system))
            try:
                _urlretrieve(file_url, install_location)
            except IOError as err:
                raise CLIError('Connection error while attempting to download azcopy ({})'.format(err))

        self.executable = install_location
        self.creds = creds

    def run_command(self, args):
        args = [self.executable] + args
        args = ' '.join(args)
        logger.warning("Azcopy command: %s", args)
        env_kwargs = {}
        if self.creds and self.creds.token_info:
            env_kwargs = {'AZCOPY_OAUTH_TOKEN_INFO': json.dumps(self.creds.token_info)}
        subprocess.call(args, env=dict(os.environ, **env_kwargs))

    def copy(self, source, destination, flags=None):
        flags = flags or []
        self.run_command(['copy', source, destination] + flags)

    def remove(self, target, flags=None):
        flags = flags or []
        self.run_command(['remove', target] + flags)

    def sync(self, source, destination, flags=None):
        flags = flags or []
        self.run_command(['sync', source, destination] + flags)


class AzCopyCredentials(object):  # pylint: disable=too-few-public-methods
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


def blob_client_auth_for_azcopy(cmd, blob_client):
    azcopy_creds = storage_client_auth_for_azcopy(cmd, blob_client, 'blob')
    if azcopy_creds is not None:
        return azcopy_creds

    # oauth mode
    token_info = Profile(cli_ctx=cmd.cli_ctx).get_raw_token(resource=STORAGE_RESOURCE_ENDPOINT)[0][2]
    try:
        token_info = _unserialize_non_msi_token_payload(token_info)
    except KeyError:  # unserialized MSI token payload
        raise Exception('MSI auth not yet supported.')
    return AzCopyCredentials(token_info=token_info)


def storage_client_auth_for_azcopy(cmd, client, service):
    if service not in SERVICES:
        raise Exception('{} not one of: {}'.format(service, str(SERVICES)))

    if client.sas_token:
        return AzCopyCredentials(sas_token=client.sas_token)

    # if account key provided, generate a sas token
    if client.account_key:
        sas_token = _generate_sas_token(cmd, client.account_name, client.account_key, service)
        return AzCopyCredentials(sas_token=sas_token)
    return None


def _unserialize_non_msi_token_payload(token_info):
    import jwt  # pylint: disable=import-error

    parsed_authority = urlparse(token_info['_authority'])
    decode = jwt.decode(token_info['accessToken'], verify=False, algorithms=['RS256'])
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


def _generate_sas_token(cmd, account_name, account_key, service):
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
        resource_type_type(cmd.loader)('sco'),
        t_account_permissions(_str='rwdlacup'),
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    )


def _get_default_install_location():
    system = platform.system()
    if system == 'Windows':
        home_dir = os.environ.get('USERPROFILE')
        if not home_dir:
            return None
        install_location = os.path.join(home_dir, r'.azcopy\azcopy.exe')
    elif system == 'Linux' or system == 'Darwin':
        install_location = '/usr/local/bin/azcopy'
    else:
        install_location = None
    return install_location


def _ssl_context():
    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url, install_location):
    req = urlopen(url, context=_ssl_context())
    if sys.version_info.major >= 3:
        import io
        zip_file = zipfile.ZipFile(io.BytesIO(req.read()))
    else:
        # If Python version is 2.X, use StringIO instead.
        import StringIO  # pylint: disable=import-error
        zip_file = zipfile.ZipFile(StringIO.StringIO(req.read()))
    for fileName in zip_file.namelist():
        if fileName.endswith('azcopy') or fileName.endswith('azcopy.exe'):
            with open(install_location, 'wb') as f:
                f.write(zip_file.read(fileName))
