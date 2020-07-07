# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_{{ name }}(cmd, {% if sdk_path %}client, {% endif %}resource_group_name, {% if sdk_property %}{{sdk_property}}, {% else %} { name }}_name, {% endif %}location=None, tags=None):
    raise CLIError('TODO: Implement `{{ name }} create`')


def list_{{ name }}(cmd, {% if sdk_path %}client, {% endif %}resource_group_name=None):
    raise CLIError('TODO: Implement `{{ name }} list`')


def update_{{ name }}(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance
