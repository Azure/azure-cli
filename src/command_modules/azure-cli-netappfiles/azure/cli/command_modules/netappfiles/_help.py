# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long


helps['netappfiles'] = """
    type: group
    short-summary: Manage Azure NetApp Files (ANF) Resources.
"""

# account

helps['netappfiles account'] = """
    type: group
    short-summary: Manage Azure NetApp Files (ANF) Account Resources.
"""

helps['netappfiles account create'] = """
    type: command
    short-summary: Create a new Azure NetApp Files (ANF) account. Note that active directory can only be applied to an existing account (using set/update).
    parameters:
        - name: --account-name -a -n
          type: string
          short-summary: The name of the ANF account
        - name: --tags
          type: string
          short-summary: A list of space separated tags to apply to the account
    examples:
        - name: Create an ANF account
          text: >
            az netappfiles account create -g group --account-name name -l location
"""

helps['netappfiles account set'] = """
    type: command
    short-summary: Sets the tags or the active directory details for a specified ANF account. Sets the active directory property to exactly what is provided. If none is provided then the active directory is removed, i.e. provide empty [].
    parameters:
        - name: --account-name -a -n
          type: string
          short-summary: The name of the ANF account
        - name: --tags
          type: string
          short-summary: A list of space separated tags to apply to the account
        - name: --active-directories
          type: string
          short-summary: An array of active directory (AD) settings in json format. Limitation one AD/subscription. Consists of the fields username (Username of Active Directory domain administrator), password (Plain text password of Active Directory domain administrator), domain (Name of the Active Directory domain), dns (Comma separated list of DNS server IP addresses for the Active Directory domain), smb_server_name (NetBIOS name of the SMB server. This name will be registered as a computer account in the AD and used to mount volumes. Must be 10 characters or less), organizational_unit (The Organizational Unit (OU) within the Windows Active Directory)
    examples:
        - name: Update the tags and active directory of an ANF account
          text: >
            az netappfiles account set -g group --account-name name --tags 'key[=value] key[=value]' --active-directories '[{"username": "aduser", "password": "aduser", "smbservername": "SMBSERVER", "dns": "1.2.3.4", "domain": "westcentralus"}]' -l westus2
        - name: Remove the active directory from the ANF account
          text: >
            az netappfiles account set -g group --account-name name --active-directories '[]' -l westus2
"""

helps['netappfiles account update'] = """
    type: command
    short-summary: Set/modify the tags or the active directory details for a specified ANF account. Active directory settings are appended only - if none are present no change is made otherwise the active directory is replaced with that provided.
    parameters:
        - name: --account-name -a -n
          type: string
          short-summary: The name of the ANF account
        - name: --tags
          type: string
          short-summary: A list of space separated tags to apply to the account
        - name: --active-directories
          type: string
          short-summary: An array of active directory (AD) settings in json format. Limitation one AD/subscription. Consists of the fields username (Username of Active Directory domain administrator), password (Plain text password of Active Directory domain administrator), domain (Name of the Active Directory domain), dns (Comma separated list of DNS server IP addresses for the Active Directory domain), smb_server_name (NetBIOS name of the SMB server. This name will be registered as a computer account in the AD and used to mount volumes. Must be 10 characters or less), organizational_unit (The Organizational Unit (OU) within the Windows Active Directory)
    examples:
        - name: Update the tags and active directory of an ANF account
          text: >
            az netappfiles account update -g group --account-name name --tags 'key[=value] key[=value]' --active-directories '[{"username": "aduser", "password": "aduser", "smbservername": "SMBSERVER", "dns": "1.2.3.4", "domain": "westcentralus"}]' -l westus2
"""

helps['netappfiles account delete'] = """
    type: command
    short-summary: Delete the specified ANF account.
    parameters:
        - name: --account-name -a -n
          type: string
          short-summary: The name of the ANF account
    examples:
        - name: Delete an ANF account
          text: >
            az netappfiles account delete -g group --account-name name
"""

helps['netappfiles account list'] = """
    type: command
    short-summary: List ANF accounts.
    examples:
        - name: List ANF accounts within a resource group
          text: >
            az netappfiles account list -g group
"""

helps['netappfiles account show'] = """
    type: command
    short-summary: Get the specified ANF account.
    parameters:
        - name: --account-name -a -n
          type: string
          short-summary: The name of the ANF account
    examples:
        - name: Get an ANF account
          text: >
            az netappfiles account show -g group --account-name name
"""

# pools

helps['netappfiles pool'] = """
    type: group
    short-summary: Manage Azure NetApp Files (ANF) Pool Resources.
"""

