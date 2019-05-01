# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def str2bool(v):
    if v == 'true':
        retval = True
    elif v == 'false':
        retval = False
    else:
        retval = None
    return retval
