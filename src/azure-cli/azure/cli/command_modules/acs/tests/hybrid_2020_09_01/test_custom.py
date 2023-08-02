# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
import shutil
import tempfile
import unittest
from unittest import mock

import yaml
from azure.cli.command_modules.acs._consts import (
    CONST_AZURE_POLICY_ADDON_NAME, CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    CONST_KUBE_DASHBOARD_ADDON_NAME, CONST_MONITORING_ADDON_NAME)
from azure.cli.command_modules.acs.custom import (
    _update_addons, k8s_install_kubectl, k8s_install_kubelogin,
    merge_kubernetes_configurations)
from azure.cli.core._config import ENV_VAR_PREFIX, GLOBAL_CONFIG_DIR
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.util import CLIError
from azure.mgmt.containerservice.v2020_11_01.models import \
    ManagedClusterAddonProfile
from knack import CLI


class MockCLI(CLI):
    def __init__(self):
        super(MockCLI, self).__init__(cli_name='mock_cli', config_dir=GLOBAL_CONFIG_DIR,
                                      config_env_var_prefix=ENV_VAR_PREFIX, commands_loader_cls=MockLoader)
        self.cloud = get_active_cloud(self)


class MockLoader(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def get_models(self, *attr_args, **_):
        from azure.cli.core.profiles import get_sdk
        return get_sdk(self.ctx, ResourceType.MGMT_CONTAINERSERVICE, 'ManagedClusterAddonProfile',
                       mod='models', operation_group='managed_clusters')


class MockCmd(object):
    def __init__(self, ctx, arguments={}):
        self.cli_ctx = ctx
        self.loader = MockLoader(self.cli_ctx)
        self.arguments = arguments

    def get_models(self, *attr_args, **kwargs):
        return get_sdk(self.cli_ctx, ResourceType.MGMT_CONTAINERSERVICE, 'ManagedClusterAddonProfile',
                       mod='models', operation_group='managed_clusters')


class AcsCustomCommandTest(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

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

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location', return_value='eastus')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client', autospec=True)
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client', autospec=True)
    def test_update_addons(self, rg_def, get_resource_groups_client, get_resources_client):
        # http_application_routing enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None

        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=True)
        self.assertIn(CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME, instance.addon_profiles)
        addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(addon_profile.enabled)

        # http_application_routing disabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=False)
        addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertFalse(addon_profile.enabled)

        # monitoring added
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=True)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertTrue(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertFalse(routing_addon_profile.enabled)

        # monitoring disabled, routing enabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=True)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(routing_addon_profile.enabled)
        self.assertEqual(sorted(list(instance.addon_profiles)), [CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME, CONST_MONITORING_ADDON_NAME])

        # azurepolicy added
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'azure-policy', enable=True)
        azurepolicy_addon_profile = instance.addon_profiles[CONST_AZURE_POLICY_ADDON_NAME]
        self.assertTrue(azurepolicy_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(routing_addon_profile.enabled)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_addon_profile.enabled)

        # azurepolicy disabled, routing enabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'azure-policy', enable=False)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=True)
        azurepolicy_addon_profile = instance.addon_profiles[CONST_AZURE_POLICY_ADDON_NAME]
        self.assertFalse(azurepolicy_addon_profile.enabled)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(routing_addon_profile.enabled)
        self.assertEqual(sorted(list(instance.addon_profiles)), [CONST_AZURE_POLICY_ADDON_NAME, CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME, CONST_MONITORING_ADDON_NAME])

        # kube-dashboard disabled, no existing dashboard addon profile
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=False)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertFalse(dashboard_addon_profile.enabled)

        # kube-dashboard enabled, no existing dashboard addon profile
        instance.addon_profiles.pop(CONST_KUBE_DASHBOARD_ADDON_NAME, None)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=True)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertTrue(dashboard_addon_profile.enabled)

        # kube-dashboard disabled, there's existing dashboard addon profile
        instance.addon_profiles.pop(CONST_KUBE_DASHBOARD_ADDON_NAME, None)
        # test lower cased key name
        instance.addon_profiles['kubedashboard'] = ManagedClusterAddonProfile(enabled=True)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=False)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertFalse(dashboard_addon_profile.enabled)

        # kube-dashboard enabled, there's existing dashboard addon profile
        instance.addon_profiles.pop(CONST_KUBE_DASHBOARD_ADDON_NAME, None)
        # test lower cased key name
        instance.addon_profiles['kubedashboard'] = ManagedClusterAddonProfile(enabled=False)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=True)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertTrue(dashboard_addon_profile.enabled)

        # monitoring enabled and then enabled again should error
        instance = mock.Mock()
        instance.addon_profiles = None
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=True)
        with self.assertRaises(CLIError):
            instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                      'clitest000001', 'clitest000001', 'monitoring', enable=True)

        # virtual-node enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'virtual-node', enable=True, subnet_name='foo')
        self.assertIn('aciConnectorLinux', instance.addon_profiles)
        addon_profile = instance.addon_profiles['aciConnectorLinux']
        self.assertTrue(addon_profile.enabled)

        # virtual-node disabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'virtual-node', enable=False)
        addon_profile = instance.addon_profiles['aciConnectorLinux']
        self.assertFalse(addon_profile.enabled)

        # ingress-appgw enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'ingress-appgw', enable=True, appgw_subnet_cidr='10.2.0.0/16')
        self.assertIn('ingressApplicationGateway', instance.addon_profiles)
        addon_profile = instance.addon_profiles['ingressApplicationGateway']
        self.assertTrue(addon_profile.enabled)

        # ingress-appgw disabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'ingress-appgw', enable=False)
        addon_profile = instance.addon_profiles['ingressApplicationGateway']
        self.assertFalse(addon_profile.enabled)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_emit_warnings(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'kubectl')
            k8s_install_kubectl(mock.MagicMock(), client_version='1.2.3', install_location=test_location)
            self.assertEqual(mock_url_retrieve.call_count, 1)
            # 3 warnings, 1st for arch, 2nd for download result, 3rd for updating PATH
            self.assertEqual(logger_mock.warning.call_count, 3)  # 3 warnings, one for download result
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
            k8s_install_kubelogin(mock.MagicMock(), client_version='0.0.4', install_location=test_location, arch="amd64")
            self.assertEqual(mock_url_retrieve.call_count, 1)
            # 3 warnings, 1st for download result, 2nd for moving file, 3rd for updating PATH
            self.assertEqual(logger_mock.warning.call_count, 3)  # 3 warnings, one for download result
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_create_installation_dir(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            k8s_install_kubelogin(mock.MagicMock(), client_version='0.0.4', install_location=test_location, arch="amd64")
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_with_custom_source_url(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubectl')
            test_ver = '1.2.5'
            test_source_url = 'http://url1'
            k8s_install_kubectl(mock.MagicMock(), client_version=test_ver, install_location=test_location, source_url=test_source_url)
            mock_url_retrieve.assert_called_with(mockUrlretrieveUrlValidator(test_source_url, test_ver), mock.ANY)
        finally:
            shutil.rmtree(temp_dir)

    @unittest.skip('No such file or directory')
    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_with_custom_source_url(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            test_ver = '1.2.6'
            test_source_url = 'http://url2'
            k8s_install_kubelogin(mock.MagicMock(), client_version=test_ver, install_location=test_location, source_url=test_source_url, arch="amd64")
            mock_url_retrieve.assert_called_with(mockUrlretrieveUrlValidator(test_source_url, test_ver), mock.ANY)
        finally:
            shutil.rmtree(temp_dir)


class mockUrlretrieveUrlValidator(object):
    def __init__(self, url, version):
        self.url = url
        self.version = version

    def __eq__(self, other):
        return other.startswith(self.url) and self.version in other


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
