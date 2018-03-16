# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid


def _gen_guid():
    return uuid.uuid4()


def _is_guid(guid):
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        pass
    return False
