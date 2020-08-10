
from msrest.serialization import Model

class RegionDetails(Model):
    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'is_default': {'key': 'is_default', 'type': 'str'},
    }

    def __init__(self, name=None, display_name=None, is_default=None):
        self.name = name
        self.display_name = display_name
        self.is_default = is_default