# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_arguments(self, _):

    with self.argument_context('parser') as c:
        c.argument('file_name', options_list=['--file-name', '-f'] , help='The name of the file to parse.')

    with self.argument_context('parser yaml') as c:
        c.argument('as_yaml', action='store_true', help='Output returned as yaml.')