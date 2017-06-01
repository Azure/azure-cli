# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import datetime
import threading

from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable

from azclishell import __version__

from azure.cli.core._profile import Profile
from azure.cli.core.telemetry import _user_agrees_to_telemetry
from azclishell.util import parse_quotes

INSTRUMENTATION_KEY = '762871d5-45a2-4d67-bf47-e396caf53d9d'


def my_context(tel_client):
    """ context for the application """
    tel_client.context.application.id = 'Azure CLI Shell'
    tel_client.context.application.ver = __version__
    tel_client.context.user.id = Profile().get_installation_id()
    tel_client.context.instrumentation_key = INSTRUMENTATION_KEY


class Telemetry(TelemetryClient):
    """ base telemetry sessions """

    start_time = None
    end_time = None

    @_user_agrees_to_telemetry
    def track_ssg(self, gesture, cmd):
        """ track shell specific gestures """
        self.track_event('az/interactive/gesture', {gesture: scrub(cmd)})
        telthread = TelThread(self.flush)
        telthread.start()

    @_user_agrees_to_telemetry
    def track_key(self, key):
        """ tracks the special key bindings """
        self.track_event('az/interactive/key/{}'.format(key))
        telthread = TelThread(self.flush)
        telthread.start()


    @_user_agrees_to_telemetry
    def start(self):
        """ starts recording stuff """
        self.start_time = str(datetime.datetime.now())

    @_user_agrees_to_telemetry
    def conclude(self):
        """ concludings recording stuff """
        self.end_time = str(datetime.datetime.now())
        self.track_event('Run', {'StartTime': str(self.start_time),
                                 'EndTime': str(self.end_time)})
        telthread = TelThread(self.flush)
        telthread.start()


class TelThread(threading.Thread):
    """ telemetry thread for exiting """
    def __init__(self, threadfunc):
        threading.Thread.__init__(self)
        self.threadfunc = threadfunc

    def run(self):
        try:
            self.threadfunc()
        except KeyboardInterrupt:
            pass


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


TC = Telemetry(INSTRUMENTATION_KEY)
enable(INSTRUMENTATION_KEY)
my_context(TC)
