# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import platform

from azure.cli.core.commands.arm import resource_exists

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def get_folded_parameter_help_string(
        display_name, allow_none=False, allow_new=False, default_none=False,
        other_required_option=None, allow_cross_sub=True):
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
        help_text = 'Name or ID of the {}, or {} for none. Uses existing resource if available or will create a new ' \
                    'resource with defaults if omitted.'
        help_text = help_text.format(display_name, quotes)
    elif not allow_new and allow_none and default_none:
        help_text = 'Name or ID of an existing {}, or none by default.'.format(display_name)
    elif allow_new and allow_none and default_none:
        help_text = 'Name or ID of a {}. Uses existing resource or creates new if specified, or none if omitted.'
        help_text = help_text.format(display_name)

    # add parent name option string (if applicable)
    if other_required_option:
        help_text = '{} If name specified, also specify {}.'.format(help_text, other_required_option)
        extra_sub_text = " or subscription" if allow_cross_sub else ""
        help_text = '{} If you want to use an existing {display_name} in other resource group{append_sub}, ' \
                    'please provide the ID instead of the name of the {display_name}'.format(help_text,
                                                                                             display_name=display_name,
                                                                                             append_sub=extra_sub_text)
    return help_text


def _validate_name_or_id(
        cli_ctx, resource_group_name, property_value, property_type, parent_value, parent_type):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
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
            subscription=get_subscription_id(cli_ctx),
            child_name_1=property_value,
            child_type_1=property_type)
        value_supplied_was_id = False
    else:
        resource_id_parts = dict(
            name=property_value,
            resource_group=resource_group_name,
            namespace=property_type.split('/')[0],
            type=property_type.split('/')[1],
            subscription=get_subscription_id(cli_ctx))
        value_supplied_was_id = False
    return (resource_id_parts, value_supplied_was_id)


def get_folded_parameter_validator(
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
    def validator(cmd, namespace):
        from azure.mgmt.core.tools import resource_id
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
                logger.warning('Ignoring: %s %s', parent_option, parent_val)
                setattr(namespace, parent_name, None)
            return  # SUCCESS

        # Create a resource ID we can check for existence.
        (resource_id_parts, value_was_id) = _validate_name_or_id(
            cmd.cli_ctx, namespace.resource_group_name, property_val, property_type, parent_val, parent_type)

        # 2) resource exists
        if resource_exists(cmd.cli_ctx, **resource_id_parts):
            setattr(namespace, type_field_name, 'existingId')
            setattr(namespace, property_name, resource_id(**resource_id_parts))
            if parent_val:
                if value_was_id:
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
