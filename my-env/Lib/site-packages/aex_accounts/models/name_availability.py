
from msrest.serialization import Model

class NameAvailability(Model):
    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'is_available': {'key': 'is_available', 'type': 'str'},
        'unavailability_reason': {'key': 'unavailability_reason', 'type': 'str'},
    }

    def __init__(self, name=None, is_available=None, unavailability_reason=None):
        self.name = name
        self.is_available = is_available
        self.unavailability_reason = unavailability_reason