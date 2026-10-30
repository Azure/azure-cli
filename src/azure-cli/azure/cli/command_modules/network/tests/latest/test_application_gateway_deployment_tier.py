# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlparse

from azure.core import PipelineClient
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.core.aaz import AAZCommand, has_value
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.network.custom import ApplicationGatewayUpdate, create_application_gateway
from azure.cli.command_modules.network.aaz.latest.network.application_gateway import List, Show, Wait


TIERS = ('Standard', 'NetworkIsolated', 'Accelerated', 'Elastic')
SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'


class ApplicationGatewayDeploymentTierTests(unittest.TestCase):

    def _create_template(self, sku='Standard_v2', **kwargs):
        cmd = mock.MagicMock()
        cmd.get_models.return_value = SimpleNamespace
        with mock.patch('azure.cli.command_modules.network.custom.get_subscription_id',
                        return_value=SUBSCRIPTION), \
                mock.patch('azure.cli.command_modules.network.custom.get_mgmt_service_client') as get_client:
            create_application_gateway(
                cmd, 'gateway', 'rg', location='eastus', sku=sku, priority=100,
                frontend_port=80, no_wait=True,
                subnet=f'/subscriptions/{SUBSCRIPTION}/resourceGroups/rg/providers/'
                       'Microsoft.Network/virtualNetworks/vnet/subnets/default',
                **kwargs
            )
        deployment = get_client.return_value.deployments.begin_create_or_update.call_args.args[2]
        resources = deployment.properties.template['resources']
        gateway, = [resource for resource in resources if resource['type'] == 'Microsoft.Network/applicationGateways']
        self.assertEqual(gateway['apiVersion'], '2026-05-01')
        self.assertNotIn('deploymentTier', gateway)
        return gateway

    def _context(self, command=ApplicationGatewayUpdate, **kwargs):
        ctx = AAZCommandCtx(
            cli_ctx=mock.MagicMock(),
            schema=command.get_arguments_schema(),
            command_args={'name': 'gateway', 'resource_group': 'rg', 'subscription': SUBSCRIPTION, **kwargs},
        )
        ctx.format_args()
        client = PipelineClient(base_url='https://management.azure.com')
        client.send_request = mock.Mock(side_effect=AssertionError('Unit tests must not send HTTP requests'))
        self.addCleanup(client.close)
        ctx._clients['MgmtClient'] = client
        return ctx

    @staticmethod
    def _session(data):
        return SimpleNamespace(context={ContentDecodePolicy.CONTEXT_NAME: data})

    def _assert_api(self, operation):
        request = operation.make_request()
        self.assertEqual(parse_qs(urlparse(request.url).query), {'api-version': ['2026-05-01']})
        return request

    def _update_request(self, existing=None, **kwargs):
        ctx = self._context(**kwargs)
        data = {
            'name': 'gateway', 'location': 'eastus', 'tags': {'original': 'tag'},
            'properties': {'sku': {'name': 'Standard_v2', 'tier': 'Standard_v2', 'capacity': 2}},
        }
        if existing is not None:
            data['properties']['deploymentTier'] = existing
        get = ApplicationGatewayUpdate.ApplicationGatewaysGet(ctx)
        self._assert_api(get)
        get.on_200(self._session(data))
        ApplicationGatewayUpdate.InstanceUpdateByJson(ctx)()
        put = ApplicationGatewayUpdate.ApplicationGatewaysCreateOrUpdate(ctx)
        request = self._assert_api(put)
        self.assertEqual(request.method, 'PUT')
        body = json.loads(request.body)
        self.assertNotIn('deploymentTier', body)
        self.assertNotIn('deployment_tier', body['properties'])
        return ctx, put, body

    def test_create_all_deployment_tiers(self):
        for sku in ('Standard_v2', 'WAF_v2'):
            for tier in TIERS:
                with self.subTest(sku=sku, tier=tier):
                    gateway = self._create_template(sku=sku, deployment_tier=tier)
                    self.assertEqual(gateway['properties']['deploymentTier'], tier)

    def test_create_omits_unspecified_deployment_tier(self):
        self.assertNotIn('deploymentTier', self._create_template()['properties'])

    def test_create_does_not_upgrade_other_network_resources(self):
        from azure.cli.command_modules.network._template_builder import IP_VERSION, LB_VERSION
        self.assertEqual(IP_VERSION, '2022-05-01')
        self.assertEqual(LB_VERSION, '2023-04-01')

    def test_update_all_deployment_tiers(self):
        for existing in ('Standard', 'FutureServiceTier'):
            for tier in TIERS:
                with self.subTest(existing=existing, tier=tier):
                    _, _, body = self._update_request(existing=existing, deployment_tier=tier)
                    self.assertEqual(body['properties']['deploymentTier'], tier)
                    self.assertEqual(body['properties']['sku']['capacity'], 2)

    def test_update_omits_absent_deployment_tier(self):
        ctx, _, body = self._update_request(tags={'updated': 'tag'})
        self.assertFalse(has_value(ctx.args.deployment_tier))
        self.assertNotIn('deploymentTier', body['properties'])
        self.assertEqual(body['tags'], {'updated': 'tag'})

    def test_unrelated_update_preserves_all_and_future_deployment_tiers(self):
        for tier in (*TIERS, 'FutureServiceTier'):
            with self.subTest(tier=tier):
                _, _, body = self._update_request(existing=tier, tags={'updated': 'tag'})
                self.assertEqual(body['properties']['deploymentTier'], tier)
                self.assertEqual(body['tags'], {'updated': 'tag'})

    def test_update_rejects_unknown_argument_but_not_unknown_service_value(self):
        enum = ApplicationGatewayUpdate.get_arguments_schema().deployment_tier.enum
        self.assertCountEqual(enum.to_choices(), TIERS)
        with self.assertRaises(InvalidArgumentValueError):
            enum['Unsupported']

    def test_update_returns_service_deployment_tier(self):
        for tier in (*TIERS, 'FutureServiceTier'):
            with self.subTest(tier=tier):
                ctx, put, _ = self._update_request(deployment_tier='Standard')
                put.on_200_201(self._session({'properties': {'deploymentTier': tier}}))
                self.assertEqual(AAZCommand.deserialize_output(ctx.vars.instance)['deploymentTier'], tier)

    def test_show_and_wait_expose_service_deployment_tier(self):
        for command in (Show, Wait):
            for tier in (*TIERS, 'FutureServiceTier'):
                with self.subTest(command=command.__name__, tier=tier):
                    ctx = self._context(command)
                    operation = command.ApplicationGatewaysGet(ctx)
                    self._assert_api(operation)
                    operation.on_200(self._session({'properties': {'deploymentTier': tier}}))
                    self.assertEqual(AAZCommand.deserialize_output(ctx.vars.instance)['deploymentTier'], tier)
                    self.assertEqual(AAZCommand.deserialize_output(
                        ctx.vars.instance, client_flatten=False)['properties']['deploymentTier'], tier)

    def test_list_exposes_service_deployment_tier_at_both_scopes(self):
        for operation_class in (List.ApplicationGatewaysList, List.ApplicationGatewaysListAll):
            for tier in (*TIERS, 'FutureServiceTier'):
                with self.subTest(operation=operation_class.__name__, tier=tier):
                    ctx = self._context(List)
                    operation = operation_class(ctx)
                    self._assert_api(operation)
                    operation.on_200(self._session({'value': [{'properties': {'deploymentTier': tier}}]}))
                    self.assertEqual(AAZCommand.deserialize_output(ctx.vars.instance.value)[0]['deploymentTier'], tier)
