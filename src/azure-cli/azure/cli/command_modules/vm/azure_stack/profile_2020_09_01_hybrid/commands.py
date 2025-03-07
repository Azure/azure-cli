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
    from .operations.ppg import PPGShow, PPGUpdate
    self.command_table["ppg show"] = PPGShow(loader=self)
    self.command_table["ppg update"] = PPGUpdate(loader=self)

    Disk = import_aaz_by_profile("disk")
    self.command_table['disk list'] = Disk.List(loader=self, table_transformer='[].' + transform_disk_show_table_output)
    self.command_table['disk show'] = Disk.Show(loader=self, table_transformer=transform_disk_show_table_output)

    from .operations.disk import DiskUpdate, DiskGrantAccess
    self.command_table["disk grant-access"] = DiskGrantAccess(loader=self)
    self.command_table["disk update"] = DiskUpdate(loader=self)

    from .operations.snapshot import SnapshotUpdate
    self.command_table['snapshot update'] = SnapshotUpdate(loader=self)

    VMSS = import_aaz_by_profile("vmss")
    self.command_table['vmss list'] = VMSS.List(loader=self,
                                                table_transformer=transform_vmss_list_with_zones_table_output)

    from .operations.capacity_reservation_group import CapacityReservationGroupList
    self.command_table['capacity reservation group list'] = CapacityReservationGroupList(loader=self)

    from .operations.sig_image_definition import SigImageDefinitionUpdate
    self.command_table['sig image-definition update'] = SigImageDefinitionUpdate(loader=self)

    from .operations.vm import VMListSizes
    self.command_table['vm list-sizes'] = VMListSizes(loader=self)

    from .operations.disk_encryption_set import DiskEncryptionSetCreate, DiskEncryptionSetUpdate
    self.command_table["disk-encryption-set create"] = DiskEncryptionSetCreate(loader=self)
    self.command_table["disk-encryption-set update"] = DiskEncryptionSetUpdate(loader=self)

    # pylint: disable=line-too-long
    SigImageVersion = import_aaz_by_profile("sig.image_version")
    self.command_table['sig image-version show'] = SigImageVersion.Show(loader=self,
                                                                        table_transformer='{Name:name, ResourceGroup:resourceGroup, ProvisioningState:provisioningState, TargetRegions: publishingProfile.targetRegions && join(`, `, publishingProfile.targetRegions[*].name), EdgeZones: publishingProfile.targetExtendedLocations && join(`, `, publishingProfile.targetExtendedLocations[*].name), ReplicationState:replicationStatus.aggregatedState}')
