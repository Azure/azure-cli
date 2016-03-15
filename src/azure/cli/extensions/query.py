def register(event_dispatcher):
    def handle_query_parameter(_, event_data):
        try:
            args = event_data['args']
            query_index = args.index('--query')
            query_value = args[query_index + 1]
            del args[query_index:query_index + 1]
            def filter_output(_, event_data):
                import jmespath
                event_data['result'] = jmespath.search(query_value, event_data['result'])
            event_dispatcher.register(event_dispatcher.FILTER_RESULT, filter_output)
        except IndexError:
            pass
        except ValueError:
            pass
    event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS, handle_query_parameter)
