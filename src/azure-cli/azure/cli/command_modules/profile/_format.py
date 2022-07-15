# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def transform_account_list(result):
    transformed = []
    for r in result:
        res = OrderedDict([('Name', r['name']),
                           ('CloudName', r['cloudName']),
                           ('SubscriptionId', r['id']),
                           ('TenantId', r['tenantId']),
                           ('State', r.get('state')),
                           ('IsDefault', r['isDefault'])])
        transformed.append(res)
    return transformed
