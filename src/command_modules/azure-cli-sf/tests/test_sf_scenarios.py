# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (
    ScenarioTest, JMESPathCheck, JMESPathCheckExists
)
import azure.cli.core.azlogging as azlogging
from mock import patch

logger = azlogging.get_az_logger(__name__)

# Should be fixed unless recordings are being recreated for new versions of Service Fabric
test_endpoint = "http://eddertester.westus2.cloudapp.azure.com:19080"


class ServiceFabricScenarioTests(ScenarioTest):

    # Application tests

    @patch("azure.cli.command_modules.sf._factory.SfConfigParser")
    def app_health_returns_aggregated_and_name_test(self):
        self.cmd(
            "az sf application health --application-id \"System\"",
            checks=[
                JMESPathCheck("name", "fabric:/System"),
                JMESPathCheckExists("aggregatedHealthState")
            ]
        )
