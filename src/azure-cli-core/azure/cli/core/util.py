# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-lines

import base64
import binascii
import getpass
import json
import logging
import os
import platform
import re
import ssl
import sys
from urllib.request import urlopen

from knack.log import get_logger
from knack.util import CLIError, to_snake_case

logger = get_logger(__name__)

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

SSLERROR_TEMPLATE = ('Certificate verification failed. This typically happens when using Azure CLI behind a proxy '
                     'that intercepts traffic with a self-signed certificate. '
                     # pylint: disable=line-too-long
                     'Please add this certificate to the trusted CA bundle. More info: https://docs.microsoft.com/cli/azure/use-cli-effectively#work-behind-a-proxy.')

QUERY_REFERENCE = ("To learn more about --query, please visit: "
                   "'https://docs.microsoft.com/cli/azure/query-azure-cli'")


_PROXYID_RE = re.compile(
    '(?i)/subscriptions/(?P<subscription>[^/]*)(/resourceGroups/(?P<resource_group>[^/]*))?'
    '(/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)(?P<children>.*))?')

_CHILDREN_RE = re.compile('(?i)/(?P<child_type>[^/]*)/(?P<child_name>[^/]*)')

_VERSION_CHECK_TIME = 'check_time'
_VERSION_UPDATE_TIME = 'update_time'

# A list of reserved names that cannot be used as admin username of VM
DISALLOWED_USER_NAMES = [
    "administrator", "admin", "user", "user1", "test", "user2",
    "test1", "user3", "admin1", "1", "123", "a", "actuser", "adm",
    "admin2", "aspnet", "backup", "console", "guest",
    "owner", "root", "server", "sql", "support", "support_388945a0",
    "sys", "test2", "test3", "user4", "user5"
]


def handle_exception(ex):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
    # For error code, follow guidelines at https://docs.python.org/2/library/sys.html#sys.exit,
    from jmespath.exceptions import JMESPathError
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import HttpOperationError, ValidationError, ClientRequestError
    from azure.common import AzureException
    from azure.core.exceptions import AzureError
    from requests.exceptions import SSLError, HTTPError
    from azure.cli.core import azclierror
    from msal_extensions.persistence import PersistenceError
    import traceback

    logger.debug("azure.cli.core.util.handle_exception is called with an exception:")
    # Print the traceback and exception message
    logger.debug(traceback.format_exc())

    error_msg = getattr(ex, 'message', str(ex))
    exit_code = 1

    if isinstance(ex, azclierror.AzCLIError):
        az_error = ex

    elif isinstance(ex, JMESPathError):
        error_msg = "Invalid jmespath query supplied for `--query`: {}".format(error_msg)
        az_error = azclierror.InvalidArgumentValueError(error_msg)
        az_error.set_recommendation(QUERY_REFERENCE)

    elif isinstance(ex, SSLError):
        az_error = azclierror.AzureConnectionError(error_msg)
        az_error.set_recommendation(SSLERROR_TEMPLATE)

    elif isinstance(ex, CloudError):
        if extract_common_error_message(ex):
            error_msg = extract_common_error_message(ex)
        status_code = str(getattr(ex, 'status_code', 'Unknown Code'))
        AzCLIErrorType = get_error_type_by_status_code(status_code)
        az_error = AzCLIErrorType(error_msg)

    elif isinstance(ex, ValidationError):
        az_error = azclierror.ValidationError(error_msg)

    elif isinstance(ex, CLIError):
        # TODO: Fine-grained analysis here
        az_error = azclierror.UnclassifiedUserFault(error_msg)

    elif isinstance(ex, AzureError):
        if extract_common_error_message(ex):
            error_msg = extract_common_error_message(ex)
        AzCLIErrorType = get_error_type_by_azure_error(ex)
        az_error = AzCLIErrorType(error_msg)

    elif isinstance(ex, AzureException):
        if is_azure_connection_error(error_msg):
            az_error = azclierror.AzureConnectionError(error_msg)
        else:
            # TODO: Fine-grained analysis here for Unknown error
            az_error = azclierror.UnknownError(error_msg)

    elif isinstance(ex, ClientRequestError):
        if is_azure_connection_error(error_msg):
            az_error = azclierror.AzureConnectionError(error_msg)
        elif isinstance(ex.inner_exception, SSLError):
            # When msrest encounters SSLError, msrest wraps SSLError in ClientRequestError
            az_error = azclierror.AzureConnectionError(error_msg)
            az_error.set_recommendation(SSLERROR_TEMPLATE)
        else:
            az_error = azclierror.ClientRequestError(error_msg)

    elif isinstance(ex, HttpOperationError):
        message, _ = extract_http_operation_error(ex)
        if message:
            error_msg = message
        status_code = str(getattr(ex.response, 'status_code', 'Unknown Code'))
        AzCLIErrorType = get_error_type_by_status_code(status_code)
        az_error = AzCLIErrorType(error_msg)

    elif isinstance(ex, HTTPError):
        status_code = str(getattr(ex.response, 'status_code', 'Unknown Code'))
        AzCLIErrorType = get_error_type_by_status_code(status_code)
        az_error = AzCLIErrorType(error_msg)

    elif isinstance(ex, KeyboardInterrupt):
        error_msg = 'Keyboard interrupt is captured.'
        az_error = azclierror.ManualInterrupt(error_msg)

    elif isinstance(ex, PersistenceError):
        # errno is already in strerror. str(ex) gives duplicated errno.
        az_error = azclierror.CLIInternalError(ex.strerror)
        if ex.errno == 0:
            az_error.set_recommendation(
                "Please report to us via Github: https://github.com/Azure/azure-cli/issues/20278")
        elif ex.errno == -2146893813:
            az_error.set_recommendation(
                "Please report to us via Github: https://github.com/Azure/azure-cli/issues/20231")
        elif ex.errno == -2146892987:
            az_error.set_recommendation(
                "Please report to us via Github: https://github.com/Azure/azure-cli/issues/21010")

    else:
        error_msg = "The command failed with an unexpected error. Here is the traceback:"
        az_error = azclierror.CLIInternalError(error_msg)
        az_error.set_exception_trace(ex)
        az_error.set_recommendation("To open an issue, please run: 'az feedback'")

    if isinstance(az_error, azclierror.ResourceNotFoundError):
        exit_code = 3

    az_error.print_error()
    az_error.send_telemetry()

    return exit_code


