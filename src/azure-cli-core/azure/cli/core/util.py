# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
import json
import getpass
import base64
import binascii
import platform
import ssl
import six
import re
import logging

from six.moves.urllib.request import urlopen  # pylint: disable=import-error
from knack.log import get_logger
from knack.util import CLIError, to_snake_case
from azure.common import AzureException

logger = get_logger(__name__)

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

SSLERROR_TEMPLATE = ('Certificate verification failed. This typically happens when using Azure CLI behind a proxy '
                     'that intercepts traffic with a self-signed certificate. '
                     # pylint: disable=line-too-long
                     'Please add this certificate to the trusted CA bundle: https://github.com/Azure/azure-cli/blob/dev/doc/use_cli_effectively.md#working-behind-a-proxy. '
                     'Error detail: {}')

_PROXYID_RE = re.compile(
    '(?i)/subscriptions/(?P<subscription>[^/]*)(/resourceGroups/(?P<resource_group>[^/]*))?'
    '(/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)(?P<children>.*))?')

_CHILDREN_RE = re.compile('(?i)/(?P<child_type>[^/]*)/(?P<child_name>[^/]*)')


def handle_exception(ex):  # pylint: disable=too-many-return-statements
    # For error code, follow guidelines at https://docs.python.org/2/library/sys.html#sys.exit,
    from jmespath.exceptions import JMESPathTypeError
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import HttpOperationError, ValidationError, ClientRequestError
    from azure.cli.core.azlogging import CommandLoggerContext

    with CommandLoggerContext(logger):
        if isinstance(ex, JMESPathTypeError):
            logger.error("\nInvalid jmespath query supplied for `--query`:\n%s", ex)
            logger.error("To learn more about --query, please visit: "
                         "https://docs.microsoft.com/cli/azure/query-azure-cli?view=azure-cli-latest")
            return 1
        if isinstance(ex, (CLIError, CloudError, AzureException)):
            logger.error(ex.args[0])
            return ex.args[1] if len(ex.args) >= 2 else 1
        if isinstance(ex, ValidationError):
            logger.error('validation error: %s', ex)
            return 1
        if isinstance(ex, ClientRequestError):
            msg = str(ex)
            if 'SSLError' in msg:
                logger.error("request failed: %s", SSLERROR_TEMPLATE.format(msg))
            else:
                logger.error("request failed: %s", ex)
            return 1
        if isinstance(ex, KeyboardInterrupt):
            return 1
        if isinstance(ex, HttpOperationError):
            try:
                response_dict = json.loads(ex.response.text)
                error = response_dict['error']

                # ARM should use ODATA v4. So should try this first.
                # http://docs.oasis-open.org/odata/odata-json-format/v4.0/os/odata-json-format-v4.0-os.html#_Toc372793091
                if isinstance(error, dict):
                    code = "{} - ".format(error.get('code', 'Unknown Code'))
                    message = error.get('message', ex)
                    logger.error("%s%s", code, message)
                else:
                    logger.error(error)

            except (ValueError, KeyError):
                logger.error(ex)
            return 1

        logger.error("The command failed with an unexpected error. Here is the traceback:\n")
        logger.exception(ex)
        logger.warning("\nTo open an issue, please run: 'az feedback'")

        return 1


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
    from pkg_resources import working_set
    return [d for d in list(working_set) if d.key == CLI_PACKAGE_NAME or d.key.startswith(COMPONENT_PREFIX)]


def _update_latest_from_pypi(versions):
    from subprocess import check_output, STDOUT, CalledProcessError

    success = False

    if not check_connectivity(max_retries=0):
        return versions, success

    try:
        cmd = [sys.executable] + \
            '-m pip search azure-cli -vv --disable-pip-version-check --no-cache-dir --retries 0'.split()
        logger.debug('Running: %s', cmd)
        log_output = check_output(cmd, stderr=STDOUT, universal_newlines=True)
        success = True
        for line in log_output.splitlines():
            if not line.startswith(CLI_PACKAGE_NAME):
                continue
            comps = line.split()
            mod = comps[0].replace(COMPONENT_PREFIX, '') or CLI_PACKAGE_NAME
            version = comps[1].replace('(', '').replace(')', '')
            try:
                versions[mod]['pypi'] = version
            except KeyError:
                pass
    except CalledProcessError:
        pass
    return versions, success


