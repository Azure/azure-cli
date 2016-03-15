from ._event_dispatcher import EventDispatcher
from .query import register as register_query
from .transform import register as register_transform

EVENT_DISPATCHER = EventDispatcher()

register_query(EVENT_DISPATCHER)
register_transform(EVENT_DISPATCHER)
