# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from azure.cli.testsdk import (
    ScenarioTest, JMESPathCheck, JMESPathCheckExists, NoneCheck
)
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.preparers import AbstractPreparer
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


class SelectNoSecClusterPreparer(AbstractPreparer):
    def __init__(self, parameter_name="endpoint",
                 endpoint="http://127.0.0.1:10550",
                 env_variable_name="AZURE_CLI_SF_ENDPOINT"):
        # Name randomization unnecessary
        super(SelectNoSecClusterPreparer, self).__init__("test", 10)
        self.endpoint = endpoint
        self.parameter_name = parameter_name
        self.env_variable_name = env_variable_name

    def create_resource(self, _, **kwargs):
        # Omit name here since there is no randomization required
        endpoint = os.environ.get(self.env_variable_name, self.endpoint)
        logger.debug("endpoint %s", endpoint)
        template = "az sf cluster select --endpoint {}"
        execute(template.format(endpoint))
        return {self.parameter_name: endpoint}


class ServiceFabricTests(ScenarioTest):

    # Application tests

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_app_health(self):
        self.cmd(
            "az sf application health --application-id \"System\"",
            checks=[
                JMESPathCheck("name", "fabric:/System"),
                JMESPathCheckExists("aggregatedHealthState")
            ]
        )

    @SelectNoSecClusterPreparer()
    def sf_test_good_none_app_type(self):
        self.cmd("az sf application type", checks=[NoneCheck()])

    @SelectNoSecClusterPreparer()
    def sf_test_good_none_app_list(self):
        self.cmd("az sf application list", checks=[
            JMESPathCheck("items", [])
        ])

    # Service tests

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_service_list(self):
        self.cmd("az sf service list --application-id \"System\"", checks=[
            JMESPathCheck(
                "items[? id == `\"System/ClusterManagerService\"`].name | [0]",
                "fabric:/System/ClusterManagerService"),
        ])

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_service_app_name(self):
        self.cmd("az sf service application-name --service-id "
                 "System/ClusterManagerService", checks=[
                     JMESPathCheck("id", "System"),
                     JMESPathCheck("name", "fabric:/System")])

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_service_health(self):
        self.cmd("az sf service health --service-id "
                 "System/ClusterManagerService", checks=[
                     JMESPathCheck("name",
                                   "fabric:/System/ClusterManagerService"),
                     JMESPathCheckExists("partitionHealthStates"),
                     JMESPathCheckExists("healthEvents")])

    @SelectNoSecClusterPreparer()
    def sf_test_good_resolve_system_service(self):
        self.cmd("az sf service resolve --service-id "
                 "System/FailoverManagerService")

    # Partition tests

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_partition_info(self):
        self.cmd(
            "az sf partition info --partition-id "
            "00000000-0000-0000-0000-000000000001",
            checks=[
                JMESPathCheckExists("ServiceKind"),
                JMESPathCheck("partitionInformation.id",
                              "00000000-0000-0000-0000-000000000001")
            ]
        )

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_partition_service_name(self):
        self.cmd(
            "az sf partition service-name --partition-id "
            "00000000-0000-0000-0000-000000000001",
            checks=[
                JMESPathCheck("name",
                              "fabric:/System/FailoverManagerService"),
                JMESPathCheck("id", "System/FailoverManagerService")
            ]
        )

    @SelectNoSecClusterPreparer()
    def sf_test_good_system_partition_health(self):
        self.cmd(
            "az sf partition health --partition-id "
            "00000000-0000-0000-0000-000000000001",
            checks=[
                JMESPathCheck("partitionId",
                              "00000000-0000-0000-0000-000000000001"),
                JMESPathCheckExists("replicaHealthStates"),
                JMESPathCheckExists("healthEvents")
            ]
        )

    # Node tests

    @SelectNoSecClusterPreparer()
    def sf_test_good_node_list(self):
        self.cmd("az sf node list", checks=[
            JMESPathCheckExists("items[0].id.id"),
            JMESPathCheckExists("items[0].name")
        ])

    # Cluster tests

    @SelectNoSecClusterPreparer()
    def sf_test_good_cluster_manifest(self):
        self.cmd("az sf cluster manifest", checks=[
            JMESPathCheckExists("manifest")
        ])

    @SelectNoSecClusterPreparer()
    def sf_test_good_cluster_code_version(self):
        self.cmd("az sf cluster code-version", checks=[
            JMESPathCheckExists("[0].codeVersion")
        ])

    @SelectNoSecClusterPreparer()
    def sf_test_good_cluster_config_version(self):
        self.cmd("az sf cluster config-version", checks=[
            JMESPathCheckExists("[0].configVersion")
        ])

    @SelectNoSecClusterPreparer()
    def sf_test_good_cluster_health(self):
        self.cmd("az sf cluster health", checks=[
            JMESPathCheckExists("aggregatedHealthState"),
            JMESPathCheck("applicationHealthStates[0].name", "fabric:/System"),
            JMESPathCheckExists("nodeHealthStates")
        ])

    # Compose tests

    @SelectNoSecClusterPreparer()
    def sf_test_good_none_compose_list(self):
        self.cmd("az sf compose list", checks=[NoneCheck()])
