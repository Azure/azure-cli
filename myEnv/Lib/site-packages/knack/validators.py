# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class DefaultStr(str):

    def __new__(cls, *args, **kwargs):
        instance = str.__new__(cls, *args, **kwargs)
        instance.is_default = True
        return instance


class DefaultInt(int):

    def __new__(cls, *args, **kwargs):
        instance = int.__new__(cls, *args, **kwargs)
        instance.is_default = True
        return instance
