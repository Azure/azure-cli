# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from enum import Enum

from knack.log import get_logger
from azure.mgmt.netapp.models import ActiveDirectory, NetAppAccount, NetAppAccountPatch, CapacityPool, \
    CapacityPoolPatch, Volume, VolumePatch, VolumePropertiesExportPolicy, ExportPolicyRule, Snapshot, \
    ReplicationObject, VolumePropertiesDataProtection, SnapshotPolicy, SnapshotPolicyPatch, HourlySchedule, \
    DailySchedule, WeeklySchedule, MonthlySchedule, VolumeSnapshotProperties, VolumeBackupProperties, BackupPolicy, \
    BackupPolicyPatch, VolumePatchPropertiesDataProtection, AccountEncryption, AuthorizeRequest, \
    BreakReplicationRequest, PoolChangeRequest, VolumeRevert, Backup, BackupPatch, LdapSearchScopeOpt, SubvolumeInfo, \
    SubvolumePatchRequest, SnapshotRestoreFiles, PlacementKeyValuePairs, VolumeGroupMetaData, VolumeGroupDetails, \
    VolumeGroupVolumeProperties

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import sdk_no_wait
from msrestazure.tools import is_valid_resource_id, parse_resource_id

logger = get_logger(__name__)

# RP expted bytes but CLI allows integer TiBs for ease of use
gib_scale = 1024 * 1024 * 1024
tib_scale = gib_scale * 1024


def _update_mapper(existing, new, keys):
    for key in keys:
        existing_value = getattr(existing, key)
        new_value = getattr(new, key)
        setattr(new, key, new_value if new_value is not None else existing_value)


