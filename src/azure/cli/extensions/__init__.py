from .query import register as register_query
from .transform import register as register_transform
from .updates import register as register_updates

def register_extensions(application):
    register_query(application)
    register_transform(application)
    register_updates(application)
