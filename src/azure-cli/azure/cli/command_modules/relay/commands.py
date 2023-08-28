# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements


def load_command_table(self, _):

    # Namespace Region
    with self.command_group('relay namespace authorization-rule'):
        from azure.cli.command_modules.relay.custom import NamespaceAuthoCreate
        self.command_table['relay namespace authorization-rule create'] = NamespaceAuthoCreate(loader=self)

    # WCF Relay Region
    with self.command_group('relay wcfrelay'):
        from azure.cli.command_modules.relay.custom import WcfrelayUpdate
        self.command_table['relay wcfrelay update'] = WcfrelayUpdate(loader=self)

    with self.command_group('relay wcfrelay authorization-rule'):
        from azure.cli.command_modules.relay.custom import WcfrelayAuthoCreate, WcfrelayAuthoUpdate
        self.command_table['relay wcfrelay authorization-rule create'] = WcfrelayAuthoCreate(loader=self)
        self.command_table['relay wcfrelay authorization-rule update'] = WcfrelayAuthoUpdate(loader=self)

    # Hybrid Connections Region
    with self.command_group('relay hyco'):
        from azure.cli.command_modules.relay.custom import HycoUpdate
        self.command_table['relay hyco update'] = HycoUpdate(loader=self)

    with self.command_group('relay hyco authorization-rule'):
        from azure.cli.command_modules.relay.custom import HycoAuthoCreate, HycoAuthoUpdate
        self.command_table['relay hyco authorization-rule create'] = HycoAuthoCreate(loader=self)
        self.command_table['relay hyco authorization-rule update'] = HycoAuthoUpdate(loader=self)