# ---- ACCOUNT ----
# pylint: disable=unused-argument
# account update - active_directory is amended with subgroup commands
def create_account(client, account_name, resource_group_name, location=None, tags=None, encryption=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    account_encryption = AccountEncryption(key_source=encryption) if encryption is not None else None
    body = NetAppAccount(location=location, tags=tags, encryption=account_encryption)
    return client.begin_create_or_update(resource_group_name, account_name, body)


# pylint: disable=unused-argument, disable=too-many-locals
# add an active directory to the netapp account
# current limitation is 1 AD/subscription
def add_active_directory(instance, account_name, resource_group_name, username, password, domain, dns,
                         smb_server_name, organizational_unit=None, kdc_ip=None, ad_name=None, site=None,
                         server_root_ca_cert=None, backup_operators=None, aes_encryption=None, ldap_signing=None,
                         security_operators=None, ldap_over_tls=None, allow_local_ldap_users=None,
                         administrators=None, encrypt_dc_conn=None, user_dn=None, group_dn=None, group_filter=None):
    ldap_search_scope = LdapSearchScopeOpt(user_dn=user_dn,
                                           group_dn=group_dn,
                                           group_membership_filter=group_filter)
    active_directories = []
    active_directory = ActiveDirectory(username=username, password=password, domain=domain, dns=dns, site=site,
                                       smb_server_name=smb_server_name, organizational_unit=organizational_unit,
                                       kdc_ip=kdc_ip, ad_name=ad_name, backup_operators=backup_operators,
                                       server_root_ca_certificate=server_root_ca_cert, aes_encryption=aes_encryption,
                                       ldap_signing=ldap_signing, security_operators=security_operators,
                                       ldap_over_tls=ldap_over_tls,
                                       allow_local_nfs_users_with_ldap=allow_local_ldap_users,
                                       administrators=administrators, encrypt_dc_connections=encrypt_dc_conn,
                                       ldap_search_scope=ldap_search_scope)
    active_directories.append(active_directory)
    body = NetAppAccountPatch(active_directories=active_directories)
    _update_mapper(instance, body, ['active_directories'])
    return body


# pylint: disable=unused-argument, disable=too-many-locals, disable=too-many-statements
# update an active directory on the netapp account
# current limitation is 1 AD/subscription
def update_active_directory(instance, account_name, resource_group_name, active_directory_id, username, password,
                            domain, dns, smb_server_name, organizational_unit=None, kdc_ip=None, ad_name=None,
                            server_root_ca_cert=None, backup_operators=None, aes_encryption=None, ldap_signing=None,
                            security_operators=None, ldap_over_tls=None, allow_local_ldap_users=None, site=None,
                            administrators=None, encrypt_dc_conn=None, user_dn=None, group_dn=None, group_filter=None):
    ad_list = instance.active_directories

    ldap_search_scope = LdapSearchScopeOpt(user_dn=user_dn,
                                           group_dn=group_dn,
                                           group_membership_filter=group_filter)

    active_directory = ActiveDirectory(active_directory_id=active_directory_id, username=username, password=password,
                                       domain=domain, dns=dns, smb_server_name=smb_server_name, site=site,
                                       organizational_unit=organizational_unit, kdc_ip=kdc_ip, ad_name=ad_name,
                                       backup_operators=backup_operators, server_root_ca_certificate=server_root_ca_cert,
                                       aes_encryption=aes_encryption, ldap_signing=ldap_signing,
                                       security_operators=security_operators, ldap_over_tls=ldap_over_tls,
                                       allow_local_nfs_users_with_ldap=allow_local_ldap_users,
                                       administrators=administrators, encrypt_dc_connections=encrypt_dc_conn,
                                       ldap_search_scope=ldap_search_scope)

    for ad in ad_list:
        if ad.active_directory_id == active_directory_id:
            instance.active_directories.remove(ad)

    instance.active_directories.append(active_directory)

    body = NetAppAccountPatch(active_directories=ad_list)
    _update_mapper(instance, body, ['active_directories'])
    return body


# list all active directories
def list_active_directories(client, account_name, resource_group_name):
    return client.get(resource_group_name, account_name).active_directories


# removes the active directory entry matching the provided id
# Note:
# The RP implementation is such that patch of active directories provides an addition type amendment, i.e.
# absence of an AD does not remove the ADs already present. To perform this a put request is required that
# asserts exactly the content provided, replacing whatever is already present including removing it if none
# are present
def remove_active_directory(client, account_name, resource_group_name, active_directory):
    instance = client.get(resource_group_name, account_name)

    for ad in instance.active_directories:
        if ad.active_directory_id == active_directory:
            instance.active_directories.remove(ad)

    active_directories = instance.active_directories
    body = NetAppAccount(location=instance.location, tags=instance.tags, active_directories=active_directories)

    return client.begin_create_or_update(resource_group_name, account_name, body)


# account update, active_directory is amended with subgroup commands
def patch_account(instance, account_name, resource_group_name, tags=None, encryption=None):
    account_encryption = AccountEncryption(key_source=encryption)
    body = NetAppAccountPatch(tags=tags, encryption=account_encryption)
    _update_mapper(instance, body, ['tags', 'encryption'])
    return body


# list accounts by subscription or resource group
def list_accounts(client, resource_group_name=None):
    if resource_group_name is None:
        return client.list_by_subscription()
    return client.list(resource_group_name)


# ---- POOL ----
# pylint: disable=no-required-location-param
def create_pool(client, account_name, pool_name, resource_group_name, service_level, size, location=None, tags=None,
                qos_type=None, cool_access=None, encryption_type=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    body = CapacityPool(service_level=service_level,
                        size=int(size) * tib_scale,
                        location=location,
                        tags=tags,
                        qos_type=qos_type,
                        cool_access=cool_access,
                        encryption_type=encryption_type)
    return client.begin_create_or_update(resource_group_name, account_name, pool_name, body)


def patch_pool(instance, size=None, qos_type=None, tags=None):
    # put operation to update the record
    if size is not None:
        size = int(size) * tib_scale
    body = CapacityPoolPatch(qos_type=qos_type, size=size, tags=tags)
    _update_mapper(instance, body, ['qos_type', 'size', 'tags'])
    return body


# ---- VOLUME ----
# pylint: disable=too-many-locals, disable=no-required-location-param
def create_volume(cmd, client, account_name, pool_name, volume_name, resource_group_name, file_path, usage_threshold,
                  vnet, location=None, subnet='default', service_level=None, protocol_types=None, volume_type=None,
                  endpoint_type=None, replication_schedule=None, remote_volume_resource_id=None, tags=None,
                  snapshot_id=None, snapshot_policy_id=None, backup_policy_id=None, backup_enabled=None, backup_id=None,
                  policy_enforced=None, vault_id=None, kerberos_enabled=None, security_style=None, throughput_mibps=None,
                  kerberos5_r=None, kerberos5_rw=None, kerberos5i_r=None,
                  kerberos5i_rw=None, kerberos5p_r=None, kerberos5p_rw=None,
                  has_root_access=None, snapshot_dir_visible=None,
                  smb_encryption=None, smb_continuously_avl=None, encryption_key_source=None,
                  rule_index=None, unix_read_only=None, unix_read_write=None, cifs=None,
                  allowed_clients=None, ldap_enabled=None, chown_mode=None, cool_access=None, coolness_period=None,
                  unix_permissions=None, is_def_quota_enabled=None, default_user_quota=None,
                  default_group_quota=None, avs_data_store=None, network_features=None, enable_subvolumes=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    subs_id = get_subscription_id(cmd.cli_ctx)

    # default the resource group of the subnet to the volume's rg unless the subnet is specified by id
    subnet_rg = resource_group_name

    # determine vnet - supplied value can be name or ARM resource Id
    if is_valid_resource_id(vnet):
        resource_parts = parse_resource_id(vnet)
        vnet = resource_parts['resource_name']
        subnet_rg = resource_parts['resource_group']

    # determine subnet - supplied value can be name or ARM reource Id
    if is_valid_resource_id(subnet):
        resource_parts = parse_resource_id(subnet)
        subnet = resource_parts['resource_name']
        subnet_rg = resource_parts['resource_group']

    # if NFSv4 is specified then the export policy must reflect this
    # the RP ordinarily only creates a default setting NFSv3.
    if protocol_types is not None and any(x in ['NFSv3', 'NFSv4.1'] for x in protocol_types) \
            and not (protocol_types == ['NFSv3'] and rule_index is None):
        rules = []
        isNfs41 = False
        isNfs3 = False

        if "NFSv4.1" in protocol_types:
            isNfs41 = True
            if allowed_clients is None:
                raise ValidationError("Parameter allowed-clients needs to be set when protocol-type is NFSv4.1")
            if rule_index is None:
                raise ValidationError("Parameter rule-index needs to be set when protocol-type is NFSv4.1")
        if "NFSv3" in protocol_types:
            isNfs3 = True
        if "CIFS" in protocol_types:
            cifs = True

        export_policy = ExportPolicyRule(rule_index=rule_index, unix_read_only=unix_read_only,
                                         unix_read_write=unix_read_write, cifs=cifs,
                                         nfsv3=isNfs3, nfsv41=isNfs41, allowed_clients=allowed_clients,
                                         kerberos5_read_only=kerberos5_r,
                                         kerberos5_read_write=kerberos5_rw,
                                         kerberos5_i_read_only=kerberos5i_r,
                                         kerberos5_i_read_write=kerberos5i_rw,
                                         kerberos5_p_read_only=kerberos5p_r,
                                         kerberos5_p_read_write=kerberos5p_rw,
                                         has_root_access=has_root_access,
                                         chown_mode=chown_mode)
        rules.append(export_policy)

        volume_export_policy = VolumePropertiesExportPolicy(rules=rules)
    else:
        volume_export_policy = None

    data_protection = None
    replication = None
    snapshot = None
    backup = None

    # Make sure volume_type is set correctly if replication parameters are set
    if endpoint_type is not None and replication_schedule is not None and remote_volume_resource_id is not None:
        volume_type = "DataProtection"

    if volume_type == "DataProtection":
        replication = ReplicationObject(endpoint_type=endpoint_type, replication_schedule=replication_schedule,
                                        remote_volume_resource_id=remote_volume_resource_id)
    if snapshot_policy_id is not None:
        snapshot = VolumeSnapshotProperties(snapshot_policy_id=snapshot_policy_id)
    if backup_policy_id is not None:
        backup = VolumeBackupProperties(backup_policy_id=backup_policy_id, policy_enforced=policy_enforced,
                                        vault_id=vault_id, backup_enabled=backup_enabled)
    if replication is not None or snapshot is not None or backup is not None:
        data_protection = VolumePropertiesDataProtection(replication=replication, snapshot=snapshot, backup=backup)

    subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (subs_id, subnet_rg, vnet, subnet)
    body = Volume(
        usage_threshold=int(usage_threshold) * gib_scale,
        creation_token=file_path,
        service_level=service_level,
        location=location,
        subnet_id=subnet_id,
        protocol_types=protocol_types,
        export_policy=volume_export_policy,
        volume_type=volume_type,
        data_protection=data_protection,
        backup_id=backup_id,
        kerberos_enabled=kerberos_enabled,
        throughput_mibps=throughput_mibps,
        snapshot_directory_visible=snapshot_dir_visible,
        security_style=security_style,
        tags=tags,
        snapshot_id=snapshot_id,
        smb_encryption=smb_encryption,
        smb_continuously_available=smb_continuously_avl,
        encryption_key_source=encryption_key_source,
        ldap_enabled=ldap_enabled,
        cool_access=cool_access,
        coolness_period=coolness_period,
        unix_permissions=unix_permissions,
        is_default_quota_enabled=is_def_quota_enabled,
        default_user_quota_in_ki_bs=default_user_quota,
        default_group_quota_in_ki_bs=default_group_quota,
        avs_data_store=avs_data_store,
        network_features=network_features,
        enable_subvolumes=enable_subvolumes)

    return client.begin_create_or_update(resource_group_name, account_name, pool_name, volume_name, body)


# -- volume update
def patch_volume(instance, usage_threshold=None, service_level=None, tags=None, vault_id=None, backup_enabled=False,
                 backup_policy_id=None, policy_enforced=False, throughput_mibps=None, snapshot_policy_id=None,
                 is_def_quota_enabled=None, default_user_quota=None, default_group_quota=None, unix_permissions=None):
    data_protection = None
    backup = None
    snapshot = None
    if vault_id is not None:
        backup = VolumeBackupProperties(vault_id=vault_id, backup_enabled=backup_enabled,
                                        backup_policy_id=backup_policy_id, policy_enforced=policy_enforced)
    if snapshot_policy_id is not None:
        snapshot = VolumeSnapshotProperties(snapshot_policy_id=snapshot_policy_id)

    if backup is not None or snapshot is not None:
        data_protection = VolumePatchPropertiesDataProtection(backup=backup, snapshot=snapshot)

    params = VolumePatch(
        usage_threshold=None if usage_threshold is None else int(usage_threshold) * gib_scale,
        service_level=service_level,
        data_protection=data_protection,
        tags=tags,
        is_default_quota_enabled=is_def_quota_enabled,
        default_user_quota_in_ki_bs=default_user_quota,
        default_group_quota_in_ki_bs=default_group_quota,
        unix_permissions=unix_permissions)
    if throughput_mibps is not None:
        params.throughput_mibps = throughput_mibps
    _update_mapper(instance, params, ['service_level', 'usage_threshold', 'tags', 'data_protection'])
    return params


# -- volume revert
def volume_revert(client, resource_group_name, account_name, pool_name, volume_name, snapshot_id):
    body = VolumeRevert(snapshot_id=snapshot_id)
    return client.begin_revert(resource_group_name, account_name, pool_name, volume_name, body)


# -- change pool
def pool_change(client, resource_group_name, account_name, pool_name, volume_name, new_pool_resource_id):
    body = PoolChangeRequest(new_pool_resource_id=new_pool_resource_id)
    return client.begin_pool_change(resource_group_name, account_name, pool_name, volume_name, body)


# -- volume replication
def authorize_replication(client, resource_group_name, account_name, pool_name, volume_name, remote_volume_resource_id=None):
    body = AuthorizeRequest(remote_volume_resource_id=remote_volume_resource_id)
    return client.begin_authorize_replication(resource_group_name, account_name, pool_name, volume_name, body)


def break_replication(client, resource_group_name, account_name, pool_name, volume_name, force_break_replication=None):
    body = BreakReplicationRequest(force_break_replication=force_break_replication)
    return client.begin_break_replication(resource_group_name, account_name, pool_name, volume_name, body)


# ---- VOLUME EXPORT POLICY ----
# add new rule to policy
def add_export_policy_rule(instance, allowed_clients, unix_read_only, unix_read_write, cifs, nfsv3, nfsv41,
                           rule_index=None, kerberos5_r=None, kerberos5_rw=None, kerberos5i_r=None, kerberos5i_rw=None,
                           kerberos5p_r=None, kerberos5p_rw=None, has_root_access=None, chown_mode=None):
    if rule_index is None:
        rule_index = 1 if len(instance.export_policy.rules) < 1 else max(rule.rule_index for rule in instance.export_policy.rules) + 1

    rules = []

    export_policy = ExportPolicyRule(rule_index=rule_index, unix_read_only=unix_read_only,
                                     unix_read_write=unix_read_write, cifs=cifs,
                                     nfsv3=nfsv3, nfsv41=nfsv41, allowed_clients=allowed_clients,
                                     kerberos5_read_only=kerberos5_r,
                                     kerberos5_read_write=kerberos5_rw,
                                     kerberos5_i_read_only=kerberos5i_r,
                                     kerberos5_i_read_write=kerberos5i_rw,
                                     kerberos5_p_read_only=kerberos5p_r,
                                     kerberos5_p_read_write=kerberos5p_rw,
                                     has_root_access=has_root_access,
                                     chown_mode=chown_mode)

    rules.append(export_policy)
    for rule in instance.export_policy.rules:
        if int(rule_index) == rule.rule_index:
            raise ValidationError("Rule index %s already exist" % rule_index)
        rules.append(rule)

    volume_export_policy = VolumePropertiesExportPolicy(rules=rules)

    params = VolumePatch(
        export_policy=volume_export_policy,
        service_level=instance.service_level,
        usage_threshold=instance.usage_threshold)
    _update_mapper(instance, params, ['export_policy'])
    return params


# list all rules
def list_export_policy_rules(client, account_name, pool_name, volume_name, resource_group_name):
    return client.get(resource_group_name, account_name, pool_name, volume_name).export_policy


# delete rule by specific index
def remove_export_policy_rule(instance, rule_index):
    rules = []
    # Note this commented out way created a patch request that included some mount target properties causing validation issues server side
    # need to investigate why, leave this for now remove after this has been ivestigated before next release please
    # look for the rule and remove
    # for rule in instance.export_policy.rules:
    #    if rule.rule_index == int(rule_index):
    #        instance.export_policy.rules.remove(rule)

    # return instance

    for rule in instance.export_policy.rules:
        if rule.rule_index != int(rule_index):
            rules.append(rule)

    volume_export_policy = VolumePropertiesExportPolicy(rules=rules)
    params = VolumePatch(
        export_policy=volume_export_policy,
        service_level=instance.service_level,
        usage_threshold=instance.usage_threshold)
    _update_mapper(instance, params, ['export_policy'])
    return params


# ---- SNAPSHOTS ----
def create_snapshot(client, resource_group_name, account_name, pool_name, volume_name, snapshot_name, location=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    body = Snapshot(location=location)
    return client.begin_create(resource_group_name, account_name, pool_name, volume_name, snapshot_name, body)


def snapshot_restore_files(client, resource_group_name, account_name, pool_name, volume_name, snapshot_name, file_paths,
                           destination_path=None):
    body = SnapshotRestoreFiles(
        file_paths=file_paths,
        destination_path=destination_path
    )
    return client.begin_restore_files(resource_group_name, account_name, pool_name, volume_name, snapshot_name, body)


# ---- SNAPSHOT POLICIES ----
def create_snapshot_policy(client, resource_group_name, account_name, snapshot_policy_name, location=None,
                           hourly_snapshots=None, hourly_minute=None,
                           daily_snapshots=None, daily_minute=None, daily_hour=None,
                           weekly_snapshots=None, weekly_minute=None, weekly_hour=None, weekly_day=None,
                           monthly_snapshots=None, monthly_minute=None, monthly_hour=None, monthly_days=None,
                           enabled=False, tags=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    body = SnapshotPolicy(
        location=location,
        hourly_schedule=HourlySchedule(snapshots_to_keep=hourly_snapshots, minute=hourly_minute),
        daily_schedule=DailySchedule(snapshots_to_keep=daily_snapshots, minute=daily_minute, hour=daily_hour),
        weekly_schedule=WeeklySchedule(snapshots_to_keep=weekly_snapshots, minute=weekly_minute,
                                       hour=weekly_hour, day=weekly_day),
        monthly_schedule=MonthlySchedule(snapshots_to_keep=monthly_snapshots, minute=monthly_minute,
                                         hour=monthly_hour, days_of_month=monthly_days),
        enabled=enabled,
        tags=tags)
    return client.create(resource_group_name, account_name, snapshot_policy_name, body)


def patch_snapshot_policy(client, resource_group_name, account_name, snapshot_policy_name, location=None,
                          hourly_snapshots=None, hourly_minute=None,
                          daily_snapshots=None, daily_minute=None, daily_hour=None,
                          weekly_snapshots=None, weekly_minute=None, weekly_hour=None, weekly_day=None,
                          monthly_snapshots=None, monthly_minute=None, monthly_hour=None, monthly_days=None,
                          enabled=False):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    body = SnapshotPolicyPatch(
        location=location,
        hourly_schedule=HourlySchedule(snapshots_to_keep=hourly_snapshots, minute=hourly_minute),
        daily_schedule=DailySchedule(snapshots_to_keep=daily_snapshots, minute=daily_minute, hour=daily_hour),
        weekly_schedule=WeeklySchedule(snapshots_to_keep=weekly_snapshots, minute=weekly_minute,
                                       hour=weekly_hour, day=weekly_day),
        monthly_schedule=MonthlySchedule(snapshots_to_keep=monthly_snapshots, minute=monthly_minute,
                                         hour=monthly_hour, days_of_month=monthly_days),
        enabled=enabled)
    return client.begin_update(resource_group_name, account_name, snapshot_policy_name, body)


# ---- VOLUME BACKUPS ----
def create_backup(client, resource_group_name, account_name, pool_name, volume_name, backup_name, location=None,
                  use_existing_snapshot=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    body = Backup(location=location, use_existing_snapshot=use_existing_snapshot)
    return client.begin_create(resource_group_name, account_name, pool_name, volume_name, backup_name, body)


def update_backup(client, resource_group_name, account_name, pool_name, volume_name, backup_name, tags=None, label=None,
                  use_existing_snapshot=None):
    body = BackupPatch(tags=tags, label=label, use_existing_snapshot=use_existing_snapshot)
    return client.begin_update(resource_group_name, account_name, pool_name, volume_name, backup_name, body)


# ---- BACKUP POLICIES ----
def create_backup_policy(client, resource_group_name, account_name, backup_policy_name, location=None,
                         daily_backups=None, weekly_backups=None, monthly_backups=None, enabled=False, tags=None):
    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    body = BackupPolicy(
        location=location,
        daily_backups_to_keep=daily_backups,
        weekly_backups_to_keep=weekly_backups,
        monthly_backups_to_keep=monthly_backups,
        enabled=enabled,
        tags=tags)
    return client.begin_create(resource_group_name, account_name, backup_policy_name, body)


def patch_backup_policy(client, resource_group_name, account_name, backup_policy_name, location=None,
                        daily_backups=None, weekly_backups=None, monthly_backups=None, enabled=False, tags=None):
    body = BackupPolicyPatch(
        location=location,
        daily_backups_to_keep=daily_backups,
        weekly_backups_to_keep=weekly_backups,
        monthly_backups_to_keep=monthly_backups,
        enabled=enabled,
        tags=tags)
    return client.begin_update(resource_group_name, account_name, backup_policy_name, body)


# ---- SUBVOLUME ----
def create_subvolume(client, resource_group_name, account_name, pool_name, volume_name, subvolume_name, path=None,
                     size=None, parent_path=None):
    body = SubvolumeInfo(
        path=path,
        size=size,
        parent_path=parent_path
    )
    return client.begin_create(resource_group_name, account_name, pool_name, volume_name, subvolume_name, body)


def patch_subvolume(client, resource_group_name, account_name, pool_name, volume_name, subvolume_name, path=None,
                    size=None):
    body = SubvolumePatchRequest(
        path=path,
        size=size
    )
    return client.begin_update(resource_group_name, account_name, pool_name, volume_name, subvolume_name, body)


# ---- VOLUME GROUPS ----
def create_volume_group(cmd, client, resource_group_name, account_name, pool_name, volume_group_name, vnet, ppg,
                        sap_sid, subnet='default', location=None, tags=None, gp_rules=None, memory=100,
                        add_snapshot_capacity=50, start_host_id=1, number_of_hots=1, prefix="", system_role="PRIMARY",
                        data_size=None, data_throughput=None, log_size=None, log_throughput=None, shared_size=None,
                        shared_throughput=None, data_backup_size=None, data_backup_throughput=None,
                        log_backup_size=None, log_backup_throughput=None, backup_nfsv3=False, no_wait=False,
                        data_repl_skd=None, data_src_id=None, shared_repl_skd=None, shared_src_id=None,
                        data_backup_repl_skd=None, data_backup_src_id=None, log_backup_repl_skd=None,
                        log_backup_src_id=None):
    if number_of_hots < 1 or number_of_hots > 3:
        raise ValidationError("Number of hosts must be between 1 and 3")
    if memory < 1 or memory > 12000:
        raise ValidationError("Memory must be between 1 and 12000")
    if add_snapshot_capacity < 0 or add_snapshot_capacity > 200:
        raise ValidationError("Additional capacity for snapshot must be between 0 and 200")
    if system_role == "DR" and number_of_hots != 1:
        raise ValidationError("Number of hosts must be 1 when creating a Disaster Recovery (DR) volume group")

    if prefix == "":
        if system_role == "HA":
            prefix = "HA-"
        if system_role == "DR":
            prefix = "DR-"
    else:
        prefix = prefix + "-"

    if location is None:
        location = client.resource_groups.get(resource_group_name).location
    rules = []
    if gp_rules is not None:
        for rule in gp_rules:
            rule = rule.split("=")
            rules.append(PlacementKeyValuePairs(key=rule[0], value=rule[1]))

    group_meta_data = VolumeGroupMetaData(
        group_description="Primary for " + volume_group_name,
        application_type="SAP-HANA",
        application_identifier="DEV",
        global_placement_rules=rules,
        deployment_spec_id="20542149-bfca-5618-1879-9863dc6767f1"
    )

    # default the resource group of the subnet to the volume's rg unless the subnet is specified by id
    subnet_rg = resource_group_name

    # determine vnet - supplied value can be name or ARM resource Id
    if is_valid_resource_id(vnet):
        resource_parts = parse_resource_id(vnet)
        vnet = resource_parts['resource_name']
        subnet_rg = resource_parts['resource_group']

    # determine subnet - supplied value can be name or ARM reource Id
    if is_valid_resource_id(subnet):
        resource_parts = parse_resource_id(subnet)
        subnet = resource_parts['resource_name']
        subnet_rg = resource_parts['resource_group']

    subscription_id = get_subscription_id(cmd.cli_ctx)
    subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % \
                (subscription_id, subnet_rg, vnet, subnet)
    pool_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.NetApp/netAppAccounts/%s/capacityPools/%s" % \
              (subscription_id, subnet_rg, account_name, pool_name)

    # Create data volume(s)
    data_volumes = []
    for i in range(start_host_id, start_host_id + number_of_hots):
        data_volumes.append(create_data_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory,
                                                          add_snapshot_capacity, str(i), data_size, data_throughput,
                                                          prefix, data_repl_skd, data_src_id))
    # Create log volume(s)
    log_volumes = []
    for i in range(start_host_id, start_host_id + number_of_hots):
        log_volumes.append(create_log_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, str(i), log_size,
                                                        log_throughput, prefix))
    total_data_volume_size = sum(int(vol.usage_threshold) for vol in data_volumes)
    total_log_volume_size = sum(int(vol.usage_threshold) for vol in log_volumes)

    # Combine volumes and create shared and backup volumes
    volumes = []
    volumes.extend(data_volumes)
    volumes.extend(log_volumes)

    volumes.append(create_shared_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, shared_size,
                                                   shared_throughput, number_of_hots, prefix, shared_repl_skd, shared_src_id))
    volumes.append(create_data_backup_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, data_backup_size,
                                                        data_backup_throughput, total_data_volume_size,
                                                        total_log_volume_size, prefix, backup_nfsv3,
                                                        data_backup_repl_skd, data_backup_src_id))
    volumes.append(create_log_backup_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, log_backup_size,
                                                       log_backup_throughput, prefix, backup_nfsv3, log_backup_repl_skd,
                                                       log_backup_src_id))

    body = VolumeGroupDetails(
        location=location,
        tags=tags,
        group_meta_data=group_meta_data,
        volumes=volumes
    )
    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, account_name, volume_group_name, body)


def create_data_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, add_snap_capacity, host_id,
                                  data_size, data_throughput, prefix, data_repl_skd=None, data_src_id=None):
    name = prefix + sap_sid + "-" + VolumeType.DATA.value + "-mnt" + (host_id.rjust(5, '0'))

    if data_size is None:
        size = calculate_usage_threshold(memory, VolumeType.DATA, add_snap_capacity=add_snap_capacity)
    else:
        size = data_size * gib_scale

    throughput = data_throughput
    if throughput is None:
        throughput = calculate_throughput(memory, VolumeType.DATA)

    data_protection = None
    if data_repl_skd is not None and data_src_id is not None:
        replication = ReplicationObject(replication_schedule=data_repl_skd,
                                        remote_volume_resource_id=data_src_id)
        data_protection = VolumePropertiesDataProtection(replication=replication)

    data_volume = VolumeGroupVolumeProperties(
        subnet_id=subnet_id,
        creation_token=name,
        capacity_pool_resource_id=pool_id,
        proximity_placement_group=ppg,
        volume_spec_name=VolumeType.DATA.value,
        protocol_types=["NFSv4.1"],
        name=name,
        usage_threshold=size,
        throughput_mibps=throughput,
        export_policy=create_default_export_policy_for_vg(),
        data_protection=data_protection
    )

    return data_volume


