#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

def register(event_dispatcher):
    def _enable_experimental_handlers(_, event_data):
        """The user can opt in to experimental event handlers by
        passing an --experimental flag on the command line
        """
        try:
            event_data['args'].remove('--experimental')
            event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                                      generate_skeleton)
            event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                                      use_skeleton)
            event_dispatcher.register(event_dispatcher.PARSING_PARAMETERS,
                                      file_argument_value)
        except ValueError:
            pass

    def file_argument_value(_, event_data):
        """Replace provided parameter value with value from file
        if the parameter value starts with a '@'
        """
        def load_file(path):
            with open(path, 'r') as f:
                return f.read()

        args = event_data['args']
        for name in args.keys():
            value = args[name]
            try:
                if str.startswith(value, '@'):
                    args[name] = load_file(value[1:])
            except TypeError:
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
