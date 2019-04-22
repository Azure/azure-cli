# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_test(cmd, client, resource_group_name, test_name, location=None, tags=None):
    raise CLIError('TODO: Implement `test create`')


def list_test(cmd, client, resource_group_name=None):
    raise CLIError('TODO: Implement `test list`')


def update_test(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance