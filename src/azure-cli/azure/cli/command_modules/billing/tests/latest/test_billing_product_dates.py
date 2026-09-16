# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import datetime
from http import HTTPStatus
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from azure.core.exceptions import DecodeError, DeserializationError, HttpResponseError, ServiceRequestError
from azure.core.paging import ItemPaged
from azure.core.pipeline.policies import SansIOHTTPPolicy
from azure.core.pipeline.transport import HttpResponse, HttpTransport
from azure.mgmt.billing import BillingManagementClient
from azure.mgmt.billing.models import Product
from azure.cli.command_modules.billing import BillingCommandsLoader
from azure.cli.command_modules.billing.custom import billing_product_list, billing_product_show
from azure.cli.core.mock import DummyCli
from azure.cli.core.util import todict
from knack.output import format_json
from knack.util import CommandResultItem
from msrest.serialization import Deserializer


_ACCOUNT = 'test-account'
_PROFILE = 'test-profile'
_ACCOUNT_PATH = '/providers/Microsoft.Billing/billingAccounts/' + _ACCOUNT
_PROFILE_PATH = _ACCOUNT_PATH + '/billingProfiles/' + _PROFILE
_NEXT_LINK = 'https://management.azure.com' + _PROFILE_PATH + '/products?api-version=2020-05-01&$skip=1'
_DATE_FIELDS = ('purchaseDate', 'endDate', 'lastChargeDate')


def _product(name='test-product', **dates):
    properties = {
        'displayName': 'Product purchased 12/02/2024',
        'productType': 'Reservation',
        'productTypeId': 'test-type',
        'status': 'Active',
        'autoRenew': 'On',
        'billingFrequency': 'Monthly',
        'quantity': 2,
        'lastCharge': {'currency': 'USD', 'value': 10.5},
        'skuId': 'test-sku',
        'skuDescription': '09/17/2025',
        'billingProfileId': _PROFILE_PATH,
        'billingProfileDisplayName': 'Test profile',
    }
    properties.update(dates)
    return {
        'id': _ACCOUNT_PATH + '/products/' + name,
        'name': name,
        'type': 'Microsoft.Billing/billingAccounts/products',
        'properties': properties,
    }


class _JsonResponse(HttpResponse):
    def __init__(self, request, payload, status_code, encoding):
        super().__init__(request, None)
        self.status_code = status_code
        self.reason = HTTPStatus(status_code).phrase
        self.content_type = 'application/json; charset=' + encoding
        self.headers = {'content-type': self.content_type}
        self._encoding = encoding
        self._body = payload if isinstance(payload, bytes) else json.dumps(payload).encode(encoding)

    def body(self):
        return self._body

    def text(self, encoding=None):
        return super().text(encoding or self._encoding)


