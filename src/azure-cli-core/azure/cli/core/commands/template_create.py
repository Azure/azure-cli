#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import argparse
import platform

from azure.cli.core._util import CLIError
from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.arm import (
    is_valid_resource_id,
    parse_resource_id,
    resource_id,
    resource_exists,
    make_camel_case)

def register_folded_cli_argument(scope, base_name, resource_type, parent_name=None, # pylint: disable=too-many-arguments
                                 parent_type=None, type_field=None,
                                 existing_id_flag_value='existingId', new_flag_value='new',
                                 none_flag_value='none', default_value_flag='new',
                                 **kwargs):
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

    quotes = '""' if platform.system() == 'Windows' else "''"
    quote_text = '  Use {} for none.'.format(quotes) if none_flag_value else ''
    flag_texts = {
        new_flag_value: '  Creates new by default.{}'.format(quote_text),
        existing_id_flag_value: '  Uses existing resource.{}'
                                .format(quote_text),
        none_flag_value: '  None by default.'
    }
    help_text = 'Name or ID of the resource.' + flag_texts[default_value_flag]

    register_cli_argument(scope, base_name, validator=validator, help=help_text, **kwargs)
    register_cli_argument(scope, type_field_name, help=argparse.SUPPRESS, default=None)

def _name_id_fold(base_name, resource_type, type_field, #pylint: disable=too-many-arguments
                  existing_id_flag_value, new_flag_value, none_flag_value,
                  parent_name=None, parent_type=None):
    def handle_folding(namespace):
        base_name_val = getattr(namespace, base_name)
        type_field_val = getattr(namespace, type_field)
        parent_name_val = getattr(namespace, parent_name) if parent_name else None

        if base_name_val is None or type_field_val is not None:
            # Either no name was specified, or the user specified the type of resource
            # (i.e. new/existing/none)
            pass
        elif base_name_val in ('', '""', "''"):
            # An empty name specified - that means that we are neither referencing an existing
            # field, or the name is set to an empty string.  We check for all types of quotes
            # so scripts can run cross-platform.
            if not none_flag_value:
                raise CLIError('Field {} cannot be none.'.format(make_camel_case(base_name)))
            setattr(namespace, type_field, none_flag_value)
            setattr(namespace, base_name, None)
        else:
            from azure.cli.core.commands.client_factory import get_subscription_id
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
            elif not new_flag_value:
                raise CLIError('Referenced resource {} does not exist. Please create the required '
                               'resource and try again.'.format(resource_id(**resource_id_parts)))
            else:
                setattr(namespace, type_field, new_flag_value)

    return handle_folding

