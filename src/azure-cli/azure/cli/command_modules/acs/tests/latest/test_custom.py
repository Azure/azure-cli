# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import tempfile
import unittest
from unittest import mock
import datetime
from dateutil.parser import parse

import yaml
from azure.cli.command_modules.acs._consts import (
    CONST_AZURE_POLICY_ADDON_NAME,
    CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_USING_AAD_MSI_AUTH,
)
from azure.cli.command_modules.acs.addonconfiguration import (
    ensure_default_log_analytics_workspace_for_monitoring,
)
from azure.cli.command_modules.acs.custom import (
    _get_command_context,
    _update_addons,
    aks_enable_addons,
    aks_stop,
    is_monitoring_addon_enabled,
    k8s_install_kubectl,
    k8s_install_kubelogin,
    merge_kubernetes_configurations,
    _update_upgrade_settings,
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
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerservice.models import (
    ManagedClusterAddonProfile,
)
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
)


class AcsCustomCommandTest(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()
        self.models = AKSManagedClusterModels(MockCmd(self.cli), ResourceType.MGMT_CONTAINERSERVICE)

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

    @unittest.skipIf(os.name == 'nt', 'Symlink test not applicable on Windows')
    def test_merge_credentials_rejects_symlink(self):
        # Create a real kubeconfig file and a symlink pointing to it
        target = tempfile.NamedTemporaryFile(delete=False, suffix='.kubeconfig')
        target.close()
        with open(target.name, 'w') as f:
            yaml.safe_dump({'clusters': [], 'contexts': [], 'users': [],
                            'current-context': '', 'kind': 'Config'}, f)
        self.addCleanup(os.remove, target.name)

        symlink_path = target.name + '.link'
        os.symlink(target.name, symlink_path)
        self.addCleanup(lambda: os.remove(symlink_path) if os.path.islink(symlink_path) else None)

        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj = {
            'clusters': [{'cluster': {'server': 'https://test'}, 'name': 'c1'}],
            'contexts': [{'context': {'cluster': 'c1', 'user': 'u1'}, 'name': 'ctx1'}],
            'users': [{'name': 'u1', 'user': {'token': 'tok'}}],
            'current-context': 'ctx1',
        }
        with open(addition.name, 'w') as f:
            yaml.safe_dump(obj, f)
        self.addCleanup(os.remove, addition.name)

        # Should raise CLIError when existing_file is a symlink
        with self.assertRaises(CLIError):
            merge_kubernetes_configurations(symlink_path, addition.name, False)

        # Verify the symlink target was not modified
        with open(target.name, 'r') as f:
            content = yaml.safe_load(f)
        self.assertEqual(content['clusters'], [])

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

        # monitoring enable with camelCase addon key does NOT preserve enableRetinaNetworkFlags
        instance = mock.MagicMock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(
                enabled=False,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                    'enableRetinaNetworkFlags': 'True',
                },
            ),
        }
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=True)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertTrue(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config.get('enableRetinaNetworkFlags'))

        # monitoring disable sets config to None
        instance = mock.MagicMock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(
                enabled=True,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                    'enableRetinaNetworkFlags': 'True',
                },
            ),
        }
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config)

        # monitoring disable without CNL also sets config to None
        instance = mock.MagicMock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(
                enabled=True,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                },
            ),
        }
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config)

        # monitoring disable with camelCase key (omsAgent) sets config to None
        instance = mock.MagicMock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(
                enabled=True,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                    'enableRetinaNetworkFlags': 'True',
                },
            ),
        }
        # The addon key normalization in _update_addons remaps camelCase to lowercase
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config)

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

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_with_gh_token(self, logger_mock, mock_url_retrieve, mock_urlopen_read):
        """Test that gh_token parameter is properly passed to HTTP requests when installing kubelogin."""
        # Mock the GitHub API response for latest release
        mock_urlopen_read.return_value = b'{"tag_name": "v0.0.30"}'
        # Mock the zip file download
        mock_url_retrieve.side_effect = create_kubelogin_zip
        
        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            test_gh_token = 'ghp_test_token_123'
            
            # Install kubelogin with gh_token
            k8s_install_kubelogin(
                mock.MagicMock(),
                client_version='latest',
                install_location=test_location,
                arch="amd64",
                gh_token=test_gh_token
            )
            
            # Verify gh_token was passed to _urlopen_read for GitHub API call
            mock_urlopen_read.assert_called_once()
            call_args = mock_urlopen_read.call_args
            self.assertEqual(call_args.kwargs.get('gh_token'), test_gh_token)
            
            # Verify the installation completed
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location', return_value='eastus')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client', autospec=True)
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client', autospec=True)
    def test_update_upgrade_settings(self, rg_def, get_resource_groups_client, get_resources_client):
        instance = mock.MagicMock()

        # Should not update mc if unset
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertIsNone(instance.upgrade_settings)

        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = True,
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2023-04-01T13:00:00Z"))

        # force_upgrade True
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertGreater(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=2)).timestamp())
        self.assertLess(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=4)).timestamp())

        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = False
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertGreater(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=2)).timestamp())
        self.assertLess(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=4)).timestamp())

        # force_upgrade False
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=True, upgrade_override_until=None)
        self.assertFalse(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertIsNone(instance.upgrade_settings.override_settings.until)

        instance.upgrade_settings = None
        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = True
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=True, upgrade_override_until=None)
        self.assertFalse(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertIsNone(instance.upgrade_settings.override_settings.until)

        # Update util
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertIsNone(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))
        
        instance.upgrade_settings = None
        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertIsNone(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))

        with self.assertRaises(InvalidArgumentValueError):
            _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until="abc")

         # Set both force_upgrade and until 
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))
        
        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = True,
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=True, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertFalse(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))

        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = False,
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))

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


