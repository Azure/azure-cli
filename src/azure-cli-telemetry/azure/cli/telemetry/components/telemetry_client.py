# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import datetime

from applicationinsights import TelemetryClient
from applicationinsights.channel import SynchronousSender, SynchronousQueue, TelemetryChannel

try:
    # Python 2.x
    import urllib2 as http_client_t
    from urllib2 import HTTPError
except ImportError:
    # Python 3.x
    import urllib.request as http_client_t
    from urllib.error import HTTPError


class CliTelemetryClient:
    def __init__(self, batch=100, sender=None):
        from azure.cli.telemetry.components.telemetry_logging import get_logger

        self._clients = dict()
        self._counter = 0
        self._batch = batch
        self._sender = sender or _NoRetrySender
        self._logger = get_logger('client')

    def add(self, raw, flush=False, force=False):
        data = self._parse_in_json(raw)
        if not data:
            return

        for instrumentation_key, records in data.items():
            client = self._get_telemetry_client(instrumentation_key)
            if not client:
                continue

            for record in records:
                name = record.get('name')
                if not name:
                    continue

                raw_properties = record.get('properties', {})
                properties = {}
                measurements = {}
                for k, v in raw_properties.items():
                    if isinstance(v, str):
                        properties[k] = v
                    else:
                        measurements[k] = v
                client.track_event(name, properties, measurements)
                self._counter += 1

        if flush:
            self.flush(force=force)

    def flush(self, force=False):
        if force or self._counter >= self._batch:
            self._logger.info('Accumulated %d events. Flush the clients.', self._counter)
            for instrumentation_key, client in self._clients.items():
                self._logger.info('Flush client %s.', instrumentation_key)
                client.flush()
            self._counter = 0

    def _parse_in_json(self, data):
        try:
            return json.loads(data.replace("'", '"'))
        except (json.JSONDecodeError, TypeError) as err:
            self._logger.debug('Fail to parse data %s to JSON. Reason %s.', data, err)
        except Exception as err:  # pylint: disable=broad-except
            self._logger.debug('Fail to parse data %s to JSON. Unexpected reason %s.', data, err)

    def _get_telemetry_client(self, instrumentation_key):
        if not instrumentation_key:
            return None

        if instrumentation_key not in self._clients:
            # In the original implementation there is a line of code enable the exception hook. Removed.
            # enable(instrumentation_key)

            channel = TelemetryChannel(queue=SynchronousQueue(self._sender()))
            client = TelemetryClient(instrumentation_key=instrumentation_key, telemetry_channel=channel)
            self._clients[instrumentation_key] = client

        return self._clients[instrumentation_key]


class _NoRetrySender(SynchronousSender):
    def __init__(self):
        from azure.cli.telemetry.components.telemetry_logging import get_logger

        super(_NoRetrySender, self).__init__()
        self._logger = get_logger('sender')

    def send(self, data_to_send):
        """ Override the default resend mechanism in SenderBase. Stop resend when it fails."""
        request_payload = json.dumps([a.write() for a in data_to_send])

        content = bytearray(request_payload, 'utf-8')
        begin = datetime.datetime.now()
        request = http_client_t.Request(self._service_endpoint_uri, content,
                                        {'Accept': 'application/json',
                                         'Content-Type': 'application/json; charset=utf-8'})
        try:
            http_client_t.urlopen(request, timeout=10)
            self._logger.info('Sending %d bytes', len(content))
        except HTTPError as e:
            self._logger.error('Upload failed. HTTPError: %s', e)
        except OSError as e:  # socket timeout
            # stop retry during socket timeout
            self._logger.error('Upload failed. OSError: %s', e)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.error('Unexpected exception: %s', e)
        finally:
            self._logger.info('Finish uploading in %f seconds.', (datetime.datetime.now() - begin).total_seconds())
