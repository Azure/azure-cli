# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.security.models import SecurityContact, AutoProvision

# --------------------------------------------------------------------------------------------
# Security Tasks
# --------------------------------------------------------------------------------------------


def list_security_tasks(client, resource_group_name=None):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    if resource_group_name:
        return client.tasks.list_by_resource_group(resource_group_name)

    return client.tasks.list()


def get_security_task(client, resource_name, resource_group_name=None):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    if resource_group_name:
        return client.tasks.get_resource_group_level_task(resource_group_name, resource_name)

    return client.tasks.get_subscription_level_task(resource_name)


# --------------------------------------------------------------------------------------------
# Security Alerts
# --------------------------------------------------------------------------------------------

def list_security_alerts(client, resource_group_name=None, location=None):

    if location:
        client.config.asc_location = location

        if resource_group_name:
            return client.list_resource_group_level_alerts_by_region(resource_group_name)

        return client.list_subscription_level_alerts_by_region()

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def get_security_alert(client, location, resource_name, resource_group_name=None):

    client.config.asc_location = location

    if resource_group_name:
        return client.get_resource_group_level_alerts(resource_name, resource_group_name)

    return client.get_subscription_level_alert(resource_name)


def update_security_alert(client, location, resource_name, status, resource_group_name=None):

    client.config.asc_location = location

    if resource_group_name:
        client.update_resource_group_level_alert_state(resource_name, status, resource_group_name)
    else:
        client.update_subscription_level_alert_state(resource_name, status)


# --------------------------------------------------------------------------------------------
# Security Settings
# --------------------------------------------------------------------------------------------


def list_security_settings(client):

    return client.list()


def get_security_setting(client, resource_name):

    return client.get(resource_name)


# --------------------------------------------------------------------------------------------
# Security Contacts
# --------------------------------------------------------------------------------------------


def list_security_contacts(client):

    return client.list()


def get_security_contact(client, resource_name):

    return client.get(resource_name)


def create_security_contact(client, resource_name, email, phone=None, alert_notifications=None, alerts_admins=None):

    if alert_notifications is None:
        alert_notifications = ''

    if alerts_admins is None:
        alerts_admins = ''

    if phone is None:
        phone = ''

    new_contact = SecurityContact(email=email,
                                  phone=phone,
                                  alert_notifications=alert_notifications,
                                  alerts_to_admins=alerts_admins)

    return client.create(resource_name, new_contact)


def delete_security_contact(client, resource_name):

    return client.delete(resource_name)


# --------------------------------------------------------------------------------------------
# Security Automatic Provisioning Settings
# --------------------------------------------------------------------------------------------

def list_security_auto_provisioning_settings(client):

    return client.list()


def get_security_auto_provisioning_setting(client, resource_name):

    return client.get(resource_name)


def update_security_auto_provisioning_setting(client, auto_provision, resource_name):

    new_auto_provision = AutoProvision(auto_provision)
    return client.create(resource_name, new_auto_provision)


def turn_off_security_auto_provisioning_setting(client, resource_name):

    new_auto_provision = AutoProvision('Off')
    return client.create(resource_name, new_auto_provision)


# --------------------------------------------------------------------------------------------
# Discovered Security Solutions
# --------------------------------------------------------------------------------------------

def list_security_discovered_security_solutions(client):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    return client.discovered_security_solutions.list()


def get_security_discovered_security_solution(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    return client.discovered_security_solutions.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# External Security Solutions
# --------------------------------------------------------------------------------------------

def list_security_external_security_solutions(client):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    return client.external_security_solutions.list()


def get_security_external_security_solution(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    return client.external_security_solutions.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Just in Time network access policies
# --------------------------------------------------------------------------------------------

def list_security_jit_network_access_policies(client, resource_group_name=None, location=None):

    if location:
        client.config.asc_location = location

        if resource_group_name:
            return client.list_by_resource_group_and_region(resource_group_name)

        return client.list_by_region()

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def get_security_jit_network_access_policy(client, location, resource_name, resource_group_name):

    client.config.asc_location = location

    return client.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Security Locations
# --------------------------------------------------------------------------------------------

def list_security_locations(client):

    return client.list()


def get_security_location(client, resource_name):

    client.config.asc_location = resource_name

    return client.get()


# --------------------------------------------------------------------------------------------
# Security Pricings
# --------------------------------------------------------------------------------------------

def list_security_pricings(client):

    return client.list()


def get_security_pricing(client, resource_name, resource_group_name=None):

    if resource_group_name:
        return client.get_resource_group_pricing(resource_group_name, resource_name)

    return client.get_subscription_pricing(resource_name)


def create_security_pricing(client, resource_name, tier, resource_group_name=None):

    if resource_group_name:
        return client.create_or_update_resource_group_pricing(resource_group_name, resource_name, tier)

    return client.update_subscription_pricing(resource_name, tier)


# --------------------------------------------------------------------------------------------
# Security Topology
# --------------------------------------------------------------------------------------------


def list_security_topology(client):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    return client.topology.list()


def get_security_topology(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client.config.asc_location = loc.name

    return client.topology.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Security Topology
# --------------------------------------------------------------------------------------------


def list_security_workspace_settings(client):

    return client.list()


def get_security_workspace_setting(client, resource_name):

    return client.get(resource_name)


def create_security_workspace_setting(client, resource_name, target_workspace):

    scope = '/subscriptions/' + client.config.subscription_id
    return client.create(resource_name, target_workspace, scope)


def delete_security_workspace_setting(client, resource_name):

    client.delete(resource_name)


# --------------------------------------------------------------------------------------------
# Security ATP
# --------------------------------------------------------------------------------------------

def get_atp_setting(client, resource_group_name, storage_account_name):

    return client.get(_construct_resource_id(client, resource_group_name, storage_account_name))


def update_atp_setting(client, resource_group_name, storage_account_name, is_enabled):

    return client.create(_construct_resource_id(client, resource_group_name, storage_account_name),
                         is_enabled=is_enabled)


def _construct_resource_id(client, resource_group_name, storage_account_name):

    from msrestazure.tools import resource_id
    return resource_id(
        subscription=client.config.subscription_id,
        resource_group=resource_group_name,
        namespace='Microsoft.Storage',
        type='storageAccounts',
        name=storage_account_name)