def extract_common_error_message(ex):
    error_msg = None
    try:
        error_msg = ex.args[0]
        for detail in ex.args[0].error.details:
            error_msg += ('\n' + detail)
    except Exception:  # pylint: disable=broad-except
        pass
    return error_msg


def extract_http_operation_error(ex):
    error_msg = None
    status_code = 'Unknown Code'
    try:
        response = json.loads(ex.response.text)
        if isinstance(response, str):
            error = response
        else:
            error = response.get('error', response.get('Error', None))
        # ARM should use ODATA v4. So should try this first.
        # http://docs.oasis-open.org/odata/odata-json-format/v4.0/os/odata-json-format-v4.0-os.html#_Toc372793091
        if isinstance(error, dict):
            status_code = error.get('code', error.get('Code', 'Unknown Code'))
            message = error.get('message', error.get('Message', ex))
            error_msg = "{}: {}".format(status_code, message)
        else:
            error_msg = error
    except (ValueError, KeyError):
        pass
    return error_msg, status_code


def get_error_type_by_azure_error(ex):
    from azure.core import exceptions
    from azure.cli.core import azclierror

    if isinstance(ex, exceptions.HttpResponseError):
        status_code = str(ex.status_code)
        return get_error_type_by_status_code(status_code)
    if isinstance(ex, exceptions.ResourceNotFoundError):
        return azclierror.ResourceNotFoundError
    if isinstance(ex, exceptions.ServiceRequestError):
        return azclierror.ClientRequestError
    if isinstance(ex, exceptions.ServiceRequestTimeoutError):
        return azclierror.AzureConnectionError
    if isinstance(ex, (exceptions.ServiceResponseError, exceptions.ServiceResponseTimeoutError)):
        return azclierror.AzureResponseError

    return azclierror.UnknownError


# pylint: disable=too-many-return-statements
def get_error_type_by_status_code(status_code):
    from azure.cli.core import azclierror

    if status_code == '400':
        return azclierror.BadRequestError
    if status_code == '401':
        return azclierror.UnauthorizedError
    if status_code == '403':
        return azclierror.ForbiddenError
    if status_code == '404':
        return azclierror.ResourceNotFoundError
    if status_code.startswith('4'):
        return azclierror.UnclassifiedUserFault
    if status_code.startswith('5'):
        return azclierror.AzureInternalError

    return azclierror.UnknownError


def is_azure_connection_error(error_msg):
    error_msg = error_msg.lower()
    if 'connection error' in error_msg \
            or 'connection broken' in error_msg \
            or 'connection aborted' in error_msg:
        return True
    return False


# pylint: disable=inconsistent-return-statements
def empty_on_404(ex):
    from msrestazure.azure_exceptions import CloudError
    if isinstance(ex, CloudError) and ex.status_code == 404:
        return None
    raise ex


def truncate_text(str_to_shorten, width=70, placeholder=' [...]'):
    if width <= 0:
        raise ValueError('width must be greater than 0.')
    s_len = width - len(placeholder)
    return str_to_shorten[:s_len] + (str_to_shorten[s_len:] and placeholder)


def get_installed_cli_distributions():
    # Stop importing pkg_resources, because importing it is slow (~200ms).
    # from pkg_resources import working_set
    # return [d for d in list(working_set) if d.key == CLI_PACKAGE_NAME or d.key.startswith(COMPONENT_PREFIX)]

    # Use the hard-coded version instead of querying all modules under site-packages.
    from azure.cli.core import __version__ as azure_cli_core_version
    from azure.cli.telemetry import __version__ as azure_cli_telemetry_version

    class VersionItem:  # pylint: disable=too-few-public-methods
        """A mock of pkg_resources.EggInfoDistribution to maintain backward compatibility."""
        def __init__(self, key, version):
            self.key = key
            self.version = version

    return [
        VersionItem('azure-cli', azure_cli_core_version),
        VersionItem('azure-cli-core', azure_cli_core_version),
        VersionItem('azure-cli-telemetry', azure_cli_telemetry_version)
    ]


def get_latest_from_github(package_path='azure-cli'):
    try:
        import requests
        git_url = "https://raw.githubusercontent.com/Azure/azure-cli/main/src/{}/setup.py".format(package_path)
        response = requests.get(git_url, timeout=10)
        if response.status_code != 200:
            logger.info("Failed to fetch the latest version from '%s' with status code '%s' and reason '%s'",
                        git_url, response.status_code, response.reason)
            return None
        for line in response.iter_lines():
            txt = line.decode('utf-8', errors='ignore')
            if txt.startswith('VERSION'):
                match = re.search(r'VERSION = \"(.*)\"$', txt)
                if match:
                    return match.group(1)
    except Exception as ex:  # pylint: disable=broad-except
        logger.info("Failed to get the latest version from '%s'. %s", git_url, str(ex))
        return None


def _update_latest_from_github(versions):
    if not check_connectivity(max_retries=0):
        return versions, False
    success = True
    for pkg in ['azure-cli-core', 'azure-cli-telemetry']:
        version = get_latest_from_github(pkg)
        if not version:
            success = False
        else:
            versions[pkg.replace(COMPONENT_PREFIX, '')]['pypi'] = version
    try:
        versions[CLI_PACKAGE_NAME]['pypi'] = versions['core']['pypi']
    except KeyError:
        pass
    return versions, success


