# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import shutil
import os
import tempfile
from mock import patch
from azure.cli.testsdk import (
    ScenarioTest, JMESPathCheck, JMESPathCheckExists, NoneCheck
)

# Should be fixed unless recordings are being recreated for new versions of Service Fabric
test_endpoint = "http://eddertester.westus2.cloudapp.azure.com:19080"
test_node_name = "_Derp_0"
test_partition_id = "00000000-0000-0000-0000-000000000001"
test_replica_id = "131413730902833907"


# pylint: disable=too-many-public-methods
class ServiceFabricScenarioTests(ScenarioTest):

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def app_health_returns_aggregated_and_name_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf application health --application-id \"System\"",
                 checks=[JMESPathCheck("name", "fabric:/System"),
                         JMESPathCheckExists("aggregatedHealthState")])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def app_list_returns_items_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf application list", checks=[JMESPathCheck("items", [])])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def app_type_returns_none_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf application type", checks=[NoneCheck()])

    def valid_application_upload_path_returns_absolute_path_test(self):
        import azure.cli.command_modules.sf.custom as sf_c
        temp_dir_path = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir_path, ignore_errors=True))
        self.assertTrue(os.path.isabs(sf_c.validate_app_path(temp_dir_path)))

    @patch("azure.cli.command_modules.sf.config.SfConfigParser")
    def single_folder_large_file_upload_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        # Specifically need a large temporary file in a temporary directory
        temp_app_dir = tempfile.mkdtemp()
        dest_app_dir = os.path.join(os.path.dirname(temp_app_dir), "tempdir00")
        os.rename(temp_app_dir, dest_app_dir)
        fd, file_path = tempfile.mkstemp(dir=dest_app_dir)
        os.close(fd)
        dest_file_path = os.path.join(dest_app_dir, "tempfile00")
        os.rename(file_path, dest_file_path)
        self.test_resources_count += 2
        self.addCleanup(lambda: shutil.rmtree(dest_app_dir, ignore_errors=True))

        with open(dest_file_path, mode='r+b') as f:
            chunk = bytearray([0] * 1024)
            for _ in range(5000):
                f.write(chunk)

        self.cmd("az sf application upload --path {0} --show-progress".format(dest_app_dir), checks=[NoneCheck()])

    # Cluster tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def cluster_code_version_returns_not_empty_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf cluster code-version", checks=[JMESPathCheckExists("[0].codeVersion")])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def cluster_config_version_returns_not_empty_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf cluster config-version", checks=[JMESPathCheckExists("[0].configVersion")])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def cluster_health_returns_aggregated_states_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf cluster health", checks=[
            JMESPathCheckExists("aggregatedHealthState"),
            JMESPathCheck("applicationHealthStates[0].name", "fabric:/System"),
            JMESPathCheckExists("nodeHealthStates")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def cluster_manifest_returns_non_empty_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf cluster manifest", checks=[JMESPathCheckExists("manifest")])

    # Compose tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def compose_list_returns_empty_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf compose list", checks=[JMESPathCheck("continuationToken", "")])

    # Node tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def node_list_returns_non_empty_ids_and_names_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf node list", checks=[
            JMESPathCheckExists("items[0].id.id"),
            JMESPathCheckExists("items[0].name")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def node_load_returns_non_empty_load_metrics(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        self.cmd("az sf node load --node-name {0}".format(test_node_name), checks=[
            JMESPathCheckExists("nodeLoadMetricInformation")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def node_system_service_replica_list_returns_non_empty_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf node replica-list --application-id System --node-name {0}"
        command = command.format(test_node_name)
        self.cmd(command, checks=[
            JMESPathCheckExists("[0].replicaRole"),
            JMESPathCheckExists("[0].replicaStatus")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def node_system_service_package_list_returns_non_empty_list_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf node service-package-list --application-id System --node-name {0}"
        command = command.format(test_node_name)
        self.cmd(command, checks=[
            JMESPathCheckExists("[0].name"),
            JMESPathCheckExists("[0].status")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def node_system_type_list_returns_non_empty_list_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf node service-type-list --application-id System --node-name {0}"
        command = command.format(test_node_name)
        self.cmd(command, checks=[
            JMESPathCheckExists("[0].codePackageName"),
            JMESPathCheckExists("[0].serviceTypeName")
        ])

    # Partition tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def system_partition_health_returns_aggregated_state_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf partition health --partition-id 00000000-0000-0000-0000-000000000001"
        self.cmd(command, checks=[
            JMESPathCheckExists("aggregatedHealthState"),
            JMESPathCheck("partitionId", "00000000-0000-0000-0000-000000000001")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def system_partition_info_returns_service_kind_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf partition info --partition-id 00000000-0000-0000-0000-000000000001"
        self.cmd(command, checks=[
            JMESPathCheck("ServiceKind", "Stateful"),
            JMESPathCheck("partitionInformation.id", "00000000-0000-0000-0000-000000000001")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def partition_name_system_service_returns_correct_name_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf partition service-name --partition-id 00000000-0000-0000-0000-000000000001"
        self.cmd(command, checks=[
            JMESPathCheck("id", "System/FailoverManagerService"),
            JMESPathCheck("name", "fabric:/System/FailoverManagerService")
        ])

    # Replica tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def replica_health_system_service_returns_aggregated_state_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf replica health --replica-id {0} --partition-id {1}"
        command = command.format(test_replica_id, test_partition_id)
        self.cmd(command, checks=[
            JMESPathCheck("partitionId", test_partition_id),
            JMESPathCheck("replicaId", test_replica_id),
            JMESPathCheckExists("aggregatedHealthState")
        ])

    # Service tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def service_application_name_returns_correct_system_name_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf service application-name --service-id System/FailoverManagerService"
        self.cmd(command, checks=[
            JMESPathCheck("id", "System"),
            JMESPathCheck("name", "fabric:/System")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def service_description_returns_correct_kind_and_name_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf service description --service-id System/FailoverManagerService"
        self.cmd(command, checks=[
            JMESPathCheck("ServiceKind", "Stateful"),
            JMESPathCheck("serviceName", "fabric:/System/FailoverManagerService")
        ])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def service_health_returns_system_services_aggregated_state_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf service health --service-id System/FailoverManagerService"
        self.cmd(command, checks=[JMESPathCheckExists("aggregatedHealthState"),
                                  JMESPathCheck("name", "fabric:/System/FailoverManagerService")])

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def service_list_returns_system_services_test(self, mock_config_parser):
        instance = mock_config_parser.return_value
        instance.no_verify_setting.return_value = False
        instance.ca_cert_info.return_value = False
        instance.connection_endpoint.return_value = test_endpoint
        instance.cert_info.return_value = False

        command = "az sf service list --application-id System"
        self.cmd(command, checks=[JMESPathCheckExists("items")])
