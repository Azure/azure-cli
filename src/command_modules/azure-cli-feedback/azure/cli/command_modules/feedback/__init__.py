# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.feedback._help  # pylint: disable=unused-import


class FeedbackCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        super(FeedbackCommandsLoader, self).load_command_table(args)
        self.cli_command(__name__, 'feedback', 'azure.cli.command_modules.feedback.custom#handle_feedback')
        return self.command_table
