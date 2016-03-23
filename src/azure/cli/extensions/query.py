def register(event_dispatcher):
    def register_global_parameter(self, parser):
        # Let the program know that we are adding a parameter --query
        parser.add_argument('--query', dest='_jmespath_query', metavar='JMESPATH', help='JMESPath query string. See http://jmespath.org/ for more information and examples.')

    def handle_query_parameter(_, args):
        # Of there is a query specified on the command line, we'll take care of that!
        query_value = args._jmespath_query
        del(args._jmespath_query)

        if query_value:
            def filter_output(_, event_data):
                import jmespath
                event_data['result'] = jmespath.search(query_value, event_data['result'])

            event_dispatcher.register(event_dispatcher.FILTER_RESULT, filter_output)

    event_dispatcher.register('GlobalParser.Created', register_global_parameter)
    event_dispatcher.register('CommandParser.Parsed', handle_query_parameter)
