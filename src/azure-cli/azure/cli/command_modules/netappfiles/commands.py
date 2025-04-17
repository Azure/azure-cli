# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

def load_command_table(self, _):
    # with self.command_group('netappfiles account'):
    #     from .custom import AccountCreate, AccountUpdate
    #     self.command_table["netappfiles account create"] = AccountCreate(loader=self)
    #     self.command_table["netappfiles account update"] = AccountUpdate(loader=self)

    with self.command_group('netappfiles account ad'):
        from .custom import ActiveDirectoryAdd, ActiveDirectoryList, ActiveDirectoryUpdate
        self.command_table["netappfiles account ad add"] = ActiveDirectoryAdd(loader=self)
        self.command_table["netappfiles account ad update"] = ActiveDirectoryUpdate(loader=self)
        self.command_table["netappfiles account ad list"] = ActiveDirectoryList(loader=self)

    with self.command_group('netappfiles pool'):
        from .custom import PoolCreate, PoolUpdate
        self.command_table["netappfiles pool create"] = PoolCreate(loader=self)
        self.command_table["netappfiles pool update"] = PoolUpdate(loader=self)

    with self.command_group('netappfiles volume'):
        from .custom import VolumeCreate, VolumeUpdate, VolumeBreakFileLocks
        self.command_table["netappfiles volume create"] = VolumeCreate(loader=self)
        self.command_table["netappfiles volume update"] = VolumeUpdate(loader=self)
        self.command_table["netappfiles volume break-file-locks"] = VolumeBreakFileLocks(loader=self)

    with self.command_group('netappfiles volume-group'):
        from .custom import VolumeGroupCreate
        self.command_table["netappfiles volume-group create"] = VolumeGroupCreate(loader=self)

    with self.command_group('netappfiles volume export-policy'):
        from .custom import ExportPolicyList, ExportPolicyAdd, ExportPolicyRemove
        self.command_table['netappfiles volume export-policy list'] = ExportPolicyList(loader=self)
        self.command_table['netappfiles volume export-policy add'] = ExportPolicyAdd(loader=self)
        self.command_table['netappfiles volume export-policy remove'] = ExportPolicyRemove(loader=self)

    with self.command_group('netappfiles volume replication'):
        from .custom import ReplicationResume
        self.command_table['netappfiles volume replication resume'] = ReplicationResume(loader=self)

    with self.command_group('netappfiles', is_preview=False):
        from .custom import UpdateNetworkSiblingSet
        self.command_table["netappfiles update-network-sibling-set"] = UpdateNetworkSiblingSet(loader=self)
