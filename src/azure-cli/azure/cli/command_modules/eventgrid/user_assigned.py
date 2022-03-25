# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from knack.util import CLIError
from azure.mgmt.eventgrid.models import (
    UserIdentityProperties
)


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddUserAssignedIdentities(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        valuesLen = len(values)
        if valuesLen != 3:
            raise CLIError('usage error: --user-assigned-identity userAssignedIdentityArmId clientId principalId')
        armId = values[0]
        clientId = values[1]
        principalId = values[2]
        user_identity_property = UserIdentityProperties(
            principalId=principalId,
            clientId=clientId)

        if namespace.user_assigned is None:
            namespace.user_assigned = {}
        namespace.user_assigned[armId] = user_identity_property