helps['netappfiles pool create'] = """
    type: command
    short-summary: Create a new Azure NetApp Files (ANF) pool.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -n -p
          type: string
          short-summary: The name of the ANF pool
        - name: --size
          type: integer
          short-summary: The size for the ANF pool. Must be in 4 tebibytes increments, expressed in bytes
        - name: --service-level
          type: string
          short-summary: The service level for the ANF pool ["Standard"|"Premium"|"Extreme"]
        - name: --tags
          type: string
          short-summary: A list of space separated tags to apply to the pool
    examples:
        - name: Create an ANF pool
          text: >
            az netappfiles pool create -g group --account-name aname --pool-name pname -l location --size 4398046511104 --service-level "Premium"
"""

helps['netappfiles pool update'] = """
    type: command
    short-summary: Update the tags of the specified ANF pool.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -n -p
          type: string
          short-summary: The name of the ANF pool
        - name: --size
          type: integer
          short-summary: The size for the ANF pool. Must be in 4 tebibytes increments, expressed in bytes
        - name: --service-level
          type: string
          short-summary: The service level for the ANF pool ["Standard"|"Premium"|"Extreme"]
        - name: --tags
          type: string
          short-summary: A list of space separated tags to apply to the pool
    examples:
        - name: Update specific values for an ANF pool
          text: >
            az netappfiles pool update -g group --account-name aname --pool-name pname --service-level "Extreme" --tags 'key[=value] key[=value]'
"""

helps['netappfiles pool delete'] = """
    type: command
    short-summary: Delete the specified ANF pool.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -n -p
          type: string
          short-summary: The name of the ANF pool
    examples:
        - name: Delete an ANF pool
          text: >
            az netappfiles pool delete -g group --account-name aname --pool-name pname
"""

helps['netappfiles pool list'] = """
    type: command
    short-summary: L:ist the ANF pools for the specified account.
    parameters:
        - name: --account-name -a -n
          type: string
          short-summary: The name of the ANF account
    examples:
        - name: List the pools for the ANF account
          text: >
            az netappfiles pool list -g group --account-name name
"""

helps['netappfiles pool show'] = """
    type: command
    short-summary: Get the specified ANF pool.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -n -p
          type: string
          short-summary: The name of the ANF pool
    examples:
        - name: Get an ANF pool
          text: >
            az netappfiles pool show -g group --account-name aname --pool-name pname
"""

# volumes

helps['netappfiles volume'] = """
    type: group
    short-summary: Manage Azure NetApp Files (ANF) Volume Resources.
"""

helps['netappfiles volume create'] = """
    type: command
    short-summary: Create a new Azure NetApp Files (ANF) volume.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -n -v
          type: string
          short-summary: The name of the ANF volume
        - name: --service-level
          type: string
          short-summary: The service level ["Standard"|"Premium"|"Extreme"]
        - name: --usage-threshold
          type: int
          short-summary: The maximum storage quota allowed for a file system in bytes. Min 100 GiB, max 100TiB"
        - name: --creation-token
          type: string
          short-summary: A unique file path identifier, from 1 to 80 characters
        - name: --subnet-id
          type: string
          short-summary: The subnet identifier
        - name: --tags
          type: string
          short-summary:  A list of space separated tags to apply to the volume
        - name: --export-policy
          type: string
          short-summary:  A json list of the parameters for export policy containing rule_index (Order index), unix_read_only (Read only access), unix_read_write (Read and write access), cifs (Allows CIFS protocol), nfsv3 (Allows NFSv3 protocol), nfsv4 (Allows NFSv4 protocol) and allowedClients (Client ingress specification as comma separated string with IPv4 CIDRs, IPv4 host addresses and host names)
    examples:
        - name: Create an ANF volume
          text: >
            az netappfiles volume create -g group --account-name aname --pool-name pname --volume-name vname -l location --service-level "Premium" --usage-threshold 107374182400 --creation-token "unique-token" --subnet-id "/subscriptions/mysubsid/resourceGroups/myrg/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/default" --export-policy '[{"allowed_clients":"0.0.0.0/0", "rule_index": "1", "unix_read_only": "true", "unix_read_write": "false", "cifs": "false", "nfsv3": "true", "nfsv3": "true", "nfsv4": "false"}]'
"""

