# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from enum import Enum


class TagUpdateOperation(str, Enum):
    merge = "Merge"
    replace = "Replace"
    delete = "Delete"
