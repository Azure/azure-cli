# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import CLIError
from azure.core.exceptions import HttpResponseError
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import validate_resource_group


def flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
    validate_resource_group(resource_group_name)
    parameter_value = value
    parameter_source = source
    try:
        # validate configuration name
        parameter = client.get(resource_group_name, server_name, configuration_name)

        # update the command with system default
        if parameter_value is None and parameter_source is None:
            parameter_value = parameter.default_value  # reset value to default

            # this should be 'system-default' but there is currently a bug in PG
            # this will reset source to be 'system-default' anyway
            parameter_source = "user-override"
        elif parameter_source is None:
            parameter_source = "user-override"
    except HttpResponseError as e:
        if parameter_value is None and parameter_source is None:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
        raise CLIError(str(e))

    parameters = postgresql_flexibleservers.models.Configuration(
        value=parameter_value,
        source=parameter_source
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


def _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value):
    parameters = postgresql_flexibleservers.models.Configuration(
        value=value,
        source=source
    )

    return resolve_poller(
        client.begin_update(resource_group_name, server_name, configuration_name, parameters), cmd.cli_ctx, 'PostgreSQL Parameter update')
