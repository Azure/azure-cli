# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
from azure.cli.core.util import CLIError
from ._client_factory import _graph_client_factory

VARIANT_GROUP_ID_ARGS = ['object_id', 'group_id', 'group_object_id']


def validate_group(namespace):
    # For AD auto-commands, here we resolve logic names to object ids needed by SDK methods
    attr, value = next(((x, getattr(namespace, x)) for x in VARIANT_GROUP_ID_ARGS
                        if hasattr(namespace, x)))
    try:
        uuid.UUID(value)
    except ValueError:
        client = _graph_client_factory()
        sub_filters = []
        sub_filters.append("startswith(displayName,'{}')".format(value))
        sub_filters.append("displayName eq '{}'".format(value))
        result = list(client.groups.list(filter=' or '.join(sub_filters)))
        count = len(result)
        if count == 1:
            setattr(namespace, attr, result[0].object_id)
        elif count == 0:
            raise CLIError("No group matches the name of '{}'".format(value))
        else:
            raise CLIError("More than one groups match the name of '{}'".format(value))


def validate_member_id(namespace):
    from azure.cli.core._profile import Profile, CLOUD
    try:
        uuid.UUID(namespace.url)
        profile = Profile()
        _, _, tenant_id = profile.get_login_credentials()
        graph_url = CLOUD.endpoints.active_directory_graph_resource_id
        namespace.url = '{}{}/directoryObjects/{}'.format(graph_url, tenant_id,
                                                          namespace.url)
    except ValueError:
        pass  # let it go, invalid values will be caught by server anyway
