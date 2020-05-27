# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _dont_fail_on_exist(ex, error_code):
    """
    don't throw exception if the resource doesn't exist.
    This is called by create_* APIs with fail_on_exist=False
    :param error:
    :param resource:
    :return:
    """
    if ex.error_code == error_code:
        return False
    raise ex
