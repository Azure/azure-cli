from __future__ import print_function
import argparse

from azure.cli._util import CLIError
from azure.cli.commands import register_cli_argument
from azure.cli.commands.azure_resource_id import AzureResourceId, resource_exists

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
            pass
        elif base_name_val == '\'\'' or base_name_val == '""' or base_name_val == '':
            setattr(namespace, type_field, none_flag_value)
        else:
            has_parent = parent_name is not None and parent_type is not None
            resource_id = base_name_val if '/' in base_name_val else None
            name = None
            if not resource_id:
                name = parent_name_val if has_parent else base_name_val

            # TODO: hook up namespace._subscription_id once we support it
            r_id = AzureResourceId(
                name_or_id=name or resource_id,
                resource_group=namespace.resource_group_name,
                full_type=parent_type if has_parent else resource_type,
                subscription_id=get_subscription_id(),
                child_name=base_name_val if has_parent else None,
                child_type=resource_type if has_parent else None)

            if resource_exists(r_id):
                setattr(namespace, type_field, existing_id_flag_value)
                setattr(namespace, base_name, str(r_id))
            elif resource_id:
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
