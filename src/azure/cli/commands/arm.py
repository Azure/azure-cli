import re
from collections import namedtuple
from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient

regex = re.compile('/subscriptions/(?P<subscription>[^/]*)/resourceGroups/(?P<resource_group>[^/]*)'
                   '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
                   '(/(?P<child_type>[^/]*)/(?P<child_name>[^/]*))?')

def resource_id(**kwargs):
    '''Create a valid resource id string from the given parts

    The method accepts the following keyword arguments:

        - subscription      Subscription id
        - resource_group    Name of resource group
        - namespace         Namespace for the resource provider (i.e. Microsoft.Compute)
        - type              Type of the resource (i.e. virtualMachines)
        - name              Name of the resource (or parent if child_name is also specified)
        - child_type        Type of the child resource
        - child_name        Name of the child resource
    '''
    rid = '/subscriptions/{subscription}'.format(**kwargs)
    try:
        rid = '/'.join((rid, 'resourceGroups/{resource_group}'.format(**kwargs)))
        rid = '/'.join((rid, 'providers/{namespace}'.format(**kwargs)))
        rid = '/'.join((rid, '{type}/{name}'.format(**kwargs)))
        rid = '/'.join((rid, '{child_type}/{child_name}'.format(**kwargs)))
    except KeyError:
        pass
    return rid

def parse_resource_id(rid):
    '''Build a dictionary with the following key/value pairs (if found)

        - subscription      Subscription id
        - resource_group    Name of resource group
        - namespace         Namespace for the resource provider (i.e. Microsoft.Compute)
        - type              Type of the resource (i.e. virtualMachines)
        - name              Name of the resource (or parent if child_name is also specified)
        - child_type        Type of the child resource
        - child_name        Name of the child resource
    '''
    m = regex.match(rid)
    if m:
        result = m.groupdict()
    else:
        result = dict(name=rid)

    return {key:value for key, value in result.items() if value is not None}

def is_valid_resource_id(rid, exception_type=None):
    is_valid = False
    try:
        is_valid = rid and resource_id(**parse_resource_id(rid)) == rid
    except KeyError:
        pass
    if not is_valid and exception_type:
        raise exception_type()
    return False



def resource_exists(resource_group, name, namespace, type, **kwargs):
    '''Checks if the given resource exists.
    '''
    odata_filter = "resourceGroup eq '{}' and name eq '{}'" \
        " and resourceType eq '{}/{}'".format(resource_group, name, namespace, type)
    client = get_mgmt_service_client(ResourceManagementClient).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing
