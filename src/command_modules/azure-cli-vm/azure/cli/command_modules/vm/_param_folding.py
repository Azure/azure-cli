import argparse

from azure.cli._util import CLIError
from azure.cli.commands import register_cli_argument
from azure.cli.commands.azure_resource_id import AzureResourceId, resource_exists

def register_folded_cli_argument(scope, base_name, resource_type, type_field=None, #pylint: disable=too-many-arguments
                                 existing_id_flag_value='existingId', new_flag_value='new',
                                 none_flag_value='none', **kwargs):
    type_field_name = type_field or base_name + '_type'
    register_cli_argument(scope, base_name, validator=_name_id_fold(base_name,
                                                                    resource_type,
                                                                    type_field_name,
                                                                    existing_id_flag_value,
                                                                    new_flag_value,
                                                                    none_flag_value), **kwargs)
    register_cli_argument(scope, type_field_name, help=argparse.SUPPRESS, default=None)

def _name_id_fold(base_name, resource_type, type_field, #pylint: disable=too-many-arguments
                  existing_id_flag_value, new_flag_value, none_flag_value):
    def handle_folding(namespace):
        name_or_id = getattr(namespace, base_name)
        if name_or_id is None:
            return
        elif name_or_id == '\'\'' or name_or_id == '""' or name_or_id == '':
            setattr(namespace, type_field, none_flag_value)
            return

        setattr(namespace, base_name, name_or_id)

        if getattr(namespace, type_field) is not None:
            return

        # TODO: hook up namespace._subscription_id once we support it
        r_id = AzureResourceId(name_or_id, namespace.resource_group_name, resource_type,
                               get_subscription_id())

        if resource_exists(r_id):
            setattr(namespace, type_field, existing_id_flag_value)
            setattr(namespace, base_name, str(r_id))
        elif '/' in name_or_id:
            raise CLIError('ID {} does not exist.  Please specify'
                           ' a name to create a new resource.'.format(name_or_id))
        else:
            setattr(namespace, type_field, new_flag_value)

    return handle_folding

def get_subscription_id():
    from azure.cli.commands.client_factory import Profile
    profile = Profile()
    _, subscription_id = profile.get_login_credentials()
    return subscription_id
