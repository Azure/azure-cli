# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):
    with self.argument_context('managementpartner') as c:
        c.argument('partner_id', help='Microsoft partner network ID')

    with self.argument_context('managementpartner show') as c:
        c.argument('partner_id', required=False)
