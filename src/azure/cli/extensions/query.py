import collections

def _register_global_parameter(parser):
    # Let the program know that we are adding a parameter --query
    global_group = parser.get_global_group()
    global_group.add_argument('--query', dest='_jmespath_query', metavar='JMESPATH',
                        help='JMESPath query string. See http://jmespath.org/ for more information and examples.') # pylint: disable=line-too-long

def register(application):
    def handle_query_parameter(args):
        try:
            query_value = args._jmespath_query_global #  pylint: disable=protected-access
            del args._jmespath_query_global

            if query_value:
                def filter_output(event_data):
                    from jmespath import search, Options
                    event_data['result'] = search(query_value, event_data['result'],
                                                  Options(collections.OrderedDict))
                application.register(application.FILTER_RESULT, filter_output)

        except AttributeError:
            pass

    application.register(application.GLOBAL_PARSER_CREATED, _register_global_parameter)
    application.register(application.COMMAND_PARSER_PARSED, handle_query_parameter)

