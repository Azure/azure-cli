from .query import register as register_query
from .transform import register as register_transform
from .experimental import register as register_experimental

def register_extensions(application):
    register_query(application.session)
    register_transform(application.session)
    register_experimental(application.session)
