# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements
from azure.cli.command_modules.vm.azure_stack._format import (
    transform_disk_show_table_output,
    transform_vmss_list_with_zones_table_output)

from .operations._util import import_aaz_by_profile


def load_command_table(self, _):
    Disk = import_aaz_by_profile("disk")
    self.command_table['disk list'] = Disk.List(loader=self, table_transformer='[].' + transform_disk_show_table_output)
    self.command_table['disk show'] = Disk.Show(loader=self, table_transformer=transform_disk_show_table_output)

    from .operations.disk import DiskUpdate, DiskGrantAccess
    self.command_table["disk grant-access"] = DiskGrantAccess(loader=self)
    self.command_table["disk update"] = DiskUpdate(loader=self)

    VMSS = import_aaz_by_profile("vmss")
    self.command_table['vmss list'] = VMSS.List(loader=self,
                                                table_transformer=transform_vmss_list_with_zones_table_output)

    from .operations.capacity_reservation_group import CapacityReservationGroupList
    self.command_table['capacity reservation group list'] = CapacityReservationGroupList(loader=self)

    from .operations.vm import VMListSizes
    self.command_table['vm list-sizes'] = VMListSizes(loader=self)