class BillingProductDateTests(unittest.TestCase):
    def _client(self, *pages, status_codes=None, encoding='utf-8'):
        status_codes = status_codes or [200] * len(pages)
        self.assertEqual(len(pages), len(status_codes))
        responses = iter(zip(pages, status_codes))

        def send(request, **_kwargs):
            payload, status_code = next(responses)
            return _JsonResponse(request, payload, status_code, encoding)

        transport = mock.MagicMock(spec=HttpTransport)
        transport.send.side_effect = send
        client = BillingManagementClient(
            credential=object(),
            subscription_id='<subscription>',
            authentication_policy=SansIOHTTPPolicy(),
            transport=transport,
            retry_total=0,
        )
        self.addCleanup(client.close)
        return client, transport

    @staticmethod
    def _json(pager):
        return json.loads(format_json(CommandResultItem(todict(list(pager)))))

    @staticmethod
    def _registered_list(client, **kwargs):
        loader = BillingCommandsLoader(DummyCli())
        command = loader.load_command_table(None)['billing product list']
        with mock.patch(
                'azure.cli.command_modules.billing.generated._client_factory.cf_billing_cl',
                return_value=client):
            return command({'cmd': command, 'account_name': _ACCOUNT, **kwargs})

    @staticmethod
    def _invoke_profile_list(client):
        output = io.StringIO()
        errors = io.StringIO()
        with tempfile.TemporaryDirectory() as config_dir, \
                mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': config_dir}), \
                mock.patch(
                    'azure.cli.command_modules.billing.generated._client_factory.cf_billing_cl',
                    return_value=client), \
                redirect_stderr(errors):
            cli = DummyCli()
            exit_code = cli.invoke([
                'billing', 'product', 'list',
                '--account-name', _ACCOUNT,
                '--profile-name', _PROFILE,
                '--output', 'json',
                '--only-show-errors',
            ], out_file=output)
        return exit_code, output.getvalue(), errors.getvalue()

    def test_unadapted_sdk_reproduces_lazy_deserialization_failure(self):
        client, transport = self._client({
            'value': [_product(purchaseDate='12/02/2024', endDate='10/01/2026')],
        })
        pager = client.products.list_by_billing_profile(_ACCOUNT, _PROFILE)
        self.assertIsInstance(pager, ItemPaged)
        transport.send.assert_not_called()
        with self.assertRaises(DeserializationError):
            list(pager)
        self.assertEqual(transport.send.call_count, 1)

    def test_product_list_uses_handwritten_override(self):
        self.assertEqual(billing_product_list.__module__, 'azure.cli.command_modules.billing.manual.custom')

    def test_profile_command_serializes_all_pages_and_preserves_fields(self):
        first = _product('first-product', purchaseDate='2024-01-02T03:04:05Z')
        second = _product('second-product', purchaseDate='12/02/2024', endDate='10/01/2026')
        client, transport = self._client(
            {'value': [first], 'nextLink': _NEXT_LINK},
            {'value': [second]},
        )
        exit_code, text, errors = self._invoke_profile_list(client)
        self.assertEqual(exit_code, 0, errors)
        products = json.loads(text)
        self.assertEqual([item['name'] for item in products], ['first-product', 'second-product'])
        self.assertEqual(products[0]['purchaseDate'], '2024-01-02T03:04:05+00:00')
        self.assertEqual(products[1]['purchaseDate'], '2024-12-02T00:00:00')
        self.assertEqual(products[1]['endDate'], '2026-10-01T00:00:00')
        self.assertIsNone(products[1]['lastChargeDate'])
        for field, value in second['properties'].items():
            if field not in _DATE_FIELDS:
                self.assertEqual(products[1][field], value)
        for field in ('id', 'name', 'type'):
            self.assertEqual(products[1][field], second[field])
        self.assertNotIn('properties', products[1])
        self.assertEqual(transport.send.call_count, 2)
        self.assertEqual(transport.send.call_args_list[1].args[0].url, _NEXT_LINK)

    def test_month_day_semantics_for_each_product_date_field(self):
        cases = (
            ('12/02/2024', datetime(2024, 12, 2)),
            ('09/17/2025', datetime(2025, 9, 17)),
            ('10/13/2025', datetime(2025, 10, 13)),
            ('10/01/2026', datetime(2026, 10, 1)),
            ('02/29/2024', datetime(2024, 2, 29)),
        )
        attributes = ('purchase_date', 'end_date', 'last_charge_date')
        for field, attribute in zip(_DATE_FIELDS, attributes):
            for value, expected in cases:
                with self.subTest(field=field, value=value):
                    client, _ = self._client({'value': [_product(**{field: value})]})
                    products = list(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))
                    self.assertIsInstance(products[0], Product)
                    self.assertEqual(getattr(products[0], attribute), expected)
                    self.assertEqual(self._json(products)[0][field], expected.isoformat())

    def test_mixed_iso_offsets_and_fractional_seconds_remain_unchanged(self):
        dates = {
            'purchaseDate': '2024-12-02T14:05:06.1234567+05:30',
            'endDate': '2026-10-01T02:03:04.000123-07:00',
            'lastChargeDate': '2025-09-17T07:08:09Z',
        }
        page = {'value': [_product('iso-product', **dates), _product('slash-product', purchaseDate='09/17/2025')]}
        client, _ = self._client(page)
        products = self._json(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))
        expected = {
            'purchaseDate': '2024-12-02T14:05:06.123456+05:30',
            'endDate': '2026-10-01T02:03:04.000123-07:00',
            'lastChargeDate': '2025-09-17T07:08:09+00:00',
        }
        for field, value in expected.items():
            self.assertEqual(products[0][field], value)
        self.assertEqual(products[1]['purchaseDate'], '2025-09-17T00:00:00')
        raw_client, _ = self._client({'value': [_product('iso-product', **dates)]})
        self.assertEqual(products[0], self._json(raw_client.products.list_by_billing_profile(_ACCOUNT, _PROFILE))[0])

    def test_null_and_missing_optional_dates(self):
        missing_properties = {'id': 'test-id', 'name': 'missing-properties'}
        null_properties = {'id': 'test-id', 'name': 'null-properties', 'properties': None}
        client, _ = self._client({
            'value': [
                _product('missing-dates'),
                _product('null-dates', purchaseDate=None, endDate=None, lastChargeDate=None),
                missing_properties,
                null_properties,
            ],
        })
        products = self._json(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))
        self.assertEqual(len(products), 4)
        for product in products:
            for field in _DATE_FIELDS:
                self.assertIsNone(product[field])

    def test_empty_list(self):
        client, transport = self._client({'value': []})
        self.assertEqual(self._json(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE)), [])
        self.assertEqual(transport.send.call_count, 1)

    def test_empty_page_still_follows_next_link(self):
        client, transport = self._client(
            {'value': [], 'nextLink': _NEXT_LINK},
            {'value': [_product(purchaseDate='12/02/2024')], 'nextLink': None},
        )
        products = self._json(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))
        self.assertEqual([item['name'] for item in products], ['test-product'])
        self.assertEqual(transport.send.call_count, 2)

    def test_invalid_dates_are_not_guessed_or_discarded(self):
        for field in _DATE_FIELDS:
            for value in (
                    '02/30/2024', '02/29/2025', '13/01/2024', '17/09/2025',
                    '00/12/2024', '12/00/2024', '12/02/0000', 'not-a-date',
                    '12/02/2024junk', ' 12/02/2024', '12/2/2024', 2024):
                with self.subTest(field=field, value=value):
                    client, _ = self._client({'value': [_product(**{field: value})]})
                    with self.assertRaises(DeserializationError):
                        list(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))

    def test_invalid_date_on_later_page_propagates(self):
        client, transport = self._client(
            {'value': [_product('first-product', purchaseDate='2024-01-02T00:00:00Z')], 'nextLink': _NEXT_LINK},
            {'value': [_product('invalid-product', purchaseDate='02/30/2024')]},
        )
        pager = billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE)
        self.assertEqual(next(pager).name, 'first-product')
        with self.assertRaises(DeserializationError):
            list(pager)
        self.assertEqual(transport.send.call_count, 2)

    def test_malformed_json_on_later_page_propagates(self):
        client, transport = self._client(
            {'value': [_product(purchaseDate='12/02/2024')], 'nextLink': _NEXT_LINK},
            b'{"value": [',
        )
        pager = billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE)
        self.assertEqual(next(pager).name, 'test-product')
        with self.assertRaises(DecodeError):
            list(pager)
        self.assertEqual(transport.send.call_count, 2)

    def test_later_invalid_date_does_not_emit_partial_cli_json(self):
        client, transport = self._client(
            {'value': [_product('first-product', purchaseDate='2024-01-02T00:00:00Z')], 'nextLink': _NEXT_LINK},
            {'value': [_product('invalid-product', purchaseDate='02/30/2024')]},
        )
        exit_code, output, _ = self._invoke_profile_list(client)
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(output, '')
        self.assertEqual(transport.send.call_count, 2)

    def test_later_http_error_does_not_emit_partial_cli_json(self):
        client, transport = self._client(
            {'value': [_product('first-product', purchaseDate='12/02/2024')], 'nextLink': _NEXT_LINK},
            {'error': {'code': 'InvalidRequest', 'message': 'Synthetic continuation failure'}},
            status_codes=[200, 400],
        )
        with self.assertLogs('cli.azure.cli.core.azclierror', level='ERROR') as logs:
            exit_code, output, _ = self._invoke_profile_list(client)
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(output, '')
        self.assertIn('Synthetic continuation failure', '\n'.join(logs.output))
        self.assertEqual(transport.send.call_count, 2)

    def test_http_errors_propagate_on_first_and_later_pages(self):
        error = {'error': {'code': 'SyntheticServiceError', 'message': 'Synthetic service failure'}}
        for status_code in (400, 404, 409, 503):
            for first_page in (True, False):
                with self.subTest(status_code=status_code, first_page=first_page):
                    pages = [error] if first_page else [
                        {'value': [_product(purchaseDate='12/02/2024')], 'nextLink': _NEXT_LINK},
                        error,
                    ]
                    statuses = [status_code] if first_page else [200, status_code]
                    client, transport = self._client(*pages, status_codes=statuses)
                    with self.assertRaises(HttpResponseError) as caught:
                        list(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))
                    self.assertEqual(caught.exception.status_code, status_code)
                    self.assertIn('Synthetic service failure', str(caught.exception))
                    self.assertEqual(transport.send.call_count, len(pages))

    def test_encoded_response_and_service_error(self):
        client, transport = self._client(
            {'value': [_product(purchaseDate='12/02/2024')], 'nextLink': _NEXT_LINK},
            {'error': {'code': 'InvalidRequest', 'message': 'Synthetic encoded failure'}},
            status_codes=[200, 400],
            encoding='utf-16',
        )
        pager = billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE)
        self.assertEqual(next(pager).purchase_date, datetime(2024, 12, 2))
        with self.assertRaisesRegex(HttpResponseError, 'Synthetic encoded failure'):
            list(pager)
        self.assertEqual(transport.send.call_count, 2)

    def test_later_transport_error_propagates(self):
        client, transport = self._client(
            {'value': [_product(purchaseDate='12/02/2024')], 'nextLink': _NEXT_LINK},
        )
        pager = billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE)
        self.assertEqual(next(pager).name, 'test-product')
        transport.send.side_effect = ServiceRequestError('Synthetic transport failure')
        with self.assertRaisesRegex(ServiceRequestError, 'Synthetic transport failure'):
            list(pager)

    def test_registered_list_preserves_routing_and_filters(self):
        filter_value = "productType eq 'Reservation'"
        routes = (
            ({}, _ACCOUNT_PATH, True),
            ({'profile_name': _PROFILE}, _PROFILE_PATH, True),
            ({'profile_name': _PROFILE, 'invoice_section_name': 'test-section'},
             _PROFILE_PATH + '/invoiceSections/test-section', True),
            ({'customer_name': 'test-customer'}, _ACCOUNT_PATH + '/customers/test-customer', False),
            ({'profile_name': _PROFILE, 'customer_name': 'test-customer'}, _PROFILE_PATH, True),
        )
        for arguments, path, accepts_filter in routes:
            with self.subTest(arguments=arguments):
                next_link = 'https://management.azure.com' + path + '/products?api-version=2020-05-01&$skip=1'
                client, transport = self._client(
                    {'value': [_product('first-product', purchaseDate='2024-01-02T00:00:00Z')],
                     'nextLink': next_link},
                    {'value': [_product('second-product', purchaseDate='12/02/2024')]},
                )
                pager = self._registered_list(client, filter_=filter_value, **arguments)
                self.assertIsInstance(pager, ItemPaged)
                transport.send.assert_not_called()
                products = self._json(pager)
                self.assertEqual([item['name'] for item in products], ['first-product', 'second-product'])
                self.assertEqual(products[1]['purchaseDate'], '2024-12-02T00:00:00')
                self.assertEqual(transport.send.call_count, 2)
                self.assertEqual(transport.send.call_args_list[1].args[0].url, next_link)
                request = transport.send.call_args_list[0].args[0]
                parsed = urlsplit(request.url)
                self.assertEqual(request.method, 'GET')
                self.assertEqual(parsed.path, path + '/products')
                expected_query = {'api-version': ['2020-05-01']}
                if accepts_filter:
                    expected_query['$filter'] = [filter_value]
                self.assertEqual(parse_qs(parsed.query), expected_query)

    def test_product_show_and_shared_deserializer_are_unaffected(self):
        original_map = copy.deepcopy(Product._attribute_map)
        client, _ = self._client(
            {'value': [_product(purchaseDate='12/02/2024')]},
            _product(purchaseDate='2024-12-02T00:00:00Z'),
            _product(purchaseDate='12/02/2024'),
        )
        original_deserializer = client.products._deserialize
        list(billing_product_list(client.products, _ACCOUNT, profile_name=_PROFILE))
        product = billing_product_show(client.products, _ACCOUNT, 'test-product')
        self.assertEqual(todict(product)['purchaseDate'], '2024-12-02T00:00:00+00:00')
        with self.assertRaises(DeserializationError):
            billing_product_show(client.products, _ACCOUNT, 'test-product')
        with self.assertRaises(DeserializationError):
            Deserializer.deserialize_iso('12/02/2024')
        self.assertEqual(Product._attribute_map, original_map)
        self.assertIs(client.products._deserialize, original_deserializer)
