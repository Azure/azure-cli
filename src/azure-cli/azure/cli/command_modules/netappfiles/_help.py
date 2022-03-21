# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['netappfiles'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Resources.
"""

helps['netappfiles account'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Account Resources.
"""

helps['netappfiles account ad'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Account active directories.
"""

helps['netappfiles account ad add'] = """
type: command
short-summary: Add an active directory to the account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
  - name: --username
    short-summary: Username of Active Directory domain administrator
  - name: --password
    short-summary: Plain text password of Active Directory domain administrator
  - name: --domain
    short-summary: Name of the Active Directory domain
  - name: --dns
    short-summary: Comma separated list of DNS server IP addresses for the Active Directory domain
  - name: --smb-server-name
    short-summary: NetBIOS name of the SMB server. This name will be registered as a computer account in the AD and used to mount volumes. Must be 10 characters or less
  - name: --organizational-unit
    short-summary: The Organizational Unit (OU) within the Windows Active Directory
  - name: --kdc-ip
    short-summary: kdc server IP addresses for the active directory machine. This optional parameter is used only while creating kerberos volume
  - name: --ad-name
    short-summary: Name of the active directory machine. This optional parameter is used only while creating kerberos volume
  - name: --server-root-ca-cert
    short-summary: When LDAP over SSL/TLS is enabled, the LDAP client is required to have base64 encoded Active Directory Certificate Service's self-signed root CA certificate, this optional parameter is used only for dual protocol with LDAP user-mapping volumes.
  - name: --backup-operators
    short-summary: Users to be added to the Built-in Backup Operator active directory group. A space separated string of unique usernames without domain specifier
  - name: --aes-encryption
    short-summary: If enabled, AES encryption will be enabled for SMB communication
  - name: --ldap-signing
    short-summary: Specifies whether or not the LDAP traffic needs to be signed
  - name: --security-operators
    short-summary: Domain Users in the Active directory to be given SeSecurityPrivilege privilege (Needed for SMB Continuously available shares for SQL). A space seperated list of unique usernames without domain specifier
  - name: --ldap-over-tls
    short-summary: Specifies whether or not the LDAP traffic needs to be secured via TLS
  - name: --allow-local-ldap-users
    short-summary: If enabled, NFS client local users can also (in addition to LDAP users) access the NFS volumes
  - name: --administrators
    short-summary: Users to be added to the Built-in Administrators active directory group. A space seperated string of unique usernames without domain specifier.
  - name: --encrypt-dc-conn
    short-summary: If enabled, Traffic between the SMB server to Domain Controller (DC) will be encrypted
  - name: --user-dn
    short-summary: This specifies the user DN, which overrides the base DN for user lookups
  - name: --group-dn
    short-summary: This specifies the group DN, which overrides the base DN for group lookups
  - name: --group-filter
    short-summary: This specifies the custom LDAP search filter to be used when looking up group membership from LDAP server
  - name: --user-dn
    short-summary: This specifies the user DN, which overrides the base DN for user lookups.
  - name: group-dn
    short-summary: This specifies the group DN, which overrides the base DN for group lookups.
  - name: group-filter
    short-summary: This specifies the custom LDAP search filter to be used when looking up group membership from LDAP server.
examples:
  - name: Add an active directory to the account
    text: >
        az netappfiles account ad add -g mygroup --name myname --username aduser --password aduser --smb-server-name SMBSERVER --dns 1.2.3.4 --domain westcentralus
"""

helps['netappfiles account ad update'] = """
type: command
short-summary: Updates an active directory to the account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
  - name: --active-directory-id
    short-summary: The id of the Active Directory
  - name: --username
    short-summary: Username of Active Directory domain administrator
  - name: --password
    short-summary: Plain text password of Active Directory domain administrator
  - name: --domain
    short-summary: Name of the Active Directory domain
  - name: --dns
    short-summary: Comma separated list of DNS server IP addresses for the Active Directory domain
  - name: --smb-server-name
    short-summary: NetBIOS name of the SMB server. This name will be registered as a computer account in the AD and used to mount volumes. Must be 10 characters or less
  - name: --organizational-unit
    short-summary: The Organizational Unit (OU) within the Windows Active Directory
  - name: --kdc-ip
    short-summary: kdc server IP addresses for the active directory machine. This optional parameter is used only while creating kerberos volume
  - name: --ad-name
    short-summary: Name of the active directory machine. This optional parameter is used only while creating kerberos volume
  - name: --server-root-ca-cert
    short-summary: When LDAP over SSL/TLS is enabled, the LDAP client is required to have base64 encoded Active Directory Certificate Service's self-signed root CA certificate, this optional parameter is used only for dual protocol with LDAP user-mapping volumes.
  - name: --backup-operators
    short-summary: Users to be added to the Built-in Backup Operator active directory group. A space seperated list of unique usernames without domain specifier
  - name: --aes-encryption
    short-summary: If enabled, AES encryption will be enabled for SMB communication
  - name: --ldap-signing
    short-summary: Specifies whether or not the LDAP traffic needs to be signed
  - name: --security-operators
    short-summary: Domain Users in the Active directory to be given SeSecurityPrivilege privilege (Needed for SMB Continuously available shares for SQL). A space seperated list of unique usernames without domain specifier
  - name: --ldap-over-tls
    short-summary: Specifies whether or not the LDAP traffic needs to be secured via TLS
  - name: --allow-local-ldap-users
    short-summary: If enabled, NFS client local users can also (in addition to LDAP users) access the NFS volumes
  - name: --administrators
    short-summary: Users to be added to the Built-in Administrators active directory group. A space seperated list of unique usernames without domain specifier.
  - name: --encrypt-dc-conn
    short-summary: If enabled, Traffic between the SMB server to Domain Controller (DC) will be encrypted
  - name: --user-dn
    short-summary: This specifies the user DN, which overrides the base DN for user lookups.
  - name: --group-dn
    short-summary: This specifies the group DN, which overrides the base DN for group lookups.
  - name: --group-filter
    short-summary: This specifies the custom LDAP search filter to be used when looking up group membership from LDAP server.
examples:
  - name: Update an active directory on the account
    text: >
        az netappfiles account ad update -g mygroup --name myname --active-directory-id 123 --username aduser --password aduser --smb-server-name SMBSERVER --dns 1.2.3.4 --domain westcentralus
"""

helps['netappfiles account ad list'] = """
type: command
short-summary: List the active directories of an account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
examples:
  - name: Add an active directory to the account
    text: >
        az netappfiles account ad list -g mygroup --name myname
"""

helps['netappfiles account ad remove'] = """
type: command
short-summary: Remove an active directory from the account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
  - name: --active-directory
    short-summary: The id of the active directory
examples:
  - name: Remove an active directory from the account
    text: >
        az netappfiles account ad remove -g mygroup --name myname --active-directory 13641da9-c0e9-4b97-84fc-4f8014a93848
"""

helps['netappfiles account create'] = """
type: command
short-summary: Create a new Azure NetApp Files (ANF) account. Note that active directories are added using the subgroup commands.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
  - name: --encryption
    short-summary: Encryption settings
examples:
  - name: Create an ANF account
    text: >
        az netappfiles account create -g mygroup --name myname -l location --tags testtag1=mytag1 testtag3=mytagg
"""

helps['netappfiles account delete'] = """
type: command
short-summary: Delete the specified ANF account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
examples:
  - name: Delete an ANF account
    text: >
        az netappfiles account delete -g mygroup --name myname
"""

helps['netappfiles account list'] = """
type: command
short-summary: List ANF accounts by subscription or by resource group name.
examples:
  - name: List ANF accounts within a resource group
    text: >
        az netappfiles account list -g mygroup
"""

helps['netappfiles account show'] = """
type: command
short-summary: Get the specified ANF account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
examples:
  - name: Get an ANF account
    text: >
        az netappfiles account show -g mygroup --name myname
"""

helps['netappfiles account update'] = """
type: command
short-summary: Set/modify the tags for a specified ANF account.
parameters:
  - name: --account-name --name -a -n
    short-summary: The name of the ANF account
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
  - name: --encryption
    short-summary: Encryption settings
examples:
  - name: Update the tags of an ANF account
    text: >
        az netappfiles account update -g mygroup --name myname --tags testtag2=mytagb
"""

helps['netappfiles account backup'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Account Backup Resources.
"""

helps['netappfiles account backup list'] = """
type: command
short-summary: Get list of all Azure NetApp Files (ANF) Account Backups.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
examples:
  - name: Get a list of all ANF account backup
    text: >
        az netappfiles account backup list -g mygroup --account-name myaccountname
"""

helps['netappfiles account backup show'] = """
type: command
short-summary: Get Backup for a Netapp Files (ANF) Account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --backup-name
    short-summary: The name of the backup
examples:
  - name: Get a list of all ANF account backup
    text: >
        az netappfiles account backup show -g mygroup --account-name myaccountname --backup-name mybackupname
"""

helps['netappfiles account backup delete'] = """
type: command
short-summary: Delete Backup for a Netapp Files (ANF) Account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --backup-name
    short-summary: The name of the backup
examples:
  - name: Get a list of all ANF account backup
    text: >
        az netappfiles account backup delete -g mygroup --account-name myaccountname --backup-name mybackupname
"""


helps['netappfiles account backup-policy'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Backup Policy Resources.
"""

helps['netappfiles account backup-policy create'] = """
type: command
short-summary: Create a new Azure NetApp Files (ANF) backup policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --backup-policy-name -b
    short-summary: The name of the ANF backup policy
  - name: --location -l
    short-summary: The location of the backup
  - name: --daily-backups -d
    short-summary: Daily backups count to keep
  - name: --weekly-backups -w
    short-summary: Weekly backups count to keep
  - name: --monthly-backups -m
    short-summary: Monthly backups count to keep
  - name: --enabled -e
    short-summary: The property to decide policy is enabled or not
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
examples:
  - name: Create an ANF backup policy
    text: >
        az netappfiles account backup-policy create -g mygroup --account-name myaccountname --backup-policy-name mybackuppolicyname -l westus2 --daily-backups 1 --enabled true
"""

helps['netappfiles account backup-policy delete'] = """
type: command
short-summary: Delete the specified ANF backup policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --backup-policy-name -b
    short-summary: The name of the ANF backup policy
examples:
  - name: Delete an ANF backup policy
    text: >
        az netappfiles account backup-policy delete -g mygroup --account-name myaccname --backup-policy-name mybackuppolicyname
"""

helps['netappfiles account backup-policy list'] = """
type: command
short-summary: List the ANF backup policy for the specified account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
examples:
  - name: List the backup policy for the ANF account
    text: >
        az netappfiles account backup-policy list -g mygroup --account-name myname
"""

helps['netappfiles account backup-policy show'] = """
type: command
short-summary: Get the specified ANF backup policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --backup-policy-name -b
    short-summary: The name of the ANF backup policy
examples:
  - name: Get an ANF backup policy
    text: >
        az netappfiles account backup-policy show -g mygroup --account-name myaccname --backup-policy-name mybackuppolicyname
"""

helps['netappfiles account backup-policy update'] = """
type: command
short-summary: Update the specified ANF backup policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --backup-policy-name -b
    short-summary: The name of the ANF backup policy
  - name: --daily-backups -d
    short-summary: Daily backups count to keep
  - name: --weekly-backups -w
    short-summary: Weekly backups count to keep
  - name: --monthly-backups -m
    short-summary: Monthly backups count to keep
  - name: --enabled -e
    short-summary: The property to decide policy is enabled or not
examples:
  - name: Update specific values for an ANF backup policy
    text: >
        az netappfiles account backup-policy update -g mygroup --account-name myaccountname --backup-policy-name mybackuppolicyname -l westus2 --daily-backups 1 --enabled false
"""


helps['netappfiles pool'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Pool Resources.
"""

helps['netappfiles pool create'] = """
type: command
short-summary: Create a new Azure NetApp Files (ANF) pool.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --name --pool-name -n -p
    short-summary: The name of the ANF pool
  - name: --size
    short-summary: The size for the ANF pool. Must be an integer number of tebibytes in multiples of 4
  - name: --service-level
    short-summary: The service level for the ANF pool
  - name: --qos-type
    short-summary: The qos type of the ANF pool
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
  - name: --cool-access
    short-summary: If enabled (true) the pool can contain cool Access enabled volumes.
  - name: --encryption-type
    short-summary: Encryption type of the capacity pool, set encryption type for data at rest for this pool and all volumes in it. This value can only be set when creating new pool. Possible values are Single or Double. Default value is Single.
examples:
  - name: Create an ANF pool
    text: >
        az netappfiles pool create -g mygroup --account-name myaccountname --name mypoolname -l westus2 --size 8 --service-level premium
"""

helps['netappfiles pool delete'] = """
type: command
short-summary: Delete the specified ANF pool.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --name --pool-name -n -p
    short-summary: The name of the ANF pool
examples:
  - name: Delete an ANF pool
    text: >
        az netappfiles pool delete -g mygroup --account-name myaccname --name mypoolname
"""

helps['netappfiles pool list'] = """
type: command
short-summary: L:ist the ANF pools for the specified account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
examples:
  - name: List the pools for the ANF account
    text: >
        az netappfiles pool list -g mygroup --account-name myname
"""

helps['netappfiles pool show'] = """
type: command
short-summary: Get the specified ANF pool.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --name --pool-name -n -p
    short-summary: The name of the ANF pool
examples:
  - name: Get an ANF pool
    text: >
        az netappfiles pool show -g mygroup --account-name myaccname --name mypoolname
"""

helps['netappfiles pool update'] = """
type: command
short-summary: Update the tags of the specified ANF pool.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --name --pool-name -n -p
    short-summary: The name of the ANF pool
  - name: --size
    short-summary: The size for the ANF pool. Must be an integer number of tebibytes in multiples of 4
  - name: --qos-type
    short-summary: The qos type of the ANF pool
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
examples:
  - name: Update specific values for an ANF pool
    text: >
        az netappfiles pool update -g mygroup --account-name myaccname --name mypoolname --tags mytag1=abcd mytag2=efgh
"""

helps['netappfiles snapshot'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Snapshot Resources.
"""

helps['netappfiles snapshot create'] = """
type: command
short-summary: Create a new Azure NetApp Files (ANF) snapshot.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --name --snapshot-name -n -s
    short-summary: The name of the ANF snapshot
examples:
  - name: Create an ANF snapshot
    text: >
        az netappfiles snapshot create -g mygroup --account-name myaccname --pool-name mypoolname --volume-name myvolname --name mysnapname -l eastus
"""

helps['netappfiles snapshot delete'] = """
type: command
short-summary: Delete the specified ANF snapshot.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --name --snapshot-name -n -s
    short-summary: The name of the ANF snapshot
examples:
  - name: Delete an ANF snapshot
    text: >
        az netappfiles snapshot delete -g mygroup --account-name myaccname --pool-name mypoolname --volume-name myvolname --name mysnapname
"""

helps['netappfiles snapshot list'] = """
type: command
short-summary: List the snapshots of an ANF volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
examples:
  - name: list the snapshots of an ANF volume
    text: >
        az netappfiles snapshot list -g mygroup --account-name myaccname --pool-name mypoolname --volume-name myvolname
"""

helps['netappfiles snapshot show'] = """
type: command
short-summary: Get the specified ANF snapshot.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --name --snapshot-name -n -s
    short-summary: The name of the ANF snapshot
examples:
  - name: Return the specified ANF snapshot
    text: >
        az netappfiles snapshot show -g mygroup --account-name myaccname --pool-name mypoolname --volume-name myvolname --name mysnapname
"""

helps['netappfiles snapshot restore-files'] = """
type: command
short-summary: Restore specified files from the specified snapshot to the active filesystem.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --name --snapshot-name -n -s
    short-summary: The name of the ANF snapshot
  - name: --file-paths
    short-summary: Required. A space seperated string of filed to be restored
  - name: --destination-path
    short-summary: Destination folder where the files will be restored
examples:
  - name: Restore files from snapshot
    text: >
        az netappfiles snapshot restore-files -g mygroup --account-name myaccname --pool-name mypoolname --volume-name myvolname --name mysnapname --file-paths myfilepaths
"""

helps['netappfiles volume'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Volume Resources.
"""

helps['netappfiles volume create'] = """
type: command
short-summary: Create a new Azure NetApp Files (ANF) volume. Export policies are applied with the subgroup commands but note that volumes are always created with a default export policy
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --service-level
    short-summary: The service level
  - name: --usage-threshold
    short-summary: The maximum storage quota allowed for a file system as integer number of GiB. Min 100 GiB, max 100TiB"
  - name: --file-path
    short-summary: A 1-80 character long alphanumeric string value that identifies a unique file share or mount point in the target delegate subnet
  - name: --vnet
    short-summary: The ARM Id or name of the vnet for the volume
  - name: --subnet
    short-summary: The ARM Id or name of the delegated subnet for the vnet. If omitted 'default' will be used
  - name: --protocol-types
    short-summary: Space seperated list of protocols that the volume can use, available protocols are "NFSv4.1", "NFSv3", "CIFS"
  - name: --volume-type
    short-summary: Whether the volume should be a data protection volume ("DataProtection"), empty if this is not a data protection volume
  - name: --endpoint-type
    short-summary: Whether the volume is source ("src") or destination ("dst")
  - name: --remote-volume-resource-id
    short-summary: The volume id of the remote volume of the replication (the destination for "src" volume endpoints and the source for "dst" endpoints)
  - name: --replication-schedule
    short-summary: The replication schedule, e.g. "_10minutely, hourly, daily, weekly, monthly"
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
  - name: --snapshot-id
    short-summary: Create a volume created from this snapshot. UUID v4 or resource identifier used to identify the Snapshot. example snapshot-id "9760acf5-4638-11e7-9bdb-020073ca3333"
  - name: --snapshot-policy-id
    short-summary: Snapshot Policy ResourceId
  - name: --backup-policy-id
    short-summary: Backup Policy Resource ID
  - name: --backup-enabled
    short-summary: Backup Enabled
  - name: --backup-id
    short-summary: Backup ID. UUID v4 or resource identifier used to identify the Backup
  - name: --policy-enforced
    short-summary: Policy Enforced
  - name: --vault-id
    short-summary: Vault Resource ID
  - name: --kerberos-enabled
    short-summary: Describe if a volume is KerberosEnabled
  - name: --throughput-mibps
    short-summary: Maximum throughput in Mibps that can be achieved by this volume
  - name: --snapshot-dir-visible
    short-summary: If enabled (true) the volume will contain a read-only .snapshot directory which provides access to each of the volume's snapshots (default to true).
  - name: --security-style
    short-summary: The security style of volume
  - name: --kerberos5-r
    short-summary: Kerberos5 Read only access
  - name: --kerberos5-rw
    short-summary: Kerberos5 Read and write access
  - name: --kerberos5i-r
    short-summary: Kerberos5i Read only access
  - name: --kerberos5i-rw
    short-summary: Kerberos5i Read and write access
  - name: --kerberos5p-r
    short-summary: Kerberos5p Read only access
  - name: --kerberos5p-rw
    short-summary: Kerberos5p Read and write access
  - name: --has-root-access
    short-summary: Has root access to volume
  - name: --smb-encryption
    short-summary: Enables encryption for in-flight smb3 data. Only applicable for SMB/DualProtocol volume. To be used with swagger version 2020-08-01 or later. Default value is False
  - name: --smb-continuously-avl
    short-summary: Enables continuously available share property for smb volume. Only applicable for SMB volume. Default value is False
  - name: --encryption-key-source
    short-summary: Encryption Key Source
  - name: --allowed-clients
    short-summary: Client ingress specification as comma separated string with IPv4 CIDRs, IPv4 host addresses and host names
  - name: --cifs
    short-summary: Allows NFSv3 protocol. Enable only for NFSv3 type volumes
  - name: --rule-index
    short-summary: Order index
  - name: --unix-read-only
    short-summary: Read only access
  - name: --unix-read-write
    short-summary: Read and write access
  - name: --ldap-enabled
    short-summary: Specifies whether LDAP is enabled or not for a given NFS volume
  - name: --chown-mode
    short-summary: This parameter specifies who is authorized to change the ownership of a file. restricted - Only root user can change the ownership of the file. unrestricted - Non-root users can change ownership of files that they own. Possible values include- Restricted, Unrestricted. Default value- Restricted.
  - name: --cool-access
    short-summary: Specifies whether Cool Access(tiering) is enabled for the volume.
  - name: --coolness-period
    short-summary: Specifies the number of days after which data that is not accessed by clients will be tiered.
  - name: --unix-permissions
    short-summary: UNIX permissions for NFS volume accepted in octal 4 digit format. First digit selects the set user ID(4), set group ID (2) and sticky (1) attributes. Second digit selects permission for the owner of the file- read (4), write (2) and execute (1). Third selects permissions for other users in the same group. the fourth for other users not in the group. 0755 - gives read/write/execute permissions to owner and read/execute to group and other users.
  - name: --is-def-quota-enabled
    short-summary: Specifies if default quota is enabled for the volume.
  - name: --default-user-quota
    short-summary: Default user quota for volume in KiBs. If isDefaultQuotaEnabled is set, the minimum value of 4 KiBs applies.
  - name: --default-group-quota
    short-summary: Default group quota for volume in KiBs. If isDefaultQuotaEnabled is set, the minimum value of 4 KiBs applies.
  - name: --avs-data-store
    short-summary: Specifies whether the volume is enabled for Azure VMware Solution (AVS) datastore purpose. Possible values are Enabled and Disabled. Default value is Disabled.
  - name: --network-features
    short-summary: Basic network, or Standard features available to the volume. Possible values are Basic and Standard. Default value is Basic.
  - name: --enable-subvolumes
    short-summary:  Flag indicating whether subvolume operations are enabled on the volume. Possible values are Enabled and Disabled. Default value is Disabled
examples:
  - name: Create an ANF volume
    text: >
        az netappfiles volume create -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname -l westus2 --service-level premium --usage-threshold 100 --file-path "unique-file-path" --vnet myvnet --subnet mysubnet --protocol-types NFSv3 NFSv4.1
"""

helps['netappfiles volume delete'] = """
type: command
short-summary: Delete the specified ANF volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --force-delete
    short-summary: An option to force delete the volume. Will cleanup resources connected to the particular volume.
examples:
  - name: Delete an ANF volume
    text: >
        az netappfiles volume delete -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname
"""

helps['netappfiles volume revert'] = """
type: command
short-summary: Revert a volume to one of its snapshots.
long-summary: Revert a volume to the snapshot specified in the body.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --snapshot-id -s
    short-summary: SnapshotId of the snapshot. UUID v4 used to identify the Snapshot, example "9760acf5-4638-11e7-9bdb-020073ca3333"
examples:
  - name: Revert a volume to one of its snapshots.
    text: >
        az netappfiles volume revert -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --snapshot-id 9760acf5-4638-11e7-9bdb-020073ca3333
"""

helps['netappfiles volume replication'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Volume replication operations.
"""

helps['netappfiles volume replication approve'] = """
type: command
short-summary: Authorize a volume as a replication destination for a specified source.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the replication source volume
  - name: --remote-volume-resource-id -d
    short-summary: The resource id of the destination replication volume
examples:
  - name: Authorize the volume as the replication destination for the source
    text: >
        az netappfiles volume replication approve -g mygroup --account-name myaccname --pool-name mypoolname --name mysourcevolname --remote-volume-resource-id /subscriptions/69a75bda-882e-44d5-8431-63421204131c/resourceGroups/mygroup1/providers/Microsoft.NetApp/netAppAccounts/myaccount1/capacityPools/mypool1/volumes/mydestinationvolume
"""

helps['netappfiles volume replication suspend'] = """
type: command
short-summary: Suspend/break a volume replication for the specified destination volume. The replication process is suspended until resumed or deleted.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the replication destination volume
  - name: --force --force-break-replication -f
    short-summary: Force break the replication
examples:
  - name: Suspend the replication process
    text: >
        az netappfiles volume replication suspend -g mygroup --account-name myaccname --pool-name mypoolname --name mydestinationvolname
"""

helps['netappfiles volume replication resume'] = """
type: command
short-summary: Resync a volume replication for the specified destination volume. The replication process is resumed from source to destination.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the replication destination volume
examples:
  - name: Resume the replication process
    text: >
        az netappfiles volume replication resume -g mygroup --account-name myaccname --pool-name mypoolname --name mydestinationvolname
"""

helps['netappfiles volume replication remove'] = """
type: command
short-summary: Delete a volume replication for the specified destination volume. The data replication objects of source and destination volumes will be removed.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the replication destination volume
examples:
  - name: Delete the replication objects of the paired volumes
    text: >
        az netappfiles volume replication remove -g mygroup --account-name myaccname --pool-name mypoolname --name mydestinationvolname
"""

helps['netappfiles volume replication re-initialize'] = """
type: command
short-summary: Re-initialise a volume replication for the specified destination volume. The replication process is resumed from source to destination.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the replication destination volume
examples:
  - name: Re-initialises the replication process
    text: >
        az netappfiles volume replication re-initialize -g mygroup --account-name myaccname --pool-name mypoolname --name mydestinationvolname
"""

helps['netappfiles volume replication status'] = """
type: command
short-summary: Get the replication status for the specified replication volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the replication destination volume
examples:
  - name: Get the replication status for the volume. Returns whether the replication is healthy, the replication schedule and the mirror state (whether replication is suspened/broken or synced/mirrored)
    text: >
        az netappfiles volume replication status -g mygroup --account-name myaccname --pool-name mypoolname --name mydestinationvolname
"""

helps['netappfiles volume export-policy'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Volume export policies.
"""

helps['netappfiles volume export-policy add'] = """
type: command
short-summary: Add a new rule to the export policy for a volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --rule-index
    short-summary: Order index. No number can be repeated. Max 6 rules.
  - name: --unix-read-only
    short-summary: Indication of read only access
  - name: --unix-read-write
    short-summary: Indication of read and write access
  - name: --cifs
    short-summary: Indication that CIFS protocol is allowed
  - name: --nfsv3
    short-summary: Indication that NFSv3 protocol is allowed
  - name: --nfsv41
    short-summary: Indication that NFSv4.1 protocol is allowed
  - name: --allowed-clients
    short-summary: Client ingress specification as comma separated string with IPv4 CIDRs, IPv4 host addresses and host names)
  - name: --kerberos5-r
    short-summary: Kerberos5 Read only access
  - name: --kerberos5-rw
    short-summary: Kerberos5 Read and write access
  - name: --kerberos5i-r
    short-summary: Kerberos5i Read only access
  - name: --kerberos5i-rw
    short-summary: Kerberos5i Read and write access
  - name: --kerberos5p-r
    short-summary: Kerberos5p Read only access
  - name: --kerberos5p-rw
    short-summary: Kerberos5p Read and write access
  - name: --has-root-access
    short-summary: Has root access to volume
  - name: --chown-mode
    short-summary: This parameter specifies who is authorized to change the ownership of a file. restricted - Only root user can change the ownership of the file. unrestricted - Non-root users can change ownership of files that they own. Possible values include- Restricted, Unrestricted. Default value- Restricted.
examples:
  - name: Add an export policy rule for the ANF volume
    text: >
        az netappfiles volume export-policy add -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --allowed-clients "1.2.3.0/24" --rule-index 2 --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false
"""

helps['netappfiles volume export-policy list'] = """
type: command
short-summary: List the export policy rules for a volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
examples:
  - name: List the export policy rules for an ANF volume
    text: >
        az netappfiles volume export-policy list -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname
"""

helps['netappfiles volume export-policy remove'] = """
type: command
short-summary: Remove a rule from the export policy for a volume by rule index. The current rules can be obtained by performing the subgroup list command.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --rule-index
    short-summary: Order index. Range 1 to 6.
examples:
  - name: Remove an export policy rule for an ANF volume
    text: >
        az netappfiles volume export-policy remove -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --rule-index 4
"""

helps['netappfiles volume list'] = """
type: command
short-summary: List the ANF Pools for the specified account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
examples:
  - name: List the ANF volumes of the pool
    text: >
        az netappfiles volume list -g mygroup --account-name myaccname --pool-name mypoolname
"""

helps['netappfiles volume show'] = """
type: command
short-summary: Get the specified ANF volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF pool
examples:
  - name: Returns the properties of the given ANF volume
    text: >
        az netappfiles volume show -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname
"""

helps['netappfiles volume update'] = """
type: command
short-summary: Update the specified ANF volume with the values provided. Unspecified values will remain unchanged. Export policies are amended/created with the subgroup commands
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --service-level
    short-summary: The service level
  - name: --usage-threshold
    short-summary: The maximum storage quota allowed for a file system as integer number of GiB. Min 100 GiB, max 100TiB
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
  - name: --backup-enabled
    short-summary: Backup Enabled
  - name: --backup-policy-id
    short-summary: Backup Policy Resource ID
  - name: --policy-enforced
    short-summary: Backup Policy Enforced
  - name: --vault-id
    short-summary: Vault Resource ID
  - name: --snapshot-policy-id
    short-summary: Snapshot Policy ResourceId
  - name: --is-def-quota-enabled
    short-summary: Specifies if default quota is enabled for the volume.
  - name: --default-user-quota
    short-summary: Default user quota for volume in KiBs. If isDefaultQuotaEnabled is set, the minimum value of 4 KiBs applies
  - name: --default-group-quota
    short-summary: Default group quota for volume in KiBs. If isDefaultQuotaEnabled is set, the minimum value of 4 KiBs applies
  - name: --throughput-mibps
    short-summary: Maximum throughput in Mibps that can be achieved by this volume and this will be accepted as input only for manual qosType volume
  - name: --unix-permissions
    short-summary: UNIX permissions for NFS volume accepted in octal 4 digit format. First digit selects the set user ID(4), set group ID (2) and sticky (1) attributes. Second digit selects permission for the owner of the file- read (4), write (2) and execute (1). Third selects permissions for other users in the same group. the fourth for other users not in the group. 0755 - gives read/write/execute permissions to owner and read/execute to group and other users.
examples:
  - name: Update an ANF volume
    text: >
        az netappfiles volume update -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --service-level ultra --usage-threshold 100 --tags mytag=specialvol
"""

helps['netappfiles volume pool-change'] = """
type: command
short-summary: Change pool for an Azure NetApp Files (ANF) volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --new-pool-resource-id -d
    short-summary: The resource id of the new ANF pool
examples:
  - name: This changes the pool for the volume myvolname from mypoolname to pool with the Id mynewresourceid
    text: >
        az netappfiles volume pool-change -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --new-pool-resource-id mynewresourceid
"""

helps['netappfiles volume backup'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Volume Backup Resources.
"""

helps['netappfiles volume backup create'] = """
type: command
short-summary: Create specified ANF volume backup.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --backup-name -b
    short-summary: The name of the ANF backup
  - name: --use-existing-snapshot
    short-summary: Manual backup an already existing snapshot. This will always be false for scheduled backups and true/false for manual backups
examples:
  - name: Returns the created ANF backup
    text: >
        az netappfiles volume backup create -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname -l westus2 --backup-name mybackupname
"""

helps['netappfiles volume backup list'] = """
type: command
short-summary: List the ANF Backups for the specified volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF pool
examples:
  - name: List the ANF backups of the volume
    text: >
        az netappfiles volume backup list -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname
"""

helps['netappfiles volume backup show'] = """
type: command
short-summary: Get the specified ANF Backup.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF pool
  - name: --backup-name -b
    short-summary: The name of the ANF backup
examples:
  - name: Returns the properties of the given ANF backup
    text: >
        az netappfiles volume backup show -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --backup-name mybackupname
"""

helps['netappfiles volume backup status'] = """
type: command
short-summary: Get backup status of the specified ANF Volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
examples:
  - name: Returns the backup status of the given ANF Volume
    text: >
        az netappfiles volume backup status -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname
"""

helps['netappfiles volume backup restore-status'] = """
type: command
short-summary: Get backup restore status of the specified ANF Volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF pool
examples:
  - name: Returns the backup restore status of the given ANF Volume
    text: >
        az netappfiles volume backup restore-status -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname
"""

helps['netappfiles volume backup update'] = """
type: command
short-summary: Update the specified ANF backup with the values provided.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --name --volume-name -n -v
    short-summary: The name of the ANF volume
  - name: --backup-name -b
    short-summary: The name of the ANF backup
  - name: --label
    short-summary: Label for backup.
  - name: --use-existing-snapshot
    short-summary: Manual backup an already existing snapshot. This will always be false for scheduled backups and true or false for manual backups.
examples:
  - name: Update an ANF backup
    text: >
        az netappfiles volume backup update -g mygroup --account-name myaccname --pool-name mypoolname --name myvolname --backup-name mybackupname
"""


helps['netappfiles snapshot policy'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Snapshot Policy Resources.
"""

helps['netappfiles snapshot policy create'] = """
type: command
short-summary: Create a new Azure NetApp Files (ANF) snapshot policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --snapshot-policy-name
    short-summary: The name of the ANF snapshot policy
  - name: --hourly-snapshots -u
    short-summary: Hourly snapshots count to keep
  - name: --daily-snapshots -d
    short-summary: Daily snapshots count to keep
  - name: --weekly-snapshots -w
    short-summary: Weekly snapshots count to keep
  - name: --monthly-snapshots -m
    short-summary: Monthly snapshots count to keep
  - name: --hourly-minute
    short-summary: Which minute the hourly snapshot should be taken
  - name: --daily-minute
    short-summary: Which minute the daily snapshot should be taken
  - name: --daily-hour
    short-summary: Which hour in UTC timezone the daily snapshot should be taken
  - name: --weekly-minute
    short-summary: Which minute the weekly snapshot should be taken
  - name: --weekly-hour
    short-summary: Which hour in UTC timezone the weekly snapshot should be taken
  - name: --weekly-day
    short-summary: Which weekday the weekly snapshot should be taken, accepts a comma separated list of week day names in english
  - name: --monthly-minute
    short-summary: Which minute the monthly snapshot should be taken
  - name: --monthly-hour
    short-summary: Which hour in UTC timezone the monthly snapshot should be taken
  - name: --monthly-days
    short-summary: Which days of the month the weekly snapshot should be taken, accepts a comma separated list of days
  - name: --enabled -e
    short-summary: The property to decide policy is enabled or not
  - name: --tags
    short-summary: Space-separated tags in `key[=value]` format
examples:
  - name: Create an ANF snapshot policy
    text: >
        az netappfiles snapshot policy create -g mygroup --account-name myaccountname --snapshot-policy-name mysnapshotpolicyname -l westus2 --hourly-snapshots 1 --hourly-minute 5 --enabled true
"""

helps['netappfiles snapshot policy delete'] = """
type: command
short-summary: Delete the specified ANF snapshot policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --snapshot-policy-name
    short-summary: The name of the ANF snapshot policy
examples:
  - name: Delete an ANF snapshot policy
    text: >
        az netappfiles snapshot policy delete -g mygroup --account-name myaccname --snapshot-policy-name mysnapshotpolicyname
"""

helps['netappfiles snapshot policy list'] = """
type: command
short-summary: List the ANF snapshot policies for the specified account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
examples:
  - name: List the snapshot policy for the ANF account
    text: >
        az netappfiles snapshot policy list -g mygroup --account-name myname
"""

helps['netappfiles snapshot policy show'] = """
type: command
short-summary: Get the specified ANF snapshot policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --snapshot-policy-name
    short-summary: The name of the ANF snapshot policy
examples:
  - name: Get an ANF snapshot policy
    text: >
        az netappfiles snapshot policy show -g mygroup --account-name myaccname --snapshot-policy-name mysnapshotpolicyname
"""

helps['netappfiles snapshot policy volumes'] = """
type: command
short-summary: Get the all ANF volumes associated with snapshot policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --snapshot-policy-name
    short-summary: The name of the ANF snapshot policy
examples:
  - name: Get ANF volumes associated with snapshot policy
    text: >
        az netappfiles snapshot policy volumes -g mygroup --account-name myaccname --snapshot-policy-name mysnapshotpolicyname
"""

helps['netappfiles snapshot policy update'] = """
type: command
short-summary: Update the specified ANF snapshot policy.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --snapshot-policy-name
    short-summary: The name of the ANF snapshot policy
  - name: --hourly-snapshots -u
    short-summary: Hourly snapshots count to keep
  - name: --daily-snapshots -d
    short-summary: Daily snapshots count to keep
  - name: --weekly-snapshots -w
    short-summary: Weekly snapshots count to keep
  - name: --monthly-snapshots -m
    short-summary: Monthly snapshots count to keep
  - name: --hourly-minute
    short-summary: Which minute the hourly snapshot should be taken
  - name: --daily-minute
    short-summary: Which minute the daily snapshot should be taken
  - name: --daily-hour
    short-summary: Which hour in UTC timezone the daily snapshot should be taken
  - name: --weekly-minute
    short-summary: Which minute the weekly snapshot should be taken
  - name: --weekly-hour
    short-summary: Which hour in UTC timezone the weekly snapshot should be taken
  - name: --weekly-day
    short-summary: Which weekday the weekly snapshot should be taken, accepts a comma separated list of week day names in english
  - name: --monthly-minute
    short-summary: Which minute the monthly snapshot should be taken
  - name: --monthly-hour
    short-summary: Which hour in UTC timezone the monthly snapshot should be taken
  - name: --monthly-days
    short-summary: Which days of the month the weekly snapshot should be taken, accepts a comma separated list of days
  - name: --enabled -e
    short-summary: The property to decide policy is enabled or not
examples:
  - name: Update specific values for an ANF snapshot policy
    text: >
        az netappfiles snapshot policy update -g mygroup --account-name myaccountname --snapshot-policy-name mysnapshotpolicyname -l westus2 --daily-snapshots 1 --enabled false
"""

helps['netappfiles vault'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Vault Resources.
"""

helps['netappfiles vault list'] = """
type: command
short-summary: List the ANF vaults for NetApp Account.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
examples:
  - name: List the vaults of the ANF account
    text: >
        az netappfiles vault list -g mygroup --account-name myname
"""

helps['netappfiles subvolume'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Subvolume Resources.
"""

helps['netappfiles subvolume create'] = """
type: command
short-summary: Create a subvolume in the specified path or clones the subvolume specified in the parentPath
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --subvolume-name
    short-summary: The name of the ANF subvolume
  - name: --path
    short-summary: Path to the subvolume
  - name: --size
    short-summary: Size of the subvolume
  - name: --parent-path
    short-summary: Path to the parent subvolume
examples:
  - name: Create a ANF subvolume
    text: >
        az netappfiles subvolume create -g mygroup --account-name myaccountname  --pool-name mypoolname --volume-name myvolumename --subvolume-name mysubvolumename
"""

helps['netappfiles subvolume update'] = """
type: command
short-summary: Update a specified ANF subvolume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --subvolume-name
    short-summary: The name of the ANF subvolume
  - name: --path
    short-summary: Path to the subvolume
  - name: --size
    short-summary: Size of the subvolume
examples:
  - name: Update a subvolume
    text: >
        az netappfiles subvolume update -g mygroup --account-name myaccountname  --pool-name mypoolname --volume-name myvolumename --subvolume-name mysubvolumename
"""

helps['netappfiles subvolume list'] = """
type: command
short-summary: List all ANF subvolumes in the specified NetApp volume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
examples:
  - name: List all subvolumes of a ANF volume
    text: >
        az netappfiles subvolume list -g mygroup --account-name myaccountname  --pool-name mypoolname --volume-name myvolumename
"""

helps['netappfiles subvolume show'] = """
type: command
short-summary: Get the path associated with a subvolumeName
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --subvolume-name
    short-summary: The name of the ANF subvolume
examples:
  - name: Get a subvolume of the ANF volume
    text: >
        az netappfiles subvolume show -g mygroup --account-name myaccountname  --pool-name mypoolname --volume-name myvolumename --subvolume-name mysubvolumename
"""

helps['netappfiles subvolume delete'] = """
type: command
short-summary: Delete a specified ANF subvolume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --subvolume-name
    short-summary: The name of the ANF subvolume
examples:
  - name: Delete a subvolume of the ANF volume
    text: >
        az netappfiles subvolume delete -g mygroup --account-name myaccountname  --pool-name mypoolname --volume-name myvolumename --subvolume-name mysubvolumename
"""

helps['netappfiles subvolume metadata'] = """
type: group
short-summary: Manage Azure NetApp Files (ANF) Subvolume Metadata Resources.
"""

helps['netappfiles subvolume metadata show'] = """
type: command
short-summary: Get the specified ANF metadata of a subvolume.
parameters:
  - name: --account-name -a
    short-summary: The name of the ANF account
  - name: --pool-name -p
    short-summary: The name of the ANF pool
  - name: --volume-name -v
    short-summary: The name of the ANF volume
  - name: --subvolume-name
    short-summary: The name of the ANF subvolume
examples:
  - name: Get a metadata of an ANF subvolume
    text: >
        az netappfiles subvolume metadata show -g mygroup --account-name myaccountname  --pool-name mypoolname --volume-name myvolumename --subvolume-name mysubvolumename
"""
