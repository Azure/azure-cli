# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class SubscriptionOperations:
    def __init__(self, parent):
        self.parent = parent

    def load_arguments(self, _):
        from azure.cli.command_modules.apim.operations.subscription.params import load_arguments
        load_arguments(self.parent.commands_loader, _)

    def load_command_table(self, _):
        from azure.cli.command_modules.apim.operations.subscription.commands import load_command_table
        load_command_table(self.parent.commands_loader, _)
