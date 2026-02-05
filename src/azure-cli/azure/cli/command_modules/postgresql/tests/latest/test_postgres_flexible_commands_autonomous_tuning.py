# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH

class FlexibleServerIndexTuningOptionsResourceMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_postgres_flexible_server_index_tuning_options(self, resource_group):
        self._test_index_tuning_options_mgmt(resource_group)

    def _test_index_tuning_options_mgmt(self, resource_group):

        # Create server with at least 4 vCores and running PostgreSQL major version of 13 or later
        location = DEFAULT_LOCATION
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        version = '16'
        storage_size = 128
        sku_name = 'Standard_D4ds_v4'
        tier = 'GeneralPurpose'

        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} --tier {} --storage-size {} --version {} -l {} --public-access none --yes'.format(
                 resource_group, server_name, sku_name, tier, storage_size, version, location))

        # Enable index tuning for server
        self.cmd('postgres flexible-server index-tuning update -g {} -s {} --enabled True'.format(resource_group, server_name),
                 checks=NoneCheck())

        # Show that index tuning is enabled
        self.cmd('postgres flexible-server index-tuning show -g {} -s {}'.format(resource_group, server_name),
                 checks=NoneCheck())

        # List settings associated with index tuning for server
        self.cmd('postgres flexible-server index-tuning list-settings -g {} -s {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # Show properties of index tuning setting for server
        self.cmd('postgres flexible-server index-tuning show-settings -g {} -s {} -n {}'.format(resource_group, server_name, 'mode'),
                 checks=[JMESPathCheck('value', 'report')])
        self.cmd('postgres flexible-server parameter show --name {} -g {} -s {}'.format('pg_qs.query_capture_mode', resource_group, server_name),
                 checks=[JMESPathCheck('value', 'all')])

        # Set new value of index tuning setting for server
        value = '1006'
        self.cmd('postgres flexible-server index-tuning set-settings -g {} -s {} -n {} -v {}'.format(resource_group, server_name,
                                                                                               'unused_reads_per_table', value),
                 checks=[JMESPathCheck('value', value)])

        # List recommendations associated with index tuning for server
        self.cmd('postgres flexible-server index-tuning list-recommendations -g {} -s {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # Disable index tuning for server
        self.cmd('postgres flexible-server index-tuning update -g {} -s {} --enabled False'.format(resource_group, server_name),
                 checks=NoneCheck())

        # Show properties of index tuning setting for server
        self.cmd('postgres flexible-server index-tuning show-settings -g {} -s {} -n {}'.format(resource_group, server_name, 'mode'),
                 checks=[JMESPathCheck('value', 'off')])

class FlexibleServerAutonomousTuningOptionsResourceMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_postgres_flexible_server_autonomous_tuning_options(self, resource_group):
        self._test_autonomous_tuning_options_mgmt(resource_group)

    def _test_autonomous_tuning_options_mgmt(self, resource_group):

        # Create server with at least 4 vCores and running PostgreSQL major version of 13 or later
        location = DEFAULT_LOCATION
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        version = '16'
        storage_size = 128
        sku_name = 'Standard_D4ds_v4'
        tier = 'GeneralPurpose'

        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} --tier {} --storage-size {} --version {} -l {} --public-access none --yes'.format(
                 resource_group, server_name, sku_name, tier, storage_size, version, location))

        # Enable autonomous tuning for server
        self.cmd('postgres flexible-server autonomous-tuning update -g {} -s {} --enabled True'.format(resource_group, server_name),
                 checks=NoneCheck())

        # Show that autonomous tuning is enabled
        self.cmd('postgres flexible-server autonomous-tuning show -g {} -s {}'.format(resource_group, server_name),
                 checks=NoneCheck())

        # List settings associated with autonomous tuning for server
        self.cmd('postgres flexible-server autonomous-tuning list-settings -g {} -s {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # Show properties of autonomous tuning setting for server
        self.cmd('postgres flexible-server autonomous-tuning show-settings -g {} -s {} -n {}'.format(resource_group, server_name, 'mode'),
                 checks=[JMESPathCheck('value', 'report')])
        self.cmd('postgres flexible-server parameter show --name {} -g {} -s {}'.format('pg_qs.query_capture_mode', resource_group, server_name),
                 checks=[JMESPathCheck('value', 'all')])

        # Set new value of autonomous tuning setting for server
        value = '1006'
        self.cmd('postgres flexible-server autonomous-tuning set-settings -g {} -s {} -n {} -v {}'.format(resource_group, server_name,
                                                                                               'unused_reads_per_table', value),
                 checks=[JMESPathCheck('value', value)])

        # List index recommendations associated with autonomous tuning for server
        self.cmd('postgres flexible-server autonomous-tuning list-index-recommendations -g {} -s {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # List table recommendations associated with autonomous tuning for server
        self.cmd('postgres flexible-server autonomous-tuning list-table-recommendations -g {} -s {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # Disable autonomous tuning for server
        self.cmd('postgres flexible-server autonomous-tuning update -g {} -s {} --enabled False'.format(resource_group, server_name),
                 checks=NoneCheck())

        # Show properties of autonomous tuning setting for server
        self.cmd('postgres flexible-server autonomous-tuning show-settings -g {} -s {} -n {}'.format(resource_group, server_name, 'mode'),
                 checks=[JMESPathCheck('value', 'off')])