# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import time
import random
from azure.cli.core.profiles import ResourceType


def validate_tags(ns):
    ''' Extracts multiple space-separated tags in key[=value] format '''
    if isinstance(ns.tags, list):
        tags_dict = {}
        for item in ns.tags:
            tags_dict.update(validate_tag(item))
        ns.tags = tags_dict


def validate_tag(string):
    ''' Extracts a single tag in key[=value] format '''
    result = {}
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result


def validate_key_value_pairs(string):
    ''' Validates key-value pairs in the following format: a=b;c=d '''
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=', 1) for x in kv_list)
    return result


def generate_deployment_name(namespace):
    if not namespace.deployment_name:
        namespace.deployment_name = \
            'azurecli{}{}'.format(str(time.time()), str(random.randint(1, 100000)))


def get_default_location_from_resource_group(namespace):
    if not namespace.location:
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        resource_client = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
        rg = resource_client.resource_groups.get(namespace.resource_group_name)
        namespace.location = rg.location  # pylint: disable=no-member


def validate_file_or_dict(string):
    import os
    string = os.path.expanduser(string)
    if os.path.exists(string):
        from azure.cli.core.util import get_file_json
        return get_file_json(string)

    from azure.cli.core.util import shell_safe_json_parse
    return shell_safe_json_parse(string)


SPECIFIED_SENTINEL = '__SET__'


class MarkSpecifiedAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """ Use this to identify when a parameter is explicitly set by the user (as opposed to a
    default). You must remove the __SET__ sentinel substring in a follow-up validator."""

    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, '{}{}'.format(SPECIFIED_SENTINEL, values))
