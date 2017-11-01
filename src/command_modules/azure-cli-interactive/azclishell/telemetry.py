# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import subprocess
import sys
import os
import json
from six.moves._thread import start_new_thread

from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable

from azclishell import __version__

from azure.cli.core._profile import Profile
from azure.cli.core.telemetry import _user_agrees_to_telemetry
from azclishell.util import parse_quotes

INSTRUMENTATION_KEY = '762871d5-45a2-4d67-bf47-e396caf53d9d'


def set_custom_properties(prop, name, value):
    actual_value = value() if hasattr(value, '__call__') else value
    if actual_value:
        prop['Context.Default.AzureCLI.' + name] = actual_value


class Telemetry(TelemetryClient):
    """ base telemetry sessions """

    def __init__(self, cli_ctx):
        super(Telemetry, self).__init__(INSTRUMENTATION_KEY, None)
        self.start_time = None
        self.end_time = None
        enable(INSTRUMENTATION_KEY)
        # adding context
        self.context.application.id = 'Azure CLI Shell'
        self.context.application.ver = __version__
        self.context.user.id = Profile(cli_ctx).get_installation_id()
        self.context.instrumentation_key = INSTRUMENTATION_KEY

    def _track_event(self, name, properties=None, measurements=None):
        """ tracks the telemetry events and pushes them out """
        self.track_event(name, properties, measurements)
        start_new_thread(self.flush, ())

    @_user_agrees_to_telemetry
    def track_ssg(self, gesture, cmd):
        """ track shell specific gestures """
        self._track_event('az/interactive/gesture', {gesture: scrub(cmd)})

    @_user_agrees_to_telemetry
    def track_key(self, key):
        """ tracks the special key bindings """
        self._track_event('az/interactive/key/{}'.format(key))

    @_user_agrees_to_telemetry
    def start(self):
        """ starts recording stuff """
        self.start_time = str(datetime.datetime.now())

    @_user_agrees_to_telemetry
    def conclude(self):
        """ concludings recording stuff """
        self.end_time = str(datetime.datetime.now())
        properties = {}
        set_custom_properties(properties, 'starttime', str(self.start_time))
        set_custom_properties(properties, 'endtime', str(self.end_time))

        subprocess.Popen([
            sys.executable,
            os.path.realpath(__file__),
            json.dumps(properties)])


def scrub(text):
    """ scrubs the parameter values from args """
    args = parse_quotes(text)
    next_scrub = False
    values = []
    for arg in args:
        if arg.startswith('-'):
            next_scrub = True
            values.append(arg)
        elif next_scrub:
            values.append('*****')
        else:
            values.append(arg)
    return ' '.join(values)


# TODO: restore this wonky telemetry thing...
# if __name__ == '__main__':
#    # If user doesn't agree to upload telemetry, this scripts won't be executed. The caller should control.
#    SHELL_TELEMETRY.track_event('az/interactive/run', json.loads(sys.argv[1]))
#    SHELL_TELEMETRY.flush()
