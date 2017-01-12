# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import argparse
import platform

import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.arm import (
    is_valid_resource_id,
    parse_resource_id,
    resource_id,
    resource_exists,
    make_camel_case)


def register_folded_cli_argument(scope, base_name, resource_type, parent_name=None,  # pylint: disable=too-many-arguments
                                 parent_option_flag=None, parent_type=None, type_field=None,
                                 existing_id_flag_value='existingId', new_flag_value='new',
                                 none_flag_value='none', default_value_flag='new',
                                 base_required=True, **kwargs):
    type_field_name = type_field or base_name + '_type'

    fold_validator = _name_id_fold(base_name,
                                   resource_type,
                                   type_field_name,
                                   existing_id_flag_value,
                                   new_flag_value,
                                   none_flag_value,
                                   parent_name,
                                   parent_option_flag,
                                   parent_type,
                                   base_required)
    custom_validator = kwargs.pop('validator', None)
    custom_help = kwargs.pop('help', None)
    if custom_validator:
        def wrapped(namespace):
            fold_validator(namespace)
            custom_validator(namespace)
        validator = wrapped
    else:
        validator = fold_validator

    if not custom_help:
        quotes = '""' if platform.system() == 'Windows' else "''"
        quote_text = ' Use {} for none.'.format(quotes) if none_flag_value else ''
        parent_text = ' If name specified, must also specify {}.'.format(
            parent_option_flag or parent_name) if parent_name else ''
        flag_texts = {
            new_flag_value: '  Creates new by default.{}'.format(quote_text),
            existing_id_flag_value: '  Uses existing resource.{}{}'
                                    .format(quote_text, parent_text),
            none_flag_value: '  None by default.'
        }
        help_text = 'Name or ID of the resource.' + flag_texts[default_value_flag]
    else:
        help_text = custom_help

    register_cli_argument(scope, base_name, validator=validator, help=help_text, **kwargs)
    register_cli_argument(scope, type_field_name, help=argparse.SUPPRESS, default=None)


def _name_id_fold(base_name, resource_type, type_field,  # pylint: disable=too-many-arguments
                  existing_id_flag_value, new_flag_value, none_flag_value,
                  parent_name=None, parent_option_flag=None, parent_type=None, base_required=True):
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
                if not parent_name_val and base_required:
                    raise CLIError("Must specify '{}' when specifying '{}' name.".format(
                        parent_option_flag or parent_name, base_name))
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

# NEW STYLE

# pylint: disable=line-too-long


def get_folded_parameter_help_string(
        display_name, allow_none=False, allow_new=False, default_none=False,
        other_required_option=None):
    """ Assembles a parameterized help string for folded parameters. """
    quotes = '""' if platform.system() == 'Windows' else "''"

    if default_none and not allow_none:
        raise CLIError('Cannot use default_none=True and allow_none=False')

    if not allow_new and not allow_none and not default_none:
        help_text = 'Name or ID of an existing {}.'.format(display_name)
    elif not allow_new and allow_none and not default_none:
        help_text = 'Name or ID of an existing {}, or {} for none.'.format(display_name, quotes)
    elif allow_new and not allow_none and not default_none:
        help_text = 'Name or ID of the {}. Will create resource if it does not exist.'.format(
            display_name)
    elif allow_new and allow_none and not default_none:
        help_text = 'Name or ID of the {}, or {} for none. Uses existing resource if available or will create a new resource with defaults if omitted.'.format(
            display_name, quotes)
    elif not allow_new and allow_none and default_none:
        help_text = 'Name or ID of an existing {}, or none by default.'.format(display_name)
    elif allow_new and allow_none and default_none:
        help_text = 'Name or ID of a {}. Uses existing resource or creates new if specified, or none if omitted.'.format(
            display_name)

    # add parent name option string (if applicable)
    if other_required_option:
        help_text = '{} If name specified, also specify {}'.format(help_text, other_required_option)
    return help_text


