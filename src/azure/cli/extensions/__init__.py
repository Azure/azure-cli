if False: # No extensions for now...
    from .._event_dispatcher import EventDispatcher
    from .query import register as register_query
    from .transform import register as register_transform
    from .experimental import register as register_experimental

    event_dispatcher = EventDispatcher()

    register_query(event_dispatcher)
    register_transform(event_dispatcher)
    register_experimental(event_dispatcher)
