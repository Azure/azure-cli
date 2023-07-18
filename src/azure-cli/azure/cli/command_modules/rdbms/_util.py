# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime
from time import sleep
from knack.arguments import ignore_type
from knack.log import get_logger
from azure.cli.core.commands import AzArgumentContext
from azure.cli.core.util import CLIError
from ._client_factory import cf_mariadb_firewall_rules, cf_postgres_firewall_rules, cf_mysql_firewall_rules
from .validators import get_combined_validator

logger = get_logger(__name__)


# pylint: disable=too-few-public-methods, import-outside-toplevel
class RdbmsArgumentContext(AzArgumentContext):

    def __init__(self, command_loader, scope, **kwargs):    # pylint: disable=unused-argument
        super().__init__(command_loader, scope)
        self.validators = []

    def expand(self, dest, model_type, group_name=None, patches=None):
        super().expand(dest, model_type, group_name, patches)

        # Remove the validator and store it into a list
        arg = self.command_loader.argument_registry.arguments[self.command_scope].get(dest, None)
        if not arg:  # when the argument context scope is N/A
            return

        self.validators.append(arg.settings['validator'])
        dest_option = ['--__{}'.format(dest.upper())]
        if dest == 'parameters':
            self.argument(dest,
                          arg_type=ignore_type,
                          options_list=dest_option,
                          validator=get_combined_validator(self.validators))
        else:
            self.argument(dest, options_list=dest_option, arg_type=ignore_type, validator=None)


# pylint: disable=inconsistent-return-statements
def parse_public_network_access_input(public_network_access):
    # pylint: disable=no-else-return
    if public_network_access is not None:
        parsed_input = public_network_access.split('-')
        if len(parsed_input) == 1 and str(parsed_input).find('.') != -1:
            return parsed_input[0], parsed_input[0]
        elif len(parsed_input) == 2:
            return parsed_input[0], parsed_input[1]
        else:
            raise CLIError('incorrect usage: --public/--public-network-access. Acceptable values are \'all\','
                           ' \'enabled\', \'disabled\', \'<startIP>\' and \'<startIP>-<destinationIP>\' '
                           'where startIP and destinationIP ranges from 0.0.0.0 to 255.255.255.255')


def create_firewall_rule(cmd, resource_group_name, server_name, start_ip, end_ip, db_engine):
    now = datetime.now()
    firewall_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                 now.second)
    if start_ip == '0.0.0.0' and end_ip == '0.0.0.0':
        logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                       'Azure resources...')
        firewall_name = 'AllowAllAzureServicesAndResourcesWithinAzureIps_{}-{}-{}_{}-{}-{}'.format(now.year, now.month,
                                                                                                   now.day, now.hour,
                                                                                                   now.minute,
                                                                                                   now.second)
    elif start_ip == end_ip:
        logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip)
    else:
        if start_ip == '0.0.0.0' and end_ip == '255.255.255.255':
            firewall_name = 'AllowAll_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                now.second)
        logger.warning('Configuring server firewall rule to accept connections from \'%s\' to \'%s\'...', start_ip,
                       end_ip)
    firewall_client = cf_postgres_firewall_rules(cmd.cli_ctx, None)
    if db_engine == 'mysql':
        firewall_client = cf_mysql_firewall_rules(cmd.cli_ctx, None)
    elif db_engine == 'mariadb':
        firewall_client = cf_mariadb_firewall_rules(cmd.cli_ctx, None)

    parameters = {'name': firewall_name, 'start_ip_address': start_ip, 'end_ip_address': end_ip}

    firewall = firewall_client.begin_create_or_update(resource_group_name, server_name, firewall_name, parameters)

    return firewall.result().name


def retryable_method(retries=3, interval_sec=5, exception_type=Exception, condition=None):
    def decorate(func):
        def call(*args, **kwargs):
            current_retry = retries
            while True:
                try:
                    return func(*args, **kwargs)
                except exception_type as ex:  # pylint: disable=broad-except
                    if condition and not condition(ex):
                        raise ex
                    current_retry -= 1
                    if current_retry <= 0:
                        raise ex
                sleep(interval_sec)
        return call
    return decorate
