# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError
from azure.cli.core.util import sdk_no_wait
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from knack.log import get_logger
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import check_resource_group, validate_citus_cluster, validate_resource_group

logger = get_logger(__name__)


def flexible_server_restart(cmd, client, resource_group_name, server_name, fail_over=None):
    validate_resource_group(resource_group_name)
    instance = client.get(resource_group_name, server_name)
    if fail_over is not None and instance.high_availability.mode not in ("ZoneRedundant", "SameZone"):
        raise ArgumentUsageError("Failing over can only be triggered for zone redundant or same zone servers.")

    if fail_over is not None:
        validate_citus_cluster(cmd, resource_group_name, server_name)
        if fail_over.lower() not in ['planned', 'forced']:
            raise InvalidArgumentValueError("Allowed failover parameters are 'Planned' and 'Forced'.")
        if fail_over.lower() == 'planned':
            fail_over = 'plannedFailover'
        elif fail_over.lower() == 'forced':
            fail_over = 'forcedFailover'
        parameters = postgresql_flexibleservers.models.RestartParameter(restart_with_failover=True,
                                                                        failover_mode=fail_over)
    else:
        parameters = postgresql_flexibleservers.models.RestartParameter(restart_with_failover=False)

    return resolve_poller(
        client.begin_restart(resource_group_name, server_name, parameters), cmd.cli_ctx, 'PostgreSQL Server Restart')


def flexible_server_stop(client, resource_group_name=None, server_name=None, no_wait=False):
    if not check_resource_group(resource_group_name):
        resource_group_name = None

    days = 7
    logger.warning("Server will be automatically started after %d days "
                   "if you do not perform a manual start operation", days)
    return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, server_name)