def create_log_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, host_id, log_size,
                                 log_throughput, prefix):
    name = prefix + sap_sid + "-" + VolumeType.LOG.value + "-mnt" + (host_id.rjust(5, '0'))

    if log_size is None:
        size = calculate_usage_threshold(memory, VolumeType.LOG)
    else:
        size = log_size * gib_scale

    if log_throughput is None:
        log_throughput = calculate_throughput(memory, VolumeType.LOG)

    log_volume = VolumeGroupVolumeProperties(
        subnet_id=subnet_id,
        creation_token=name,
        capacity_pool_resource_id=pool_id,
        proximity_placement_group=ppg,
        volume_spec_name=VolumeType.LOG.value,
        protocol_types=["NFSv4.1"],
        name=name,
        usage_threshold=size,
        throughput_mibps=log_throughput,
        export_policy=create_default_export_policy_for_vg()
    )

    return log_volume


def create_shared_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, shared_size,
                                    shared_throughput, number_of_hosts, prefix, shared_repl_skd=None, shared_src_id=None):
    name = prefix + sap_sid + "-" + VolumeType.SHARED.value

    if shared_size is None:
        size = calculate_usage_threshold(memory, VolumeType.SHARED, total_host_count=number_of_hosts)
    else:
        size = shared_size * gib_scale

    if shared_throughput is None:
        shared_throughput = calculate_throughput(memory, VolumeType.SHARED)

    data_protection = None
    if shared_repl_skd is not None and shared_src_id is not None:
        replication = ReplicationObject(replication_schedule=shared_repl_skd,
                                        remote_volume_resource_id=shared_src_id)
        data_protection = VolumePropertiesDataProtection(replication=replication)

    shared_volume = VolumeGroupVolumeProperties(
        subnet_id=subnet_id,
        creation_token=name,
        capacity_pool_resource_id=pool_id,
        proximity_placement_group=ppg,
        volume_spec_name=VolumeType.SHARED.value,
        protocol_types=["NFSv4.1"],
        name=name,
        usage_threshold=size,
        throughput_mibps=shared_throughput,
        export_policy=create_default_export_policy_for_vg(),
        data_protection=data_protection
    )

    return shared_volume


