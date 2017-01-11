# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import json
import locale
import os
import platform
import re
import sys
import traceback
import uuid
from functools import wraps

import azure.cli.core.decorators as decorators
import azure.cli.core.telemetry_upload as telemetry_core

PRODUCT_NAME = 'azurecli'
TELEMETRY_VERSION = '0.0.1.4'
AZURE_CLI_PREFIX = 'Context.AzureCLI.'

decorators.is_diagnostics_mode = telemetry_core.in_diagnostic_mode


def _user_agrees_to_telemetry(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if not _get_azure_cli_config().getboolean('core', 'collect_telemetry', fallback=True):
            return
        else:
            return func(*args, **kwargs)

    return _wrapper


class TelemetrySession(object):  # pylint: disable=too-many-instance-attributes
    start_time = None
    end_time = None
    application = None
    arg_complete_env_name = None

    correlation_id = str(uuid.uuid4())
    command = 'unknown'
    output_type = 'none'
    parameters = []

    result = 'None'
    result_summary = None

    payload_properties = None

    exceptions = []

    def __init__(self):
        pass

    def add_exception(self, exception, description=None, message=None):
        details = {
            'Reserved.DataModel.EntityType': 'Fault',
            'Reserved.DataModel.Fault.Description': description,
            'Reserved.DataModel.Correlation.X': self.correlation_id,
            'Reserved.DataModel.Fault.TypeString': exception.__class__.__name__,
            'Reserved.DataModel.Fault.Exception.Message': _remove_cmd_chars(
                message or str(exception)),
            'Reserved.DataModel.Fault.Exception.StackTrace': _remove_cmd_chars(_get_stack_trace()),
            'Reserved.DataModel.Fault.Exception.ErrorCode': _remove_cmd_chars(_get_error_hash())
        }
        self.exceptions.append(details)

    @decorators.suppress_all_exceptions(raise_in_diagnostics=True, fallback_return=None)
    def generate_payload(self):
        events = []
        base = self._get_base_properties()
        cli = self._get_azure_cli_properties()

        user_task = self._get_user_task_properties()
        user_task.update(base)
        user_task.update(cli)

        events.append({'name': self.event_name, 'properties': user_task})

        for f in self.exceptions:
            f.update(base)
            f.update(cli)
            f.update({'Reserved.DataModel.CorrelationId': str(uuid.uuid4())})
            events.append({'name': self.event_name, 'properties': f})

        payload = json.dumps(events)
        return _remove_symbols(payload)

    def _get_base_properties(self):
        return {
            'Reserved.ChannelUsed': 'AI',
            'Reserved.EventId': str(uuid.uuid4()),
            'Reserved.SequenceNumber': 1,
            'Reserved.SessionId': str(uuid.uuid4()),
            'Reserved.TimeSinceSessionStart': 0,

            'Reserved.DataModel.Source': 'DataModelAPI',
            'Reserved.DataModel.EntitySchemaVersion': 4,
            'Reserved.DataModel.Severity': 0,
            'Reserved.DataModel.ProductName': PRODUCT_NAME,
            'Reserved.DataModel.FeatureName': self.feature_name,
            'Reserved.DataModel.EntityName': self.command_name,
            'Reserved.DataModel.CorrelationId': self.correlation_id,
            'Context.Default.VS.Core.ExeName': PRODUCT_NAME,
            'Context.Default.VS.Core.ExeVersion': platform.python_version(),
            'Context.Default.VS.Core.MacAddressHash': _get_hash_mac_address(),
            'Context.Default.VS.Core.Machine.Id': _get_hash_machine_id(),
            'Context.Default.VS.Core.OS.Type': platform.system().lower(),  # eg. darwin, windows
            'Context.Default.VS.Core.OS.Version': platform.version().lower(),  # eg. 10.0.14942
            'Context.Default.VS.Core.TelemetryApi.ProductVersion': _get_core_version(),
            'Context.Default.VS.Core.User.Id': _get_installation_id(),
            'Context.Default.VS.Core.User.IsMicrosoftInternal': 'False',
            'Context.Default.VS.Core.User.IdOptedIn': 'True',
            'Context.Default.VS.Core.BuildNumber': '{}@{}'.format(self.product_version,
                                                                  self.module_version)
        }

    def _get_user_task_properties(self):
        result = {
            'Reserved.DataModel.EntityType': 'UserTask',
            'Reserved.DataModel.Action.Type': 'Atomic',
            'Reserved.DataModel.Action.Result': self.result
        }

        if self.result_summary:
            result['Reserved.DataModel.Action.ResultSummary'] = self.result_summary

        return result

    def _get_azure_cli_properties(self):
        source = 'az' if self.arg_complete_env_name not in os.environ else 'completer'
        result = {}
        self.set_custom_properties(result, 'Source', source)
        self.set_custom_properties(result,
                                   'ClientRequestId',
                                   lambda: self.application.session['headers'][
                                       'x-ms-client-request-id'])
        self.set_custom_properties(result, 'CoreVersion', _get_core_version)
        self.set_custom_properties(result, 'InstallationId', _get_installation_id)
        self.set_custom_properties(result, 'ShellType', _get_shell_type)
        self.set_custom_properties(result, 'UserAzureId', _get_user_azure_id)
        self.set_custom_properties(result, 'UserAzureSubscriptionId', _get_azure_subscription_id)
        self.set_custom_properties(result, 'DefaultOutputType',
                                   lambda: _get_azure_cli_config().get('core', 'output',
                                                                       fallback='unknown'))
        self.set_custom_properties(result, 'EnvironmentVariables', _get_env_string)
        self.set_custom_properties(result, 'Locale',
                                   lambda: '{},{}'.format(locale.getdefaultlocale()[0],
                                                          locale.getdefaultlocale()[1]))
        self.set_custom_properties(result, 'StartTime', str(self.start_time))
        self.set_custom_properties(result, 'EndTime', str(self.end_time))
        self.set_custom_properties(result, 'OutputType', self.output_type)
        self.set_custom_properties(result, 'Parameters', self.parameters)

        return result

    @property
    def command_name(self):
        return self.command.lower().replace('-', '').replace(' ', '-')

    @property
    def event_name(self):
        return '{}/{}/{}'.format(PRODUCT_NAME, self.feature_name, self.command_name)

    @property
    def feature_name(self):
        # 'model-name-to-be-implemented'
        return 'none'

    @property
    def module_version(self):
        # 'model-version-to-be-implemented'
        return 'none'

    @property
    def product_version(self):
        return _get_core_version()

    @classmethod
    @decorators.suppress_all_exceptions(raise_in_diagnostics=True)
    def set_custom_properties(cls, prop, name, value):
        actual_value = value() if hasattr(value, '__call__') else value
        if actual_value:
            prop[AZURE_CLI_PREFIX + name] = actual_value


_session = TelemetrySession()


# public api

@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def start():
    _session.start_time = datetime.datetime.now()


@_user_agrees_to_telemetry
@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def conclude():
    _session.end_time = datetime.datetime.now()

    payload = _session.generate_payload()
    if payload:
        import subprocess
        subprocess.Popen([sys.executable, os.path.realpath(telemetry_core.__file__), payload])


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def set_exception(exception, summary=None):
    if not summary:
        _session.result_summary = summary

    _session.add_exception(exception)


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def set_failure(summary=None):
    if _session.result != 'None':
        return

    _session.result = 'Failure'
    if summary:
        _session.result_summary = _remove_cmd_chars(summary)


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def set_success(summary=None):
    if _session.result != 'None':
        return

    _session.result = 'Success'
    if summary:
        _session.result_summary = _remove_cmd_chars(summary)


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def set_user_fault(summary=None):
    if _session.result != 'None':
        return

    _session.result = 'UserFault'
    if summary:
        _session.result_summary = _remove_cmd_chars(summary)


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def set_application(application, arg_complete_env_name):
    _session.application, _session.arg_complete_env_name = application, arg_complete_env_name


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def set_command_details(command, output_type=None, parameters=None):
    _session.command = command
    _session.output_type = output_type
    _session.parameters = parameters


# definitions

@decorators.call_once
@decorators.suppress_all_exceptions(fallback_return={})
def _get_azure_cli_config():
    from azure.cli.core._config import az_config
    return az_config


# internal utility functions

@decorators.suppress_all_exceptions(fallback_return=None)
def _get_core_version():
    from azure.cli.core import __version__ as core_version
    return core_version


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_installation_id():
    return _get_profile().get_installation_id()


@decorators.call_once
@decorators.suppress_all_exceptions(fallback_return=None)
def _get_profile():
    from azure.cli.core._profile import Profile
    return Profile()


@decorators.suppress_all_exceptions(fallback_return='')
@decorators.hash256_result
def _get_hash_mac_address():
    s = ''
    for index, c in enumerate(hex(uuid.getnode())[2:].upper()):
        s += c
        if index % 2:
            s += '-'

    s = s.strip('-')

    return s


@decorators.suppress_all_exceptions(fallback_return='')
def _get_hash_machine_id():
    # Definition: Take first 128bit of the SHA256 hashed MAC address and convert them into a GUID
    return str(uuid.UUID(_get_hash_mac_address()[0:32]))


@decorators.suppress_all_exceptions(fallback_return='')
@decorators.hash256_result
def _get_user_azure_id():
    return _get_profile().get_current_account_user()


def _get_env_string():
    return _remove_cmd_chars(_remove_symbols(str([v for v in os.environ
                                                  if v.startswith('AZURE_CLI')])))


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_azure_subscription_id():
    return _get_profile().get_login_credentials()[1]


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


@decorators.suppress_all_exceptions(fallback_return='')
@decorators.hash256_result
def _get_error_hash():
    return str(sys.exc_info()[1])


@decorators.suppress_all_exceptions(fallback_return='')
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


def _remove_cmd_chars(s):
    if isinstance(s, str):
        return s.replace("'", '_').replace('"', '_').replace('\r\n', ' ').replace('\n', ' ')
    return s


def _remove_symbols(s):
    if isinstance(s, str):
        for c in '$%^&|':
            s = s.replace(c, '_')
    return s
