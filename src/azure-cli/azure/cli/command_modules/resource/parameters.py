# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from enum import Enum
from azure.core import CaseInsensitiveEnumMeta


class TagUpdateOperation(str, Enum):
    merge = "Merge"
    replace = "Replace"
    delete = "Delete"


class StacksActionOnUnmanage(str, Enum, metaclass=CaseInsensitiveEnumMeta):
    DELETE_ALL = "deleteAll"
    DELETE_RESOURCES = "deleteResources"
    DETACH_ALL = "detachAll"
