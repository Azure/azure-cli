# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import todict
from knack import events
from azure.cli.core.commands.events import EVENT_INVOKER_PRE_LOAD_ARGUMENTS

logger = get_logger(__name__)


def register_global_query_example_argument(cli_ctx):
    '''Register --query-example argument, and register handler
    '''

    def handle_example_parameter(cli, **kwargs):  # pylint: disable=unused-argument
        args = kwargs['args']
        if args._query_example is not None:  # pylint: disable=protected-access
            cli_ctx.invocation.data['output'] = 'table'

            def analyze_output(cli_ctx, **kwargs):
                tree_builder = TreeBuilder()
                tree_builder.build(kwargs['event_data']['result'])
                kwargs['event_data']['result'] = tree_builder.generate_example(
                    args._query_example)  # pylint: disable=protected-access
                cli_ctx.unregister_event(
                    events.EVENT_INVOKER_FILTER_RESULT, analyze_output)

            cli_ctx.register_event(
                events.EVENT_INVOKER_FILTER_RESULT, analyze_output)
            cli_ctx.invocation.data['query_active'] = True

    def register_query_example(cli, **kwargs):
        from knack.experimental import ExperimentalItem
        commands_loader = kwargs.get('commands_loader')
        cmd_tbl = commands_loader.command_table
        experimental_info = ExperimentalItem(cli.local_context.cli_ctx,
                                             object_type='parameter', target='_query_example')
        default_kwargs = {
            'help': 'Recommend JMESPath string for you. Currently this is a dummy parameter',
            'arg_group': 'Global',
            'is_experimental': True,
            'nargs': '*',
            'experimental_info': experimental_info
        }
        for _, cmd in cmd_tbl.items():
            cmd.add_argument('_query_example', *
                             ['--query-example'], **default_kwargs)

    cli_ctx.register_event(
        EVENT_INVOKER_PRE_LOAD_ARGUMENTS, register_query_example
    )
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_example_parameter)


class TreeBuilder:
    '''Parse entry. Generate parse tree from json. And then give examples.
    '''

    def __init__(self):
        self._data = None

    def build(self, data):
        '''Build a query tree with a given json file
        :param str data: json format data
        '''
        self._data = data

    def generate_example(self, keywords_list):  # pylint: disable=unused-argument, no-self-use
        examples = []
        return todict(examples)
