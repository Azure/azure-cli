# coding=utf-8
# --------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class ApiResourceLocation(Model):
    """ApiResourceLocation.
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'area': {'key': 'area', 'type': 'str'},
        'resource_name': {'key': 'resourceName', 'type': 'str'},
        'route_template': {'key': 'routeTemplate', 'type': 'str'},
        'resource_version': {'key': 'resourceVersion', 'type': 'int'},
        'min_version': {'key': 'minVersion', 'type': 'float'},
        'max_version': {'key': 'maxVersion', 'type': 'float'},
        'released_version': {'key': 'releasedVersion', 'type': 'str'},
    }

    def __init__(self, id=None, area=None, resource_name=None,
                 route_template=None, resource_version=None,
                 min_version=None, max_version=None,
                 released_version=None):
        super(ApiResourceLocation, self).__init__()
        self.id = id
        self.area = area
        self.resource_name = resource_name
        self.route_template = route_template
        self.resource_version = resource_version
        self.min_version = min_version
        self.max_version = max_version
        self.released_version = released_version
