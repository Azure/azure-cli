# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def register(event_dispatcher):
    def _enable_experimental_handlers(_, event_data):
        """The user can opt in to experimental event handlers by
        passing an --experimental flag on the command line
        """
        try:
            event_data['args'].remove('--experimental')
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

    event_dispatcher.register(event_dispatcher.REGISTER_GLOBAL_PARAMETERS,
                              _enable_experimental_handlers)
