from azure.cli.main import logger, EVENT_DISPATCHER

@EVENT_DISPATCHER.event_handler(EVENT_DISPATCHER.REGISTER_GLOBAL_PARAMETERS)
def handle_query_parameter(name, event_data):
    try:
        args = event_data['args']
        query_index = args.index('--query')
        query_value = args[query_index + 1]
        del args[query_index:query_index + 1]
        def filter_output(name, event_data):
            import jmespath

            event_data['result'] = jmespath.search(query_value, event_data['result'])
            logger.debug('Execution done... returning')

        EVENT_DISPATCHER.register(EVENT_DISPATCHER.FILTER_RESULT, filter_output)
    except IndexError:
        pass
    except ValueError:
        pass
