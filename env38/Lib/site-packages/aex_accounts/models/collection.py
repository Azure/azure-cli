
from msrest.serialization import Model

class Collection(Model):
    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
    }

    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name