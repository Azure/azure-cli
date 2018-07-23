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
from collections import defaultdict
from functools import wraps

import azure.cli.core.decorators as decorators

PRODUCT_NAME = 'azurecli'
TELEMETRY_VERSION = '0.0.1.4'
AZURE_CLI_PREFIX = 'Context.Default.AzureCLI.'
DEFAULT_INSTRUMENTATION_KEY = 'c4395b75-49cc-422c-bc95-c7d51aef5d46'
CORRELATION_ID_PROP_NAME = 'Reserved.DataModel.CorrelationId'


class TelemetrySession(object):  # pylint: disable=too-many-instance-attributes
    def __init__(self, correlation_id=None, application=None):
        self.start_time = None
        self.end_time = None
        self.application = application
        self.arg_complete_env_name = None
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.command = 'execute-unknown-command'
        self.output_type = 'none'
        self.parameters = []
        self.result = 'None'
        self.result_summary = None
        self.payload_properties = None
        self.exceptions = []
        self.module_correlation = None
        self.extension_name = None
        self.extension_version = None
        self.feedback = None
        self.extension_management_detail = None
        self.raw_command = None
        self.mode = 'default'
        # A dictionary with the application insight instrumentation key
        # as the key and an array of telemetry events as value
        self.events = defaultdict(list)
        # stops generate_payload() from adding new azurecli/command event
        # used for interactive to send new custom event upon exit
        self.suppress_new_event = False

    def add_exception(self, exception, fault_type, description=None, message=''):
        fault_type = _remove_symbols(fault_type).replace('"', '').replace("'", '').replace(' ', '-')
        details = {
            'Reserved.DataModel.EntityType': 'Fault',
            'Reserved.DataModel.Fault.Description': description or fault_type,
            'Reserved.DataModel.Correlation.1': '{},UserTask,'.format(self.correlation_id),
            'Reserved.DataModel.Fault.TypeString': exception.__class__.__name__,
            'Reserved.DataModel.Fault.Exception.Message': _remove_cmd_chars(
                message or str(exception)),
            'Reserved.DataModel.Fault.Exception.StackTrace': _remove_cmd_chars(_get_stack_trace()),
            AZURE_CLI_PREFIX + 'FaultType': fault_type.lower()
        }

        fault_name = '{}/fault'.format(PRODUCT_NAME)

        self.exceptions.append((fault_name, details))

    @decorators.suppress_all_exceptions(fallback_return=None)
    def generate_payload(self):
        if not self.suppress_new_event:
            base = self._get_base_properties()
            cli = self._get_azure_cli_properties()

            user_task = self._get_user_task_properties()
            user_task.update(base)
            user_task.update(cli)

            self.events[DEFAULT_INSTRUMENTATION_KEY].append({
                'name': '{}/command'.format(PRODUCT_NAME),
                'properties': user_task
            })

            for name, props in self.exceptions:
                props.update(base)
                props.update(cli)
                props.update({CORRELATION_ID_PROP_NAME: str(uuid.uuid4()),
                              'Reserved.EventId': str(uuid.uuid4())})
                self.events[DEFAULT_INSTRUMENTATION_KEY].append({
                    'name': name,
                    'properties': props
                })

        payload = json.dumps(self.events, separators=(',', ':'))
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
            CORRELATION_ID_PROP_NAME: self.correlation_id,

            'Context.Default.VS.Core.ExeName': PRODUCT_NAME,
            'Context.Default.VS.Core.ExeVersion': '{}@{}'.format(
                self.product_version, self.module_version),
            'Context.Default.VS.Core.MacAddressHash': _get_hash_mac_address(),
            'Context.Default.VS.Core.Machine.Id': _get_hash_machine_id(),
            'Context.Default.VS.Core.OS.Type': platform.system().lower(),  # eg. darwin, windows
            'Context.Default.VS.Core.OS.Version': platform.version().lower(),  # eg. 10.0.14942
            'Context.Default.VS.Core.User.Id': _get_installation_id(),
            'Context.Default.VS.Core.User.IsMicrosoftInternal': 'False',
            'Context.Default.VS.Core.User.IsOptedIn': 'True',
            'Context.Default.VS.Core.TelemetryApi.ProductVersion': '{}@{}'.format(
                PRODUCT_NAME, _get_core_version())
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
        if self.arg_complete_env_name and self.arg_complete_env_name in os.environ:
            source = 'completer'
        else:
            source = 'az'
        result = {}
        ext_info = '{}@{}'.format(self.extension_name, self.extension_version) if self.extension_name else None
        set_custom_properties(result, 'Source', source)
        set_custom_properties(result,
                              'ClientRequestId',
                              lambda: self.application.data['headers'][
                                  'x-ms-client-request-id'])
        set_custom_properties(result, 'CoreVersion', _get_core_version)
        set_custom_properties(result, 'TelemetryVersion', "2.0")
        set_custom_properties(result, 'InstallationId', _get_installation_id)
        set_custom_properties(result, 'ShellType', _get_shell_type)
        set_custom_properties(result, 'UserAzureId', _get_user_azure_id)
        set_custom_properties(result, 'UserAzureSubscriptionId', _get_azure_subscription_id)
        set_custom_properties(result, 'DefaultOutputType',
                              lambda: _get_config().get('core', 'output', fallback='unknown'))
        set_custom_properties(result, 'EnvironmentVariables', _get_env_string)
        set_custom_properties(result, 'Locale',
                              lambda: '{},{}'.format(locale.getdefaultlocale()[0], locale.getdefaultlocale()[1]))
        set_custom_properties(result, 'StartTime', str(self.start_time))
        set_custom_properties(result, 'EndTime', str(self.end_time))
        set_custom_properties(result, 'OutputType', self.output_type)
        set_custom_properties(result, 'RawCommand', self.raw_command)
        set_custom_properties(result, 'Params', ','.join(self.parameters or []))
        set_custom_properties(result, 'PythonVersion', platform.python_version())
        set_custom_properties(result, 'ModuleCorrelation', self.module_correlation)
        set_custom_properties(result, 'ExtensionName', ext_info)
        set_custom_properties(result, 'Feedback', self.feedback)
        set_custom_properties(result, 'ExtensionManagementDetail', self.extension_management_detail)
        set_custom_properties(result, 'Mode', self.mode)

        return result

    @property
    def command_name(self):
        return self.command.lower().replace('-', '').replace(' ', '-')

    @property
    def feature_name(self):
        # The feature name is used to created the event name. The feature name should be eventually
        # the module name. However, it takes time to resolve the actual module name using pip
        # module. Therefore, a hard coded replacement is used before a better solution is
        # implemented
        return 'command'

    @property
    def module_version(self):
        # TODO: find a efficient solution to retrieve module version
        return 'none'

    @property
    def product_version(self):
        return _get_core_version()


