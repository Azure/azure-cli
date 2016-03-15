def register(event_dispatcher):
    def _enable_experimental_handlers(_, event_data):
        """The user can opt in to experimental event handlers by
        passing an --experimental flag on the command line
        """
        try:
            event_data['args'].remove('--experimental')
            event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                                      id_filter)
            event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                                      generate_skeleton)
            event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                                      use_skeleton)
        except ValueError:
            pass

    def id_filter(_, event_data):
        """Filter to only return the Id property
        from the result.
        """
        try:
            event_data['args'].remove('--id-only')
            def filter_output(_, event_data):
                import jmespath
                event_data['result'] = jmespath.search('[*].id', event_data['result'])
            event_dispatcher.register(event_dispatcher.TRANSFORM_RESULT, filter_output)
        except IndexError:
            pass
        except ValueError:
            pass

    def generate_skeleton(_, event_data): #pylint: disable=unused-variable
        try:
            def switcheroo(_, event_data):
                """We replace the handler for the command
                to our skeleton generator function as the user
                didn't actually want to run the command but rather
                get a skeleton that can later be used as input
                """
                def skeleton_generator(parsed, _):
                    # TODO: Use the command definition to
                    # generate an appropriate skeleton...
                    return parsed

                event_data['handler'] = skeleton_generator
            event_data['args'].remove('--generate-skeleton')
            event_dispatcher.register(event_dispatcher.EXECUTING_COMMAND, switcheroo)
        except ValueError:
            pass

    def use_skeleton(_, event_data):
        try:
            args = event_data['args']
            skeleton_index = args.index('--use-skeleton')
            skeleton_value = args[skeleton_index + 1] # pylint: disable=unused-variable

            def overlay_arguments(_, event_data): # pylint: disable=unused-argument
                # TODO: overlay the arguments with the data in the skeleton file
                # passed to us...
                pass

            event_dispatcher.register(event_dispatcher.PARSING_PARAMETERS, overlay_arguments)
        except ValueError:
            pass

    event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                              _enable_experimental_handlers)
