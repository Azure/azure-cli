import argparse

from azure.cli._util import CLIError
from azure.cli.commands import register_cli_argument
from azure.cli.commands.arm import is_valid_resource_id, resource_id, resource_exists

def register_folded_cli_argument(scope, base_name, resource_type, type_field=None, #pylint: disable=too-many-arguments
                                 existing_id_flag_value='existingId', new_flag_value='new',
                                 **kwargs):
    type_field_name = type_field or base_name + '_type'
    register_cli_argument(scope, base_name, action=_name_id_fold(base_name,
                                                                 resource_type,
                                                                 type_field_name,
                                                                 existing_id_flag_value,
                                                                 new_flag_value), **kwargs)
    register_cli_argument(scope, type_field_name, help=argparse.SUPPRESS, default=None)

def _name_id_fold(base_name, resource_type, type_field, #pylint: disable=too-many-arguments
                  existing_id_flag_value, new_flag_value):
    class NameIdFoldAction(argparse.Action): #pylint: disable=too-few-public-methods
        def __call__(self, parser, namespace, values, option_string=None):
            name_or_id = values
            if not name_or_id:
                return

            setattr(namespace, base_name, name_or_id)

            if getattr(namespace, type_field) is not None:
                return

            # TODO: hook up namespace._subscription_id once we support it
            if is_valid_resource_id(name_or_id):
                r_id = name_or_id
            else:
                r_id = resource_id(name=name_or_id,
                                   resource_group=namespace.resource_group_name,
                                   type=resource_type,
                                   subscription=get_subscription_id())

            if resource_exists(r_id):
                setattr(namespace, type_field, existing_id_flag_value)
                setattr(namespace, base_name, str(r_id))
            elif '/' in name_or_id:
                raise CLIError('ID {} does not exist.  Please specify'
                               ' a name to create a new resource.'.format(name_or_id))
            else:
                setattr(namespace, type_field, new_flag_value)

    return NameIdFoldAction

def get_subscription_id():
    from azure.cli.commands.client_factory import Profile
    profile = Profile()
    _, subscription_id = profile.get_login_credentials()
    return subscription_id
