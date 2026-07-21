# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from enum import Enum

class ExpiryOptionType(Enum):
    never_expire = "NeverExpire"
    relative_to_now = "RelativeToNow"
    relative_to_creation_date = "RelativeToCreationDate"
    absolute = "Absolute"