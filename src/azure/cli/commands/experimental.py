# pylint: skip-file
from __future__ import print_function
import json
from importlib import import_module
import azure.cli._logging as _logging

logger = _logging.get_az_logger(__name__)

class CliSubresourceCommandSet(object):

    IGNORE_PROPERTIES = ['etag', 'id', 'provisioning_state']    

    def __init__(self, set_name, parent, child_key):
        self.set_name = set_name
        parent_comps = parent.split('.')
        # import the parent module and parent resource class
        module = import_module('.'.join(parent_comps[:-1]))
        parent_class = getattr(module, parent_comps[-1])
        self.child_name = ''
        self.child_class = None
        self.command_set_type = None

        # retrieve the entry for child resource
        child_entry = getattr(parent_class, '_attribute_map')[child_key]

        child_path = child_entry['key']
        child_type = child_entry['type']
        if child_type.startswith('[') and child_type.endswith(']'):
            self.child_name = child_type[1:-1]
            self.command_set_type = 'list'
        else:
            self.child_name = child_type
            self.command_set_type = 'object'
        self.child_class = getattr(module, self.child_name)

        # retrieve child attribute map and remove ignored or subresource attributes
        self.child_attrs = getattr(self.child_class, '_attribute_map')
        for key in self.IGNORE_PROPERTIES:
            self.child_attrs.pop(key, None)
        subresource_attrs = [key for key in self.child_attrs.keys() \
            if 'SubResource' in self.child_attrs[key]['type']]
        for key in subresource_attrs:
            self.child_attrs.pop(key, None)
        print(json.dumps(self.child_attrs, indent=2, sort_keys=True))

def _add_subresource(client, kwargs):
    # get subresource list from parent resource
    # add subresource to list if it doesn't exit--error if it does
    # update parent resource
    pass

def _remove_subresource(client, kwargs):
    # get subresource list from parent resource
    # remove subresource from list
    # update parent resource
    pass

def _get_subresource(client, kwargs):
    # get subresource list from parent resource
    # return subresource item or None
    pass

def _list_subresource(client, kwargs):
    # return subresource list from parent resource
    pass

def _set_subresource(client, kwargs):
    # get subresource list from parent resource
    # get subresource from list
    # update subresource parameters
    # update parent resource
    pass
