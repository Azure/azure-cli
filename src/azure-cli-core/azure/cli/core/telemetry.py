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
from knack.util import CLIError
from azure.cli.core import decorators
from azure.cli.telemetry import DEFAULT_INSTRUMENTATION_KEY

PRODUCT_NAME = 'azurecli'
TELEMETRY_VERSION = '0.0.1.4'
AZURE_CLI_PREFIX = 'Context.Default.AzureCLI.'
CORRELATION_ID_PROP_NAME = 'Reserved.DataModel.CorrelationId'
# Put a config section or key (section.name) in the allowed set to allow recording the config
# values in the section or for the key with 'az config set'
ALLOWED_CONFIG_SECTIONS_OR_KEYS = {'auto-upgrade', 'extension', 'core', 'logging.enable_log_file',
                                   'output.show_survey_link'}


class TelemetrySession:  # pylint: disable=too-many-instance-attributes
    def __init__(self, correlation_id=None, application=None):
        self.instrumentation_key = {DEFAULT_INSTRUMENTATION_KEY}
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
        self.event_id = str(uuid.uuid4())
        self.cli_recommendation = None
        self.feedback = None
        self.extension_management_detail = None
        self.raw_command = None
        self.command_preserve_casing = None
        self.is_cmd_idx_rebuild_triggered = False
        self.show_survey_message = False
        self.region_input = None
        self.region_identified = None
        self.mode = 'default'
        # The AzCLIError sub-class name
        self.error_type = 'None'
        # The class name of the raw exception
        self.exception_name = 'None'
        self.init_time_elapsed = None
        self.invoke_time_elapsed = None
        self.debug_info = []
        # A dictionary with the application insight instrumentation key
        # as the key and an array of telemetry events as value
        self.events = defaultdict(list)
        # stops generate_payload() from adding new azurecli/command event
        # used for interactive to send new custom event upon exit
        self.suppress_new_event = False
        self.poll_start_time = None
        self.poll_end_time = None
        self.secrets_detected = None
        self.secret_keys = None
        self.secret_names = None
        self.user_agent = None
        # authentication-related
        self.enable_broker_on_windows = None
        self.msal_telemetry = None
        self.login_experience_v2 = None

    def add_event(self, name, properties):
        for key in self.instrumentation_key:
            self.events[key].append({
                'name': name,
                'properties': properties
            })

    def add_exception(self, exception, fault_type, description=None, message=''):
        # Move the exception info into userTask record, in order to make one Telemetry record for one command
        self.exception_name = exception.__class__.__name__

        # Backward compatible, so there are duplicated info recorded
        # The logic below should be removed along with self.exceptions after confirmation
        fault_type = _remove_symbols(fault_type).replace('"', '').replace("'", '').replace(' ', '-')
        details = {
            'Reserved.DataModel.EntityType': 'Fault',
            'Reserved.DataModel.Fault.Description': description or fault_type,
            'Reserved.DataModel.Correlation.1': '{},UserTask,'.format(self.correlation_id),
            'Reserved.DataModel.Fault.TypeString': exception.__class__.__name__,
            'Reserved.DataModel.Fault.Exception.Message': _remove_cmd_chars(
                message or str(exception)),
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

            self.add_event('{}/command'.format(PRODUCT_NAME), user_task)

            for name, props in self.exceptions:
                props.update(base)
                props.update(cli)
                props.update({CORRELATION_ID_PROP_NAME: str(uuid.uuid4()),
                              'Reserved.EventId': self.event_id})
                self.add_event(name, props)

        payload = json.dumps(self.events, separators=(',', ':'))
        return _remove_symbols(payload)

    def _get_base_properties(self):
        return {
            'Reserved.ChannelUsed': 'AI',
            'Reserved.EventId': self.event_id,
            'Reserved.SequenceNumber': 1,
            'Reserved.SessionId': _get_session_id(),
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
            'Context.Default.VS.Core.OS.Platform': platform.platform().lower(),  # eg. windows-10-10.0.19041-sp0
            # the distro info is complement of platform info for linux
            'Context.Default.VS.Core.Distro.Name': _get_distro_name(),  # eg. 'CentOS Linux 8'
            'Context.Default.VS.Core.Distro.Id': _get_distro_id(),  # eg. 'centos'
            'Context.Default.VS.Core.Distro.Version': _get_distro_version(),  # eg. '8.4.2105'
            'Context.Dafault.VS.Core.Istty': str(sys.stdin.isatty()),
            'Context.Default.VS.Core.DevDeviceId': _get_device_id(),
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
                              lambda: self.application.data['headers'].get('x-ms-client-request-id', ''))
        set_custom_properties(result, 'UserAgent', _get_user_agent())
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
                              lambda: '{},{}'.format(locale.getlocale()[0], locale.getlocale()[1]))
        set_custom_properties(result, 'StartTime', str(self.start_time))
        set_custom_properties(result, 'EndTime', str(self.end_time))
        set_custom_properties(result, 'InitTimeElapsed', str(self.init_time_elapsed))
        set_custom_properties(result, 'InvokeTimeElapsed', str(self.invoke_time_elapsed))
        set_custom_properties(result, 'OutputType', self.output_type)
        set_custom_properties(result, 'RawCommand', self.raw_command)
        set_custom_properties(result, 'CommandPreserveCasing',
                              self.command_preserve_casing or '')
        set_custom_properties(result, 'IsCmdIdxRebuildTriggered', str(self.is_cmd_idx_rebuild_triggered))
        set_custom_properties(result, 'Params', ','.join(self.parameters or []))
        set_custom_properties(result, 'PythonVersion', platform.python_version())
        set_custom_properties(result, 'ModuleCorrelation', self.module_correlation)
        set_custom_properties(result, 'ExtensionName', ext_info)
        set_custom_properties(result, 'CLIRecommendation', self.cli_recommendation)
        set_custom_properties(result, 'Feedback', self.feedback)
        set_custom_properties(result, 'ExtensionManagementDetail', self.extension_management_detail)
        set_custom_properties(result, 'Mode', self.mode)
        from azure.cli.core._environment import _ENV_AZ_INSTALLER
        set_custom_properties(result, 'Installer', os.getenv(_ENV_AZ_INSTALLER))
        set_custom_properties(result, 'error_type', self.error_type)
        set_custom_properties(result, 'exception_name', self.exception_name)
        set_custom_properties(result, 'debug_info', ','.join(self.debug_info))
        set_custom_properties(result, 'PollStartTime', str(self.poll_start_time))
        set_custom_properties(result, 'PollEndTime', str(self.poll_end_time))
        set_custom_properties(result, 'CloudName', _get_cloud_name())
        set_custom_properties(result, 'ShowSurveyMessage', str(self.show_survey_message))
        set_custom_properties(result, 'RegionInput', self.region_input)
        set_custom_properties(result, 'RegionIdentified', self.region_identified)
        set_custom_properties(result, 'SecretsWarning', _get_secrets_warning_config())
        set_custom_properties(result, 'SecretsDetected', str(self.secrets_detected))
        set_custom_properties(result, 'SecretKeys', ','.join(self.secret_keys or []))
        set_custom_properties(result, 'SecretNames', ','.join(self.secret_names or []))
        # authentication-related
        set_custom_properties(result, 'EnableBrokerOnWindows', str(self.enable_broker_on_windows))
        set_custom_properties(result, 'MsalTelemetry', self.msal_telemetry)
        set_custom_properties(result, 'LoginExperienceV2', str(self.login_experience_v2))

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


