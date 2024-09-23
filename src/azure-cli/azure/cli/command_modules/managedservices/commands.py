# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def load_command_table(self, _):
    with self.command_group("managedservices definition"):
        from .custom import DefinitionCreate, DefinitionList, DefinitionShow, DefinitionDelete
        self.command_table["managedservices definition create"] = DefinitionCreate(loader=self)
        self.command_table["managedservices definition list"] = DefinitionList(loader=self)
        self.command_table["managedservices definition show"] = DefinitionShow(loader=self)
        self.command_table["managedservices definition delete"] = DefinitionDelete(loader=self)

    with self.command_group("managedservices assignment"):
        from .custom import AssignmentCreate, AssignmentList, AssignmentShow, AssignmentDelete
        self.command_table["managedservices assignment create"] = AssignmentCreate(loader=self)
        self.command_table["managedservices assignment list"] = AssignmentList(loader=self)
        self.command_table["managedservices assignment show"] = AssignmentShow(loader=self)
        self.command_table["managedservices assignment delete"] = AssignmentDelete(loader=self)
