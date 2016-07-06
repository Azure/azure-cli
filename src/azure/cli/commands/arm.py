import re

from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient

regex = re.compile('/subscriptions/(?P<subscription>[^/]*)/resourceGroups/(?P<resource_group>[^/]*)'
                   '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
                   '(/(?P<child_type>[^/]*)/(?P<child_name>[^/]*))?')

def resource_id(**kwargs):
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
    m = regex.match(rid)
    if m:
        result = m.groupdict()
    else:
        result = dict(name=rid)

    return {key:value for key, value in result.items() if value is not None}

def is_valid_resource_id(rid):
    try:
        return rid and resource_id(**parse_resource_id(rid)) == rid
    except KeyError:
        return False

def resource_exists(**kwargs):
    odata_filter = "resourceGroup eq '{resource_group}' and name eq '{name}'" \
        " and resourceType eq '{namespace}/{type}'".format(**kwargs)
    client = get_mgmt_service_client(ResourceManagementClient).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing
