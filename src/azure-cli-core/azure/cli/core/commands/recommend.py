# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import todict
from knack import events
from azure.cli.core.commands.events import EVENT_INVOKER_PRE_LOAD_ARGUMENTS

logger = get_logger(__name__)


def register_global_query_recommend_argument(cli_ctx):
    '''Register --query-recommend argument, and register handler
    '''

    def handle_recommend_parameter(cli, **kwargs):  # pylint: disable=unused-argument
        args = kwargs['args']
        if args._query_recommend is not None:  # pylint: disable=protected-access
            cli_ctx.invocation.data['output'] = 'table'

            def analyze_output(cli_ctx, **kwargs):
                tree_builder = TreeBuilder()
                tree_builder.build(kwargs['event_data']['result'])
                kwargs['event_data']['result'] = tree_builder.generate_recommend(
                    args._query_recommend)  # pylint: disable=protected-access
                cli_ctx.unregister_event(
                    events.EVENT_INVOKER_FILTER_RESULT, analyze_output)

            cli_ctx.register_event(
                events.EVENT_INVOKER_FILTER_RESULT, analyze_output)
            cli_ctx.invocation.data['query_active'] = True

    def register_query_recommend(cli, **kwargs):
        from knack.experimental import ExperimentalItem
        commands_loader = kwargs.get('commands_loader')
        cmd_tbl = commands_loader.command_table
        experimental_info = ExperimentalItem(cli.local_context.cli_ctx,
                                             object_type='parameter', target='_query_recommend')
        default_kwargs = {
            'help': 'Recommend JMESPath string for you. Currently this is a dummy parameter',
            'arg_group': 'Global',
            'is_experimental': True,
            'nargs': '*',
            'experimental_info': experimental_info
        }
        for _, cmd in cmd_tbl.items():
            cmd.add_argument('_query_recommend', *
                             ['--query-recommend'], **default_kwargs)

    cli_ctx.register_event(
        EVENT_INVOKER_PRE_LOAD_ARGUMENTS, register_query_recommend
    )
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_recommend_parameter)


class TreeBuilder:
    '''Parse entry. Generate parse tree from json. And
    then give recommendation
    '''

    def __init__(self):
        self._data = None

    def build(self, data):
        '''Build a query tree with a given json file
        :param str data: json format data
        '''
        self._data = data

    def generate_recommend(self, keywords_list):  # pylint: disable=unused-argument, no-self-use
        recommendations = []
        return todict(recommendations)
