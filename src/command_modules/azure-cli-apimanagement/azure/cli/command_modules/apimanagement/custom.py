# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_apimanagement(cmd, client, resource_group_name, apimanagement_name, location=None, tags=None):
    raise CLIError('TODO: Implement `apimanagement create`')


def list_apimanagement(cmd, client, resource_group_name=None):
    raise CLIError('TODO: Implement `apimanagement list`')


def update_apimanagement(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance