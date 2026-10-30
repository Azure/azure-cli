# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.core import get_default_cli
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.command_modules.storage.aaz.latest.storage.account.network_security_perimeter_configuration import (
    List as NspList, Show as NspShow)
from azure.cli.command_modules.storage.operations.account import FileServiceUsage


class StorageManagementAazResponseTest(unittest.TestCase):

    def setUp(self):
        self.cli_ctx = get_default_cli()

    def _deserialize_response(self, command_type, operation_type, payload):
        ctx = AAZCommandCtx(self.cli_ctx, command_type.get_arguments_schema(), {})
        ctx._clients['MgmtClient'] = Mock()
        operation = operation_type(ctx)
        operation.on_200(SimpleNamespace(context={ContentDecodePolicy.CONTEXT_NAME: payload}))
        command = command_type(cli_ctx=self.cli_ctx)
        command.ctx = ctx
        return command._output()

    def test_nsp_show_and_list_preserve_service_tags(self):
        for tags in (['Storage', 'AzureMonitor'], []):
            with self.subTest(tags=tags):
                access_rule = {
                    'name': 'inbound',
                    'properties': {
                        'direction': 'Inbound',
                        'addressPrefixes': ['10.0.0.0/8'],
                        'serviceTags': tags
                    }
                }
                configuration = {
                    'name': 'myconfiguration',
                    'properties': {'profile': {'accessRules': [access_rule]}}
                }
                show = self._deserialize_response(
                    NspShow, NspShow.NetworkSecurityPerimeterConfigurationsGet, configuration)
                listed = self._deserialize_response(
                    NspList, NspList.NetworkSecurityPerimeterConfigurationsList, {'value': [configuration]})
                self.assertEqual(access_rule, show['profile']['accessRules'][0])
                self.assertEqual([show], listed)
                self.assertEqual('myconfiguration', show['name'])

    def test_nsp_responses_without_service_tags_remain_compatible(self):
        configuration = {
            'name': 'myconfiguration',
            'properties': {'profile': {'accessRules': [{'name': 'legacy', 'properties': {'direction': 'Inbound'}}]}}
        }
        show = self._deserialize_response(
            NspShow, NspShow.NetworkSecurityPerimeterConfigurationsGet, configuration)
        listed = self._deserialize_response(
            NspList, NspList.NetworkSecurityPerimeterConfigurationsList, {'value': [configuration]})
        self.assertNotIn('serviceTags', show['profile']['accessRules'][0]['properties'])
        self.assertEqual([show], listed)

    def test_nsp_requests_use_september_api(self):
        for command_type, operation_type in (
                (NspShow, NspShow.NetworkSecurityPerimeterConfigurationsGet),
                (NspList, NspList.NetworkSecurityPerimeterConfigurationsList)):
            with self.subTest(command=command_type.__name__):
                ctx = AAZCommandCtx(self.cli_ctx, command_type.get_arguments_schema(), {})
                ctx._clients['MgmtClient'] = Mock()
                operation = operation_type(ctx)
                self.assertEqual('2026-09-01', command_type._aaz_info['version'])
                self.assertEqual({'api-version': '2026-09-01'}, operation.query_parameters)
                self.assertEqual('GET', operation.method)

    def test_file_service_usage_preserves_read_only_guardrail_scalars(self):
        limits = {
            'minProvisionedStorageGiB': 32,
            'guardrailIOScalar': 1.5,
            'guardrailBandwidthScalar': 2.5
        }
        result = self._deserialize_response(
            FileServiceUsage, FileServiceUsage.FileServicesGetServiceUsage,
            {'name': 'default', 'properties': {'fileShareLimits': limits}})
        self.assertEqual(limits, result['properties']['fileShareLimits'])
        schema = FileServiceUsage.FileServicesGetServiceUsage._build_schema_on_200()
        self.assertTrue(schema.properties.file_share_limits._flags['read_only'])
        args = FileServiceUsage.get_arguments_schema()
        self.assertNotIn('guardrail_io_scalar', args._fields)
        self.assertNotIn('guardrail_bandwidth_scalar', args._fields)
