# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, DEFAULT_LOCATION
from .server_preparer import ServerPreparer

class FlexibleServerFabricMirroringMgmtScenarioTest(ScenarioTest):
    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_fabric_mirroring_mgmt(self, resource_group, server):
        self._test_fabric_mirroring_mgmt(resource_group, server)


    def _test_fabric_mirroring_mgmt(self, resource_group, server):
        # create a database
        database2_name = 'flexibleserverdb'
        self.cmd('postgres flexible-server db create -g {} -s {} -d {}'.format(resource_group, server, database2_name),
                 checks=[JMESPathCheck('name', database2_name)])

        # enable system assigned managed identity
        self.cmd('postgres flexible-server identity update -g {} -s {} --system-assigned Enabled'
                 .format(resource_group, server),
                 checks=[JMESPathCheck('type', 'SystemAssigned')])

        # enable fabric mirroring
        database1 = 'postgres'
        self.cmd('postgres flexible-server fabric-mirroring start -g {} --server-name {} --database-names {} --yes'
                    .format(resource_group, server, database1))
        self.cmd('postgres flexible-server parameter show --name azure.fabric_mirror_enabled -g {} -s {}'.format(resource_group, server),
                 checks=[JMESPathCheck('value', 'on')])
        self.cmd('postgres flexible-server parameter show --name azure.mirror_databases -g {} -s {}'.format(resource_group, server),
                 checks=[JMESPathCheck('value', database1)])

        # update mirrored database
        self.cmd('postgres flexible-server fabric-mirroring update-databases -g {} --server-name {} --database-names {} --yes'
                 .format(resource_group, server, database2_name),
                 checks=[JMESPathCheck('value', database2_name)])

        # disable fabric mirroring
        self.cmd('postgres flexible-server fabric-mirroring stop -g {} --server-name {} --yes'
                 .format(resource_group, server))
        self.cmd('postgres flexible-server parameter show --name azure.fabric_mirror_enabled -g {} -s {}'.format(resource_group, server),
                 checks=[JMESPathCheck('value', 'off')])