from msrest.serialization import Model

class Pools(Model):
    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'value': {'key': 'value', 'type': '[PoolDetails]'},
    }

    def __init__(self, count=None, value=None):
        self.count = count
        self.value = value