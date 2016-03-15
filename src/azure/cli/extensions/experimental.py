from azure.cli.main import logger, EVENT_DISPATCHER

@EVENT_DISPATCHER.event_handler(EVENT_DISPATCHER.REGISTER_GLOBAL_PARAMETERS)
def _enable_experimental_handlers(name, event_data):
    """The user can opt in to experimental event handlers by 
    passing an --experimental flag on the command line
    """
    try:
        event_data['args'].remove('--experimental')
        EVENT_DISPATCHER.register(EVENT_DISPATCHER.REGISTER_GLOBAL_PARAMETERS, id_filter)
        EVENT_DISPATCHER.register(EVENT_DISPATCHER.REGISTER_GLOBAL_PARAMETERS, generate_skeleton)
        EVENT_DISPATCHER.register(EVENT_DISPATCHER.REGISTER_GLOBAL_PARAMETERS, use_skeleton)
    except ValueError:
        pass

def id_filter(name, event_data):
    """Filter to only return the Id property
    from the result.
    """
    try:
        event_data['args'].remove('--id-only')        
        def filter_output(name, event_data):
            import jmespath

            event_data['result'] = jmespath.search('[*].id', event_data['result'])
            logger.debug('Execution done... returning')

        EVENT_DISPATCHER.register(EVENT_DISPATCHER.TRANSFORM_RESULT, filter_output)
    except IndexError:
        pass
    except ValueError:
        pass

def generate_skeleton(name, event_data):
    try:
        def switcheroo(name, event_data):
            """We replace the handler for the command
            to our skeleton generator function as the user
            didn't actually want to run the command but rather
            get a skeleton that can later be used as input
            """
            def skeleton_generator(parsed, unexpected):
                # TODO: Use the command definition to 
                # generate an appropriate skeleton...
                print(event_data)
                return parsed

            event_data['handler'] = skeleton_generator


        event_data['args'].remove('--generate-skeleton')
        EVENT_DISPATCHER.register(EVENT_DISPATCHER.EXECUTING_COMMAND, switcheroo)
    except ValueError:
        pass

def use_skeleton(name, event_data):
    try:
        args = event_data['args']
        skeleton_index = args.index('--use-skeleton')
        skeleton_value = args[skeleton_index + 1]

        def overlay_arguments(name, event_data):
            # TODO: overlay the arguments with the data in the skeleton file 
            # passed to us...
            pass

        EVENT_DISPATCHER.register(EVENT_DISPATCHER.PARSING_PARAMETERS, overlay_arguments)

    except ValueError:
        pass

def file_argument(name, event_data):
    args = event_data['args']

    pass