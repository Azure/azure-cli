import re

from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient

regex = re.compile('/subscriptions/(?P<subscription>[^/]*)/resourceGroups/(?P<resource_group>[^/]*)'
                   '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
                   '(/(?P<child_type>[^/]*)/(?P<child_name>[^/]*))?')

def resource_id(**kwargs):
    id = '/subscriptions/{subscription}'.format(**kwargs)
    try:
        id = '/'.join((id, 'resourceGroups/{resource_group}'.format(**kwargs)))
        id = '/'.join((id, 'providers/{namespace}'.format(**kwargs)))
        id = '/'.join((id, '{type}/{name}'.format(**kwargs)))
        id = '/'.join((id, '{child_type}/{child_name}'.format(**kwargs)))
    except KeyError:
        pass
    return id

def parse_resource_id(id):
    m = regex.match(id)
    if m:
        result = m.groupdict()
    else:
        result = {
            'name': id
            }
    return {key:value for key, value in result.items() if value is not None}

def is_valid_resource_id(id):
    return resource_id(**parse_resource_id(id)) == id

def resource_exists(r_id):
    odata_filter = "resourceGroup eq '{0}' and name eq '{1}'" \
        " and resourceType eq '{2}'".format(r_id.resource_group, r_id.name, r_id.full_type)
    client = get_mgmt_service_client(ResourceManagementClient).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing
