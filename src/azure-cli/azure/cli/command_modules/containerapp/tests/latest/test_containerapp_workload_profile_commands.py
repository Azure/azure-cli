# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import yaml

from azure.cli.core.azclierror import ValidationError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, JMESPathCheckNotExists,
                               JMESPathCheckExists)

from azure.cli.command_modules.containerapp.tests.latest.common import (write_test_file, clean_up_test_file)
from .common import TEST_LOCATION

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppWorkloadProfilesTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    def test_containerapp_env_workload_profiles_list_supported(self):
        self.cmd('containerapp env workload-profile list-supported -l northeurope', checks=[
            JMESPathCheck('[?name==`NC48-A100`].properties.gpus', [2]),
            JMESPathCheck('[?name==`NC96-A100`].properties.gpus', [4]),
            JMESPathCheckExists('[?name==`NC48-A100`]'),
            JMESPathCheckExists('[?name==`NC96-A100`]'),
            JMESPathCheckExists('[?name==`D4`]'),
            JMESPathCheckExists('[?name==`D8`]'),
            JMESPathCheckExists('[?name==`D16`]'),
            JMESPathCheckExists('[?name==`D32`]'),
            JMESPathCheckExists('[?name==`E4`]'),
            JMESPathCheckExists('[?name==`E8`]'),
            JMESPathCheckExists('[?name==`E16`]'),
            JMESPathCheckExists('[?name==`E32`]'),
            JMESPathCheckExists('[?name==`Consumption`]'),
            JMESPathCheck('[?name==`D4`].properties.category', ["GeneralPurpose"]),
            JMESPathCheck('[?name==`D4`].properties.cores', [4]),
            JMESPathCheck('[?name==`D4`].properties.displayName', ["Dedicated-D4"]),
            JMESPathCheck('[?name==`D4`].properties.memoryGiB', [16]),
        ])

        self.cmd('containerapp env workload-profile list-supported -l eastus', checks=[
            JMESPathCheckNotExists('[?name==`NC48-A100`]'),
            JMESPathCheckNotExists('[?name==`NC96-A100`]'),
            JMESPathCheckExists('[?name==`D4`]'),
            JMESPathCheckExists('[?name==`D8`]'),
            JMESPathCheckExists('[?name==`D16`]'),
            JMESPathCheckExists('[?name==`D32`]'),
            JMESPathCheckExists('[?name==`E4`]'),
            JMESPathCheckExists('[?name==`E8`]'),
            JMESPathCheckExists('[?name==`E16`]'),
            JMESPathCheckExists('[?name==`E32`]'),
            JMESPathCheckExists('[?name==`Consumption`]'),
            JMESPathCheck('[?name==`D4`].properties.category', ["GeneralPurpose"]),
            JMESPathCheck('[?name==`D4`].properties.cores', [4]),
            JMESPathCheck('[?name==`D4`].properties.displayName', ["Dedicated-D4"]),
            JMESPathCheck('[?name==`D4`].properties.memoryGiB', [16]),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_env_workload_profiles_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        vnet = self.create_random_name(prefix='name', length=24)
        app1 = self.create_random_name(prefix='app1', length=24)
        app2 = self.create_random_name(prefix='app2', length=24)

        self.cmd('containerapp env create -g {} -n {} --location {}  --logs-destination none --enable-workload-profiles'.format(resource_group, env, TEST_LOCATION))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(60)

        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd("az containerapp env workload-profile list-supported -l {}".format(TEST_LOCATION))

        profiles = self.cmd("az containerapp env workload-profile list -g {} -n {}".format(resource_group, env)).get_output_in_json()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]["properties"]["name"].lower(), "consumption")
        self.assertEqual(profiles[0]["properties"]["workloadProfileType"].lower(), "consumption")

        self.cmd("az containerapp env workload-profile add -g {} -n {} --workload-profile-name my-d4 --workload-profile-type D4 --min-nodes 2 --max-nodes 3".format(resource_group, env))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(60)
        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd("az containerapp env workload-profile show -g {} -n {} --workload-profile-name my-d4 ".format(resource_group, env), checks=[
            JMESPathCheck("properties.name", "my-d4"),
            JMESPathCheck("properties.maximumCount", 3),
            JMESPathCheck("properties.minimumCount", 2),
            JMESPathCheck("properties.workloadProfileType", "D4"),
        ])

        self.cmd("az containerapp env workload-profile update -g {} -n {} --workload-profile-name my-d4 --min-nodes 1 --max-nodes 2".format(resource_group, env))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(60)
        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd("az containerapp env workload-profile show -g {} -n {} --workload-profile-name my-d4 ".format(resource_group, env), checks=[
            JMESPathCheck("properties.name", "my-d4"),
            JMESPathCheck("properties.maximumCount", 2),
            JMESPathCheck("properties.minimumCount", 1),
            JMESPathCheck("properties.workloadProfileType", "D4"),
        ])

        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --environment {} -n {} --workload-profile-name Consumption".format(resource_group, env, app1))
        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --environment {} -n {} --workload-profile-name my-d4".format(resource_group, env, app2))
        self.cmd('containerapp delete -g {} -n {} --yes'.format(resource_group, app1), expect_failure=False)
        self.cmd('containerapp delete -g {} -n {} --yes'.format(resource_group, app2), expect_failure=False)
        self.cmd('containerapp env delete -g {} -n {} --yes'.format(resource_group, env), expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_create_enable_workload_profiles_three_state_flag(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        self.cmd('containerapp env create -g {} -n {} --logs-destination none --enable-workload-profiles false'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.workloadProfiles", None),
        ])

        with self.assertRaisesRegex(ValidationError,
                                     "Cannot add workload profile because the environment doesn't enable workload profile.\n"
                                     "If you want to use Consumption and Dedicated environment, please create a new one with 'az containerapp env create'."):
            self.cmd(
                'containerapp env workload-profile add -w wp -g {} -n {} --workload-profile-type D4 --min-nodes 1 --max-nodes 2'.format(
                    resource_group, env))

        with self.assertRaisesRegex(ValidationError,
                                     "Cannot update workload profile because the environment doesn't enable workload profile.\n"
                                     "If you want to use Consumption and Dedicated environment, please create a new one with 'az containerapp env create'."):
            self.cmd(
                'containerapp env workload-profile update -w wp -g {} -n {} --min-nodes 1 --max-nodes 2'.format(
                    resource_group, env))

        self.cmd('containerapp env delete -g {} -n {} --yes --no-wait'.format(resource_group, env), expect_failure=False)

        env1 = self.create_random_name(prefix='env1', length=24)
        self.cmd('containerapp env create -g {} -n {} --logs-destination none'.format(
            resource_group, env1), expect_failure=False, checks=[
            JMESPathCheck("name", env1),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])
        self.cmd('containerapp env delete -g {} -n {} --yes --no-wait'.format(resource_group, env1), expect_failure=False)

        env2 = self.create_random_name(prefix='env2', length=24)
        self.cmd('containerapp env create -g {} -n {} --logs-destination none --enable-workload-profiles'.format(
            resource_group, env2), expect_failure=False, checks=[
            JMESPathCheck("name", env2),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])
        self.cmd('containerapp env delete -g {} -n {} --yes --no-wait'.format(resource_group, env2),
                 expect_failure=False)

        env3 = self.create_random_name(prefix='env3', length=24)
        self.cmd('containerapp env create -g {} -n {} --logs-destination none --enable-workload-profiles true'.format(
            resource_group, env3), expect_failure=False, checks=[
            JMESPathCheck("name", env3),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])
        self.cmd('containerapp env delete -g {} -n {} --yes --no-wait'.format(resource_group, env3), expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_env_workload_profiles_delete(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        vnet = self.create_random_name(prefix='name', length=24)

        self.cmd("az network vnet create -l {} --address-prefixes '14.0.0.0/16' -g {} -n {}".format(TEST_LOCATION, resource_group, vnet))
        sub_id = self.cmd("az network vnet subnet create --address-prefixes '14.0.0.0/22' --delegations Microsoft.App/environments -n sub -g {} --vnet-name {}".format(resource_group, vnet)).get_output_in_json()["id"]

        self.cmd('containerapp env create -g {} -n {} -s {} --location {}  --logs-destination none --enable-workload-profiles'.format(resource_group, env, sub_id, TEST_LOCATION))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(30)

        self.cmd("az containerapp env workload-profile add -g {} -n {} --workload-profile-name my-d8 --workload-profile-type D8 --min-nodes 1 --max-nodes 1".format(resource_group, env))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(30)

        self.cmd("az containerapp env workload-profile show -g {} -n {} --workload-profile-name my-d8 ".format(resource_group, env), checks=[
            JMESPathCheck("properties.name", "my-d8"),
            JMESPathCheck("properties.maximumCount", 1),
            JMESPathCheck("properties.minimumCount", 1),
            JMESPathCheck("properties.workloadProfileType", "D8"),
        ])

        profiles = self.cmd("az containerapp env workload-profile list -g {} -n {}".format(resource_group, env)).get_output_in_json()
        self.assertEqual(len(profiles), 2)

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(30)

        self.cmd("az containerapp env workload-profile delete -g {} -n {} --workload-profile-name my-d8 ".format(resource_group, env))

        profiles = self.cmd("az containerapp env workload-profile list -g {} -n {}".format(resource_group, env)).get_output_in_json()
        self.assertEqual(len(profiles), 1)
        self.cmd('containerapp env delete -g {} -n {} --yes'.format(resource_group, env), expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_create_with_workloadprofile_yaml(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='yaml', length=24)

        containerapp_env = self.cmd('containerapp env create -g {} -n {} --location {}  --logs-destination none --enable-workload-profiles'.format(resource_group, env, TEST_LOCATION)).get_output_in_json()
        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(120)

        self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env), checks=[
            JMESPathCheck('name', env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ]).get_output_in_json()

        workload_profile_name = "my-e16"

        self.cmd("az containerapp env workload-profile add -g {} -n {} --workload-profile-name {} --workload-profile-type E16 --min-nodes 1 --max-nodes 3".format(resource_group, env, workload_profile_name))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(30)

        self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env), checks=[
            JMESPathCheck('name', env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ]).get_output_in_json()

        self.cmd("az containerapp env workload-profile show -g {} -n {} --workload-profile-name my-e16 ".format(resource_group, env), checks=[
            JMESPathCheck("properties.name", workload_profile_name),
            JMESPathCheck("properties.maximumCount", 3),
            JMESPathCheck("properties.minimumCount", 1),
            JMESPathCheck("properties.workloadProfileType", "E16"),
        ])

        revision_01 = "revision01"
        containerapp_yaml_text_01 = f"""
            location: {TEST_LOCATION}
            type: Microsoft.App/containerApps
            tags:
                tagname: value
            properties:
              managedEnvironmentId: {containerapp_env["id"]}
              workloadProfileName: {workload_profile_name}
              configuration:
                activeRevisionsMode: Multiple
                ingress:
                  external: true
                  allowInsecure: false
                  targetPort: 80
                  traffic:
                    - latestRevision: true
                      weight: 100
                  transport: Auto
                  ipSecurityRestrictions:
                    - name: name
                      ipAddressRange: "1.1.1.1/10"
                      action: "Allow"
              template:
                revisionSuffix: {revision_01}
                containers:
                  - image: nginx
                    name: nginx
                    env:
                      - name: HTTP_PORT
                        value: 80
                    command:
                      - npm
                      - start
                    resources:
                      cpu: 10.0
                      memory: 5Gi
                scale:
                  minReplicas: 1
                  maxReplicas: 3
            """
        containerapp_file_name_01 = f"{self._testMethodName}_containerapp_01.yml"

        write_test_file(containerapp_file_name_01, containerapp_yaml_text_01)
        self.cmd(f'containerapp create -n {app} -g {resource_group} --environment {env} --yaml {containerapp_file_name_01}')

        self.assertContainerappProperties(containerapp_env, resource_group, app, workload_profile_name, revision_01, "10.0", "5Gi")

        revision_02 = "revision02"
        containerapp_yaml_text_02 = containerapp_yaml_text_01.replace(workload_profile_name, "Consumption")
        containerapp_yaml_text_02 = containerapp_yaml_text_02.replace("cpu: 10.0", "cpu: 0.5")
        containerapp_yaml_text_02 = containerapp_yaml_text_02.replace("memory: 5Gi", "memory: 1Gi")
        containerapp_yaml_text_02 = containerapp_yaml_text_02.replace(revision_01, revision_02)

        containerapp_file_name_02 = f"{self._testMethodName}_containerapp_02.yml"
        write_test_file(containerapp_file_name_02, containerapp_yaml_text_02)

        self.cmd(f'containerapp update -n {app} -g {resource_group} --yaml {containerapp_file_name_02}')

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(30)

        self.assertContainerappProperties(containerapp_env, resource_group, app, "Consumption", revision_02, "0.5", "1Gi")

        clean_up_test_file(containerapp_file_name_01)
        clean_up_test_file(containerapp_file_name_02)
        self.cmd('containerapp delete -g {} -n {} --yes'.format(resource_group, app), expect_failure=False)
        self.cmd('containerapp env delete -g {} -n {} --yes --no-wait'.format(resource_group, env), expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_env_workload_profiles_e2e_no_waits(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        vnet = self.create_random_name(prefix='name', length=24)
        app1 = self.create_random_name(prefix='app1', length=24)
        app2 = self.create_random_name(prefix='app2', length=24)

        self.cmd('containerapp env create -g {} -n {} --location {}  --logs-destination none --enable-workload-profiles'.format(resource_group, env, TEST_LOCATION))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() in ["waiting", "inprogress"]:
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()
        time.sleep(30)

        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd("az containerapp env workload-profile list-supported -l {}".format(TEST_LOCATION))

        profiles = self.cmd("az containerapp env workload-profile list -g {} -n {}".format(resource_group, env)).get_output_in_json()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]["properties"]["name"].lower(), "consumption")
        self.assertEqual(profiles[0]["properties"]["workloadProfileType"].lower(), "consumption")

        self.cmd("az containerapp env workload-profile add -g {} -n {} --workload-profile-name my-d4 --workload-profile-type D4 --min-nodes 2 --max-nodes 3".format(resource_group, env))

        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --revision-suffix suf1 --environment {} -n {} --workload-profile-name my-d4 --cpu 0.5 --memory 1Gi".format(resource_group, env, app1))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        self.cmd(f'containerapp show -g {resource_group} -n {app1}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.template.revisionSuffix", "suf1"),
            JMESPathCheck("properties.workloadProfileName", "my-d4"),
            JMESPathCheck("properties.template.containers[0].resources.cpu", "0.5"),
            JMESPathCheck("properties.template.containers[0].resources.memory", "1Gi")
        ])

        self.cmd("az containerapp env workload-profile update -g {} -n {} --workload-profile-name my-d4 --min-nodes 1 --max-nodes 2".format(resource_group, env))

        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --revision-suffix suf2 --environment {} -n {} --workload-profile-name my-d4 --cpu 0.5 --memory 1Gi".format(resource_group, env, app2))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.template.revisionSuffix", "suf2"),
            JMESPathCheck("properties.workloadProfileName", "my-d4"),
            JMESPathCheck("properties.template.containers[0].resources.cpu", "0.5"),
            JMESPathCheck("properties.template.containers[0].resources.memory", "1Gi")
        ])
        self.cmd('containerapp delete -g {} -n {} --yes'.format(resource_group, app1), expect_failure=False)
        self.cmd('containerapp delete -g {} -n {} --yes'.format(resource_group, app2), expect_failure=False)
        self.cmd('containerapp env delete -g {} -n {} --yes'.format(resource_group, env), expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_env_enable_workload_profiles_infer_env_type_v1(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='env', length=24)
        self.cmd('containerapp env create -g {} -n {} --logs-destination none --enable-workload-profiles false'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.workloadProfiles", None),
        ])

        self.cmd('containerapp env create -g {} -n {} --enable-workload-profiles --logs-destination none'.format(resource_group, env), expect_failure=True)
        self.cmd('containerapp env create -g {} -n {} -w --logs-destination none'.format(resource_group, env), expect_failure=True)

        self.cmd('containerapp env create -g {} -n {} -w false --logs-destination none'.format(resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.workloadProfiles", None),
        ])

        self.cmd('containerapp env create -g {} -n {} --enable-workload-profiles false --logs-destination none'.format(resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.workloadProfiles", None),
        ])

        self.cmd('containerapp env create -g {} -n {} --logs-destination none'.format(resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.workloadProfiles", None),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_env_enable_workload_profiles_infer_env_type_v2(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='env', length=24)
        self.cmd('containerapp env create -g {} -n {} --logs-destination none'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd('containerapp env create -g {} -n {} --logs-destination none'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd('containerapp env create -g {} -n {} --enable-workload-profiles --logs-destination none'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd('containerapp env create -g {} -n {} -w --logs-destination none'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd('containerapp env create -g {} -n {} --enable-workload-profiles false --logs-destination none'.format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])
        self.cmd('containerapp env create -g {} -n {} -w false --logs-destination none'.format(resource_group, env).format(
            resource_group, env), expect_failure=False, checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.workloadProfiles)", 1),
            JMESPathCheck('properties.workloadProfiles[0].name', "Consumption", case_sensitive=False),
            JMESPathCheck('properties.workloadProfiles[0].workloadProfileType', "Consumption", case_sensitive=False),
        ])

        self.cmd('containerapp env delete -g {} -n {} --yes --no-wait'.format(resource_group, env), expect_failure=False)

    def assertContainerappProperties(self, containerapp_env, rg, app, workload_profile_name, revision, cpu, mem):
        self.cmd(f'containerapp show -g {rg} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.ingress.external", True),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].name", "name"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].ipAddressRange", "1.1.1.1/10"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", revision),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3),
            JMESPathCheck("properties.workloadProfileName", workload_profile_name),
            JMESPathCheck("properties.template.containers[0].resources.cpu", cpu),
            JMESPathCheck("properties.template.containers[0].resources.memory", mem)
        ])