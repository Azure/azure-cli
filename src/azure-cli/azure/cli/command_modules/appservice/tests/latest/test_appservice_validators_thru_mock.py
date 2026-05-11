# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.core.azclierror import ArgumentUsageError

from azure.cli.command_modules.appservice._validators import (
    _normalize_http_headers,
    _normalize_ip_address_list,
    _validate_ip_address_existence,
    _validate_service_tag_existence,
)


class _StubRule:
    """Minimal stand-in for azure.mgmt.web.models.IpSecurityRestriction."""

    def __init__(self, ip_address, headers=None):
        self.ip_address = ip_address
        self.headers = headers


class NormalizeHttpHeadersTest(unittest.TestCase):
    def test_none_and_empty_normalize_equally(self):
        self.assertEqual(_normalize_http_headers(None), {})
        self.assertEqual(_normalize_http_headers([]), {})
        self.assertEqual(_normalize_http_headers({}), {})

    def test_cli_form_lowercases_header_names(self):
        result = _normalize_http_headers(['X-Forwarded-For=10.0.0.1/32'])
        self.assertEqual(result, {'x-forwarded-for': frozenset({'10.0.0.1/32'})})

    def test_cli_form_repeated_names_accumulate(self):
        result = _normalize_http_headers([
            'x-forwarded-for=10.0.0.1/32',
            'x-forwarded-for=10.0.0.2/32',
        ])
        self.assertEqual(result, {'x-forwarded-for': frozenset({'10.0.0.1/32', '10.0.0.2/32'})})

    def test_sdk_form_value_order_insensitive(self):
        a = _normalize_http_headers({'x-forwarded-for': ['10.0.0.1/32', '10.0.0.2/32']})
        b = _normalize_http_headers({'x-forwarded-for': ['10.0.0.2/32', '10.0.0.1/32']})
        self.assertEqual(a, b)

    def test_cli_and_sdk_forms_compare_equal(self):
        cli = _normalize_http_headers([
            'x-forwarded-for=10.0.0.1/32',
            'x-forwarded-for=10.0.0.2/32',
        ])
        sdk = _normalize_http_headers({'x-forwarded-for': ['10.0.0.2/32', '10.0.0.1/32']})
        self.assertEqual(cli, sdk)

    def test_drops_empty_values(self):
        self.assertEqual(_normalize_http_headers(['x-forwarded-for=']), {})
        self.assertEqual(_normalize_http_headers({'x-forwarded-for': [None, '']}), {})

    def test_ignores_malformed_cli_entries_without_equals(self):
        self.assertEqual(_normalize_http_headers(['no-equals-here']), {})


class NormalizeIpAddressListTest(unittest.TestCase):
    def test_empty_inputs(self):
        self.assertEqual(_normalize_ip_address_list(None), frozenset())
        self.assertEqual(_normalize_ip_address_list(''), frozenset())

    def test_single_cidr(self):
        self.assertEqual(
            _normalize_ip_address_list('10.0.0.1/32'),
            frozenset({'10.0.0.1/32'}),
        )

    def test_order_independent(self):
        a = _normalize_ip_address_list('10.0.0.1/32,10.0.0.2/32')
        b = _normalize_ip_address_list('10.0.0.2/32,10.0.0.1/32')
        self.assertEqual(a, b)

    def test_strips_whitespace_around_entries(self):
        self.assertEqual(
            _normalize_ip_address_list('10.0.0.1/32, 10.0.0.2/32'),
            frozenset({'10.0.0.1/32', '10.0.0.2/32'}),
        )


class ValidateIpAddressExistenceTest(unittest.TestCase):
    def _make_namespace(self, ip_address, http_headers=None, scm_site=False):
        ns = mock.MagicMock()
        ns.resource_group_name = 'rg'
        ns.name = 'app'
        ns.slot = None
        ns.scm_site = scm_site
        ns.ip_address = ip_address
        ns.http_headers = http_headers
        return ns

    def _patch_configs(self, rules):
        configs = mock.MagicMock()
        configs.ip_security_restrictions = rules
        configs.scm_ip_security_restrictions = []
        return mock.patch(
            'azure.cli.command_modules.appservice._validators._generic_site_operation',
            return_value=configs,
        )

    def test_blocks_exact_duplicate_no_headers(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace('36.12.195.236/32')
        with self._patch_configs([_StubRule('36.12.195.236/32')]):
            with self.assertRaises(ArgumentUsageError) as ctx:
                _validate_ip_address_existence(cmd, ns)
        msg = str(ctx.exception)
        self.assertIn('already exists', msg)
        self.assertNotIn('HTTP header filter', msg)
        self.assertIn('add a --http-header filter', msg)

    def test_allows_same_ip_with_different_xff(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace(
            '36.12.195.236/32',
            http_headers=['x-forwarded-for=10.0.0.2/32'],
        )
        existing = _StubRule(
            '36.12.195.236/32',
            headers={'x-forwarded-for': ['10.0.0.1/32']},
        )
        with self._patch_configs([existing]):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Different XFF filter should be allowed')

    def test_allows_same_ip_with_headers_vs_no_headers(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace(
            '36.12.195.236/32',
            http_headers=['x-forwarded-for=10.0.0.1/32'],
        )
        with self._patch_configs([_StubRule('36.12.195.236/32', headers=None)]):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Existing rule without headers should not block a header-filtered rule')

    def test_blocks_same_ip_and_identical_headers(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace(
            '36.12.195.236/32',
            http_headers=['x-forwarded-for=10.0.0.1/32'],
        )
        existing = _StubRule(
            '36.12.195.236/32',
            headers={'x-forwarded-for': ['10.0.0.1/32']},
        )
        with self._patch_configs([existing]):
            with self.assertRaises(ArgumentUsageError) as ctx:
                _validate_ip_address_existence(cmd, ns)
        msg = str(ctx.exception)
        self.assertIn('HTTP header filter', msg)
        self.assertIn('vary the --http-header values', msg)

    def test_blocks_when_value_order_differs_for_same_header(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace(
            '36.12.195.236/32',
            http_headers=[
                'x-forwarded-for=10.0.0.2/32',
                'x-forwarded-for=10.0.0.1/32',
            ],
        )
        existing = _StubRule(
            '36.12.195.236/32',
            headers={'x-forwarded-for': ['10.0.0.1/32', '10.0.0.2/32']},
        )
        with self._patch_configs([existing]):
            with self.assertRaises(ArgumentUsageError):
                _validate_ip_address_existence(cmd, ns)

    def test_allows_different_ip(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace('36.12.195.236/32')
        with self._patch_configs([_StubRule('1.2.3.4/32')]):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Different IP should not be blocked')

    def test_handles_none_access_rules(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace('10.0.0.1/32')
        with self._patch_configs(None):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('No existing rules should not raise')

    def test_multi_ip_blocks_when_order_differs_but_set_matches(self):
        """Comma-separated IP lists in a single rule are unordered for ARM purposes."""
        cmd = mock.MagicMock()
        ns = self._make_namespace('10.0.0.2/32,10.0.0.1/32')
        existing = _StubRule('10.0.0.1/32,10.0.0.2/32')
        with self._patch_configs([existing]):
            with self.assertRaises(ArgumentUsageError):
                _validate_ip_address_existence(cmd, ns)

    def test_multi_ip_allows_when_set_differs(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace('10.0.0.1/32,10.0.0.3/32')
        existing = _StubRule('10.0.0.1/32,10.0.0.2/32')
        with self._patch_configs([existing]):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Different IP set should not be blocked')

    def test_scm_path_is_isolated_from_main(self):
        """scm_site=True must inspect scm_ip_security_restrictions only."""
        cmd = mock.MagicMock()
        ns = self._make_namespace('36.12.195.236/32', scm_site=True)
        configs = mock.MagicMock()
        configs.ip_security_restrictions = [_StubRule('36.12.195.236/32')]
        configs.scm_ip_security_restrictions = []
        with mock.patch(
            'azure.cli.command_modules.appservice._validators._generic_site_operation',
            return_value=configs,
        ):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Main-site duplicate must not affect SCM path')

    def test_namespace_without_http_headers_attr(self):
        """Real argparse Namespaces may omit http_headers when not declared."""
        from types import SimpleNamespace
        cmd = mock.MagicMock()
        ns = SimpleNamespace(
            resource_group_name='rg',
            name='app',
            slot=None,
            scm_site=False,
            ip_address='10.0.0.1/32',
        )
        with self._patch_configs([]):
            try:
                _validate_ip_address_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Missing http_headers attribute should be treated as no headers')


class ValidateServiceTagExistenceTest(unittest.TestCase):
    def _make_namespace(self, service_tag, http_headers=None, scm_site=False):
        ns = mock.MagicMock()
        ns.resource_group_name = 'rg'
        ns.name = 'app'
        ns.slot = None
        ns.scm_site = scm_site
        ns.service_tag = service_tag
        ns.http_headers = http_headers
        return ns

    def _patch_configs(self, rules):
        configs = mock.MagicMock()
        configs.ip_security_restrictions = rules
        configs.scm_ip_security_restrictions = []
        return mock.patch(
            'azure.cli.command_modules.appservice._validators._generic_site_operation',
            return_value=configs,
        )

    def test_blocks_exact_duplicate(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace('AzureFrontDoor.Backend')
        with self._patch_configs([_StubRule('AzureFrontDoor.Backend')]):
            with self.assertRaises(ArgumentUsageError):
                _validate_service_tag_existence(cmd, ns)

    def test_allows_same_tag_with_different_fdid(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace(
            'AzureFrontDoor.Backend',
            http_headers=['x-azure-fdid=22222222-2222-2222-2222-222222222222'],
        )
        existing = _StubRule(
            'AzureFrontDoor.Backend',
            headers={'x-azure-fdid': ['11111111-1111-1111-1111-111111111111']},
        )
        with self._patch_configs([existing]):
            try:
                _validate_service_tag_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('Different x-azure-fdid filter should be allowed')

    def test_blocks_when_tag_and_headers_match(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace(
            'AzureFrontDoor.Backend',
            http_headers=['x-azure-fdid=11111111-1111-1111-1111-111111111111'],
        )
        existing = _StubRule(
            'AzureFrontDoor.Backend',
            headers={'x-azure-fdid': ['11111111-1111-1111-1111-111111111111']},
        )
        with self._patch_configs([existing]):
            with self.assertRaises(ArgumentUsageError):
                _validate_service_tag_existence(cmd, ns)

    def test_handles_none_access_rules(self):
        cmd = mock.MagicMock()
        ns = self._make_namespace('AzureFrontDoor.Backend')
        with self._patch_configs(None):
            try:
                _validate_service_tag_existence(cmd, ns)
            except ArgumentUsageError:
                self.fail('No existing rules should not raise')


if __name__ == '__main__':
    unittest.main()