def get_az_version_string():
    from azure.cli.core.extension import get_extensions, EXTENSIONS_DIR, DEV_EXTENSION_SOURCES

    output = six.StringIO()
    versions = {}

    # get locally installed versions
    for dist in get_installed_cli_distributions():
        if dist.key == CLI_PACKAGE_NAME:
            versions[CLI_PACKAGE_NAME] = {'local': dist.version}
        elif dist.key.startswith(COMPONENT_PREFIX):
            comp_name = dist.key.replace(COMPONENT_PREFIX, '')
            versions[comp_name] = {'local': dist.version}

    # get the versions from pypi
    versions, success = _update_latest_from_pypi(versions)
    updates_available = 0

    def _print(val=''):
        print(val, file=output)

    def _get_version_string(name, version_dict):
        from distutils.version import LooseVersion  # pylint: disable=import-error,no-name-in-module
        local = version_dict['local']
        pypi = version_dict.get('pypi', None)
        if pypi and LooseVersion(pypi) > LooseVersion(local):
            return name.ljust(25) + local.rjust(15) + ' *'
        return name.ljust(25) + local.rjust(15)

    ver_string = _get_version_string(CLI_PACKAGE_NAME, versions.pop(CLI_PACKAGE_NAME))
    if '*' in ver_string:
        updates_available += 1
    _print(ver_string)
    _print()
    for name in sorted(versions.keys()):
        ver_string = _get_version_string(name, versions.pop(name))
        if '*' in ver_string:
            updates_available += 1
        _print(ver_string)
    _print()
    extensions = get_extensions()
    if extensions:
        _print('Extensions:')
        for ext in extensions:
            if ext.ext_type == 'dev':
                _print(ext.name.ljust(20) + ext.version.rjust(20) + ' (dev) ' + ext.path)
            else:
                _print(ext.name.ljust(20) + (ext.version or 'Unknown').rjust(20))
        _print()
    _print("Python location '{}'".format(sys.executable))
    _print("Extensions directory '{}'".format(EXTENSIONS_DIR))
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
        updates_available = -1
    return version_string, updates_available


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


def shell_safe_json_parse(json_or_dict_string, preserve_order=False):
    """ Allows the passing of JSON or Python dictionary strings. This is needed because certain
    JSON strings in CMD shell are not received in main's argv. This allows the user to specify
    the alternative notation, which does not have this problem (but is technically not JSON). """
    try:
        if not preserve_order:
            return json.loads(json_or_dict_string)
        from collections import OrderedDict
        return json.loads(json_or_dict_string, object_pairs_hook=OrderedDict)
    except ValueError as json_ex:
        try:
            import ast
            return ast.literal_eval(json_or_dict_string)
        except SyntaxError:
            raise CLIError(json_ex)
        except ValueError as ex:
            logger.debug(ex)  # log the exception which could be a python dict parsing error.
            raise CLIError(json_ex)  # raise json_ex error which is more readable and likely.


def b64encode(s):
    """
    Encodes a string to base64 on 2.x and 3.x
    :param str s: latin_1 encoded string
    :return: base64 encoded string
    :rtype: str
    """
    encoded = base64.b64encode(six.b(s))
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
    import os
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


DISABLE_VERIFY_VARIABLE_NAME = "AZURE_CLI_DISABLE_CONNECTION_VERIFICATION"


def should_disable_connection_verify():
    import os
    return bool(os.environ.get(DISABLE_VERIFY_VARIABLE_NAME))


def poller_classes():
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.polling.poller import LROPoller
    return (AzureOperationPoller, LROPoller)


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


def sdk_no_wait(no_wait, func, *args, **kwargs):
    if no_wait:
        kwargs.update({'raw': True, 'polling': False})
    return func(*args, **kwargs)


def open_page_in_browser(url):
    import subprocess
    import webbrowser
    platform_name, _ = _get_platform_info()

    if is_wsl():   # windows 10 linux subsystem
        try:
            return subprocess.call(['cmd.exe', '/c', "start {}".format(url.replace('&', '^&'))])
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
    # python 2, `platform.uname()` returns: tuple(system, node, release, version, machine, processor)
    platform_name = getattr(uname, 'system', None) or uname[0]
    release = getattr(uname, 'release', None) or uname[2]
    return platform_name.lower(), release.lower()


def is_wsl():
    platform_name, release = _get_platform_info()
    return platform_name == 'linux' and release.split('-')[-1] == 'microsoft'


def is_windows():
    platform_name, _ = _get_platform_info()
    return platform_name == 'windows'


def can_launch_browser():
    import os
    import webbrowser
    platform_name, _ = _get_platform_info()
    if is_wsl() or platform_name != 'linux':
        return True
    # per https://unix.stackexchange.com/questions/46305/is-there-a-way-to-retrieve-the-name-of-the-desktop-environment
    # and https://unix.stackexchange.com/questions/193827/what-is-display-0
    # we can check a few env vars
    gui_env_vars = ['DESKTOP_SESSION', 'XDG_CURRENT_DESKTOP', 'DISPLAY']
    result = True
    if platform_name == 'linux':
        if any(os.getenv(v) for v in gui_env_vars):
            try:
                default_browser = webbrowser.get()
                if getattr(default_browser, 'name', None) == 'www-browser':  # text browser won't work
                    result = False
            except webbrowser.Error:
                result = False
        else:
            result = False

    return result


