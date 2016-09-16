#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
from __future__ import print_function
import getpass
import datetime
import subprocess
import json
import os
import sys
import platform
import locale

from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable
from azure.cli.core import __version__ as core_version
from azure.cli.core._profile import Profile
from azure.cli.core._util import CLIError

_DEBUG_TELEMETRY = 'AZURE_CLI_DEBUG_TELEMETRY'
client = {}
telemetry_records = []
APPLICATION = {}
ARGCOMPLETE_ENV_NAME = None

def set_application(application, argcomplete_env_name):
    global APPLICATION #pylint: disable=global-statement
    APPLICATION = application
    global ARGCOMPLETE_ENV_NAME #pylint: disable=global-statement
    ARGCOMPLETE_ENV_NAME = argcomplete_env_name

def init_telemetry():
    try:
        instrumentation_key = '02b91c82-6729-4241-befc-e6d02ca4fbba'

        global client #pylint: disable=global-statement
        client = TelemetryClient(instrumentation_key)

        client.context.application.id = 'Azure CLI'
        client.context.application.ver = core_version
        client.context.user.id = _get_user_machine_id()

        enable(instrumentation_key)
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex

def user_agrees_to_telemetry():
    # TODO: agreement, needs to take Y/N from the command line
    # and needs a "skip" param to not show (for scripts)
    return True

def log_telemetry(name, log_type='event', **kwargs):
    """
    IMPORTANT: do not log events with quotes in the name, properties or measurements;
    those events may fail to upload.  Also, telemetry events must be verified in
    the backend because successful upload does not guarentee success.
    """
    try:
        name = _remove_quotes(name)
        _sanitize_inputs(kwargs)

        source = 'az'
        if _in_ci():
            source = 'CI'
        elif ARGCOMPLETE_ENV_NAME in os.environ:
            source = 'completer'

        types = ['event', 'pageview']
        if log_type not in types:
            raise ValueError('Type {} is not supported.  Available types: {}'.format(log_type,
                                                                                     types))

        profile = Profile()
        props = {}
        _safe_exec(props, 'time', lambda: str(datetime.datetime.now()))
        _safe_exec(props, 'x-ms-client-request-id',
                   lambda: APPLICATION.session['headers']['x-ms-client-request-id'])
        _safe_exec(props, 'command', lambda: APPLICATION.session.get('command', None))
        _safe_exec(props, 'version', lambda: core_version)
        _safe_exec(props, 'source', lambda: source)
        _safe_exec(props, 'installation-id', profile.get_installation_id)
        _safe_exec(props, 'python-version', lambda: _make_safe(str(platform.python_version())))
        _safe_exec(props, 'shell-type', _get_shell_type)
        _safe_exec(props, 'locale', lambda: '{},{}'.format(locale.getdefaultlocale()[0],
                                                           locale.getdefaultlocale()[1]))
        _safe_exec(props, 'user-machine-id', _get_user_machine_id)
        _safe_exec(props, 'user-azure-id', _get_user_azure_id)
        _safe_exec(props, 'azure-subscription-id', _get_azure_subscription_id)

        if kwargs:
            props.update(**kwargs)

        telemetry_records.append({
            'name': name,
            'type': log_type,
            'properties': props
            })
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex

def _safe_exec(props, key, fn):
    try:
        props[key] = fn()
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex

def _get_user_machine_id():
    return hash(platform.node() + getpass.getuser())

def _get_user_azure_id():
    try:
        profile = Profile()
        return hash(profile.get_current_account_user())
    except CLIError:
        pass

def _get_azure_subscription_id():
    try:
        profile = Profile()
        return profile.get_login_credentials()[1]
    except CLIError:
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
        return _make_safe(os.environ.get('SHELL'))

def _sanitize_inputs(d):
    for key, value in d.items():
        if isinstance(value, str):
            d[key] = _remove_quotes(value)
        elif isinstance(value, list):
            d[key] = [_remove_quotes(v) for v in value]
            if next((v for v in value if isinstance(v, list) or isinstance(v, dict)),
                    None) is not None:
                raise ValueError('List object too complex, will fail server-side')
        elif isinstance(value, dict):
            d[key] = {key:_remove_quotes(v) for key, v in value.items()}
            if next((v for v in value.values() if isinstance(v, list) or isinstance(v, dict)),
                    None) is not None:
                raise ValueError('Dict object too complex, will fail server-side')

def _remove_quotes(s):
    if isinstance(s, str):
        return s.replace("'", '_').replace('"', '_')
    return s

def _make_safe(s):
    for c in '$%^&|':
        s = s.replace(c, '_')
    return s

def _in_ci():
    return os.environ.get('CONTINUOUS_INTEGRATION') and os.environ.get('TRAVIS')

def _debugging():
    return _in_ci() or _DEBUG_TELEMETRY in os.environ

def telemetry_flush():
    try:
        client.flush()
        if not telemetry_records:
            return

        subprocess.Popen([sys.executable,
                          os.path.realpath(__file__),
                          _make_safe(json.dumps(telemetry_records))])
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex

def upload_telemetry(data_to_save):
    data_to_save = json.loads(data_to_save.replace("'", '"'))

    for record in data_to_save:
        if record['type'] == 'event':
            client.track_event(record['name'],
                               record['properties'])
        elif record['type'] == 'pageview':
            client.track_pageview(record['name'],
                                  url=record['name'],
                                  properties=record['properties'])
    client.flush()
    if _debugging():
        print('telemetry upload complete')

if __name__ == '__main__':
    try:
        init_telemetry()
        upload_telemetry(sys.argv[1])
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex
