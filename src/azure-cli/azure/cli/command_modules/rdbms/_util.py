# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
import random
from knack.config import CLIConfig
from knack.log import get_logger
from azure.cli.core.commands import AzArgumentContext
from azure.cli.core.commands import LongRunningOperation, _is_poller
from azure.mgmt.resource.resources.models import ResourceGroup
from ._client_factory import resource_client_factory

logger = get_logger(__name__)

DEFAULT_LOCATION = 'northeurope'

class RdbmsArgumentContext(AzArgumentContext):  # pylint: disable=too-few-public-methods

    def __init__(self, command_loader, scope, **kwargs):    # pylint: disable=unused-argument
        super(RdbmsArgumentContext, self).__init__(command_loader, scope)
        self.validators = []

    def expand(self, dest, model_type, group_name=None, patches=None):
        super(RdbmsArgumentContext, self).expand(dest, model_type, group_name, patches)

        from knack.arguments import ignore_type

        # Remove the validator and store it into a list
        arg = self.command_loader.argument_registry.arguments[self.command_scope].get(dest, None)
        if not arg:  # when the argument context scope is N/A
            return

        self.validators.append(arg.settings['validator'])
        dest_option = ['--__{}'.format(dest.upper())]
        if dest == 'parameters':
            from .validators import get_combined_validator
            self.argument(dest,
                          arg_type=ignore_type,
                          options_list=dest_option,
                          validator=get_combined_validator(self.validators))
        else:
            self.argument(dest, options_list=dest_option, arg_type=ignore_type, validator=None)


def resolve_poller(result, cli_ctx, name):
    if _is_poller(result):
        return LongRunningOperation(cli_ctx, 'Starting {}'.format(name))(result)
    return result


def create_random_resource_name(prefix='azure', length=15):
    append_length = length - len(prefix)
    digits = [str(random.randrange(10)) for i in range(append_length)]
    return prefix + ''.join(digits)


def generate_missing_parameters(cmd, location, resource_group_name, server_name, administrator_login_password):

    # if location is not passed as a parameter or is missing from local context
    if location is None:
        location = DEFAULT_LOCATION

    # If resource group is there in local context, check for its existence.
    resource_group_exists = True
    if resource_group_name is not None:
        logger.warning('Checking the existence of the resource group \'%s\'...', resource_group_name)
        resource_group_exists = _check_resource_group_existence(cmd, resource_group_name)
        logger.warning('Resource group \'%s\' exists ? : %s ', resource_group_name, resource_group_exists)

    # If resource group is not passed as a param or is not in local context or the rg in the local context has been deleted
    if not resource_group_exists or resource_group_name is None:
        resource_group_name = _create_resource_group(cmd, location, resource_group_name)

    # If servername is not passed, always create a new server - even if it is stored in the local context
    if server_name is None:
        server_name = create_random_resource_name('server')
        # cmd.cli_ctx.local_context.get_value('server-name')
        cmd.cli_ctx.local_context.set(['all'], 'server-name', server_name)  # Setting the location in the local context

    if administrator_login_password is None:
        administrator_login_password = str(uuid.uuid4())

    # This is for the case when user does not pass a location but the resource group exists in the local context.
    #  In that case, the location needs to be set to the location of the rg, not the default one.
    location = _update_location(cmd, resource_group_name)

    return location, resource_group_name, server_name, administrator_login_password


def _update_location(cmd, resource_group_name):
    resource_client = resource_client_factory(cmd.cli_ctx)
    rg = resource_client.resource_groups.get(resource_group_name)
    location = rg.location
    cmd.cli_ctx.local_context.set(['all'], 'location', location)  # Setting the location in the local context
    return location


def _create_resource_group(cmd, location, resource_group_name):
    if resource_group_name is None:
        resource_group_name = create_random_resource_name('group')
    params = ResourceGroup(location=location)
    resource_client = resource_client_factory(cmd.cli_ctx)
    logger.warning('Creating Resource Group \'%s\'...', resource_group_name)
    resource_client.resource_groups.create_or_update(resource_group_name, params)
    cmd.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group_name)
    return resource_group_name


def _check_resource_group_existence(cmd, resource_group_name):
    resource_client = resource_client_factory(cmd.cli_ctx)
    return  resource_client.resource_groups.check_existence(resource_group_name)