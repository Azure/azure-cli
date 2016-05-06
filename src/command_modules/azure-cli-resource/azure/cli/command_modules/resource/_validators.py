import collections

from azure.cli.parser import IncorrectUsageError

def validate_resource_type(string):
    ''' Validates that resource type is provided in <namespace>/<type> format '''
    type_comps = string.split('/')
    try:
        namespace_comp = type_comps[0]
        resource_comp = type_comps[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')
    ResourceType = collections.namedtuple('ResourceType', 'namespace type')
    return ResourceType(namespace=namespace_comp, type=resource_comp)

def validate_parent(string):
    ''' Validates that parent is provided in <type>/<name> format '''
    if not string:
        return string
    parent_comps = string.split('/')
    try:
        type_comp = parent_comps[0]
        name_comp = parent_comps[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --parent must be in <type>/<name> format.')
    ParentType = collections.namedtuple('ParentType', 'type name')
    return ParentType(type=type_comp, name=name_comp)
