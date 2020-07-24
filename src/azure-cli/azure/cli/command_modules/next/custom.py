# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_next(cmd, resource_group_name, next_name, location=None, tags=None):
    raise CLIError('TODO: Implement `next create`')


def list_next(cmd, resource_group_name=None):
    raise CLIError('TODO: Implement `next list`')


def update_next(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance