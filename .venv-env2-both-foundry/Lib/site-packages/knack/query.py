# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections

from .events import (EVENT_PARSER_GLOBAL_CREATE, EVENT_INVOKER_POST_PARSE_ARGS,
                     EVENT_INVOKER_FILTER_RESULT)
from .util import CtxTypeError


class CLIQuery(object):

    @staticmethod
    def jmespath_type(raw_query):
        """Compile the query with JMESPath and return the compiled result.
        JMESPath raises exceptions which subclass from ValueError.
        In addition though, JMESPath can raise a KeyError.
        ValueErrors are caught by argparse so argument errors can be generated.
        """
        from jmespath import compile as compile_jmespath
        try:
            return compile_jmespath(raw_query)
        except KeyError as ex:
            # Raise a ValueError which argparse can handle
            raise ValueError from ex

    @staticmethod
    def on_global_arguments(_, **kwargs):
        arg_group = kwargs.get('arg_group')
        arg_group.add_argument('--query', dest='_jmespath_query', metavar='JMESPATH',
                               help='JMESPath query string. See http://jmespath.org/ for more'
                                    ' information and examples.',
                               type=CLIQuery.jmespath_type)

    @staticmethod
    def handle_query_parameter(cli_ctx, **kwargs):
        args = kwargs['args']
        query_expression = args._jmespath_query  # pylint: disable=protected-access
        del args._jmespath_query
        if query_expression:
            def filter_output(cli_ctx, **kwargs):
                from jmespath import Options
                kwargs['event_data']['result'] = query_expression.search(
                    kwargs['event_data']['result'], Options(collections.OrderedDict))
                cli_ctx.unregister_event(EVENT_INVOKER_FILTER_RESULT, filter_output)
            cli_ctx.register_event(EVENT_INVOKER_FILTER_RESULT, filter_output)
            cli_ctx.invocation.data['query_active'] = True

    def __init__(self, cli_ctx=None):
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.cli_ctx.register_event(EVENT_PARSER_GLOBAL_CREATE, CLIQuery.on_global_arguments)
        self.cli_ctx.register_event(EVENT_INVOKER_POST_PARSE_ARGS, CLIQuery.handle_query_parameter)
