import argparse

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
        npv = [v for v in rt[0].api_versions if "preview" not in v]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise IncorrectUsageError(
            'API version is required and could not be resolved for resource {}/{}'
            .format(resource_type.namespace, resource_type.type))

class ResourceResolveAPIAction(argparse.Action): # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        rcf = _resource_client_factory()
        namespace.api_version = namespace.api_version or \
            _resolve_api_version(rcf, values, namespace.parent_resource_path)
        namespace.resource_type = values.type
        namespace.resource_provider_namespace = values.namespace
        namespace.parent_resource_path = '{}/{}'.format(
            namespace.parent_resource_path.type,
            namespace.parent_resource_path.name) if namespace.parent_resource_path else ''
