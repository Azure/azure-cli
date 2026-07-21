# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import time
import random

from azure.cli.core.profiles import ResourceType

from knack.log import get_logger
from knack.util import CLIError
from knack.validators import DefaultStr, DefaultInt  # pylint: disable=unused-import

JSON_RECOMMENDATION_MESSAGE = "Please provide a valid JSON file path or JSON string."

logger = get_logger(__name__)


class IterateAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Action used to collect argument values in an IterateValue list
    The application will loop through each value in the IterateValue
    and execeute the associated handler for each
    """

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, IterateValue(values))


class IterateValue(list):
    """Marker class to indicate that, when found as a value in the parsed namespace
    from argparse, the handler should be invoked once per value in the list with all
    other values in the parsed namespace frozen.

    Typical use is to allow multiple ID parameter to a show command etc.
    """
    pass  # pylint: disable=unnecessary-pass


def validate_tags(ns):
    """ Extracts multiple space-separated tags in key[=value] format """
    if isinstance(ns.tags, list):
        tags_dict = {}
        for item in ns.tags:
            tags_dict.update(validate_tag(item))
        ns.tags = tags_dict


def validate_tag(string):
    """ Extracts a single tag in key[=value] format """
    result = {}
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result


def validate_key_value_pairs(string):
    """ Validates key-value pairs in the following format: a=b;c=d """
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=', 1) for x in kv_list)
    return result


def generate_deployment_name(namespace):
    if not namespace.deployment_name:
        namespace.deployment_name = \
            'azurecli{}{}'.format(str(time.time()), str(random.randint(1, 100000)))


def get_default_location_from_resource_group(cmd, namespace):
    if not namespace.location:
        from azure.cli.core.commands.client_factory import get_mgmt_service_client

        # We don't use try catch here to let azure.cli.core.parser.AzCliCommandParser.validation_error
        # handle exceptions, such as azure.core.exceptions.ResourceNotFoundError
        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        rg = resource_client.resource_groups.get(namespace.resource_group_name)
        namespace.location = rg.location  # pylint: disable=no-member

        logger.debug("using location '%s' from resource group '%s'", namespace.location, rg.name)


def validate_file_or_dict(string):
    """Parse string as a JSON file or in-line JSON string."""
    import os
    string = os.path.expanduser(string)
    try:
        if os.path.exists(string):
            from azure.cli.core.util import get_file_json
            # Error 1: 'string' is an existing file path, but the file contains invalid JSON string
            # ex has no recommendation
            return get_file_json(string)

        # Error 2: If string ends with '.json', it can't be a JSON string, since a JSON string must ends with
        # ], }, or ", so it must be JSON file, and we don't allow parsing it as in-line string
        if string.endswith('.json'):
            raise CLIError("JSON file does not exist: '{}'".format(string))

        from azure.cli.core.util import shell_safe_json_parse
        # Error 3: string is a non-existing file path or invalid JSON string
        # ex has recommendations for shell interpretation
        return shell_safe_json_parse(string)
    except CLIError as ex:
        from azure.cli.core.azclierror import InvalidArgumentValueError
        new_ex = InvalidArgumentValueError(ex, recommendation=JSON_RECOMMENDATION_MESSAGE)
        # Preserve the recommendation
        if hasattr(ex, "recommendations"):
            new_ex.set_recommendation(ex.recommendations)
        raise new_ex from ex


def validate_parameter_set(namespace, required, forbidden, dest_to_options=None, description=None):
    """ validates that a given namespace contains the specified required parameters and does not contain any of
        the provided forbidden parameters (unless the value came from a default). """

    missing_required = [x for x in required if not getattr(namespace, x)]
    included_forbidden = [x for x in forbidden if getattr(namespace, x) and
                          not hasattr(getattr(namespace, x), 'is_default')]
    if missing_required or included_forbidden:
        def _dest_to_option(dest):
            try:
                return dest_to_options[dest]
            except (KeyError, TypeError):
                # assume the default dest to option
                return '--{}'.format(dest).replace('_', '-')

        error = 'invalid usage{}{}'.format(' for ' if description else ':', description)
        if missing_required:
            missing_string = ', '.join(_dest_to_option(x) for x in missing_required)
            error = '{}\n\tmissing: {}'.format(error, missing_string)
        if included_forbidden:
            forbidden_string = ', '.join(_dest_to_option(x) for x in included_forbidden)
            error = '{}\n\tnot applicable: {}'.format(error, forbidden_string)
        raise CLIError(error)
