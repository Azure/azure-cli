# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):  # pylint: disable=unused-argument
    with self.argument_context('lab vm claim') as c:
        c.argument('name', options_list=['--name', '-n'], id_part='child_name_1',
                   help='Name of the virtual machine to claim.')
        c.argument('lab_name', id_part='name', help='Name of the lab.')
