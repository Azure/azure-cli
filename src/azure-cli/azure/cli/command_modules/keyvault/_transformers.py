# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def filter_out_managed_resources(output):
    return [_ for _ in output if not getattr(_, 'managed')] if output else output
