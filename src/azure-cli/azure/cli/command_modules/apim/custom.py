# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_apim(cmd, client, resource_group_name, apimanamagement, location=None, tags=None):
    raise CLIError('TODO: Implement `apim create`')


def list_apim(cmd, client, resource_group_name=None):
    raise CLIError('TODO: Implement `apim list`')


def update_apim(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance