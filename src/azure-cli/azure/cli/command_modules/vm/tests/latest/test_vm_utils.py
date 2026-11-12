# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from urllib.parse import parse_qs, unquote, urlencode, urlparse

from azure.core import PipelineClient
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.command_modules.vm._vm_utils import list_sku_info
from azure.cli.command_modules.vm.aaz.latest.vm import ListSkus
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.mock import DummyCli


class TestListSkuInfo(unittest.TestCase):

    def setUp(self):
        self.cli_ctx = mock.MagicMock()
        patcher = mock.patch('azure.cli.command_modules.vm.aaz.latest.vm.ListSkus')
        self.list_skus_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.list_skus = self.list_skus_cls.return_value
        self.skus = [
            {'name': 'Standard_D2s_v5', 'locations': ['eastus']},
            {'name': 'Standard_D4s_v5', 'locations': ['westus', 'EastUS']},
            {'name': 'Standard_D8s_v5', 'locations': ['westus']},
        ]
        self.list_skus.return_value = self.skus

    def test_location_filter(self):
        for location in ('eastus', 'EastUS', 'EASTUS'):
            with self.subTest(location=location):
                self.list_skus_cls.reset_mock()
                result = list_sku_info(self.cli_ctx, location)

                self.list_skus_cls.assert_called_once_with(cli_ctx=self.cli_ctx)
                self.list_skus.assert_called_once_with(command_args={'filter': "location eq 'eastus'"})
                self.assertEqual(result, self.skus[:2])

    def test_no_location(self):
        for location in (None, ''):
            with self.subTest(location=location):
                self.list_skus_cls.reset_mock()
                result = list_sku_info(self.cli_ctx, location)

                self.list_skus_cls.assert_called_once_with(cli_ctx=self.cli_ctx)
                self.list_skus.assert_called_once_with(command_args={})
                self.assertEqual(result, self.skus)

    def test_no_matching_location(self):
        self.assertEqual(list_sku_info(self.cli_ctx, 'centralus'), [])
        self.list_skus.assert_called_once_with(command_args={'filter': "location eq 'centralus'"})

    def test_empty_response(self):
        self.list_skus.return_value = []

        self.assertEqual(list_sku_info(self.cli_ctx, 'eastus'), [])

    def test_request_error_propagates(self):
        self.list_skus.side_effect = RuntimeError('SKU request failed')

        with self.assertRaisesRegex(RuntimeError, 'SKU request failed'):
            list_sku_info(self.cli_ctx, 'eastus')

    def test_restrictions_preserved(self):
        self.skus[0]['restrictions'] = [{
            'type': 'Location',
            'reasonCode': 'NotAvailableForSubscription',
            'values': ['eastus'],
        }]

        result = list_sku_info(self.cli_ctx, 'eastus')

        self.assertEqual(result, self.skus[:2])
        self.assertEqual(result[0]['restrictions'], self.skus[0]['restrictions'])

    def test_location_literal_escaped(self):
        list_sku_info(self.cli_ctx, "eastus' or location eq 'westus")

        self.list_skus.assert_called_once_with(command_args={
            'filter': "location eq 'eastus'' or location eq ''westus'",
        })

    def test_filter_serialized_as_query_parameter(self):
        list_sku_info(self.cli_ctx, 'eastus')
        command_args = self.list_skus.call_args.kwargs['command_args']
        with mock.patch('azure.cli.core.aaz._command_ctx.Profile'):
            ctx = AAZCommandCtx(
                cli_ctx=self.cli_ctx,
                schema=ListSkus.get_arguments_schema(),
                command_args=command_args,
            )
        with mock.patch.object(ctx, 'get_http_client'):
            operation = ListSkus.ResourceSkusList(ctx)

        self.assertEqual(unquote(operation.query_parameters['$filter']), "location eq 'eastus'")


class TestListSkuInfoRequests(unittest.TestCase):

    def test_paginated_requests(self):
        subscription_id = '00000000-0000-0000-0000-000000000000'
        endpoint = 'https://management.azure.com'
        path = '/subscriptions/{}/providers/Microsoft.Compute/skus'.format(subscription_id)
        skus = [
            {'name': 'Standard_D2s_v5', 'locations': ['eastus']},
            {'name': 'Standard_D4s_v5', 'locations': ['eastus']},
        ]
        cli_ctx = DummyCli()

        for location in (None, 'eastus'):
            with self.subTest(location=location):
                query = {'api-version': '2019-04-01'}
                if location:
                    query['$filter'] = "location eq 'eastus'"
                next_query = dict(query, **{'$skiptoken': 'next-page'})
                pages = [
                    {'value': skus[:1], 'nextLink': endpoint + path + '?' + urlencode(next_query)},
                    {'value': skus[1:]},
                ]
                sessions = []
                for page in pages:
                    session = mock.Mock()
                    session.http_response.status_code = 200
                    session.context = {ContentDecodePolicy.CONTEXT_NAME: page}
                    sessions.append(session)

                with PipelineClient(base_url=endpoint) as client, \
                        mock.patch.object(client, 'send_request', side_effect=sessions) as send_request, \
                        mock.patch.object(AAZCommandCtx, 'get_http_client', return_value=client), \
                        mock.patch.object(AAZCommandCtx, 'subscription_id',
                                          new_callable=mock.PropertyMock, return_value=subscription_id):
                    result = list(list_sku_info(cli_ctx, location))

                self.assertEqual(result, skus)
                self.assertEqual(send_request.call_count, 2)
                for call, expected_query in zip(send_request.call_args_list, (query, next_query)):
                    request = call.kwargs['request']
                    self.assertEqual(request.method, 'GET')
                    self.assertEqual(urlparse(request.url).path, path)
                    self.assertEqual(parse_qs(urlparse(request.url).query),
                                     {key: [value] for key, value in expected_query.items()})
