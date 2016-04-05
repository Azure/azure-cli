from .query import register as register_query
from .transform import register as register_transform

def register_extensions(application):
    register_query(application)
    register_transform(application)
