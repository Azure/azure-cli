from azure.cli.parser import IncorrectUsageError

from ._factory import _resource_client_factory

def _resolve_api_version(rcf, resource_type, parent=None):

    provider = rcf.providers.get(resource_type.namespace)
    resource_type_str = '{}/{}'.format(parent.type, resource_type.type) \
        if parent else resource_type.type

    rt = [t for t in provider.resource_types if t.resource_type == resource_type_str]
    if not rt:
        raise IncorrectUsageError('Resource type {} not found.'
                                  .format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise IncorrectUsageError(
            'API version is required and could not be resolved for resource {}/{}'
            .format(resource_type.namespace, resource_type.type))

def handle_resource_parameters(**kwargs):
    args = vars(kwargs['args'])

    param_set = set(['resource_type', 'api_version',
                     'resource_provider_namespace', 'parent_resource_path'])
    if not param_set.issubset(set(args.keys())):
        return

    resource_tuple = args.get('resource_type')
    parent_tuple = args.get('parent_resource_path')

    rcf = _resource_client_factory()
    args['api_version'] = args.get('api_version') or \
        _resolve_api_version(rcf, resource_tuple, parent_tuple)
    args['resource_type'] = resource_tuple.type
    args['resource_provider_namespace'] = resource_tuple.namespace
    args['parent_resource_path'] = '{}/{}'.format(
        parent_tuple.type,
        parent_tuple.name) if parent_tuple else ''