def has_exceptions():
    return len(_session.exceptions) > 0


def _user_agrees_to_telemetry(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if not is_telemetry_enabled():
            return None
        return func(*args, **kwargs)

    return _wrapper


# public api


@decorators.suppress_all_exceptions()
def start(mode=None):
    if mode:
        _session.mode = mode
    _session.start_time = datetime.datetime.utcnow()


@decorators.suppress_all_exceptions()
def set_init_time_elapsed(init_time_elapsed):
    _session.init_time_elapsed = init_time_elapsed


@decorators.suppress_all_exceptions()
def set_invoke_time_elapsed(invoke_time_elapsed):
    _session.invoke_time_elapsed = invoke_time_elapsed


@decorators.suppress_all_exceptions()
def poll_start():
    _session.poll_start_time = datetime.datetime.utcnow()


@decorators.suppress_all_exceptions()
def poll_end():
    _session.poll_end_time = datetime.datetime.utcnow()


@_user_agrees_to_telemetry
@decorators.suppress_all_exceptions()
def flush():
    from azure.cli.core._environment import get_config_dir
    from azure.cli.telemetry import save

    # flush out current information
    _session.end_time = datetime.datetime.utcnow()
    save(get_config_dir(), _session.generate_payload())

    # reset session fields, retaining correlation id and application
    _session.__init__(correlation_id=_session.correlation_id, application=_session.application)  # pylint: disable=unnecessary-dunder-call


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
    if not _session.result_summary:
        _session.result_summary = _remove_cmd_chars(summary)

    _session.add_exception(exception, fault_type=fault_type, description=summary)


@decorators.suppress_all_exceptions()
def set_error_type(error_type):
    if _session.result != 'None':
        return
    _session.error_type = error_type


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
def set_debug_info(key, info):
    if key == 'ConfigSet':
        info = _process_config_set_debug_info(info)

    debug_info = '{}: {}'.format(key, info)
    _session.debug_info.append(debug_info)


@decorators.suppress_all_exceptions()
def _process_config_set_debug_info(info):
    processed_info = []
    # info is a list of tuples
    for key, section, value in info:
        if section in ALLOWED_CONFIG_SECTIONS_OR_KEYS or key in ALLOWED_CONFIG_SECTIONS_OR_KEYS:
            processed_info.append('{}={}'.format(key, value))
        else:
            processed_info.append('{}={}'.format(key, '***' if value else value))
    return ' '.join(processed_info)


@decorators.suppress_all_exceptions()
def set_application(application, arg_complete_env_name):
    _session.application, _session.arg_complete_env_name = application, arg_complete_env_name


@decorators.suppress_all_exceptions()
def set_feedback(feedback):
    """ This method is used for modules in which user feedback is collected. The data can be an arbitrary string but it
    will be truncated at 512 characters to avoid abusing the telemetry."""
    _session.feedback = feedback[:512]


@decorators.suppress_all_exceptions()
def set_cli_recommendation(api_version, feedback):
    # This function returns the user's selection and feedback on the cli-recommendation results
    # Please refer to feedback_design.md of cli-recommendation for detailed information
    # json.dumps converts the JSON-formatted feedback into a string format before storing it in the telemetry database.
    # Telemetry property only accepts string inputs, and it cannot directly upload JSON content.
    _session.cli_recommendation = json.dumps({"api_version": api_version, "feedback": feedback})


@decorators.suppress_all_exceptions()
def set_extension_management_detail(ext_name, ext_version):
    content = '{}@{}'.format(ext_name, ext_version)
    _session.extension_management_detail = content[:512]


@decorators.suppress_all_exceptions()
def set_command_index_rebuild_triggered(is_cmd_idx_rebuild_triggered=False):
    _session.is_cmd_idx_rebuild_triggered = is_cmd_idx_rebuild_triggered


@decorators.suppress_all_exceptions()
def set_command_details(command, output_type=None, parameters=None, extension_name=None,
                        extension_version=None, command_preserve_casing=None):
    _session.command = command
    _session.output_type = output_type
    _session.parameters = parameters
    _session.extension_name = extension_name
    _session.extension_version = extension_version
    _session.command_preserve_casing = command_preserve_casing


@decorators.suppress_all_exceptions()
def set_module_correlation_data(correlation_data):
    _session.module_correlation = correlation_data[:512]


@decorators.suppress_all_exceptions()
def set_raw_command_name(command):
    # the raw command name user inputs
    _session.raw_command = command


@decorators.suppress_all_exceptions()
def set_survey_info(show_survey_message):
    # whether showed the intercept survey message or not
    _session.show_survey_message = show_survey_message


@decorators.suppress_all_exceptions()
def set_region_identified(region_input, region_identified):
    # Record the region input by customers
    _session.region_input = region_input
    # Record the region we have recommended to customers
    _session.region_identified = region_identified


# region authentication-related
@decorators.suppress_all_exceptions()
def set_broker_info(enable_broker_on_windows):
    # Log the value of `enable_broker_on_windows`
    _session.enable_broker_on_windows = enable_broker_on_windows


@decorators.suppress_all_exceptions()
def set_msal_telemetry(msal_telemetry):
    if not _session.msal_telemetry:
        _session.msal_telemetry = msal_telemetry


@decorators.suppress_all_exceptions()
def set_login_experience_v2(login_experience_v2):
    _session.login_experience_v2 = login_experience_v2
# endregion


@decorators.suppress_all_exceptions()
def set_user_agent(user_agent):
    if user_agent:
        _session.user_agent = user_agent


@decorators.suppress_all_exceptions()
def set_secrets_detected(secrets_detected, secret_keys=None, secret_names=None):
    _session.secrets_detected = secrets_detected
    if secret_keys:
        _session.secret_keys = secret_keys
    if secret_names:
        _session.secret_names = secret_names


@decorators.suppress_all_exceptions()
def add_dedicated_instrumentation_key(dedicated_instrumentation_key):
    if not dedicated_instrumentation_key:
        return

    from collections.abc import Iterable
    if isinstance(dedicated_instrumentation_key, str):
        _session.instrumentation_key.add(dedicated_instrumentation_key)
    elif isinstance(dedicated_instrumentation_key, Iterable):
        _session.instrumentation_key.update(dedicated_instrumentation_key)


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


@decorators.suppress_all_exceptions()
def is_telemetry_enabled():
    from azure.cli.core.cloud import cloud_forbid_telemetry
    if cloud_forbid_telemetry(_session.application):
        return False
    return _get_config().getboolean('core', 'collect_telemetry', fallback=True)


# definitions

@decorators.call_once
@decorators.suppress_all_exceptions(fallback_return={})
def _get_config():
    return _session.application.config


@decorators.suppress_all_exceptions()
def _get_secrets_warning_config():
    from configparser import NoSectionError, NoOptionError
    try:
        show_secrets_warning = _get_config().getboolean('clients', 'show_secrets_warning')
        return 'on' if show_secrets_warning else 'off'
    except (NoSectionError, NoOptionError):
        return None


# internal utility functions

@decorators.suppress_all_exceptions(fallback_return=None)
def _get_core_version():
    from azure.cli.core import __version__ as core_version
    return core_version


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_device_id():
    # This is a shared id with VS code telemetry
    from deviceid import get_device_id
    return get_device_id()


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_installation_id():
    return _get_profile().get_installation_id()


@decorators.suppress_all_exceptions(fallback_return="")
def _get_session_id():
    # As a workaround to get the terminal info as SessionId, this function may not be accurate.

    def get_hash_result(content):
        import hashlib

        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        return hasher.hexdigest()

    # Usually, more than one layer of sub-process will be started when excuting a CLI command. While, the create time
    # of these sub-processes will be very close, usually in several milliseconds. We use 1 second as the threshold here.
    # When the difference of create time between current process and its parent process is larger than the threshold,
    # the parent process will be viewed as the terminal process.
    try:
        # psutil is not available on cygwin
        import psutil
    except ImportError:
        return ""
    time_threshold = 1
    process = psutil.Process()
    while process and process.ppid() and process.pid != process.ppid():
        parent_process = process.parent()
        if parent_process and process.create_time() - parent_process.create_time() > time_threshold:
            content = '{}{}{}'.format(_get_installation_id(), parent_process.create_time(), parent_process.pid)
            return get_hash_result(content)
        process = parent_process
    return ""


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
def _get_distro_name():
    try:
        import distro
        return distro.name(pretty=True)
    except ImportError:
        return ''


@decorators.suppress_all_exceptions(fallback_return='')
def _get_distro_id():
    try:
        import distro
        return distro.id()
    except ImportError:
        return ''


@decorators.suppress_all_exceptions(fallback_return='')
def _get_distro_version():
    try:
        import distro
        return distro.version()
    except ImportError:
        return ''


@decorators.suppress_all_exceptions(fallback_return='')
@decorators.hash256_result
def _get_user_azure_id():
    try:
        return _get_profile().get_current_account_user()
    except CLIError:
        return ''


def _get_env_string():
    return _remove_cmd_chars(_remove_symbols(str([v for v in os.environ
                                                  if v.startswith('AZURE_CLI')])))


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_azure_subscription_id():
    try:
        return _get_profile().get_subscription_id()
    except CLIError:
        return None


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_cloud_name():
    try:
        return _session.application.cloud.name
    except AttributeError:
        return 'unknown'


def _get_shell_type():
    # This method is not accurate and needs improvement, for instance all shells on Windows return 'cmd'.
    if 'ZSH_VERSION' in os.environ:
        return 'zsh'
    if 'BASH_VERSION' in os.environ:
        return 'bash'
    if 'KSH_VERSION' in os.environ or 'FCEDIT' in os.environ:
        return 'ksh'
    if 'WINDIR' in os.environ:
        return 'cmd'
    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        return 'cloud-shell'
    return _remove_cmd_chars(_remove_symbols(os.environ.get('SHELL')))


@decorators.suppress_all_exceptions(fallback_return='')
def _get_user_agent():
    if _session.user_agent:
        return _session.user_agent
    from azure.cli.core.util import get_az_user_agent
    agents = [get_az_user_agent()]
    if 'AZURE_HTTP_USER_AGENT' in os.environ:
        agents.append(os.environ['AZURE_HTTP_USER_AGENT'])
    return ' '.join(agents)


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