def create_data_backup_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, data_backup_size,
                                         data_backup_throughput, total_data_volume_size, total_log_volume_size,
                                         prefix, backup_nfsv3, data_backup_repl_skd, data_backup_src_id):
    name = prefix + sap_sid + "-" + VolumeType.DATA_BACKUP.value

    if data_backup_size is None:
        size = calculate_usage_threshold(memory, VolumeType.DATA_BACKUP, data_size=total_data_volume_size,
                                         log_size=total_log_volume_size)
    else:
        size = data_backup_size * gib_scale

    if data_backup_throughput is None:
        data_backup_throughput = calculate_throughput(memory, VolumeType.DATA_BACKUP)

    data_protection = None
    if data_backup_repl_skd is not None and data_backup_src_id is not None:
        replication = ReplicationObject(replication_schedule=data_backup_repl_skd,
                                        remote_volume_resource_id=data_backup_src_id)
        data_protection = VolumePropertiesDataProtection(replication=replication)

    data_backup_volume = VolumeGroupVolumeProperties(
        subnet_id=subnet_id,
        creation_token=name,
        capacity_pool_resource_id=pool_id,
        proximity_placement_group=ppg,
        volume_spec_name=VolumeType.DATA_BACKUP.value,
        protocol_types=['NFSv4.1'] if not backup_nfsv3 else ['NFSv3'],
        name=name,
        usage_threshold=size,
        throughput_mibps=data_backup_throughput,
        export_policy=create_default_export_policy_for_vg(backup_nfsv3),
        data_protection=data_protection
    )

    return data_backup_volume


