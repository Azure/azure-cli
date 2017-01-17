# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import getpass
import hashlib
import json
import locale
import os
import platform
import re
import subprocess
import sys
import traceback
from functools import wraps

__all__ = ['set_application', 'log_telemetry', 'flush_telemetry']

DIAGNOSTICS_TELEMETRY_ENV_NAME = 'AZURE_CLI_DIAGNOSTICS_TELEMETRY'
INSTRUMENTATION_KEY = '02b91c82-6729-4241-befc-e6d02ca4fbba'


# internal decorators

def _suppress_one_exception(expected_exception, raise_in_debug=False, fallback_return=None):
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except expected_exception as the_exception:
                if raise_in_debug and _in_diagnostic_mode():
                    raise the_exception
                else:
                    return fallback_return

        return _wrapped_func

    return _decorator


def _suppress_all_exceptions(raise_in_debug=False, fallback_return=None):
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:  # nopa, pylint: disable=broad-except
                if raise_in_debug and _in_diagnostic_mode():
                    raise ex
                elif fallback_return:
                    return fallback_return
                else:
                    pass

        return _wrapped_func

    return _decorator


# exposed methods

def set_application(application, arg_complete_env_name):
    if not _user_agrees_to_telemetry() or not telemetry_service:
        return

    telemetry_service.application = application
    telemetry_service.arg_complete_env_name = arg_complete_env_name


def log_telemetry(name, log_type='event', **kwargs):
    if not _user_agrees_to_telemetry() or not telemetry_service:
        return

    return telemetry_service.log(name, log_type=log_type, **kwargs)


def flush_telemetry():
    if not _user_agrees_to_telemetry() or not telemetry_service:
        return

    return telemetry_service.flush()


# internal utility functions and classes

