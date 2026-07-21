# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from time import sleep
from knack.arguments import ignore_type
from knack.log import get_logger
from azure.cli.core.commands import AzArgumentContext
from azure.cli.core.util import CLIError
from .validators import get_combined_validator

logger = get_logger(__name__)


# pylint: disable=too-few-public-methods, import-outside-toplevel
class PostgreSQLArgumentContext(AzArgumentContext):

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


def get_autonomous_tuning_settings_map():
    return {
        'analysis_interval': 'index_tuning.analysis_interval',
        'max_columns_per_index': 'index_tuning.max_columns_per_index',
        'max_index_count': 'index_tuning.max_index_count',
        'max_indexes_per_table': 'index_tuning.max_indexes_per_table',
        'max_queries_per_database': 'index_tuning.max_queries_per_database',
        'max_regression_factor': 'index_tuning.max_regression_factor',
        'max_total_size_factor': 'index_tuning.max_total_size_factor',
        'min_improvement_factor': 'index_tuning.min_improvement_factor',
        'mode': 'index_tuning.mode',
        'unused_dml_per_table': 'index_tuning.unused_dml_per_table',
        'unused_min_period': 'index_tuning.unused_min_period',
        'unused_reads_per_table': 'index_tuning.unused_reads_per_table'
    }