_session = TelemetrySession()


def _user_agrees_to_telemetry(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if not _get_config().getboolean('core', 'collect_telemetry', fallback=True):
            return None
        return func(*args, **kwargs)

    return _wrapper


# public api


@decorators.suppress_all_exceptions()
def start(mode=None):
    if mode:
        _session.mode = mode
    _session.start_time = datetime.datetime.utcnow()


@_user_agrees_to_telemetry
@decorators.suppress_all_exceptions()
def flush():
    from azure.cli.core._environment import get_config_dir
    from azure.cli.telemetry import save

    # flush out current information
    _session.end_time = datetime.datetime.utcnow()
    save(get_config_dir(), _session.generate_payload())

    # reset session fields, retaining correlation id and application
    _session.__init__(correlation_id=_session.correlation_id, application=_session.application)


@_user_agrees_to_telemetry
@decorators.suppress_all_exceptions()
def conclude():
    from azure.cli.core._environment import get_config_dir
    from azure.cli.telemetry import save

    _session.end_time = datetime.datetime.utcnow()
    save(get_config_dir(), _session.generate_payload())


@decorators.suppress_all_exceptions()
def suppress_new_events(unsuppress=False):
    _session.suppress_new_event = not unsuppress


@decorators.suppress_all_exceptions()
def set_custom_properties(prop, name, value):
    actual_value = value() if hasattr(value, '__call__') else value

    if actual_value is not None:
        prop[AZURE_CLI_PREFIX + name] = actual_value


@decorators.suppress_all_exceptions()
def set_exception(exception, fault_type, summary=None):
    if not summary:
        _session.result_summary = summary

    _session.add_exception(exception, fault_type=fault_type, description=summary)


@decorators.suppress_all_exceptions()
def set_failure(summary=None):
    if _session.result != 'None':
        return

    _session.result = 'Failure'
    if summary:
        _session.result_summary = _remove_cmd_chars(summary)


@decorators.suppress_all_exceptions()
def set_success(summary=None):
    if _session.result != 'None':
        return

    _session.result = 'Success'
    if summary:
        _session.result_summary = _remove_cmd_chars(summary)


@decorators.suppress_all_exceptions()
def set_user_fault(summary=None):
    if _session.result != 'None':
        return

    _session.result = 'UserFault'
    if summary:
        _session.result_summary = _remove_cmd_chars(summary)


@decorators.suppress_all_exceptions()
def set_application(application, arg_complete_env_name):
    _session.application, _session.arg_complete_env_name = application, arg_complete_env_name


@decorators.suppress_all_exceptions()
def set_feedback(feedback):
    """ This method is used for modules in which user feedback is collected. The data can be an arbitrary string but it
    will be truncated at 512 characters to avoid abusing the telemetry."""
    _session.feedback = feedback[:512]


@decorators.suppress_all_exceptions()
def set_extension_management_detail(ext_name, ext_version):
    content = '{}@{}'.format(ext_name, ext_version)
    _session.extension_management_detail = content[:512]


@decorators.suppress_all_exceptions()
def set_command_details(command, output_type=None, parameters=None, extension_name=None, extension_version=None):
    _session.command = command
    _session.output_type = output_type
    _session.parameters = parameters
    _session.extension_name = extension_name
    _session.extension_version = extension_version


@decorators.suppress_all_exceptions()
def set_module_correlation_data(correlation_data):
    _session.module_correlation = correlation_data[:512]


@decorators.suppress_all_exceptions()
def set_raw_command_name(command):
    # the raw command name user inputs
    _session.raw_command = command


@decorators.suppress_all_exceptions()
def add_extension_event(extension_name, properties, instrumentation_key=DEFAULT_INSTRUMENTATION_KEY):
    set_custom_properties(properties, 'ExtensionName', extension_name)
    _add_event('extension', properties, instrumentation_key=instrumentation_key)


@decorators.suppress_all_exceptions()
def add_interactive_event(properties, instrumentation_key=DEFAULT_INSTRUMENTATION_KEY):
    _add_event('interactive', properties, instrumentation_key=instrumentation_key)


@decorators.suppress_all_exceptions()
def _add_event(event_name, properties, instrumentation_key=DEFAULT_INSTRUMENTATION_KEY):
    # Inject correlation ID into the new event
    properties.update({
        CORRELATION_ID_PROP_NAME: _session.correlation_id,
    })

    _session.events[instrumentation_key].append({
        'name': '{}/{}'.format(PRODUCT_NAME, event_name),
        'properties': properties
    })


# definitions

@decorators.call_once
@decorators.suppress_all_exceptions(fallback_return={})
def _get_config():
    return _session.application.config


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
    return Profile(cli_ctx=_session.application)


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
    return _get_profile().get_subscription_id()


def _get_shell_type():
    if 'ZSH_VERSION' in os.environ:
        return 'zsh'
    elif 'BASH_VERSION' in os.environ:
        return 'bash'
    elif 'KSH_VERSION' in os.environ or 'FCEDIT' in os.environ:
        return 'ksh'
    elif 'WINDIR' in os.environ:
        return 'cmd'
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
