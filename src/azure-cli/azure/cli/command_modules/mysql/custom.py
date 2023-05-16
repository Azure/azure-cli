# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_mysql(cmd, resource_group_name, mysql_name, location=None, tags=None):
    raise CLIError('TODO: Implement `mysql create`')


def list_mysql(cmd, resource_group_name=None):
    raise CLIError('TODO: Implement `mysql list`')


def update_mysql(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance