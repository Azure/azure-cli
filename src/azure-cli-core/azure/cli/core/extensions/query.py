# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections


def jmespath_type(raw_query):
    '''Compile the query with JMESPath and return the compiled result.
       JMESPath raises exceptions which subclass from ValueError.
       In addition though, JMESPath can raise a KeyError.
       ValueErrors are caught by argparse so argument errors can be generated.
    '''
    from jmespath import compile as compile_jmespath
    try:
        return compile_jmespath(raw_query)
    except KeyError:
        # Raise a ValueError which argparse can handle
        raise ValueError


def _register_global_parameter(global_group):
    # Argparse uses __name__ of the function used for 'type' when generating error message.
    # We set __name__ for our function here.
    jmespath_type.__name__ = 'query'
    # Let the program know that we are adding a parameter --query
    global_group.add_argument('--query', dest='_jmespath_query', metavar='JMESPATH',
                              help='JMESPath query string. See http://jmespath.org/ for more'
                                   ' information and examples.',
                              type=jmespath_type)


def register(application):
    def handle_query_parameter(**kwargs):
        args = kwargs['args']
        query_expression = args._jmespath_query  # pylint: disable=protected-access
        del args._jmespath_query
        if query_expression:
            def filter_output(**kwargs):
                from jmespath import Options
                kwargs['event_data']['result'] = query_expression.search(
                    kwargs['event_data']['result'], Options(collections.OrderedDict))
                application.remove(application.FILTER_RESULT, filter_output)
            application.register(application.FILTER_RESULT, filter_output)
            application.session['query_active'] = True

    application.register(application.GLOBAL_PARSER_CREATED, _register_global_parameter)
    application.register(application.COMMAND_PARSER_PARSED, handle_query_parameter)
