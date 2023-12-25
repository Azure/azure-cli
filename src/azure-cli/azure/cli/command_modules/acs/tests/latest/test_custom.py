# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import tempfile
import unittest
from unittest import mock

import yaml
from azure.cli.command_modules.acs._consts import (
    CONST_AZURE_POLICY_ADDON_NAME,
    CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
)
from azure.cli.command_modules.acs.custom import (
    _get_command_context,
    _update_addons,
    aks_stop,
    k8s_install_kubectl,
    k8s_install_kubelogin,
    merge_kubernetes_configurations,
)
from azure.cli.command_modules.acs.managed_cluster_decorator import (
    AKSManagedClusterModels,
)
from azure.cli.command_modules.acs.tests.latest.mocks import (
    MockCLI,
    MockClient,
    MockCmd,
    MockUrlretrieveUrlValidator,
)
from azure.cli.command_modules.acs.tests.latest.utils import (
    create_kubelogin_zip,
    get_test_data_file_path,
)
from azure.cli.core.util import CLIError
from azure.cli.core.profiles import ResourceType
from azure.mgmt.containerservice.v2020_03_01.models import (
    ManagedClusterAddonProfile,
)


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
            mock_url_retrieve.assert_called_with(MockUrlretrieveUrlValidator(test_source_url, test_ver), mock.ANY)
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
            mock_url_retrieve.assert_called_with(MockUrlretrieveUrlValidator(test_source_url, test_ver), mock.ANY)
        finally:
            shutil.rmtree(temp_dir)

class TestAKSCommand(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)
        self.client = MockClient()

    def test_aks_stop(self):
        # public cluster: call begin_stop
        mc_1 = self.models.ManagedCluster(location="test_location")
        self.client.get = mock.Mock(
            return_value=mc_1
        )
        self.client.begin_stop = mock.Mock(
            return_value=None
        )
        self.assertEqual(aks_stop(self.cmd, self.client, "rg", "name"), None)

        # private cluster: call begin_stop
        mc_2 = self.models.ManagedCluster(location="test_location")
        api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile()
        api_server_access_profile.enable_private_cluster = True
        mc_2.api_server_access_profile = api_server_access_profile
        self.client.get = mock.Mock(
            return_value=mc_2
        )
        self.client.begin_stop = mock.Mock(
            return_value=None
        )
        self.assertEqual(aks_stop(self.cmd, self.client, "rg", "name", False), None)


class TestRunCommand(unittest.TestCase):
    def test_get_command_context_invalid_file(self):
        with self.assertRaises(CLIError) as cm:
            _get_command_context([get_test_data_file_path("notexistingfile")])
        self.assertIn('notexistingfile is not valid file, or not accessable.', str(
            cm.exception))

    def test_get_command_context_mixed(self):
        with self.assertRaises(CLIError) as cm:
            _get_command_context(
                [".", get_test_data_file_path("ns.yaml")])
        self.assertEqual(str(
            cm.exception), '. is used to attach current folder, not expecting other attachements.')

    def test_get_command_context_empty(self):
        context = _get_command_context([])
        self.assertEqual(context, "")

    def test_get_command_context_valid(self):
        context = _get_command_context(
            [get_test_data_file_path("ns.yaml"), get_test_data_file_path("dummy.json")])
        self.assertNotEqual(context, '')


if __name__ == "__main__":
    unittest.main()
