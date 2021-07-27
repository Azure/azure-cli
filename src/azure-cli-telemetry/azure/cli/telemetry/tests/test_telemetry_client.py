# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from unittest import mock
import os
import unittest

from applicationinsights.channel import SynchronousSender

try:
    # Python 2.x
    import urllib2 as http_client_t
    from urllib2 import HTTPError
except ImportError:
    # Python 3.x
    import urllib.request as http_client_t
    from urllib.error import HTTPError

from azure.cli.telemetry.components.telemetry_client import (CliTelemetryClient, _NoRetrySender, http_client_t)

TEST_RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), 'resources')


class _TestSender(SynchronousSender):
    instances = []

    def __init__(self):
        super(_TestSender, self).__init__()
        _TestSender.instances.append(self)

        self.data = []

    def send(self, data_to_send):
        self.data.append(data_to_send)


class TestTelemetryClient(unittest.TestCase):
    def setUp(self):
        # load sample data
        self.sample_records = []
        for f in os.listdir(TEST_RESOURCE_FOLDER):
            with open(os.path.join(TEST_RESOURCE_FOLDER, f), mode='r') as fq:
                for line in fq.readlines():
                    self.sample_records.append(line[20:])

        del _TestSender.instances[:]

    def test_telemetry_client_without_flush(self):
        client = CliTelemetryClient(sender=_TestSender)

        self.assertEqual(0, len(_TestSender.instances))

        for r in self.sample_records[:10]:
            client.add(r)

        self.assertEqual(1, len(_TestSender.instances))
        sender = _TestSender.instances[0]

        self.assertEqual(0, len(sender.data))

        # flush is skipped because record collection size is small
        client.flush()
        self.assertEqual(0, len(sender.data))

        # force flush should send data set even it is smaller than the batch threshold
        # there should be 10 envelops in the batch of data
        client.flush(force=True)
        self.assertEqual(1, len(sender.data))
        self.assertEqual(10, len(sender.data[0]))

        # repeat flush should not duplicate data
        client.flush(force=True)
        self.assertEqual(1, len(sender.data))

        # default batch size is 100, ensure data is sent after accumulation
        del sender.data[:]
        count = 0
        for r in self.sample_records:
            client.add(r, flush=True)

            count += 1
            if not count % 100:
                self.assertEqual(1, len(sender.data))
                del sender.data[:]
            else:
                self.assertEqual(0, len(sender.data))


class TestNoRetrySender(unittest.TestCase):
    def setUp(self):
        # build some data in the form of envelops
        del _TestSender.instances[:]
        client = CliTelemetryClient(sender=_TestSender)
        with open(os.path.join(TEST_RESOURCE_FOLDER, 'cache'), mode='r') as fq:
            for line in fq.readlines()[:5]:
                client.add(line[20:], flush=True, force=True)
        self.sample_data = _TestSender.instances[0].data

    def test_limited_retry_sender(self):
        mock_url_open = mock.Mock()

        with mock.patch.object(http_client_t, 'urlopen', mock_url_open):
            sender = _NoRetrySender()
            sender.send(self.sample_data[0])

        mock_url_open.assert_called_once()
        args, kwargs = mock_url_open.call_args

        self.assertEqual(10, kwargs['timeout'])

        data = json.loads(args[0].data.decode('utf-8'))[0]
        self.assertEqual('Microsoft.ApplicationInsights.Event', data['name'])
        self.assertEqual('UserTask', data['data']['baseData']['properties']['Reserved.DataModel.EntityType'])
        self.assertEqual('azurecli', data['data']['baseData']['properties']['Reserved.DataModel.ProductName'])

    def test_limited_retry_sender_http_error(self):
        mock_url_open = mock.Mock()
        mock_url_open.side_effect = HTTPError('', 500, 'expected', [], None)

        with mock.patch.object(http_client_t, 'urlopen', mock_url_open):
            sender = _NoRetrySender()
            sender.send(self.sample_data[0])

        mock_url_open.assert_called_once()
        args, kwargs = mock_url_open.call_args

        self.assertEqual(10, kwargs['timeout'])

        data = json.loads(args[0].data.decode('utf-8'))[0]
        self.assertEqual('Microsoft.ApplicationInsights.Event', data['name'])
        self.assertEqual('UserTask', data['data']['baseData']['properties']['Reserved.DataModel.EntityType'])
        self.assertEqual('azurecli', data['data']['baseData']['properties']['Reserved.DataModel.ProductName'])

    def test_limited_retry_sender_os_error(self):
        mock_url_open = mock.Mock()
        mock_url_open.side_effect = OSError('error')

        with mock.patch.object(http_client_t, 'urlopen', mock_url_open):
            sender = _NoRetrySender()
            sender.send(self.sample_data[0])

        mock_url_open.assert_called_once()

    def test_limited_retry_sender_other_exception(self):
        mock_url_open = mock.Mock()
        mock_url_open.side_effect = ValueError('error')

        with mock.patch.object(http_client_t, 'urlopen', mock_url_open):
            sender = _NoRetrySender()
            sender.send(self.sample_data[0])

        mock_url_open.assert_called_once()


if __name__ == '__main__':
    unittest.main()
