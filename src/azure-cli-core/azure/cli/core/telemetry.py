#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
from __future__ import print_function
import getpass
import time
import subprocess
import json
import os
import sys

from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable
from azure.cli.core import __version__ as core_version

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
        client.context.user.id = hash(getpass.getuser())

        enable(instrumentation_key)
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex

def user_agrees_to_telemetry():
    # TODO: agreement, needs to take Y/N from the command line
    # and needs a "skip" param to not show (for scripts)
    return True

def log_event(event_name, **kwargs):
    """
    IMPORTANT: do not log events with quotes in the name, properties or measurements;
    those events may fail to upload.  Also, telemetry events must be verified in
    the backend because successful upload does not guarentee success.
    """
    try:
        event_name = _remove_quotes(event_name)
        _sanitize_inputs(kwargs)

        source = 'az'
        if _in_ci():
            source = 'CI'
        elif ARGCOMPLETE_ENV_NAME in os.environ:
            source = 'completer'

        props = {
            'time': str(time.time()),
            'x-ms-client-request-id': APPLICATION.session['headers']['x-ms-client-request-id'],
            'command': APPLICATION.session.get('command', None),
            'version': core_version,
            'source': source
            }

        if kwargs:
            props.update(**kwargs)

        telemetry_records.append({
            'name': event_name,
            'properties': props
            })
    except Exception as ex: #pylint: disable=broad-except
        # Never fail the command because of telemetry, unless debugging
        if _debugging():
            raise ex

def _sanitize_inputs(kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = _remove_quotes(value)
        elif isinstance(value, list):
            kwargs[key] = [_remove_quotes(v) for v in value]
            if next((v for v in value if isinstance(v, list) or isinstance(v, dict)),
                    None) is not None:
                raise ValueError('List object too complex, will fail server-side')
        elif isinstance(value, dict):
            kwargs[key] = {key:_remove_quotes(v) for key, v in value.items()}
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
        client.track_event(record['name'],
                           record['properties'])
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