def create_log_backup_volume_properties(subnet_id, sap_sid, pool_id, ppg, memory, log_backup_size,
                                        log_backup_throughput, prefix, backup_nfsv3, log_backup_repl_skd,
                                        log_backup_src_id):
    name = prefix + sap_sid + "-" + VolumeType.LOG_BACKUP.value

    if log_backup_size is None:
        size = calculate_usage_threshold(memory, VolumeType.LOG_BACKUP)
    else:
        size = log_backup_size * gib_scale

    if log_backup_throughput is None:
        log_backup_throughput = calculate_throughput(memory, VolumeType.LOG_BACKUP)

    data_protection = None
    if log_backup_repl_skd is not None and log_backup_src_id is not None:
        replication = ReplicationObject(replication_schedule=log_backup_repl_skd,
                                        remote_volume_resource_id=log_backup_src_id)
        data_protection = VolumePropertiesDataProtection(replication=replication)

    log_backup = VolumeGroupVolumeProperties(
        subnet_id=subnet_id,
        creation_token=name,
        capacity_pool_resource_id=pool_id,
        proximity_placement_group=ppg,
        volume_spec_name=VolumeType.LOG_BACKUP.value,
        protocol_types=['NFSv4.1'] if not backup_nfsv3 else ['NFSv3'],
        name=name,
        usage_threshold=size,
        throughput_mibps=log_backup_throughput,
        export_policy=create_default_export_policy_for_vg(backup_nfsv3),
        data_protection=data_protection
    )

    return log_backup


# Memory should be sent in as GiB and additional snapshot capacity as percentage (0-200). Usage is returned in bytes.
def calculate_usage_threshold(memory, volume_type, add_snap_capacity=50, total_host_count=1, data_size=50, log_size=50):
    if volume_type == VolumeType.DATA:
        usage = ((add_snap_capacity / 100) * memory + memory)
        return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
    if volume_type == VolumeType.LOG:
        if memory < 512:
            usage = memory * 0.5  # 50%
            return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
        return 512 * gib_scale
    if volume_type == VolumeType.SHARED:
        usage = ((total_host_count + 3) / 4) * memory
        return int(usage) * gib_scale if usage > 1024 else 1024 * gib_scale  # MIN 1 TiB
    if volume_type == VolumeType.DATA_BACKUP:
        usage = (data_size / gib_scale) + (log_size / gib_scale)
        return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
    if volume_type == VolumeType.LOG_BACKUP:
        return 512 * gib_scale


# Memory should be sent in in GiB. Returns throughput in MiB/s.
# pylint: disable=too-many-return-statements
def calculate_throughput(memory, volume_type):
    if volume_type == VolumeType.DATA:
        if memory <= 1024:
            return 400
        if memory <= 2048:
            return 600
        if memory <= 4096:
            return 800
        if memory <= 6144:
            return 1000
        if memory <= 8192:
            return 1200
        if memory <= 10248:
            return 1400
        return 1500
    if volume_type == VolumeType.LOG:
        if memory <= 4096:
            return 250
        return 500
    if volume_type == VolumeType.SHARED:
        return 64
    if volume_type == VolumeType.DATA_BACKUP:
        return 128
    if volume_type == VolumeType.LOG_BACKUP:
        return 250


def create_default_export_policy_for_vg(nfsv3=False):
    rules = []
    export_policy = ExportPolicyRule(rule_index=1, unix_read_only=False, unix_read_write=True, nfsv3=nfsv3,
                                     nfsv41=not nfsv3, allowed_clients="0.0.0.0/0")
    rules.append(export_policy)
    volume_export_policy = VolumePropertiesExportPolicy(rules=rules)
    return volume_export_policy


class VolumeType(Enum):
    DATA = "data"
    LOG = "log"
    SHARED = "shared"
    DATA_BACKUP = "data-backup"
    LOG_BACKUP = "log-backup"