helps['netappfiles volume update'] = """
    type: command
    short-summary: Update the specified ANF volume with the values provided. Unspecified values will remain unchanged.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -n -v
          type: string
          short-summary: The name of the ANF volume
        - name: --service-level
          type: string
          short-summary: The service level ["Standard"|"Premium"|"Extreme"]
        - name: --usage-threshold
          type: int
          short-summary: The maximum storage quota allowed for a file system in bytes. Min 100 GiB, max 100TiB"
        - name: --tags
          type: string
          short-summary:  A list of space separated tags to apply to the volume
        - name: --export-policy
          type: string
          short-summary:  A json list of the parameters for export policy containing rule_index (Order index), unix_read_only (Read only access), unix_read_write (Read and write access), cifs (Allows CIFS protocol), nfsv3 (Allows NFSv3 protocol), nfsv4 (Allows NFSv4 protocol) and allowedClients (Client ingress specification as comma separated string with IPv4 CIDRs, IPv4 host addresses and host names)
    examples:
        - name: Create an ANF volume
          text: >
            az netappfiles volume update -g group --account-name aname --pool-name pname --volume-name vname --service-level level --usage-threshold 107374182400 --tags 'key[=value] key[=value]' --export-policy '[{"allowed_clients":"1.2.3.0/24", "rule_index": "1", "unix_read_only": "true", "unix_read_write": "false", "cifs": "false", "nfsv3": "true", "nfsv3": "true", "nfsv4": "false"}, {"allowed_clients":"1.2.4.0/24", "rule_index": "2", "unix_read_only": "true", "unix_read_write": "false", "cifs": "false", "nfsv3": "true", "nfsv3": "true", "nfsv4": "false"}]'
"""

helps['netappfiles volume delete'] = """
    type: command
    short-summary: Delete the specified ANF volume.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -n -v
          type: string
          short-summary: The name of the ANF volume
    examples:
        - name: Delete an ANF volume
          text: >
            az netappfiles volume delete -g group --account-name aname --pool-name pname --volume-name vname
"""

helps['netappfiles volume list'] = """
    type: command
    short-summary: List the ANF Pools for the specified account.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -n -p
          type: string
          short-summary: The name of the ANF pool
    examples:
        - name: List the ANF volumes of the pool
          text: >
            az netappfiles volume list -g group --account-name aname --pool-name pname
"""

helps['netappfiles volume show'] = """
    type: command
    short-summary: Get the specified ANF volume.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -n -v
          type: string
          short-summary: The name of the ANF pool
    examples:
        - name: Returns the properties of the given ANF volume
          text: >
            az netappfiles volume show -g group --account-name aname --pool-name pname --volume-name vname
"""

# mounttargets

helps['netappfiles mount-target'] = """
    type: group
    short-summary: Manage Azure NetApp Files (ANF) Mount Target Resources.
"""

helps['netappfiles mount-target list'] = """
    type: command
    short-summary: List the mount targets of an ANF volume.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -v
          type: string
          short-summary: The name of the ANF pool
    examples:
        - name: list the mount targets of an ANF volume
          text: >
            az netappfiles mount-target list -g group --account-name aname --pool-name pname --volume-name vname
"""

# snapshots

helps['netappfiles snapshot'] = """
    type: group
    short-summary: Manage Azure NetApp Files (ANF) Snapshot Resources.
"""

helps['netappfiles snapshot create'] = """
    type: command
    short-summary: Create a new Azure NetApp Files (ANF) snapshot.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -v
          type: string
          short-summary: The name of the ANF volume
        - name: --snapshot-name -n -s
          type: string
          short-summary: The name of the ANF snapshot
        - name: --file-system-id
          type: string
          short-summary: The uuid of the volume
    examples:
        - name: Create an ANF snapshot
          text: >
            az netappfiles snapshot create -g group --account-name account-name --pool-name pname --volume-name vname --snapshot-name sname -l location --file-system-id volume-uuid
"""

helps['netappfiles snapshot delete'] = """
    type: command
    short-summary: Delete the specified ANF snapshot.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -v
          type: string
          short-summary: The name of the ANF volume
        - name: --snapshot-name -n -s
          type: string
          short-summary: The name of the ANF snapshot
    examples:
        - name: Delete an ANF snapshot
          text: >
            az netappfiles snapshot delete -g group --account-name aname --pool-name pname --volume-name vname --snapshot-name sname
"""

helps['netappfiles snapshot list'] = """
    type: command
    short-summary: List the snapshots of an ANF volume.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -n -v
          type: string
          short-summary: The name of the ANF volume
    examples:
        - name: list the snapshots of an ANF volume
          text: >
            az netappfiles snapshot list -g group --account-name aname --pool-name pname --volume-name vname
"""

helps['netappfiles snapshot show'] = """
    type: command
    short-summary: Get the specified ANF snapshot.
    parameters:
        - name: --account-name -a
          type: string
          short-summary: The name of the ANF account
        - name: --pool-name -p
          type: string
          short-summary: The name of the ANF pool
        - name: --volume-name -v
          type: string
          short-summary: The name of the ANF volume
        - name: --snapshot-name -n -s
          type: string
          short-summary: The name of the ANF snapshot
    examples:
        - name: Return the specified ANF snapshot
          text: >
            az netappfiles snapshot show -g group --account-name aname --pool-name pname --volume-name vname --snapshot-name sname
"""
