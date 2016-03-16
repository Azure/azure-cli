from collections import defaultdict

class EventDispatcher(object):
    """Register for and raise events.

    During the execution of a command, a set of events are raised
    that allow extensions to change the flow of actions.

    Clients can register handlers by calling the `EventDispatcher.register`
    method passing in the event handler function.
    """

    REGISTER_GLOBAL_PARAMETERS = 'RegisterGlobalParameters'
    PARSING_PARAMETERS = 'ParsingParameters'
    VALIDATING_PARAMETERS = 'ValidatingParameters'
    EXECUTING_COMMAND = 'ExecutingCommand'
    TRANSFORM_RESULT = 'TransformResult'
    FILTER_RESULT = 'FilterResult'

    def __init__(self):
        self._handlers = defaultdict(lambda: [])

    def raise_event(self, name, event_data):
        for func in self._handlers[name]:
            func(name, event_data)

    def register(self, name, handler):
        '''Register a callable that will be called when the
        event `name` is raised.

        param: name: The name of the event
        param: handler: Function that takes two parameters;
          name: name of the event raised
          event_data: `dict` with event specific data.
        '''
        self._handlers[name].append(handler)

    def event_handler(self, name):
        '''Any function decorated by @event_handler will
        be registered as a handler for the given event name
        '''
        def wrapper(func):
            self.register(name, func)
            return func
        return wrapper