def _validate_name_or_id(
        resource_group_name, property_value, property_type, parent_value, parent_type):
    from azure.cli.core.commands.client_factory import get_subscription_id
    has_parent = parent_type is not None
    if is_valid_resource_id(property_value):
        resource_id_parts = parse_resource_id(property_value)
        value_supplied_was_id = True
    elif has_parent:
        resource_id_parts = dict(
            name=parent_value,
            resource_group=resource_group_name,
            namespace=parent_type.split('/')[0],
            type=parent_type.split('/')[1],
            subscription=get_subscription_id(),
            child_name=property_value,
            child_type=property_type)
        value_supplied_was_id = False
    else:
        resource_id_parts = dict(
            name=property_value,
            resource_group=resource_group_name,
            namespace=property_type.split('/')[0],
            type=property_type.split('/')[1],
            subscription=get_subscription_id())
        value_supplied_was_id = False
    return (resource_id_parts, value_supplied_was_id)


def get_folded_parameter_validator(  # pylint: disable=too-many-arguments
        property_name, property_type, property_option,
        parent_name=None, parent_type=None, parent_option=None,
        allow_none=False, allow_new=False, default_none=False):

    # Ensure that all parent parameters are specified if any are
    parent_params = [parent_name, parent_type, parent_option]
    has_parent = any(parent_params)
    if has_parent and not all(parent_params):
        raise CLIError('All parent parameters must be specified (name, type, option) if any are.')

    if default_none and not allow_none:
        raise CLIError('Cannot use default_none=True if allow_none=False')

    # construct the validator
    def validator(namespace):
        type_field_name = '{}_type'.format(property_name)
        property_val = getattr(namespace, property_name, None)
        parent_val = getattr(namespace, parent_name, None) if parent_name else None

        # Check for the different scenarios (order matters)
        # 1) provided value indicates None (pair of empty quotes)
        if property_val in ('', '""', "''") or (property_val is None and default_none):
            if not allow_none:
                raise CLIError('{} cannot be None.'.format(property_option))
            setattr(namespace, type_field_name, 'none')
            setattr(namespace, property_name, None)
            if parent_name and parent_val:
                logger = _logging.get_az_logger(__name__)
                logger.warning('Ignoring: %s %s', parent_option, parent_val)
                setattr(namespace, parent_name, None)
            return  # SUCCESS

        # Create a resource ID we can check for existence.
        (resource_id_parts, value_was_id) = _validate_name_or_id(
            namespace.resource_group_name, property_val, property_type, parent_val, parent_type)

        # 2) resource exists
        if resource_exists(**resource_id_parts):
            setattr(namespace, type_field_name, 'existingId')
            setattr(namespace, property_name, resource_id(**resource_id_parts))
            if parent_val:
                if value_was_id:
                    logger = _logging.get_az_logger(__name__)
                    logger.warning('Ignoring: %s %s', parent_option, parent_val)
                setattr(namespace, parent_name, None)
            return  # SUCCESS

        # if a parent name was required but not specified, raise a usage error
        if has_parent and not value_was_id and not parent_val and not allow_new:
            raise ValueError('incorrect usage: {0} ID | {0} NAME {1} NAME'.format(
                property_option, parent_option))

        # if non-existent ID was supplied, throw error depending on whether a new resource can
        # be created.
        if value_was_id:
            usage_message = '{} NAME'.format(property_option) if not has_parent \
                else '{} NAME [{} NAME]'.format(property_option, parent_option)
            action_message = 'Specify ( {} ) to create a new resource.'.format(usage_message) if \
                allow_new else 'Create the required resource and try again.'
            raise CLIError('{} {} does not exist. {}'.format(
                property_name, property_val, action_message))

        # 3) try to create new resource
        if allow_new:
            setattr(namespace, type_field_name, 'new')
        else:
            raise CLIError(
                '{} {} does not exist. Create the required resource and try again.'.format(
                    property_name, property_val))

    return validator
