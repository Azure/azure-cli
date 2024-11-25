# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements
from azure.cli.command_modules.vm.azure_stack._format import (
    transform_vmss_list_without_zones_table_output)

from .operations._util import import_aaz_by_profile


def load_command_table(self, _):
    VMSS = import_aaz_by_profile("vmss")
    self.command_table['vmss list'] = VMSS.List(loader=self,
                                                table_transformer=transform_vmss_list_without_zones_table_output)

    from .operations.capacity_reservation_group import CapacityReservationGroupList
    self.command_table['capacity reservation group list'] = CapacityReservationGroupList(loader=self)