def get_cached_latest_versions(versions=None):
    """ Get the latest versions from a cached file"""
    import datetime
    from azure.cli.core._session import VERSIONS

    if not versions:
        versions = _get_local_versions()

    if VERSIONS[_VERSION_UPDATE_TIME]:
        version_update_time = datetime.datetime.strptime(VERSIONS[_VERSION_UPDATE_TIME], '%Y-%m-%d %H:%M:%S.%f')
        if datetime.datetime.now() < version_update_time + datetime.timedelta(days=1):
            cache_versions = VERSIONS['versions']
            if cache_versions and cache_versions['azure-cli']['local'] == versions['azure-cli']['local']:
                return cache_versions.copy(), True

    versions, success = _update_latest_from_github(versions)
    VERSIONS['versions'] = versions
    VERSIONS[_VERSION_UPDATE_TIME] = str(datetime.datetime.now())
    return versions.copy(), success


def _get_local_versions():
    # get locally installed versions
    versions = {}
    for dist in get_installed_cli_distributions():
        if dist.key == CLI_PACKAGE_NAME:
            versions[CLI_PACKAGE_NAME] = {'local': dist.version}
        elif dist.key.startswith(COMPONENT_PREFIX):
            comp_name = dist.key.replace(COMPONENT_PREFIX, '')
            versions[comp_name] = {'local': dist.version}
    return versions


def get_az_version_string(use_cache=False):  # pylint: disable=too-many-statements
    from azure.cli.core.extension import get_extensions, EXTENSIONS_DIR, DEV_EXTENSION_SOURCES, EXTENSIONS_SYS_DIR
    import io
    output = io.StringIO()
    versions = _get_local_versions()

    # get the versions from pypi
    versions, success = get_cached_latest_versions(versions) if use_cache else _update_latest_from_github(versions)
    updates_available_components = []

    def _print(val=''):
        print(val, file=output)

    def _get_version_string(name, version_dict):
        from packaging.version import parse  # pylint: disable=import-error,no-name-in-module
        local = version_dict['local']
        pypi = version_dict.get('pypi', None)
        if pypi and parse(pypi) > parse(local):
            return name.ljust(25) + local.rjust(15) + ' *'
        return name.ljust(25) + local.rjust(15)

    ver_string = _get_version_string(CLI_PACKAGE_NAME, versions.pop(CLI_PACKAGE_NAME))
    if '*' in ver_string:
        updates_available_components.append(CLI_PACKAGE_NAME)
    _print(ver_string)
    _print()
    for name in sorted(versions.keys()):
        ver_string = _get_version_string(name, versions.pop(name))
        if '*' in ver_string:
            updates_available_components.append(name)
        _print(ver_string)
    _print()
    extensions = get_extensions()
    if extensions:
        _print('Extensions:')
        for ext in extensions:
            if ext.ext_type == 'dev':
                _print(ext.name.ljust(20) + (ext.version or 'Unknown').rjust(20) + ' (dev) ' + ext.path)
            else:
                _print(ext.name.ljust(20) + (ext.version or 'Unknown').rjust(20))
        _print()

    _print('Dependencies:')
    dependencies_versions = get_dependency_versions()
    for k, v in dependencies_versions.items():
        _print(k.ljust(20) + v.rjust(20))
    _print()

    _print("Python location '{}'".format(os.path.abspath(sys.executable)))
    _print("Extensions directory '{}'".format(EXTENSIONS_DIR))
    if os.path.isdir(EXTENSIONS_SYS_DIR) and os.listdir(EXTENSIONS_SYS_DIR):
        _print("Extensions system directory '{}'".format(EXTENSIONS_SYS_DIR))
    if DEV_EXTENSION_SOURCES:
        _print("Development extension sources:")
        for source in DEV_EXTENSION_SOURCES:
            _print('    {}'.format(source))
    _print()
    _print('Python ({}) {}'.format(platform.system(), sys.version))
    _print()
    _print('Legal docs and information: aka.ms/AzureCliLegal')
    _print()
    version_string = output.getvalue()

    # if unable to query PyPI, use sentinel value to flag that
    # we couldn't check for updates
    if not success:
        updates_available_components = None
    return version_string, updates_available_components


def get_az_version_json():
    from azure.cli.core.extension import get_extensions
    versions = {'extensions': {}}

    for dist in get_installed_cli_distributions():
        versions[dist.key] = dist.version
    extensions = get_extensions()
    if extensions:
        for ext in extensions:
            versions['extensions'][ext.name] = ext.version or 'Unknown'
    return versions


def get_dependency_versions():
    versions = {}
    # Add msal version
    try:
        from msal import __version__ as msal_version
    except ImportError:
        msal_version = "N/A"
    versions['msal'] = msal_version

    # Add azure-mgmt-resource version
    try:
        # Track 2 >=15.0.0
        # pylint: disable=protected-access
        from azure.mgmt.resource._version import VERSION as azure_mgmt_resource_version
    except ImportError:
        try:
            # Track 1 <=13.0.0
            from azure.mgmt.resource.version import VERSION as azure_mgmt_resource_version
        except ImportError:
            azure_mgmt_resource_version = "N/A"
    versions['azure-mgmt-resource'] = azure_mgmt_resource_version

    return versions


def show_updates_available(new_line_before=False, new_line_after=False):
    from azure.cli.core._session import VERSIONS
    import datetime

    if VERSIONS[_VERSION_CHECK_TIME]:
        version_check_time = datetime.datetime.strptime(VERSIONS[_VERSION_CHECK_TIME], '%Y-%m-%d %H:%M:%S.%f')
        if datetime.datetime.now() < version_check_time + datetime.timedelta(days=7):
            return

    _, updates_available_components = get_az_version_string(use_cache=True)
    if updates_available_components:
        if new_line_before:
            logger.warning("")
        show_updates(updates_available_components, only_show_when_updates_available=True)
        if new_line_after:
            logger.warning("")
    VERSIONS[_VERSION_CHECK_TIME] = str(datetime.datetime.now())


def show_updates(updates_available_components, only_show_when_updates_available=False):
    if updates_available_components is None:
        if not only_show_when_updates_available:
            logger.warning('Unable to check if your CLI is up-to-date. Check your internet connection.')
    elif updates_available_components:  # pylint: disable=too-many-nested-blocks
        if in_cloud_console():
            warning_msg = 'You have %i updates available. They will be updated with the next build of Cloud Shell.'
        else:
            warning_msg = "You have %i updates available."
            if CLI_PACKAGE_NAME in updates_available_components:
                warning_msg = "{} Consider updating your CLI installation with 'az upgrade'".format(warning_msg)
        logger.warning(warning_msg, len(updates_available_components))
    elif not only_show_when_updates_available:
        print('Your CLI is up-to-date.')


def get_json_object(json_string):
    """ Loads a JSON string as an object and converts all keys to snake case """

    def _convert_to_snake_case(item):
        if isinstance(item, dict):
            new_item = {}
            for key, val in item.items():
                new_item[to_snake_case(key)] = _convert_to_snake_case(val)
            return new_item
        if isinstance(item, list):
            return [_convert_to_snake_case(x) for x in item]
        return item

    return _convert_to_snake_case(shell_safe_json_parse(json_string))


def get_file_json(file_path, throw_on_empty=True, preserve_order=False):
    content = read_file_content(file_path)
    if not content and not throw_on_empty:
        return None
    try:
        return shell_safe_json_parse(content, preserve_order)
    except CLIError as ex:
        raise CLIError("Failed to parse {} with exception:\n    {}".format(file_path, ex))


def read_file_content(file_path, allow_binary=False):
    from codecs import open as codecs_open
    # Note, always put 'utf-8-sig' first, so that BOM in WinOS won't cause trouble.
    for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be']:
        try:
            with codecs_open(file_path, encoding=encoding) as f:
                logger.debug("attempting to read file %s as %s", file_path, encoding)
                return f.read()
        except (UnicodeError, UnicodeDecodeError):
            pass

    if allow_binary:
        try:
            with open(file_path, 'rb') as input_file:
                logger.debug("attempting to read file %s as binary", file_path)
                return base64.b64encode(input_file.read()).decode("utf-8")
        except Exception:  # pylint: disable=broad-except
            pass
    raise CLIError('Failed to decode file {} - unknown decoding'.format(file_path))


def shell_safe_json_parse(json_or_dict_string, preserve_order=False, strict=True):
    """ Allows the passing of JSON or Python dictionary strings. This is needed because certain
    JSON strings in CMD shell are not received in main's argv. This allows the user to specify
    the alternative notation, which does not have this problem (but is technically not JSON). """
    try:
        if not preserve_order:
            return json.loads(json_or_dict_string, strict=strict)
        from collections import OrderedDict
        return json.loads(json_or_dict_string, object_pairs_hook=OrderedDict, strict=strict)
    except ValueError as json_ex:
        try:
            import ast
            return ast.literal_eval(json_or_dict_string)
        except Exception as ex:
            logger.debug(ex)  # log the exception which could be a python dict parsing error.

            # Echo the JSON received by CLI
            msg = "Failed to parse JSON: {}\nError detail: {}".format(json_or_dict_string, json_ex)

            # Recommendation for all shells
            from azure.cli.core.azclierror import InvalidArgumentValueError
            recommendation = "The JSON may have been parsed by the shell. See " \
                             "https://docs.microsoft.com/cli/azure/use-cli-effectively#use-quotation-marks-in-arguments"

            # Recommendation especially for PowerShell
            parent_proc = get_parent_proc_name()
            if parent_proc and parent_proc.lower() in ("powershell.exe", "pwsh.exe"):
                recommendation += "\nPowerShell requires additional quoting rules. See " \
                                  "https://github.com/Azure/azure-cli/blob/dev/doc/quoting-issues-with-powershell.md"

            # Raise from json_ex error which is more likely to be the original error
            raise InvalidArgumentValueError(msg, recommendation=recommendation) from json_ex


def b64encode(s):
    """
    Encodes a string to base64 on 2.x and 3.x
    :param str s: latin_1 encoded string
    :return: base64 encoded string
    :rtype: str
    """
    encoded = base64.b64encode(s.encode("latin-1"))
    return encoded if encoded is str else encoded.decode('latin-1')


def b64_to_hex(s):
    """
    Decodes a string to base64 on 2.x and 3.x
    :param str s: base64 encoded string
    :return: uppercase hex string
    :rtype: str
    """
    decoded = base64.b64decode(s)
    hex_data = binascii.hexlify(decoded).upper()
    if isinstance(hex_data, bytes):
        return str(hex_data.decode("utf-8"))
    return hex_data


def random_string(length=16, force_lower=False, digits_only=False):
    from string import ascii_letters, digits, ascii_lowercase
    from random import choice
    choice_set = digits
    if not digits_only:
        choice_set += ascii_lowercase if force_lower else ascii_letters
    return ''.join([choice(choice_set) for _ in range(length)])


def hash_string(value, length=16, force_lower=False):
    """ Generate a deterministic hashed string."""
    import hashlib
    m = hashlib.sha256()
    try:
        m.update(value)
    except TypeError:
        m.update(value.encode())
    digest = m.hexdigest()
    digest = digest.lower() if force_lower else digest
    while len(digest) < length:
        digest = digest + digest
    return digest[:length]


def in_cloud_console():
    return os.environ.get('ACC_CLOUD', None)


