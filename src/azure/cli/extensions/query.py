import collections

from azure.cli._util import CLIError

def _register_global_parameter(global_group):
    # Let the program know that we are adding a parameter --query
    global_group.add_argument('--query', dest='_jmespath_query', metavar='JMESPATH',
                              help='JMESPath query string. See http://jmespath.org/ for more information and examples.') # pylint: disable=line-too-long

def register(application):
    def handle_query_parameter(**kwargs):
        from jmespath import compile as compile_jmespath
        from jmespath.exceptions import ParseError
        args = kwargs['args']
        jmespath_query = None
        try:
            jmespath_query = args._jmespath_query # pylint: disable=protected-access
            query_expression = compile_jmespath(jmespath_query) if jmespath_query else None
            del jmespath_query

            if query_expression:
                def filter_output(**kwargs):
                    from jmespath import search, Options
                    kwargs['event_data']['result'] = query_expression.search(
                        kwargs['event_data']['result'], Options(collections.OrderedDict))
                    application.remove(application.FILTER_RESULT, filter_output)
                application.register(application.FILTER_RESULT, filter_output)
        except ParseError as ex:
            raise CLIError(ex)
        except KeyError:
            raise CLIError("Error processing query {}".format(jmespath_query if jmespath_query else ''))
        except AttributeError:
            pass

    application.register(application.GLOBAL_PARSER_CREATED, _register_global_parameter)
    application.register(application.COMMAND_PARSER_PARSED, handle_query_parameter)