class _TelemetryService(object):
    TELEMETRY_VERSION = '0.0.1.4'

    @_suppress_all_exceptions(raise_in_debug=True)
    def __init__(self):
        from applicationinsights import TelemetryClient
        from applicationinsights.exceptions import enable

        self.arg_complete_env_name = None
        self.client = None
        self.application = None
        self.records = []
        self.az_config = _get_azure_cli_config()
        self.core_version = _get_core_version()

        self.client = TelemetryClient(INSTRUMENTATION_KEY)
        self.client.context.application.id = 'Azure CLI'
        self.client.context.application.ver = self.core_version
        self.client.context.user.id = _get_user_machine_id()
        self.client.context.device.type = 'az'

        enable(INSTRUMENTATION_KEY)

    @_suppress_all_exceptions(raise_in_debug=True)
    def log(self, name, log_type='event', **kwargs):
        """
        IMPORTANT: do not log events with quotes in the name, properties or measurements;
        those events may fail to upload.  Also, telemetry events must be verified in
        the backend because successful upload does not guarentee success.
        """
        if not _user_agrees_to_telemetry():
            return

        # Now we now we want to log telemetry, get the profile
        profile = _get_profile()

        name = _remove_cmd_chars(name)
        _sanitize_inputs(kwargs)

        source = 'completer' if self.arg_complete_env_name in os.environ else 'az'

        types = ['event', 'pageview', 'trace']
        if log_type not in types:
            raise ValueError('Type {} is not supported.  Available types: {}'.format(log_type,
                                                                                     types))

        props = {
            'telemetry-version': self.TELEMETRY_VERSION
        }
        _safe_exec(props, 'time', lambda: str(datetime.datetime.now()))
        _safe_exec(props, 'x-ms-client-request-id',
                   lambda: self.application.session['headers']['x-ms-client-request-id'])
        _safe_exec(props, 'command', lambda: self.application.session.get('command', None))
        _safe_exec(props, 'version', lambda: self.core_version)
        _safe_exec(props, 'source', lambda: source)
        _safe_exec(props, 'installation-id', lambda: _get_installation_id(profile))
        _safe_exec(props, 'python-version',
                   lambda: _remove_symbols(str(platform.python_version())))
        _safe_exec(props, 'shell-type', _get_shell_type)
        _safe_exec(props, 'locale', lambda: '{},{}'.format(locale.getdefaultlocale()[0],
                                                           locale.getdefaultlocale()[1]))
        _safe_exec(props, 'user-machine-id', _get_user_machine_id)
        _safe_exec(props, 'user-azure-id', lambda: _get_user_azure_id(profile))
        _safe_exec(props, 'azure-subscription-id', lambda: _get_azure_subscription_id(profile))
        _safe_exec(props, 'default-output-type', lambda: self.az_config.get('core', 'output',
                                                                            fallback='unknown'))
        _safe_exec(props, 'environment', _get_env_string)
        if log_type == 'trace':
            _safe_exec(props, 'trace', _get_stack_trace)
            _safe_exec(props, 'error-hash', _get_error_hash)

        if kwargs:
            props.update(**kwargs)

        self.records.append({
            'name': name,
            'type': log_type,
            'properties': props
        })

    @_suppress_all_exceptions(raise_in_debug=True)
    def flush(self):
        self.client.flush()
        if not self.records:
            return

        data = _remove_symbols(json.dumps(self.records))
        subprocess.Popen([sys.executable, os.path.realpath(__file__), data])

    @_suppress_all_exceptions(raise_in_debug=True)
    def upload(self, data_to_save):
        data_to_save = json.loads(data_to_save.replace("'", '"'))

        for record in data_to_save:
            if record['type'] == 'pageview':
                self.client.track_pageview(record['name'],
                                           url=record['name'],
                                           properties=record['properties'])
            else:
                self.client.track_event(record['name'],
                                        record['properties'])

        self.client.flush()

        if _in_diagnostic_mode():
            sys.stdout.write('Telemetry upload begins\n')
            json.dump(data_to_save, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write('\nTelemetry upload completes\n')


def _user_agrees_to_telemetry():
    return _get_azure_cli_config().getboolean('core', 'collect_telemetry', fallback=True)


@_suppress_all_exceptions(fallback_return={})
def _get_azure_cli_config():
    from azure.cli.core._config import az_config
    return az_config


@_suppress_all_exceptions(fallback_return=None)
def _get_core_version():
    from azure.cli.core import __version__ as core_version
    return core_version


@_suppress_all_exceptions(raise_in_debug=True)
def _safe_exec(props, key, fn):
    props[key] = fn()


@_suppress_one_exception(expected_exception=AttributeError, fallback_return=None)
def _get_installation_id(profile):
    try:
        return profile.get_installation_id()
    except AttributeError:
        return None


@_suppress_all_exceptions(fallback_return=None)
def _get_profile():
    from azure.cli.core._profile import Profile
    return Profile()


def _get_env_string():
    return _remove_cmd_chars(_remove_symbols(str([v for v in os.environ
                                                  if v.startswith('AZURE_CLI')])))


def _get_user_machine_id():
    return _get_hash(platform.node() + getpass.getuser())


def _get_user_azure_id(profile):
    try:
        from azure.cli.core._util import CLIError
    except ImportError:
        CLIError = Exception

    try:
        return _get_hash(profile.get_current_account_user())
    except (AttributeError, CLIError):  # pylint: disable=broad-except
        return None


def _get_hash(s):
    hash_object = hashlib.sha256(s.encode('utf-8'))
    return str(hash_object.hexdigest())


def _get_azure_subscription_id(profile):
    try:
        from azure.cli.core._util import CLIError
    except ImportError:
        CLIError = Exception

    try:
        return profile.get_login_credentials()[1]
    except (AttributeError, CLIError):  # pylint: disable=broad-except
        pass


def _get_shell_type():
    if 'ZSH_VERSION' in os.environ:
        return 'zsh'
    elif 'BASH_VERSION' in os.environ:
        return 'bash'
    elif 'KSH_VERSION' in os.environ or 'FCEDIT' in os.environ:
        return 'ksh'
    elif 'WINDIR' in os.environ:
        return 'cmd'
    else:
        return _remove_cmd_chars(_remove_symbols(os.environ.get('SHELL')))


def _get_error_hash():
    err = sys.exc_info()[1]
    return _remove_cmd_chars(_remove_symbols(_get_hash(str(err))))


def _get_stack_trace():
    def _get_root_path():
        dir_path = os.path.dirname(os.path.realpath(__file__))
        head, tail = os.path.split(dir_path)
        while tail and tail != 'azure-cli':
            head, tail = os.path.split(head)
        return head

    def _remove_root_paths(s):
        site_package_regex = re.compile('.*\\\\site-packages\\\\')

        root = _get_root_path()
        frames = [p.replace(root, '') for p in s]
        return str([site_package_regex.sub('site-packages\\\\', f) for f in frames])

    _, _, ex_traceback = sys.exc_info()
    trace = traceback.format_tb(ex_traceback)
    return _remove_cmd_chars(_remove_symbols(_remove_root_paths(trace)))


def _sanitize_inputs(d):
    for key, value in d.items():
        if isinstance(value, str):
            d[key] = _remove_cmd_chars(value)
        elif isinstance(value, list):
            d[key] = [_remove_cmd_chars(v) for v in value]
            if next((v for v in value if isinstance(v, list) or isinstance(v, dict)),
                    None) is not None:
                raise ValueError('List object too complex, will fail server-side')
        elif isinstance(value, dict):
            d[key] = {key: _remove_cmd_chars(v) for key, v in value.items()}
            if next((v for v in value.values() if isinstance(v, list) or isinstance(v, dict)),
                    None) is not None:
                raise ValueError('Dict object too complex, will fail server-side')
        else:
            d[key] = _remove_cmd_chars(str(value))


def _remove_cmd_chars(s):
    if isinstance(s, str):
        return s.replace("'", '_').replace('"', '_').replace('\r\n', ' ').replace('\n', ' ')
    return s


def _remove_symbols(s):
    if isinstance(s, str):
        for c in '$%^&|':
            s = s.replace(c, '_')
    return s


def _in_diagnostic_mode():
    """
    When the telemetry runs in the diagnostic mode, exception are not suppressed and telemetry
    traces are dumped to the stdout.
    """
    return bool(os.environ.get(DIAGNOSTICS_TELEMETRY_ENV_NAME, False))


def _upload_telemetry(data):
    telemetry_service.upload(data)


# module global variables and initialization the module

if _user_agrees_to_telemetry():
    telemetry_service = _TelemetryService()
else:
    telemetry_service = None


if __name__ == '__main__':
    if _user_agrees_to_telemetry():
        telemetry_service.upload(sys.argv[1])
