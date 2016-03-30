import collections

def register(event_dispatcher):
    def handle_query_parameter(_, event_data):
        try:
            args = event_data['args']
            query_index = args.index('--query')
            query_value = args[query_index + 1]
            del args[query_index:query_index + 1]
        except ValueError:
            pass
        else:
            def filter_output(_, event_data):
                import jmespath
                event_data['result'] = jmespath.search(query_value, event_data['result'],
                                                       jmespath.Options(collections.OrderedDict))
            event_dispatcher.register(event_dispatcher.FILTER_RESULT, filter_output)
    event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS, handle_query_parameter)
