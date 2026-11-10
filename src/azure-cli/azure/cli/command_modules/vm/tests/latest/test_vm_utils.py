# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from urllib.parse import unquote

from azure.cli.command_modules.vm._vm_utils import list_sku_info
from azure.cli.command_modules.vm.aaz.latest.vm import ListSkus
from azure.cli.core.aaz._command_ctx import AAZCommandCtx


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
                result = list_sku_info(self.cli_ctx, location)

                self.list_skus_cls.assert_called_with(cli_ctx=self.cli_ctx)
                self.list_skus.assert_called_with(command_args={'filter': "location eq 'eastus'"})
                self.assertEqual(result, self.skus[:2])

    def test_no_location(self):
        for location in (None, ''):
            with self.subTest(location=location):
                result = list_sku_info(self.cli_ctx, location)

                self.list_skus.assert_called_with(command_args={})
                self.assertEqual(result, self.skus)

    def test_no_matching_location(self):
        self.assertEqual(list_sku_info(self.cli_ctx, 'centralus'), [])
        self.list_skus.assert_called_once_with(command_args={'filter': "location eq 'centralus'"})

    def test_empty_response(self):
        self.list_skus.return_value = []

        self.assertEqual(list_sku_info(self.cli_ctx, 'eastus'), [])

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
