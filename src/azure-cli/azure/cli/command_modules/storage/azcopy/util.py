# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
import subprocess
import datetime
import zipfile
import stat
from urllib.parse import urlparse
from urllib.request import urlopen
from azure.cli.core._profile import Profile
from azure.cli.core.api import get_config_dir
from knack.log import get_logger
from knack.util import CLIError
from packaging.version import parse as parse_version

logger = get_logger(__name__)


STORAGE_RESOURCE_ENDPOINT = "https://storage.azure.com"
SERVICES = {'blob', 'file'}
AZCOPY_VERSION = '10.13.0'


class AzCopy:
    def __init__(self, creds=None):
        self.system = platform.system()
        install_location = _get_default_install_location()
        self.executable = None
        if os.path.isfile(install_location):
            self.executable = install_location
            version = self.check_version()
            if not version or parse_version(version) < parse_version(AZCOPY_VERSION):
                self.executable = None
        else:
            try:
                import re
                args = ["azcopy", "--version"]
                out_bytes = subprocess.check_output(args)
                out_text = out_bytes.decode('utf-8')
                version = re.findall(r"azcopy version (.+?)\n", out_text)[0]
                if version and parse_version(version) >= parse_version(AZCOPY_VERSION):
                    self.executable = "azcopy"
            except Exception:  # pylint: disable=broad-except
                self.executable = None
        self.creds = creds
        if not self.executable:
            logger.warning("Azcopy not found, installing at %s", install_location)
            self.install_azcopy(install_location)
            self.executable = install_location

    def install_azcopy(self, install_location):
        install_dir = os.path.dirname(install_location)
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
        base_url = 'https://azcopyvnext-awgzd8g7aagqhzhe.b02.azurefd.net/release20211027/azcopy_{}_{}_{}.{}'
        if self.system == 'Windows':
            if platform.machine().endswith('64'):
                file_url = base_url.format('windows', 'amd64', AZCOPY_VERSION, 'zip')
                if _verify_url(file_url) is None:
                    file_url = _verify_url('https://aka.ms/InstallAzCopyForCLIWindowsX64')
            else:
                file_url = base_url.format('windows', '386', AZCOPY_VERSION, 'zip')
                if _verify_url(file_url) is None:
                    file_url = _verify_url('https://aka.ms/InstallAzCopyForCLIWindows')
        elif self.system == 'Linux':
            file_url = base_url.format('linux', 'amd64', AZCOPY_VERSION, 'tar.gz')
            if _verify_url(file_url) is None:
                file_url = _verify_url('https://aka.ms/InstallAzCopyForCLILinux')
        elif self.system == 'Darwin':
            file_url = base_url.format('darwin', 'amd64', AZCOPY_VERSION, 'zip')
            if _verify_url(file_url) is None:
                file_url = _verify_url('https://aka.ms/InstallAzCopyForCLIDarwin')
        else:
            raise CLIError('Azcopy ({}) does not exist.'.format(self.system))
        try:
            os.chmod(install_dir, os.stat(install_dir).st_mode | stat.S_IWUSR)
            _urlretrieve(file_url, install_location)
            os.chmod(install_location,
                     os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError as err:
            azcopy_install_guide = 'https://learn.microsoft.com/azure/storage/common/storage-use-azcopy-v10'
            raise CLIError('Connection error while attempting to download azcopy {}. You could also install the '
                           'specified azcopy version to {} manually following the guide here: {} '
                           '({})'.format(AZCOPY_VERSION, install_dir, azcopy_install_guide, err))

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
        for i, v in enumerate(args_hides):
            if v.find('sig') > 0:
                args_hides[i] = v[0:v.index('sig') + 4]
        logger.warning("Azcopy command: %s", args_hides)
        env_kwargs = {}
        if self.creds and self.creds.tenant_id:
            env_kwargs = {'AZCOPY_TENANT_ID': self.creds.tenant_id,
                          'AZCOPY_AUTO_LOGIN_TYPE': 'AzCLI'}
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
    def __init__(self, sas_token=None, token_info=None, tenant_id=None):
        self.sas_token = sas_token
        self.token_info = token_info
        self.tenant_id = tenant_id


def login_auth_for_azcopy(cmd):
    raw_token = Profile(cli_ctx=cmd.cli_ctx).get_raw_token(resource=STORAGE_RESOURCE_ENDPOINT)
    token_info = raw_token[0][2]
    try:
        token_info = _unserialize_non_msi_token_payload(token_info)
    except KeyError:  # unserialized MSI token payload
        # if msi token, only get the tenant_id, AzCopy will get the account token from AzCLI directly
        tenant_id = raw_token[2]
        return AzCopyCredentials(tenant_id=tenant_id)
    return AzCopyCredentials(token_info=token_info)


def client_auth_for_azcopy(cmd, client):
    # prefer oauth mode, if account-key is not provided
    is_oauth = True
    credential = client.credential
    if credential:
        if isinstance(credential, dict) and "account_key" in credential:
            is_oauth = False
        elif hasattr(credential, "account_key"):
            is_oauth = False
        elif isinstance(credential, str):
            sas_indicators = ["sig=", "sv=", "sr=", "se=", "sp="]
            for indicator in sas_indicators:
                if indicator in credential:
                    is_oauth = False
                    break

    if is_oauth:
        raw_token = Profile(cli_ctx=cmd.cli_ctx).get_raw_token(resource=STORAGE_RESOURCE_ENDPOINT)
        token_info = raw_token[0][2]
        try:
            token_info = _unserialize_non_msi_token_payload(token_info)
        except KeyError:  # unserialized token payload
            # if msi token, only get the tenant_id, AzCopy will get the account token from AzCLI directly
            tenant_id = raw_token[2]
            return AzCopyCredentials(tenant_id=tenant_id)
        return AzCopyCredentials(token_info=token_info)

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
    kwargs = {
        'account_name': account_name,
        'account_key': account_key,
        'resource_types': resource_types,
        'permission': permissions
    }
    from ..util import create_short_lived_blob_service_sas_track2, create_short_lived_file_service_sas_track2
    if service == 'blob':
        sas_token = create_short_lived_blob_service_sas_track2(cmd, **kwargs)
    elif service == 'file':
        sas_token = create_short_lived_file_service_sas_track2(cmd, **kwargs)
    return sas_token


def _get_default_install_location():
    system = platform.system()
    _config_dir = get_config_dir()
    _azcopy_installation_dir = os.path.join(_config_dir, "bin")
    if system == 'Windows':
        install_location = os.path.join(_azcopy_installation_dir, 'azcopy.exe')
    elif system in ('Linux', 'Darwin'):
        install_location = os.path.join(_azcopy_installation_dir, 'azcopy')
    else:
        raise CLIError('The {} platform is not currently supported. If you want to know which platforms are supported, '
                       'please refer to the document for supported platforms: '
                       'https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10#download-azcopy'
                       .format(system))
    return install_location


def _urlretrieve(url, install_location):
    import io
    logger.warning('Downloading AzCopy from %s', url)
    req = urlopen(url)
    compressedFile = io.BytesIO(req.read())
    if url.endswith('zip'):
        zip_file = zipfile.ZipFile(compressedFile)
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


def _verify_url(url):
    from urllib.error import HTTPError, URLError
    try:
        response = urlopen(url)
        if response.code == 200:
            return response.url
        return None
    except (HTTPError, URLError):
        logger.warning('There is an error downloading from the url: %s', url)
        return None
