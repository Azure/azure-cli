# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):
    with self.argument_context('find') as c:
        c.argument('criteria', options_list=['--search-query', '-q'], help='Query text to find.', nargs='+')
        c.argument('reindex', help='Clear the current index and reindex the command modules.')
