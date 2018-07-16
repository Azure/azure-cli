# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

def load_arguments(self, _):
    with self.argument_context('loganalytics') as c:
        c.argument('workspace', options_list=['--workspace', '-w'], help='GUID representing the workspace of a Log Analytics Workspace', required=True)
        c.argument('kql', help='Query to execute over Log Analytics data.', required=True)
