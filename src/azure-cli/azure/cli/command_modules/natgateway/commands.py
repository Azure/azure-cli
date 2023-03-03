# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def load_command_table(self, _):
    from .custom import NATGatewayCreate, NATGatewayUpdate
    self.command_table["network nat gateway create"] = NATGatewayCreate(loader=self)
    self.command_table["network nat gateway update"] = NATGatewayUpdate(loader=self)