def get_arg_list(op):
    import inspect

    try:
        # only supported in python3 - falling back to argspec if not available
        sig = inspect.signature(op)
        return sig.parameters
    except AttributeError:
        sig = inspect.getargspec(op)  # pylint: disable=deprecated-method
        return sig.args


def is_track2(client_class):
    """ IS this client a autorestv3/track2 one?.
    Could be refined later if necessary.
    """
    from inspect import getfullargspec as get_arg_spec
    args = get_arg_spec(client_class.__init__).args
    return "credential" in args


DISABLE_VERIFY_VARIABLE_NAME = "AZURE_CLI_DISABLE_CONNECTION_VERIFICATION"


def should_disable_connection_verify():
    return bool(os.environ.get(DISABLE_VERIFY_VARIABLE_NAME))


def poller_classes():
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.polling.poller import LROPoller
    from azure.core.polling import LROPoller as AzureCoreLROPoller
    return (AzureOperationPoller, LROPoller, AzureCoreLROPoller)


def augment_no_wait_handler_args(no_wait_enabled, handler, handler_args):
    """ Populates handler_args with the appropriate args for no wait """
    h_args = get_arg_list(handler)
    if 'no_wait' in h_args:
        handler_args['no_wait'] = no_wait_enabled
    if 'raw' in h_args and no_wait_enabled:
        # support autorest 2
        handler_args['raw'] = True
    if 'polling' in h_args and no_wait_enabled:
        # support autorest 3
        handler_args['polling'] = False

    # Support track2 SDK.
    # In track2 SDK, there is no parameter 'polling' in SDK, but just use '**kwargs'.
    # So we check the name of the operation to see if it's a long running operation.
    # The name of long running operation in SDK is like 'begin_xxx_xxx'.
    op_name = handler.__name__
    if op_name and op_name.startswith('begin_') and no_wait_enabled:
        handler_args['polling'] = False


def sdk_no_wait(no_wait, func, *args, **kwargs):
    if no_wait:
        kwargs.update({'polling': False})
    return func(*args, **kwargs)


def open_page_in_browser(url):
    import subprocess
    import webbrowser
    platform_name, _ = _get_platform_info()

    if is_wsl():   # windows 10 linux subsystem
        try:
            # https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe
            # Ampersand (&) should be quoted
            return subprocess.Popen(
                ['powershell.exe', '-NoProfile', '-Command', 'Start-Process "{}"'.format(url)]).wait()
        except OSError:  # WSL might be too old  # FileNotFoundError introduced in Python 3
            pass
    elif platform_name == 'darwin':
        # handle 2 things:
        # a. On OSX sierra, 'python -m webbrowser -t <url>' emits out "execution error: <url> doesn't
        #    understand the "open location" message"
        # b. Python 2.x can't sniff out the default browser
        return subprocess.Popen(['open', url])
    try:
        return webbrowser.open(url, new=2)  # 2 means: open in a new tab, if possible
    except TypeError:  # See https://bugs.python.org/msg322439
        return webbrowser.open(url, new=2)


def _get_platform_info():
    uname = platform.uname()
    return uname.system.lower(), uname.release.lower()


def is_wsl():
    platform_name, release = _get_platform_info()
    # "Official" way of detecting WSL: https://github.com/Microsoft/WSL/issues/423#issuecomment-221627364
    # Run `uname -a` to get 'release' without python
    #   - WSL 1: '4.4.0-19041-Microsoft'
    #   - WSL 2: '4.19.128-microsoft-standard'
    return platform_name == 'linux' and 'microsoft' in release


def is_windows():
    platform_name, _ = _get_platform_info()
    return platform_name == 'windows'


def can_launch_browser():
    import webbrowser
    platform_name, _ = _get_platform_info()

    if platform_name != 'linux':
        # Only Linux may have no browser
        return True

    # Using webbrowser to launch a browser is the preferred way.
    try:
        webbrowser.get()
        return True
    except webbrowser.Error:
        # Don't worry. We may still try powershell.exe.
        pass

    if is_wsl():
        # Docker container running on WSL 2 also shows WSL, but it can't launch a browser.
        # If powershell.exe is on PATH, it can be called to launch a browser.
        import shutil
        if shutil.which("powershell.exe"):
            return True

    return False


def get_command_type_kwarg(custom_command=False):
    return 'custom_command_type' if custom_command else 'command_type'


def reload_module(module):
    # reloading the imported module to update
    if module in sys.modules:
        from importlib import reload
        reload(sys.modules[module])


def get_default_admin_username():
    try:
        username = getpass.getuser()
    except KeyError:
        username = None
    if username is None or username.lower() in DISALLOWED_USER_NAMES:
        logger.warning('Default username %s is a reserved username. Use azureuser instead.', username)
        username = 'azureuser'
    return username


def _find_child(parent, *args, **kwargs):
    # tuple structure (path, key, dest)
    path = kwargs.get('path', None)
    key_path = kwargs.get('key_path', None)
    comps = zip(path.split('.'), key_path.split('.'), args)
    current = parent
    for path, key, val in comps:
        current = getattr(current, path, None)
        if current is None:
            raise CLIError("collection '{}' not found".format(path))
        match = next((x for x in current if getattr(x, key).lower() == val.lower()), None)
        if match is None:
            raise CLIError("item '{}' not found in {}".format(val, path))
        current = match
    return current


def find_child_item(parent, *args, **kwargs):
    path = kwargs.get('path', '')
    key_path = kwargs.get('key_path', '')
    if len(args) != len(path.split('.')) != len(key_path.split('.')):
        raise CLIError('command authoring error: args, path and key_path must have equal number of components.')
    return _find_child(parent, *args, path=path, key_path=key_path)


