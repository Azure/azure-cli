# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    # Python 2.x
    import urllib2 as HTTPClient
    from urllib2 import HTTPError
except ImportError:
    # Python 3.x
    import urllib.request as HTTPClient
    from urllib.error import HTTPError

import os
import sys
import json
import six

from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable
from applicationinsights.channel import SynchronousSender, SynchronousQueue, TelemetryChannel

import azure.cli.core.decorators as decorators

DIAGNOSTICS_TELEMETRY_ENV_NAME = 'AZURE_CLI_DIAGNOSTICS_TELEMETRY'


class LimitedRetrySender(SynchronousSender):
    def __init__(self):
        super(LimitedRetrySender, self).__init__()

    def send(self, data_to_send):
        """ Override the default resend mechanism in SenderBase. Stop resend when it fails."""
        request_payload = json.dumps([a.write() for a in data_to_send])

        request = HTTPClient.Request(self._service_endpoint_uri, bytearray(request_payload, 'utf-8'),
                                     {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8'})
        try:
            HTTPClient.urlopen(request, timeout=10)
        except HTTPError as e:
            if in_diagnostic_mode():
                sys.stdout.write('\nUpload failed. HTTPError: {}\n'.format(e))
        except OSError as e:  # socket timeout
            # stop retry during socket timeout
            if in_diagnostic_mode():
                sys.stdout.write('\nUpload failed. OSError: {}.\n'.format(e))
        except Exception as e:  # pylint: disable=broad-except
            if in_diagnostic_mode():
                sys.stdout.write('\nUnexpected exception: {}\n'.format(e))


def in_diagnostic_mode():
    """
    When the telemetry runs in the diagnostic mode, exception are not suppressed and telemetry
    traces are dumped to the stdout.
    """
    return bool(os.environ.get(DIAGNOSTICS_TELEMETRY_ENV_NAME, False))


@decorators.suppress_all_exceptions(raise_in_diagnostics=True)
def upload(data_to_save):
    if in_diagnostic_mode():
        sys.stdout.write('Telemetry upload begins\n')

    try:
        data_to_save = json.loads(data_to_save.replace("'", '"'))
    except Exception as err:  # pylint: disable=broad-except
        if in_diagnostic_mode():
            sys.stdout.write('ERROR: {}/n'.format(str(err)))
            sys.stdout.write('Raw [{}]/n'.format(data_to_save))

    for instrumentation_key in data_to_save:
        client = TelemetryClient(instrumentation_key=instrumentation_key,
                                 telemetry_channel=TelemetryChannel(queue=SynchronousQueue(LimitedRetrySender())))
        enable(instrumentation_key)

        for record in data_to_save[instrumentation_key]:
            name = record['name']
            raw_properties = record['properties']
            properties = {}
            measurements = {}
            for k, v in raw_properties.items():
                if isinstance(v, six.string_types):
                    properties[k] = v
                else:
                    measurements[k] = v
            client.track_event(record['name'], properties, measurements)

            if in_diagnostic_mode():
                sys.stdout.write(
                    '\nTrack Event: {}\nProperties: {}\nMeasurements: {}'.format(name, json.dumps(properties, indent=2),
                                                                                 json.dumps(measurements, indent=2)))

        client.flush()

    if in_diagnostic_mode():
        sys.stdout.write('\nTelemetry upload completes\n')


if __name__ == '__main__':
    # If user doesn't agree to upload telemetry, this scripts won't be executed. The caller should control.
    decorators.is_diagnostics_mode = in_diagnostic_mode
    upload(sys.argv[1])
