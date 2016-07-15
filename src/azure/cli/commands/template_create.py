from __future__ import print_function
import argparse

from azure.cli._util import CLIError
from azure.cli.commands import register_cli_argument
from azure.cli.commands.arm import (
    is_valid_resource_id,
    parse_resource_id,
    resource_id,
    resource_exists)

def register_folded_cli_argument(scope, base_name, resource_type, parent_name=None, # pylint: disable=too-many-arguments
                                 parent_type=None, type_field=None,
                                 existing_id_flag_value='existingId', new_flag_value='new',
                                 none_flag_value='none', **kwargs):
    type_field_name = type_field or base_name + '_type'

    fold_validator = _name_id_fold(base_name,
                                   resource_type,
                                   type_field_name,
                                   existing_id_flag_value,
                                   new_flag_value,
                                   none_flag_value,
                                   parent_name,
                                   parent_type)
    custom_validator = kwargs.pop('validator', None)
    if custom_validator:
        def wrapped(namespace):
            fold_validator(namespace)
            custom_validator(namespace)
        validator = wrapped
    else:
        validator = fold_validator

    register_cli_argument(scope, base_name, validator=validator, **kwargs)
    register_cli_argument(scope, type_field_name, help=argparse.SUPPRESS, default=None)

def _name_id_fold(base_name, resource_type, type_field, #pylint: disable=too-many-arguments
                  existing_id_flag_value, new_flag_value, none_flag_value, parent_name=None,
                  parent_type=None):
    def handle_folding(namespace):
        base_name_val = getattr(namespace, base_name)
        type_field_val = getattr(namespace, type_field)
        parent_name_val = getattr(namespace, parent_name) if parent_name else None

        if base_name_val is None or type_field_val is not None:
            # Either no name was specified, or the user specified the type of resource
            # (i.e. new/existing/none)
            pass
        elif base_name_val == '':
            # An empty name specified - that means that we are neither referencing an existing
            # field, or the name is set to an empty string
            setattr(namespace, type_field, none_flag_value)
        else:
            from azure.cli.commands.client_factory import get_subscription_id
            has_parent = parent_name is not None and parent_type is not None
            if is_valid_resource_id(base_name_val):
                resource_id_parts = parse_resource_id(base_name_val)
            elif has_parent:
                resource_id_parts = dict(
                    name=parent_name_val,
                    resource_group=namespace.resource_group_name,
                    namespace=parent_type.split('/')[0],
                    type=parent_type.split('/')[1],
                    subscription=get_subscription_id(),
                    child_name=base_name_val,
                    child_type=resource_type)
            else:
                resource_id_parts = dict(
                    name=base_name_val,
                    resource_group=namespace.resource_group_name,
                    namespace=resource_type.split('/')[0],
                    type=resource_type.split('/')[1],
                    subscription=get_subscription_id())

            if resource_exists(**resource_id_parts):
                setattr(namespace, type_field, existing_id_flag_value)
                setattr(namespace, base_name, resource_id(**resource_id_parts))
            elif is_valid_resource_id(base_name_val):
                raise CLIError('ID {} does not exist. Please specify '
                               'a name to create a new resource.'.format(
                                   resource_id(**resource_id_parts)))
            else:
                setattr(namespace, type_field, new_flag_value)

    return handle_folding

