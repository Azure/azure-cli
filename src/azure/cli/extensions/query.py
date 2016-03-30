import collections

def register(event_dispatcher):
    def handle_query_parameter(_, event_data):
        try:
            query_value = args._jmespath_query #  pylint: disable=protected-access
            del args._jmespath_query

            if query_value:
                def filter_output(event_data):
                    import jmespath
                    event_data['result'] = jmespath.search(query_value, event_data['result'],
                                                           jmespath.Options(collections.OrderedDict))
                application.register(application.FILTER_RESULT, filter_output)

        except AttributeError:
            pass

    application.register(application.GLOBAL_PARSER_CREATED, _register_global_parameter)
    application.register(application.COMMAND_PARSER_PARSED, handle_query_parameter)

