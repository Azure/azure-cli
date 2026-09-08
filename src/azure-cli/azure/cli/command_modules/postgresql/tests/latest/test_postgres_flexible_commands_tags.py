# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
from datetime import datetime, timezone
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


def _unique_tag_subset_check(tags):
    unique_tags = {}
    for tag in tags.split():
        key, value = tag.split('=', 1)
        unique_tags[key] = value

    if not unique_tags:
        return JMESPathCheck('tags', {})

    subset_query = 'tags.{{{}}}'.format(', '.join('{0}: {0}'.format(key) for key in unique_tags))
    return JMESPathCheck(subset_query, unique_tags)


class PostgreSQLFlexibleServerTagsMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_tags_mgmt(self, resource_group):
        self._test_flexible_server_tags_mgmt(resource_group)

    def _test_flexible_server_tags_mgmt(self, resource_group):

        initial_tags = "tag1=value1 tag2=value2 tag3=value3"
        new_tags = "tag4=value4 tag5=value5"
        new_repeated_tags = "tag6=value6a tag6=value6b tag7=value7"
        # Following two are defined for the future, for when backend supports properly using passed tags to restore and revive operations.
        restored_server_tags = "tag8=value8 tag9=value9"
        revived_server_tags = "tag10=value10 tag11=value11"

        # Create server.
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location

        primary_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        first_level_replica_1 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        first_level_replica_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        cascade_replica_1 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        cascade_replica_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restored_server_1 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restored_server_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        revive_dropped_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        # Create server with three tags.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tags {} --public-access enabled --yes'
                 .format(resource_group, primary_server, location, initial_tags))

        # Validate that tags are added to the created server.
        self.cmd('postgres flexible-server show -g {} -n {}'
                                 .format(resource_group, primary_server),
                                 checks=[_unique_tag_subset_check(initial_tags)])

        # Update server tags with two new tags, and validate that the original tags are removed and only the new tags are present on the server.
        self.cmd('postgres flexible-server update -g {} -n {} --tags {}'
                 .format(resource_group, primary_server, new_tags),
                 checks=[_unique_tag_subset_check(new_tags)])

        # Update server tags with two new repeated tags, and validate that only one of the repeated tags is present along with the other new tag, while all original tags are removed from the server.
        self.cmd('postgres flexible-server update -g {} -n {} --tags {}'
                 .format(resource_group, primary_server, new_repeated_tags),
                 checks=[_unique_tag_subset_check(new_repeated_tags)])

        # Stop server.
        self.cmd('postgres flexible-server stop -g {} -n {}'.format(resource_group, primary_server))

        # Update server tags with original tags while server is stopped. Not supported for flexible server. Expect failure.
        self.cmd('postgres flexible-server update -g {} -n {} --tags {}'
                 .format(resource_group, primary_server, initial_tags), expect_failure=True)

        # Start server.
        self.cmd('postgres flexible-server start -g {} -n {}'.format(resource_group, primary_server))

        # Update server tags with original tags. Should succeed now that server is started.
        self.cmd('postgres flexible-server update -g {} -n {} --tags {}'
                 .format(resource_group, primary_server, initial_tags),
                 checks=[_unique_tag_subset_check(initial_tags)])
        
        # Add a first level read replica to the server and don't provide tags, to validate that tags are inherited from its source server.
        self.cmd('postgres flexible-server replica create -g {} -n {} --source-server {} --location {} --yes'
                 .format(resource_group, first_level_replica_1, primary_server, location),
                 checks=[_unique_tag_subset_check(initial_tags)])

        # Add a cascade read replica to the first read replica and provide tags, to validate that these provided tags are properly set on cascade replica.
        self.cmd('postgres flexible-server replica create -g {} -n {} --source-server {} --location {} --tags {} --yes'
                 .format(resource_group, cascade_replica_1, first_level_replica_1, location, new_repeated_tags),
                 checks=[_unique_tag_subset_check(new_repeated_tags)])

        # Add a first level read replica to the server and provide tags, to validate that these provided tags are properly set on the first level replica.
        self.cmd('postgres flexible-server replica create -g {} -n {} --source-server {} --location {} --tags {} --yes'
                 .format(resource_group, first_level_replica_2, primary_server, location, new_repeated_tags),
                 checks=[_unique_tag_subset_check(new_repeated_tags)])

        # Add a cascade read replica to the second read replica and provide tags, to validate that these provided tags are properly set on the cascade replica.
        self.cmd('postgres flexible-server replica create -g {} -n {} --source-server {} --location {} --tags {} --yes'
                 .format(resource_group, cascade_replica_2, first_level_replica_2, location, ""),
                 checks=[_unique_tag_subset_check("")])
        
        # Confirm that primary server has at least one backup before testing restore with tags, as restore operation requires a backup to be present.
        self.cmd('postgres flexible-server backup list -g {} -s {}'.format(resource_group, primary_server),
                 checks=[JMESPathCheck("length(@) >= `1`", True)])

        restore_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Restore server from backup without specific tags, to validate that tags on the restored server are inherited from those on the source server.
        self.cmd('postgres flexible-server restore -g {} -n {} --source-server {} --restore-time {} --yes'
                 .format(resource_group, restored_server_1, primary_server, restore_time_utc),
                 checks=[_unique_tag_subset_check(initial_tags)])
        
        # Update server tags with empty tags.
        self.cmd('postgres flexible-server update -g {} -n {} --tags {}'
                 .format(resource_group, primary_server, ""),
                 checks=[_unique_tag_subset_check("")])

        # Restore server from backup without specific tags, to validate that tags on the restored server are inherited from those on the source server.
        self.cmd('postgres flexible-server restore -g {} -n {} --source-server {} --restore-time {} --yes'
                 .format(resource_group, restored_server_2, primary_server, restore_time_utc),
                 checks=[_unique_tag_subset_check("")])

        # Update server tags with original tags.
        self.cmd('postgres flexible-server update -g {} -n {} --tags {}'
                 .format(resource_group, primary_server, initial_tags),
                 checks=[_unique_tag_subset_check(initial_tags)])
        
        # Fetch primary server resource identifier to be used as source server for revive operation.
        primary_server_resource_id = self.cmd('postgres flexible-server show -g {} -n {} --query id -o tsv'
                                            .format(resource_group, primary_server)).output.strip()

        # Delete servers in dependency order: deepest replicas first, then their source servers.
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, cascade_replica_1),
                 checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, cascade_replica_2),
                 checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, first_level_replica_1),
                 checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, first_level_replica_2),
                 checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, primary_server),
                 checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, restored_server_1),
                 checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, restored_server_2),
                 checks=NoneCheck())

        # Sleep for 5 minutes to ensure that the deleted primary server is fully deleted before attempting revive operation, as revive operation on a server that is not fully deleted is not allowed.
        os.environ.get(ENV_LIVE_TEST, False) and time.sleep(5 * 60)

        # Revive dropped server without specific tags, to validate that tags on the revived server are inherited from those on the tombstoned server.
        self.cmd('postgres flexible-server revive-dropped -g {} -n {} --source-server {} --location {}'
                 .format(resource_group, revive_dropped_server, primary_server_resource_id, location),
                 checks=[_unique_tag_subset_check(initial_tags)])
        
        # Delete revived server to clean up after test.
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, revive_dropped_server),
                 checks=NoneCheck())
