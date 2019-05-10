# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
from knack.log import get_logger
from azure.mgmt.netapp.models import ActiveDirectory, NetAppAccount, NetAppAccountPatch, CapacityPool, Volume, VolumePatch, VolumePropertiesExportPolicy, ExportPolicyRule, Snapshot

logger = get_logger(__name__)


def generate_tags(tag):
    if tag is None:
        return None

    tags = {}
    tag_list = tag.split(" ")
    for tag_item in tag_list:
        parts = tag_item.split("=", 1)
        if len(parts) == 2:
            # two parts, everything after first '=' is the tag's value
            tags[parts[0]] = parts[1]
        elif len(parts) == 1:
            # one part, no tag value
            tags[parts[0]] = ""
    return tags


def _update_mapper(existing, new, keys):
    for key in keys:
        existing_value = getattr(existing, key)
        new_value = getattr(new, key)
        setattr(new, key, new_value if new_value is not None else existing_value)


def build_active_directories(active_directories=None):
    acc_active_directories = None

    if active_directories:
        acc_active_directories = []
        ad_list = json.loads(active_directories)
        for ad in ad_list:
            username = ad['username'] if 'username' in ad else None
            password = ad['password'] if 'password' in ad else None
            domain = ad['domain'] if 'domain' in ad else None
            dns = ad['dns'] if 'dns' in ad else None
            smbservername = ad['smbservername'] if 'smbservername' in ad else None
            organizational_unit = ad['organizational_unit'] if 'organizational_unit' in ad else None
            active_directory = ActiveDirectory(username=username, password=password, domain=domain, dns=dns, smb_server_name=smbservername, organizational_unit=organizational_unit)
            acc_active_directories.append(active_directory)

    return acc_active_directories


# pylint: disable=unused-argument
def create_account(cmd, client, account_name, resource_group_name, location, tag=None, active_directories=None):
    acc_active_directories = build_active_directories(active_directories)
    body = NetAppAccount(location=location, tags=generate_tags(tag), active_directories=acc_active_directories)
    return client.create_or_update(body, resource_group_name, account_name)


# pylint: disable=unused-argument
def update_account(cmd, client, account_name, resource_group_name, location, tag=None, active_directories=None):
    # Note: this set command is required in addition to the update
    # The RP implementation is such that patch of active directories provides an addition type amendment, i.e.
    # absence of an AD does not remove the ADs already present. To perform this a set command is required that
    # asserts exactly the content provided, replacing whatever is already present including removing it if none
    # is present
    acc_active_directories = build_active_directories(active_directories)
    body = NetAppAccountPatch(location=location, tags=generate_tags(tag), active_directories=acc_active_directories)
    return client.create_or_update(body, resource_group_name, account_name)


def patch_account(cmd, instance, account_name, resource_group_name, location, tag=None, active_directories=None):
    # parameters for active directory here will add to the existing ADs but cannot remove them
    # current limitation however is 1 AD/subscription
    acc_active_directories = build_active_directories(active_directories)
    body = NetAppAccountPatch(location=location, tags=generate_tags(tag), active_directories=acc_active_directories)
    _update_mapper(instance, body, ['location', 'active_directories', 'tags'])
    return body


def create_pool(cmd, client, account_name, pool_name, resource_group_name, location, size, service_level, tag=None):
    body = CapacityPool(service_level=service_level, size=int(size), location=location, tags=generate_tags(tag))
    return client.create_or_update(body, resource_group_name, account_name, pool_name)


def patch_pool(cmd, instance, location=None, size=None, service_level=None, tag=None):
    # put operation to update the record
    if size is not None:
        size = int(size)
    body = CapacityPool(service_level=service_level, size=size, location=location, tags=generate_tags(tag))
    _update_mapper(instance, body, ['location', 'service_level', 'size', 'tags'])
    return body


def build_export_policy_rules(export_policy=None):
    rules = []

    if export_policy:
        ep_list = json.loads(export_policy)
        for ep in ep_list:
            rule_index = ep['rule_index'] if 'rule_index' in ep else None
            unix_read_only = ep['unix_read_only'] if 'unix_read_only' in ep else None
            unix_read_write = ep['unix_read_write'] if 'unix_read_write' in ep else None
            cifs = ep['cifs'] if 'cifs' in ep else None
            nfsv3 = ep['nfsv3'] if 'nfsv3' in ep else None
            nfsv4 = ep['nfsv4'] if 'nfsv4' in ep else None
            allowed_clients = ep['allowed_clients'] if 'allowed_clients' in ep else None
            export_policy = ExportPolicyRule(rule_index=rule_index, unix_read_only=unix_read_only, unix_read_write=unix_read_write, cifs=cifs, nfsv3=nfsv3, nfsv4=nfsv4, allowed_clients=allowed_clients)
            rules.append(export_policy)

    return rules


def create_volume(cmd, client, account_name, pool_name, volume_name, resource_group_name, location, service_level, creation_token, usage_threshold, subnet_id, tag=None, export_policy=None):
    rules = build_export_policy_rules(export_policy)
    volume_export_policy = VolumePropertiesExportPolicy(rules=rules) if rules != [] else None

    body = Volume(
        usage_threshold=int(usage_threshold),
        creation_token=creation_token,
        service_level=service_level,
        location=location,
        subnet_id=subnet_id,
        tags=generate_tags(tag),
        export_policy=volume_export_policy)

    return client.create_or_update(body, resource_group_name, account_name, pool_name, volume_name)


def patch_volume(cmd, instance, service_level=None, usage_threshold=None, tag=None, export_policy=None):

    # the export policy provided replaces any existing eport policy
    rules = build_export_policy_rules(export_policy)
    volume_export_policy = VolumePropertiesExportPolicy(rules=rules) if rules != [] else None

    params = VolumePatch(
        usage_threshold=None if usage_threshold is None else int(usage_threshold),
        service_level=service_level,
        tags=generate_tags(tag),
        export_policy=volume_export_policy)
    _update_mapper(instance, params, ['service_level', 'usage_threshold', 'tags', 'export_policy'])
    return params


def create_snapshot(cmd, client, account_name, pool_name, volume_name, snapshot_name, resource_group_name, location, file_system_id=None):
    body = Snapshot(location=location, file_system_id=file_system_id)
    return client.create(body, resource_group_name, account_name, pool_name, volume_name, snapshot_name)
