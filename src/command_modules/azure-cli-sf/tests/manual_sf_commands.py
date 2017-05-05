# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from azure.cli.testsdk import (
    ScenarioTest, JMESPathCheck, JMESPathCheckExists
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

    package_path = "/media/share/EchoServerApplication3"
    package_name = "EchoServerApplication3"
    application_type_name = "EchoServerApp"
    application_type_version = "3.0"
    application_name = "fabric:/app1"
    application_id = "app1"

    # Application tests

    @SelectNoSecClusterPreparer()
    def sf_test_application_lifecycle(self):
        self.cmd("az sf application upload --path {}".format(
            self.package_path
        ))

        self.cmd(
            "az sf application provision "
            "--application-type-build-path {}".format(
                self.package_name
            )
        )

        self.cmd(
            "az sf application type",
            checks=[
                JMESPathCheck(
                    "items[0].name",
                    self.application_type_name
                ),
                JMESPathCheck(
                    "items[0].version",
                    self.application_type_version
                )
            ]
        )

        self.cmd(
            "az sf application create "
            "--app-type {} --version {} --name {}".format(
                self.application_type_name,
                self.application_type_version,
                self.application_name
            )
        )

        self.cmd(
            "az sf application list",
            checks=[
                JMESPathCheck("items[0].id", self.application_id)
            ]
        )

        self.cmd(
            "az sf application health "
            "--application-id {}".format(self.application_id),
            checks=[
                JMESPathCheck("name", self.application_name),
                JMESPathCheckExists("aggregatedHealthState")
            ]
        )

        self.cmd(
            "az sf application delete --application-id {}".format(
                self.application_id
            )
        )

        self.cmd(
            "az sf application unprovision "
            "--application-type-name {} "
            "--application-type-version {}".format(
                self.application_type_name, self.application_type_version
            )
        )
