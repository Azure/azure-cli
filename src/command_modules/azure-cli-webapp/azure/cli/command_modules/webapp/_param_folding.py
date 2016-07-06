from __future__ import print_function
import argparse

from azure.cli._util import CLIError
from azure.cli.commands import register_cli_argument
from azure.cli.commands.arm import is_valid_resource_id, resource_id, resource_exists

def register_folded_cli_argument(scope, base_name, resource_type, parent_name=None, # pylint: disable=too-many-arguments
                                 parent_type=None, type_field=None,
                                 existing_id_flag_value='existingId', new_flag_value='new',
                                 none_flag_value='none', post_validator=None, **kwargs):
    type_field_name = type_field or base_name + '_type'
    register_cli_argument(scope, base_name, validator=_name_id_fold(base_name,
                                                                    resource_type,
                                                                    type_field_name,
                                                                    existing_id_flag_value,
                                                                    new_flag_value,
                                                                    none_flag_value,
                                                                    parent_name,
                                                                    parent_type,
                                                                    post_validator), **kwargs)
    register_cli_argument(scope, type_field_name, help=argparse.SUPPRESS, default=None)

def _name_id_fold(base_name, resource_type, type_field, #pylint: disable=too-many-arguments
                  existing_id_flag_value, new_flag_value, none_flag_value, parent_name=None,
                  parent_type=None, post_validator=None):
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
            has_parent = parent_name is not None and parent_type is not None
            if is_valid_resource_id(base_name_val):
                resource_id = base_name_val
            elif has_parent:
                resource_id = resource_id(
                    name_or_id=parent_name_val,
                    resource_group=namespace.resource_group_name,
                    full_type=parent_type,
                    subscription_id=get_subscription_id(),
                    child_name=base_name_val,
                    child_type=resource_type)
            else:
                resource_id = resource_id(
                    name_or_id=base_name_val,
                    resource_group=namespace.resource_group_name,
                    full_type= resource_type,
                    subscription_id=get_subscription_id())

            if resource_exists(resource_id):
                setattr(namespace, type_field, existing_id_flag_value)
                setattr(namespace, base_name, resource_id)
            elif is_valid_resource_id(base_name_val):
                raise CLIError('ID {} does not exist. Please specify '
                               'a name to create a new resource.'.format(resource_id))
            else:
                setattr(namespace, type_field, new_flag_value)

        if post_validator:
            post_validator(namespace)

    return handle_folding

def get_subscription_id():
    from azure.cli.commands.client_factory import Profile
    profile = Profile()
    _, subscription_id = profile.get_login_credentials()
    return subscription_id