def get_command_type_kwarg(custom_command=False):
    return 'custom_command_type' if custom_command else 'command_type'


def reload_module(module):
    # reloading the imported module to update
    try:
        from importlib import reload
    except ImportError:
        pass  # for python 2
    reload(sys.modules[module])


def get_default_admin_username():
    try:
        return getpass.getuser()
    except KeyError:
        return None


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


def check_connectivity(url='https://example.org', max_retries=5, timeout=1):
    import requests
    import timeit
    start = timeit.default_timer()
    success = None
    try:
        s = requests.Session()
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


def send_raw_request(cli_ctx, method, uri, headers=None, uri_parameters=None,  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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
    agents = [get_az_user_agent()]

    # Borrow AZURE_HTTP_USER_AGENT from msrest
    # https://github.com/Azure/msrest-for-python/blob/4cc8bc84e96036f03b34716466230fb257e27b36/msrest/pipeline/universal.py#L70
    _ENV_ADDITIONAL_USER_AGENT = 'AZURE_HTTP_USER_AGENT'
    import os
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

    # If uri is an ARM resource ID, like /subscriptions/xxx/resourcegroups/xxx?api-version=2019-07-01,
    # default to Azure Resource Manager.
    # https://management.azure.com/ + subscriptions/xxx/resourcegroups/xxx?api-version=2019-07-01
    if '://' not in uri:
        uri = cli_ctx.cloud.endpoints.resource_manager + uri.lstrip('/')

    # Replace common tokens with real values. It is for smooth experience if users copy and paste the url from
    # Azure Rest API doc
    from azure.cli.core._profile import Profile
    profile = Profile()
    if '{subscriptionId}' in uri:
        uri = uri.replace('{subscriptionId}', profile.get_subscription_id())

    if not skip_authorization_header and uri.lower().startswith('https://'):
        if not resource:
            endpoints = cli_ctx.cloud.endpoints
            # If uri starts with ARM endpoint, like https://management.azure.com/,
            # use active_directory_resource_id for resource.
            # This follows the same behavior as azure.cli.core.commands.client_factory._get_mgmt_service_client
            if uri.lower().startswith(endpoints.resource_manager.rstrip('/')):
                resource = endpoints.active_directory_resource_id
            else:
                from azure.cli.core.cloud import CloudEndpointNotSetException
                for p in [x for x in dir(endpoints) if not x.startswith('_')]:
                    try:
                        value = getattr(endpoints, p)
                    except CloudEndpointNotSetException:
                        continue
                    if isinstance(value, six.string_types) and uri.lower().startswith(value.lower()):
                        resource = value
                        break
        if resource:
            token_info, _, _ = profile.get_raw_token(resource)
            logger.debug('Retrievd AAD token for resource: %s', resource or 'ARM')
            token_type, token, _ = token_info
            headers = headers or {}
            headers['Authorization'] = '{} {}'.format(token_type, token)
        else:
            logger.warning("Can't derive appropriate Azure AD resource from --url to acquire an access token. "
                           "If access token is required, use --resource to specify the resource")
    try:
        # https://requests.readthedocs.io/en/latest/user/advanced/#prepared-requests
        s = Session()
        req = Request(method=method, url=uri, headers=headers, params=uri_parameters, data=body)
        prepped = s.prepare_request(req)

        # Merge environment settings into session
        settings = s.merge_environment_settings(prepped.url, {}, None, not should_disable_connection_verify(), None)
        _log_request(prepped)
        r = s.send(prepped, **settings)
        _log_response(r)
    except Exception as ex:  # pylint: disable=broad-except
        raise CLIError(ex)

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


class ConfiguredDefaultSetter(object):

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

    import os
    from azure.cli.core._environment import _ENV_AZ_INSTALLER
    if _ENV_AZ_INSTALLER in os.environ:
        agents.append('({})'.format(os.environ[_ENV_AZ_INSTALLER]))

    # msrest already has this
    # https://github.com/Azure/msrest-for-python/blob/4cc8bc84e96036f03b34716466230fb257e27b36/msrest/pipeline/universal.py#L70
    # if ENV_ADDITIONAL_USER_AGENT in os.environ:
    #     agents.append(os.environ[ENV_ADDITIONAL_USER_AGENT])

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