def find_child_collection(parent, *args, **kwargs):
    path = kwargs.get('path', '')
    key_path = kwargs.get('key_path', '')
    arg_len = len(args)
    key_len = len(key_path.split('.'))
    path_len = len(path.split('.'))
    if arg_len != key_len and path_len != arg_len + 1:
        raise CLIError('command authoring error: args and key_path must have equal number of components, and '
                       'path must have one extra component (the path to the collection of interest.')
    parent = _find_child(parent, *args, path=path, key_path=key_path)
    collection_path = path.split('.')[-1]
    collection = getattr(parent, collection_path, None)
    if collection is None:
        raise CLIError("collection '{}' not found".format(collection_path))
    return collection


def check_connectivity(url='https://azure.microsoft.com', max_retries=5, timeout=1):
    import requests
    import timeit
    start = timeit.default_timer()
    success = None
    try:
        with requests.Session() as s:
            s.mount(url, requests.adapters.HTTPAdapter(max_retries=max_retries))
            s.head(url, timeout=timeout)
            success = True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as ex:
        logger.info('Connectivity problem detected.')
        logger.debug(ex)
        success = False
    stop = timeit.default_timer()
    logger.debug('Connectivity check: %s sec', stop - start)
    return success


def send_raw_request(cli_ctx, method, url, headers=None, uri_parameters=None,  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
                     body=None, skip_authorization_header=False, resource=None, output_file=None,
                     generated_client_request_id_name='x-ms-client-request-id'):
    import uuid
    from requests import Session, Request
    from requests.structures import CaseInsensitiveDict

    result = CaseInsensitiveDict()
    for s in headers or []:
        try:
            temp = shell_safe_json_parse(s)
            result.update(temp)
        except CLIError:
            key, value = s.split('=', 1)
            result[key] = value
    headers = result

    # If Authorization header is already provided, don't bother with the token
    if 'Authorization' in headers:
        skip_authorization_header = True

    # Handle User-Agent
    agents = [get_az_rest_user_agent()]

    # Borrow AZURE_HTTP_USER_AGENT from msrest
    # https://github.com/Azure/msrest-for-python/blob/4cc8bc84e96036f03b34716466230fb257e27b36/msrest/pipeline/universal.py#L70
    _ENV_ADDITIONAL_USER_AGENT = 'AZURE_HTTP_USER_AGENT'
    if _ENV_ADDITIONAL_USER_AGENT in os.environ:
        agents.append(os.environ[_ENV_ADDITIONAL_USER_AGENT])

    # Custom User-Agent provided as command argument
    if 'User-Agent' in headers:
        agents.append(headers['User-Agent'])
    headers['User-Agent'] = ' '.join(agents)

    if generated_client_request_id_name:
        headers[generated_client_request_id_name] = str(uuid.uuid4())

    # try to figure out the correct content type
    if body:
        try:
            _ = shell_safe_json_parse(body)
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
        except Exception:  # pylint: disable=broad-except
            pass

    # add telemetry
    headers['CommandName'] = cli_ctx.data['command']
    if cli_ctx.data.get('safe_params'):
        headers['ParameterSetName'] = ' '.join(cli_ctx.data['safe_params'])

    result = {}
    for s in uri_parameters or []:
        try:
            temp = shell_safe_json_parse(s)
            result.update(temp)
        except CLIError:
            key, value = s.split('=', 1)
            result[key] = value
    uri_parameters = result or None

    endpoints = cli_ctx.cloud.endpoints
    # If url is an ARM resource ID, like /subscriptions/xxx/resourcegroups/xxx?api-version=2019-07-01,
    # default to Azure Resource Manager.
    # https://management.azure.com + /subscriptions/xxx/resourcegroups/xxx?api-version=2019-07-01
    if '://' not in url:
        url = endpoints.resource_manager.rstrip('/') + url

    # Replace common tokens with real values. It is for smooth experience if users copy and paste the url from
    # Azure Rest API doc
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    if '{subscriptionId}' in url:
        url = url.replace('{subscriptionId}', cli_ctx.data['subscription_id'] or profile.get_subscription_id())

    # Prepare the Bearer token for `Authorization` header
    if not skip_authorization_header and url.lower().startswith('https://'):
        # Prepare `resource` for `get_raw_token`
        if not resource:
            # If url starts with ARM endpoint, like `https://management.azure.com/`,
            # use `active_directory_resource_id` for resource, like `https://management.core.windows.net/`.
            # This follows the same behavior as `azure.cli.core.commands.client_factory._get_mgmt_service_client`
            if url.lower().startswith(endpoints.resource_manager.rstrip('/')):
                resource = endpoints.active_directory_resource_id
            else:
                from azure.cli.core.cloud import CloudEndpointNotSetException
                for p in [x for x in dir(endpoints) if not x.startswith('_')]:
                    try:
                        value = getattr(endpoints, p)
                    except CloudEndpointNotSetException:
                        continue
                    if isinstance(value, str) and url.lower().startswith(value.lower()):
                        resource = value
                        break
        if resource:
            # Prepare `subscription` for `get_raw_token`
            # If this is an ARM request, try to extract subscription ID from the URL.
            # But there are APIs which don't require subscription ID, like /subscriptions, /tenants
            # TODO: In the future when multi-tenant subscription is supported, we won't be able to uniquely identify
            #   the token from subscription anymore.
            token_subscription = None
            if url.lower().startswith(endpoints.resource_manager.rstrip('/')):
                token_subscription = _extract_subscription_id(url)
            if token_subscription:
                logger.debug('Retrieving token for resource %s, subscription %s', resource, token_subscription)
                token_info, _, _ = profile.get_raw_token(resource, subscription=token_subscription)
            else:
                logger.debug('Retrieving token for resource %s', resource)
                token_info, _, _ = profile.get_raw_token(resource)
            token_type, token, _ = token_info
            headers = headers or {}
            headers['Authorization'] = '{} {}'.format(token_type, token)
        else:
            logger.warning("Can't derive appropriate Azure AD resource from --url to acquire an access token. "
                           "If access token is required, use --resource to specify the resource")

    # https://requests.readthedocs.io/en/latest/user/advanced/#prepared-requests
    s = Session()
    req = Request(method=method, url=url, headers=headers, params=uri_parameters, data=body)
    prepped = s.prepare_request(req)

    # Merge environment settings into session
    settings = s.merge_environment_settings(prepped.url, {}, None, not should_disable_connection_verify(), None)
    _log_request(prepped)
    r = s.send(prepped, **settings)
    _log_response(r)

    if not r.ok:
        reason = r.reason
        if r.text:
            reason += '({})'.format(r.text)
        raise CLIError(reason)
    if output_file:
        with open(output_file, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
    return r


def _extract_subscription_id(url):
    """Extract the subscription ID from an ARM request URL."""
    subscription_regex = '/subscriptions/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    match = re.search(subscription_regex, url, re.IGNORECASE)
    if match:
        subscription_id = match.groups()[0]
        logger.debug('Found subscription ID %s in the URL %s', subscription_id, url)
        return subscription_id
    logger.debug('No subscription ID specified in the URL %s', url)
    return None


def _log_request(request):
    """Log a client request. Copied from msrest
    https://github.com/Azure/msrest-for-python/blob/3653d29fc44da408898b07c710290a83d196b777/msrest/http_logger.py#L39
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return

    try:
        logger.info("Request URL: %r", request.url)
        logger.info("Request method: %r", request.method)
        logger.info("Request headers:")
        for header, value in request.headers.items():
            if header.lower() == 'authorization':
                # Trim at least half of the token but keep at most 20 characters
                preserve_length = min(int(len(value) * 0.5), 20)
                value = value[:preserve_length] + '...'
            logger.info("    %r: %r", header, value)
        logger.info("Request body:")

        # We don't want to log the binary data of a file upload.
        import types
        if isinstance(request.body, types.GeneratorType):
            logger.info("File upload")
        else:
            logger.info(str(request.body))
    except Exception as err:  # pylint: disable=broad-except
        logger.info("Failed to log request: %r", err)


def _log_response(response, **kwargs):
    """Log a server response. Copied from msrest
    https://github.com/Azure/msrest-for-python/blob/3653d29fc44da408898b07c710290a83d196b777/msrest/http_logger.py#L68
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return None

    try:
        logger.info("Response status: %r", response.status_code)
        logger.info("Response headers:")
        for res_header, value in response.headers.items():
            logger.info("    %r: %r", res_header, value)

        # We don't want to log binary data if the response is a file.
        logger.info("Response content:")
        pattern = re.compile(r'attachment; ?filename=["\w.]+', re.IGNORECASE)
        header = response.headers.get('content-disposition')

        if header and pattern.match(header):
            filename = header.partition('=')[2]
            logger.info("File attachments: %s", filename)
        elif response.headers.get("content-type", "").endswith("octet-stream"):
            logger.info("Body contains binary data.")
        elif response.headers.get("content-type", "").startswith("image"):
            logger.info("Body contains image data.")
        else:
            if kwargs.get('stream', False):
                logger.info("Body is streamable")
            else:
                logger.info(response.content.decode("utf-8-sig"))
        return response
    except Exception as err:  # pylint: disable=broad-except
        logger.info("Failed to log response: %s", repr(err))
        return response


class ScopedConfig:

    def __init__(self, cli_config, use_local_config=None):
        self.use_local_config = use_local_config
        if self.use_local_config is None:
            self.use_local_config = False
        self.cli_config = cli_config
        # here we use getattr/setattr to prepare the situation that "use_local_config" might not be available
        self.original_use_local_config = getattr(cli_config, 'use_local_config', None)

    def __enter__(self):
        self.cli_config.use_local_config = self.use_local_config

    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(self.cli_config, 'use_local_config', self.original_use_local_config)


ConfiguredDefaultSetter = ScopedConfig


def _ssl_context():
    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def urlretrieve(url):
    req = urlopen(url, context=_ssl_context())
    return req.read()


def parse_proxy_resource_id(rid):
    """Parses a resource_id into its various parts.

    Return an empty dictionary, if invalid resource id.

    :param rid: The resource id being parsed
    :type rid: str
    :returns: A dictionary with with following key/value pairs (if found):

        - subscription:            Subscription id
        - resource_group:          Name of resource group
        - namespace:               Namespace for the resource provider (i.e. Microsoft.Compute)
        - type:                    Type of the root resource (i.e. virtualMachines)
        - name:                    Name of the root resource
        - child_type_{level}:      Type of the child resource of that level
        - child_name_{level}:      Name of the child resource of that level
        - last_child_num:          Level of the last child

    :rtype: dict[str,str]
    """
    if not rid:
        return {}
    match = _PROXYID_RE.match(rid)
    if match:
        result = match.groupdict()
        children = _CHILDREN_RE.finditer(result['children'] or '')
        count = None
        for count, child in enumerate(children):
            result.update({
                key + '_%d' % (count + 1): group for key, group in child.groupdict().items()})
        result['last_child_num'] = count + 1 if isinstance(count, int) else None
        result.pop('children', None)
        return {key: value for key, value in result.items() if value is not None}
    return None


def get_az_user_agent():
    # Dynamically load the core version
    from azure.cli.core import __version__ as core_version

    agents = ["AZURECLI/{}".format(core_version)]

    from azure.cli.core._environment import _ENV_AZ_INSTALLER
    if _ENV_AZ_INSTALLER in os.environ:
        agents.append('({})'.format(os.environ[_ENV_AZ_INSTALLER]))

    # msrest already has this
    # https://github.com/Azure/msrest-for-python/blob/4cc8bc84e96036f03b34716466230fb257e27b36/msrest/pipeline/universal.py#L70
    # if ENV_ADDITIONAL_USER_AGENT in os.environ:
    #     agents.append(os.environ[ENV_ADDITIONAL_USER_AGENT])

    return ' '.join(agents)


def get_az_rest_user_agent():
    """Get User-Agent for az rest calls"""

    agents = ['python/{}'.format(platform.python_version()),
              '({})'.format(platform.platform()),
              get_az_user_agent()
              ]

    return ' '.join(agents)


def user_confirmation(message, yes=False):
    if yes:
        return
    from knack.prompting import prompt_y_n, NoTTYException
    try:
        if not prompt_y_n(message):
            raise CLIError('Operation cancelled.')
    except NoTTYException:
        raise CLIError(
            'Unable to prompt for confirmation as no tty available. Use --yes.')


def get_linux_distro():
    if platform.system() != 'Linux':
        return None, None

    try:
        with open('/etc/os-release') as lines:
            tokens = [line.strip() for line in lines]
    except Exception:  # pylint: disable=broad-except
        return None, None

    release_info = {}
    for token in tokens:
        if '=' in token:
            k, v = token.split('=', 1)
            release_info[k.lower()] = v.strip('"')

    return release_info.get('name', None), release_info.get('version_id', None)


def roughly_parse_command(args):
    # Roughly parse the command part: <az vm create> --name vm1
    # Similar to knack.invocation.CommandInvoker._rudimentary_get_command, but we don't need to bother with
    # positional args
    nouns = []
    for arg in args:
        if arg and arg[0] != '-':
            nouns.append(arg)
        else:
            break
    return ' '.join(nouns).lower()


def is_guid(guid):
    import uuid
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        return False


def handle_version_update():
    """Clean up information in local files that may be invalidated
    because of a version update of Azure CLI
    """
    try:
        from azure.cli.core._session import VERSIONS
        from packaging.version import parse  # pylint: disable=import-error,no-name-in-module
        from azure.cli.core import __version__
        if not VERSIONS['versions']:
            get_cached_latest_versions()
        elif parse(VERSIONS['versions']['core']['local']) != parse(__version__):
            logger.debug("Azure CLI has been updated.")
            logger.debug("Clean up versions and refresh cloud endpoints information in local files.")
            VERSIONS['versions'] = {}
            VERSIONS['update_time'] = ''
            from azure.cli.core.cloud import refresh_known_clouds
            refresh_known_clouds()
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning(ex)


def _get_parent_proc_name():
    # Un-cached function to get parent process name.
    try:
        import psutil
    except ImportError as ex:
        logger.debug(ex)
        return None

    try:
        parent = psutil.Process(os.getpid()).parent()

        # On Windows, when CLI is run inside a virtual env, there will be 2 python.exe.
        if parent and parent.name().lower() == 'python.exe':
            parent = parent.parent()

        if parent:
            # On Windows, powershell.exe launches cmd.exe to launch python.exe.
            grandparent = parent.parent()
            if grandparent:
                grandparent_name = grandparent.name().lower()
                if grandparent_name in ("powershell.exe", "pwsh.exe"):
                    return grandparent.name()
            # if powershell.exe or pwsh.exe is not the grandparent, simply return the parent's name.
            return parent.name()
    except psutil.AccessDenied as ex:
        # Ignore due to https://github.com/giampaolo/psutil/issues/1980
        logger.debug(ex)
    return None


def get_parent_proc_name():
    # This function wraps _get_parent_proc_name, as psutil calls are time-consuming, so use a
    # function-level cache to save the result.
    # NOTE: The return value may be None if getting parent proc name fails, so always remember to
    # check it first before calling string methods like lower().
    if not hasattr(get_parent_proc_name, "return_value"):
        parent_proc_name = _get_parent_proc_name()
        setattr(get_parent_proc_name, "return_value", parent_proc_name)
    return getattr(get_parent_proc_name, "return_value")


def is_modern_terminal():
    """In addition to knack.util.is_modern_terminal, detect Cloud Shell."""
    import knack.util
    return knack.util.is_modern_terminal() or in_cloud_console()


def rmtree_with_retry(path):
    # A workaround for https://bugs.python.org/issue33240
    # Retry shutil.rmtree several times, but even if it fails after several retries, don't block the command execution.
    retry_num = 3
    import time
    while True:
        try:
            import shutil
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            # The folder has already been deleted. No further retry is needed.
            # errno: 2, winerror: 3, strerror: 'The system cannot find the path specified'
            return
        except OSError as err:
            if retry_num > 0:
                logger.warning("Failed to delete '%s': %s. Retrying ...", path, err)
                retry_num -= 1
                time.sleep(1)
            else:
                logger.warning("Failed to delete '%s': %s. You may try to delete it manually.", path, err)
                break


def get_secret_store(cli_ctx, name):
    """Create a process-concurrency-safe azure.cli.core.auth.persistence.SecretStore instance that can be used to
    save secret data.
    """
    from azure.cli.core._environment import get_config_dir
    from azure.cli.core.auth.persistence import load_secret_store
    # Save to CLI's config dir, by default ~/.azure
    location = os.path.join(get_config_dir(), name)
    # We honor the system type (Windows, Linux, or MacOS) and global config
    encrypt = should_encrypt_token_cache(cli_ctx)
    return load_secret_store(location, encrypt)


def should_encrypt_token_cache(cli_ctx):
    # Only enable encryption for Windows (for now).
    fallback = sys.platform.startswith('win32')

    # EXPERIMENTAL: Use core.encrypt_token_cache=False to turn off token cache encryption.
    # encrypt_token_cache affects both MSAL token cache and service principal entries.
    encrypt = cli_ctx.config.getboolean('core', 'encrypt_token_cache', fallback=fallback)

    return encrypt