class TestAddonConfigurationAzureBleuCloud(unittest.TestCase):
    """Test cases for AzureBleu Cloud region mapping in addon configuration."""

    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)
        # Set cloud name to AzureBleuCloud
        self.cmd.cli_ctx.cloud.name = 'AzureBleuCloud'

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_bleufrancecentral_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that bleufrancecentral region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'bleufrancecentral'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-BLEUC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-BLEUC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-BLEUC',
            {'location': 'bleufrancecentral'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-BLEUC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-BLEUC', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_bleufrancesouth_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that bleufrancesouth region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'bleufrancesouth'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-BLEUS/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-BLEUS'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-BLEUS',
            {'location': 'bleufrancesouth'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-BLEUS', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-BLEUS', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_unknown_bleu_region_defaults_to_bleufrancecentral(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that unknown regions in AzureBleu cloud default to bleufrancecentral."""
        # Arrange
        mock_get_rg_location.return_value = 'unknownregion'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-BLEUC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-BLEUC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with default region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-BLEUC',
            {'location': 'bleufrancecentral'}
        )
        
        # Verify the workspace resource ID contains the default region code
        self.assertIn('DefaultResourceGroup-BLEUC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-BLEUC', result)


class TestAddonConfigurationAzureDelosCloud(unittest.TestCase):
    """Test cases for AzureDelos Cloud region mapping in addon configuration."""

    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)
        # Set cloud name to AzureDelosCloud
        self.cmd.cli_ctx.cloud.name = 'AzureDelosCloud'

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_deloscloudgermanycentral_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that deloscloudgermanycentral region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'deloscloudgermanycentral'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-DELOSC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-DELOSC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-DELOSC',
            {'location': 'deloscloudgermanycentral'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-DELOSC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-DELOSC', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_deloscloudgermanynorth_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that deloscloudgermanynorth region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'deloscloudgermanynorth'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-DELOSN/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-DELOSN'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-DELOSN',
            {'location': 'deloscloudgermanynorth'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-DELOSN', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-DELOSN', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_unknown_delos_region_defaults_to_deloscloudgermanycentral(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that unknown regions in AzureDelos cloud default to deloscloudgermanycentral."""
        # Arrange
        mock_get_rg_location.return_value = 'unknownregion'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-DELOSC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-DELOSC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with default region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-DELOSC',
            {'location': 'deloscloudgermanycentral'}
        )
        
        # Verify the workspace resource ID contains the default region code
        self.assertIn('DefaultResourceGroup-DELOSC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-DELOSC', result)


class TestIsMonitoringAddonEnabled(unittest.TestCase):
    """Tests for the is_monitoring_addon_enabled helper in custom.py."""

    def test_monitoring_enabled_with_lowercase_key(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(enabled=True, config={}),
        }
        self.assertTrue(is_monitoring_addon_enabled("monitoring", instance))

    def test_monitoring_enabled_with_camelcase_key(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(enabled=True, config={}),
        }
        self.assertTrue(is_monitoring_addon_enabled("monitoring", instance))

    def test_monitoring_disabled_with_camelcase_key(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(enabled=False, config={}),
        }
        self.assertFalse(is_monitoring_addon_enabled("monitoring", instance))

    def test_no_monitoring_addon_at_all(self):
        instance = mock.Mock()
        instance.addon_profiles = {}
        self.assertFalse(is_monitoring_addon_enabled("monitoring", instance))

    def test_non_monitoring_addon(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(enabled=True, config={}),
        }
        self.assertFalse(is_monitoring_addon_enabled("http_application_routing", instance))


class TestAksEnableAddonsAutoHLSM(unittest.TestCase):
    """Tests for auto-detection of HLSM when CNL is active in aks_enable_addons."""

    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)

    def _build_instance(self, cnl_flag=None, addon_key=CONST_MONITORING_ADDON_NAME):
        """Build a mock cluster instance with monitoring addon."""
        config = {
            'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
            CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
        }
        if cnl_flag is not None:
            config['enableRetinaNetworkFlags'] = cnl_flag
        instance = mock.MagicMock()
        instance.addon_profiles = {
            addon_key: ManagedClusterAddonProfile(enabled=True, config=config),
        }
        instance.service_principal_profile.client_id = "msi"
        instance.api_server_access_profile = None
        instance.location = "eastus"
        return instance

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_auto_enabled_when_cnl_active(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When CNL is active and HLSM not set, HLSM should auto-enable."""
        instance = self._build_instance(cnl_flag="True")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertTrue(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_not_auto_enabled_when_cnl_inactive(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When CNL is not active and HLSM not set, HLSM should remain None."""
        instance = self._build_instance(cnl_flag=None)
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertIsNone(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_explicit_true_not_overridden(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When HLSM is explicitly True, auto-detection should not change it."""
        instance = self._build_instance(cnl_flag="True")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring",
                          enable_high_log_scale_mode=True)

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertTrue(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_explicit_false_not_overridden_by_cnl(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When HLSM is explicitly False, auto-detection should not override even with CNL active."""
        instance = self._build_instance(cnl_flag="True")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring",
                          enable_high_log_scale_mode=False)

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertFalse(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_auto_enabled_with_cnl_lowercase_true(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """CNL flag value 'true' (lowercase) should also trigger auto-HLSM."""
        instance = self._build_instance(cnl_flag="true")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertTrue(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_not_auto_enabled_when_cnl_false(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When CNL flag is 'false', HLSM should not auto-enable."""
        instance = self._build_instance(cnl_flag="false")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertIsNone(kwargs.get("enable_high_log_scale_mode"))


if __name__ == "__main__":
    unittest.main()
