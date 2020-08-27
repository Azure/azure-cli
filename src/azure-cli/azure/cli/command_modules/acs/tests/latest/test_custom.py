# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file
import mock
import os
import platform
import requests
import tempfile
import shutil
import unittest
import yaml

from msrestazure.azure_exceptions import CloudError
from azure.graphrbac.models import GraphErrorException
from azure.cli.command_modules.acs._params import (regions_in_preview,
                                                   regions_in_prod)
from azure.cli.command_modules.acs.custom import (merge_kubernetes_configurations, list_acs_locations,
                                                  _acs_browse_internal, _add_role_assignment, _get_default_dns_prefix,
                                                  create_application, _update_addons,
                                                  _ensure_container_insights_for_monitoring,
                                                  k8s_install_kubectl, k8s_install_kubelogin)
from azure.mgmt.containerservice.models import (ContainerServiceOrchestratorTypes,
                                                ContainerService,
                                                ContainerServiceOrchestratorProfile)
from azure.cli.core.util import CLIError


class AcsCustomCommandTest(unittest.TestCase):
    def test_list_acs_locations(self):
        client, cmd = mock.MagicMock(), mock.MagicMock()
        regions = list_acs_locations(client, cmd)
        prodregions = regions["productionRegions"]
        previewregions = regions["previewRegions"]
        self.assertListEqual(prodregions, regions_in_prod, "Production regions doesn't match")
        self.assertListEqual(previewregions, regions_in_preview, "Preview regions doesn't match")

    def test_get_default_dns_prefix(self):
        name = 'test5678910'
        resource_group_name = 'resource_group_with_underscore'
        sub_id = '123456789'

        dns_name_prefix = _get_default_dns_prefix(name, resource_group_name, sub_id)
        self.assertEqual(dns_name_prefix, "test567891-resourcegroupwit-123456")

        name = '1test5678910'
        dns_name_prefix = _get_default_dns_prefix(name, resource_group_name, sub_id)
        self.assertEqual(dns_name_prefix, "a1test5678-resourcegroupwit-123456")

    def test_add_role_assignment_basic(self):
        role = 'Owner'
        sp = '1234567'
        cli_ctx = mock.MagicMock()

        with mock.patch(
                'azure.cli.command_modules.acs.custom.create_role_assignment') as create_role_assignment:
            ok = _add_role_assignment(cli_ctx, role, sp, delay=0)
            create_role_assignment.assert_called_with(cli_ctx, role, sp, True, scope=None)
            self.assertTrue(ok, 'Expected _add_role_assignment to succeed')

    def test_add_role_assignment_msi_basic(self):
        role = 'Owner'
        sp = '1234567'
        cli_ctx = mock.MagicMock()

        with mock.patch(
                'azure.cli.command_modules.acs.custom.create_role_assignment') as create_role_assignment:
            ok = _add_role_assignment(cli_ctx, role, sp, False, delay=0)
            create_role_assignment.assert_called_with(cli_ctx, role, sp, False, scope=None)
            self.assertTrue(ok, 'Expected _add_role_assignment with msi to succeed')

    def test_add_role_assignment_exists(self):
        role = 'Owner'
        sp = '1234567'
        cli_ctx = mock.MagicMock()

        with mock.patch(
                'azure.cli.command_modules.acs.custom.create_role_assignment') as create_role_assignment:
            resp = requests.Response()
            resp.status_code = 409
            resp._content = b'Conflict'
            err = CloudError(resp)
            err.message = 'The role assignment already exists.'
            create_role_assignment.side_effect = err
            ok = _add_role_assignment(cli_ctx, role, sp, delay=0)

            create_role_assignment.assert_called_with(cli_ctx, role, sp, True, scope=None)
            self.assertTrue(ok, 'Expected _add_role_assignment to succeed')

    def test_add_role_assignment_fails(self):
        role = 'Owner'
        sp = '1234567'
        cli_ctx = mock.MagicMock()

        with mock.patch(
                'azure.cli.command_modules.acs.custom.create_role_assignment') as create_role_assignment:
            resp = requests.Response()
            resp.status_code = 500
            resp._content = b'Internal Error'
            err = CloudError(resp)
            err.message = 'Internal Error'
            create_role_assignment.side_effect = err
            ok = _add_role_assignment(cli_ctx, role, sp, delay=0)

            create_role_assignment.assert_called_with(cli_ctx, role, sp, True, scope=None)
            self.assertFalse(ok, 'Expected _add_role_assignment to fail')

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    def test_browse_k8s(self, get_subscription_id):
        acs_info = ContainerService(location="location", orchestrator_profile={}, master_profile={}, linux_profile={})
        acs_info.orchestrator_profile = ContainerServiceOrchestratorProfile(
            orchestrator_type=ContainerServiceOrchestratorTypes.kubernetes)
        client, cmd = mock.MagicMock(), mock.MagicMock()

        with mock.patch('azure.cli.command_modules.acs.custom._get_acs_info',
                        return_value=acs_info) as get_acs_info:
            with mock.patch(
                    'azure.cli.command_modules.acs.custom._k8s_browse_internal') as k8s_browse:
                _acs_browse_internal(client, cmd, acs_info, 'resource-group', 'name', False, 'ssh/key/file')
                get_acs_info.assert_called_once()
                k8s_browse.assert_called_with('name', acs_info, False, 'ssh/key/file')

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    def test_browse_dcos(self, get_subscription_id):
        acs_info = ContainerService(location="location", orchestrator_profile={}, master_profile={}, linux_profile={})
        acs_info.orchestrator_profile = ContainerServiceOrchestratorProfile(
            orchestrator_type=ContainerServiceOrchestratorTypes.dcos)
        client, cmd = mock.MagicMock(), mock.MagicMock()

        with mock.patch(
                'azure.cli.command_modules.acs.custom._dcos_browse_internal') as dcos_browse:
            _acs_browse_internal(client, cmd, acs_info, 'resource-group', 'name', False, 'ssh/key/file')
            dcos_browse.assert_called_with(acs_info, False, 'ssh/key/file')

    def test_merge_credentials_non_existent(self):
        self.assertRaises(CLIError, merge_kubernetes_configurations, 'non', 'existent', False)

    def test_merge_credentials_broken_yaml(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        with open(existing.name, 'w+') as stream:
            stream.write('{ broken')
        self.addCleanup(os.remove, existing.name)

        obj2 = {
            'clusters': [
                'cluster2'
            ],
            'contexts': [
                'context2'
            ],
            'users': [
                'user2'
            ],
            'current-context': 'cluster2',
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        self.assertRaises(CLIError, merge_kubernetes_configurations, existing.name, addition.name, False)

    def test_merge_credentials(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster1'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context1'
                }
            ],
            'current-context': 'context1',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)
        self.addCleanup(os.remove, existing.name)

        obj2 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'current-context': 'aztest',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'user2',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        merge_kubernetes_configurations(existing.name, addition.name, False)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.assertEqual(len(merged['clusters']), 2)
        self.assertEqual(merged['clusters'], [obj1['clusters'][0], obj2['clusters'][0]])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'], [obj1['contexts'][0], obj2['contexts'][0]])
        self.assertEqual(len(merged['users']), 2)
        self.assertEqual(merged['users'], [obj1['users'][0], obj2['users'][0]])
        self.assertEqual(merged['current-context'], obj2['current-context'])

    def test_merge_admin_credentials(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'apiVersion': 'v1',
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'aztest'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'aztest'
                }
            ],
            'current-context': 'aztest',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'clusterUser_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)
        self.addCleanup(os.remove, existing.name)
        obj2 = {
            'apiVersion': 'v1',
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'aztest'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterAdmin_aztest_aztest'
                    },
                    'name': 'aztest'
                }
            ],
            'current-context': 'aztest',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'clusterAdmin_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token2'
                    }
                }
            ]
        }
        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        merge_kubernetes_configurations(existing.name, addition.name, False)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.assertEqual(len(merged['clusters']), 1)
        self.assertEqual([c['cluster'] for c in merged['clusters']],
                         [{'certificate-authority-data': 'certificateauthoritydata1',
                           'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'}])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'],
                         [{'context': {'cluster': 'aztest', 'user': 'clusterUser_aztest_aztest'},
                           'name': 'aztest'},
                          {'context': {'cluster': 'aztest', 'user': 'clusterAdmin_aztest_aztest'},
                           'name': 'aztest-admin'}])
        self.assertEqual(len(merged['users']), 2)
        self.assertEqual([u['name'] for u in merged['users']],
                         ['clusterUser_aztest_aztest', 'clusterAdmin_aztest_aztest'])
        self.assertEqual(merged['current-context'], 'aztest-admin')

    def test_merge_credentials_missing(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': None,
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context1'
                }
            ],
            'current-context': 'context1',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)
        self.addCleanup(os.remove, existing.name)

        obj2 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'current-context': 'context2',
            'kind': 'Config',
            'preferences': {},
            'users': None
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        merge_kubernetes_configurations(existing.name, addition.name, False)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.assertEqual(len(merged['clusters']), 1)
        self.assertEqual(merged['clusters'], [obj2['clusters'][0]])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'], [obj1['contexts'][0], obj2['contexts'][0]])
        self.assertEqual(len(merged['users']), 1)
        self.assertEqual(merged['users'], [obj1['users'][0]])
        self.assertEqual(merged['current-context'], obj2['current-context'])

    def test_merge_credentials_already_present(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://cluster1-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster1'
                },
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://cluster2-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'cluster1User_aztest_aztest'
                    },
                    'name': 'context1'
                },
                {
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'cluster1User_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'users': [
                {
                    'name': 'cluster1User_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token2'
                    }
                },
                {
                    'name': 'cluster2User_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token2'
                    }
                }
            ],
            'current-context': 'context1',
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)

        obj2 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://other2-aztest-abc456-abcd4567.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'cluster2',
                        'user': 'cluster1_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'users': [
                {
                    'name': 'cluster2User_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token3'
                    }
                }
            ],
            'current-context': 'some-context',
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        with self.assertRaises(CLIError):
            merge_kubernetes_configurations(existing.name, addition.name, False)

        merge_kubernetes_configurations(existing.name, addition.name, True)
        self.addCleanup(os.remove, addition.name)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.addCleanup(os.remove, existing.name)

        self.assertEqual(len(merged['clusters']), 2)
        expected_clusters = [
            obj1['clusters'][0],
            obj2['clusters'][0]
        ]
        self.assertEqual(merged['clusters'], expected_clusters)
        self.assertEqual(len(merged['contexts']), 2)
        expected_contexts = [
            obj1['contexts'][0],
            obj2['contexts'][0]
        ]
        self.assertEqual(merged['contexts'], expected_contexts)
        self.assertEqual(len(merged['users']), 2)
        expected_users = [
            obj1['users'][0],
            obj2['users'][0]
        ]
        self.assertEqual(merged['users'], expected_users)
        self.assertEqual(merged['current-context'], obj2['current-context'])

    def test_acs_sp_create_failed_with_polished_error_if_due_to_permission(self):

        class FakedError(object):
            def __init__(self, message):
                self.message = message

        def _test_deserializer(resp_type, response):
            err = FakedError('Insufficient privileges to complete the operation')
            return err

        client = mock.MagicMock()
        client.create.side_effect = GraphErrorException(_test_deserializer, None)

        # action
        with self.assertRaises(CLIError) as context:
            create_application(client, 'acs_sp', 'http://acs_sp', ['http://acs_sp'])

        # assert we handled such error
        self.assertTrue(
            'https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal' in str(context.exception))

    @mock.patch('azure.cli.command_modules.acs.custom._get_rg_location', return_value='eastus')
    @mock.patch('azure.cli.command_modules.acs.custom.cf_resource_groups', autospec=True)
    @mock.patch('azure.cli.command_modules.acs.custom.cf_resources', autospec=True)
    def test_update_addons(self, rg_def, cf_resource_groups, cf_resources):
        # http_application_routing enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None
        cmd = mock.MagicMock()
        instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'http_application_routing', enable=True)
        self.assertIn('httpApplicationRouting', instance.addon_profiles)
        addon_profile = instance.addon_profiles['httpApplicationRouting']
        self.assertTrue(addon_profile.enabled)

        # http_application_routing enabled
        instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'http_application_routing', enable=False)
        addon_profile = instance.addon_profiles['httpApplicationRouting']
        self.assertFalse(addon_profile.enabled)

        # monitoring added
        instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'monitoring', enable=True)
        monitoring_addon_profile = instance.addon_profiles['omsagent']
        self.assertTrue(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles['httpApplicationRouting']
        self.assertFalse(routing_addon_profile.enabled)

        # monitoring disabled, routing enabled
        instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'monitoring', enable=False)
        instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000', 'clitest000001',
                                  'http_application_routing', enable=True)
        monitoring_addon_profile = instance.addon_profiles['omsagent']
        self.assertFalse(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles['httpApplicationRouting']
        self.assertTrue(routing_addon_profile.enabled)
        self.assertEqual(sorted(list(instance.addon_profiles)), ['httpApplicationRouting', 'omsagent'])

        # monitoring enabled and then enabled again should error
        instance = mock.Mock()
        instance.addon_profiles = None
        instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'monitoring', enable=True)
        with self.assertRaises(CLIError):
            instance = _update_addons(cmd, instance, '00000000-0000-0000-0000-000000000000',
                                      'clitest000001', 'monitoring', enable=True)

    @mock.patch('azure.cli.command_modules.acs.custom.cf_resources', autospec=True)
    @mock.patch('azure.cli.command_modules.acs.custom._invoke_deployment')
    def test_ensure_container_insights_for_monitoring(self, invoke_def, cf_resources):
        cmd = mock.Mock()
        addon = mock.Mock()
        wsID = "/subscriptions/1234abcd-cad5-417b-1234-aec62ffa6fe7/resourcegroups/mbdev/providers/microsoft.operationalinsights/workspaces/mbdev"
        addon.config = {
            'logAnalyticsWorkspaceResourceID': wsID
        }
        self.assertTrue(_ensure_container_insights_for_monitoring(cmd, addon))
        args, kwargs = invoke_def.call_args
        self.assertEqual(args[3]['resources'][0]['type'], "Microsoft.Resources/deployments")
        self.assertEqual(args[4]['workspaceResourceId']['value'], wsID)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_emit_warnings(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'kubectl')
            k8s_install_kubectl(mock.MagicMock(), client_version='1.2.3', install_location=test_location)
            self.assertEqual(mock_url_retrieve.call_count, 1)
            # 2 warnings, 1st for download result; 2nd for updating PATH
            self.assertEqual(logger_mock.warning.call_count, 2)  # 2 warnings, one for download result
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_create_installation_dir(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'foo', 'kubectl')
            k8s_install_kubectl(mock.MagicMock(), client_version='1.2.3', install_location=test_location)
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_emit_warnings(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = os.path.realpath(tempfile.mkdtemp())  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'kubelogin')
            k8s_install_kubelogin(mock.MagicMock(), client_version='0.0.4', install_location=test_location)
            self.assertEqual(mock_url_retrieve.call_count, 1)
            # 2 warnings, 1st for download result; 2nd for updating PATH
            self.assertEqual(logger_mock.warning.call_count, 2)  # 2 warnings, one for download result
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_create_installation_dir(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            k8s_install_kubelogin(mock.MagicMock(), client_version='0.0.4', install_location=test_location)
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)


def create_kubelogin_zip(file_url, download_path):
    import zipfile
    try:
        cwd = os.getcwd()
        temp_dir = os.path.realpath(tempfile.mkdtemp())
        os.chdir(temp_dir)
        bin_dir = 'bin'
        system = platform.system()
        if system == 'Windows':
            bin_dir += '/windows_amd64'
        elif system == 'Linux':
            bin_dir += '/linux_amd64'
        elif system == 'Darwin':
            bin_dir += '/darwin_amd64'
        os.makedirs(bin_dir)
        bin_location = os.path.join(bin_dir, 'kubelogin')
        open(bin_location, 'a').close()
        with zipfile.ZipFile(download_path, 'w', zipfile.ZIP_DEFLATED) as outZipFile:
            outZipFile.write(bin_location)
    finally:
        os.chdir(cwd)
        shutil.rmtree(temp_dir)
