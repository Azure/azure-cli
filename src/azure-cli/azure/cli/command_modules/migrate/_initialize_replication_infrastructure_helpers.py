# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.command_modules.migrate._helpers import (
    send_get_request,
    get_resource_by_id,
    delete_resource,
    create_or_update_resource,
    generate_hash_for_artifact,
    APIVersion,
    ProvisioningState,
    AzLocalInstanceTypes,
    FabricInstanceTypes,
    ReplicationPolicyDetails,
    RoleDefinitionIds,
    StorageAccountProvisioningState
)
import json


def validate_required_parameters(resource_group_name,
                                 project_name,
                                 source_appliance_name,
                                 target_appliance_name):
    # Validate required parameters
    if not resource_group_name:
        raise CLIError("resource_group_name is required.")
    if not project_name:
        raise CLIError("project_name is required.")
    if not source_appliance_name:
        raise CLIError("source_appliance_name is required.")
    if not target_appliance_name:
        raise CLIError("target_appliance_name is required.")


def get_and_validate_resource_group(cmd, subscription_id,
                                    resource_group_name):
    """Get and validate that the resource group exists."""
    rg_uri = (f"/subscriptions/{subscription_id}/"
              f"resourceGroups/{resource_group_name}")
    resource_group = get_resource_by_id(
        cmd, rg_uri, APIVersion.Microsoft_Resources.value)
    if not resource_group:
        raise CLIError(
            f"Resource group '{resource_group_name}' does not exist "
            f"in the subscription.")
    print(f"Selected Resource Group: '{resource_group_name}'")
    return rg_uri


def get_migrate_project(cmd, project_uri, project_name):
    """Get and validate migrate project."""
    migrate_project = get_resource_by_id(
        cmd, project_uri, APIVersion.Microsoft_Migrate.value)
    if not migrate_project:
        raise CLIError(f"Migrate project '{project_name}' not found.")

    if (migrate_project.get('properties', {}).get('provisioningState') !=
            ProvisioningState.Succeeded.value):
        raise CLIError(
            f"Migrate project '{project_name}' is not in a valid state.")

    return migrate_project


def get_data_replication_solution(cmd, project_uri):
    """Get Data Replication Service Solution."""
    amh_solution_name = (
        "Servers-Migration-ServerMigration_DataReplication")
    amh_solution_uri = f"{project_uri}/solutions/{amh_solution_name}"
    amh_solution = get_resource_by_id(
        cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value)
    if not amh_solution:
        raise CLIError(
            f"No Data Replication Service Solution "
            f"'{amh_solution_name}' found.")
    return amh_solution


def get_discovery_solution(cmd, project_uri):
    """Get Discovery Solution."""
    discovery_solution_name = "Servers-Discovery-ServerDiscovery"
    discovery_solution_uri = (
        f"{project_uri}/solutions/{discovery_solution_name}")
    discovery_solution = get_resource_by_id(
        cmd, discovery_solution_uri, APIVersion.Microsoft_Migrate.value)
    if not discovery_solution:
        raise CLIError(
            f"Server Discovery Solution '{discovery_solution_name}' "
            f"not found.")
    return discovery_solution


def get_and_setup_replication_vault(cmd, amh_solution, rg_uri):
    """Get and setup replication vault with managed identity."""
    # Validate Replication Vault
    vault_id = (amh_solution.get('properties', {})
                .get('details', {})
                .get('extendedDetails', {})
                .get('vaultId'))
    if not vault_id:
        raise CLIError(
            "No Replication Vault found. Please verify your "
            "Azure Migrate project setup.")

    replication_vault_name = vault_id.split("/")[8]
    vault_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication/"
        f"replicationVaults/{replication_vault_name}")
    replication_vault = get_resource_by_id(
        cmd, vault_uri, APIVersion.Microsoft_DataReplication.value)
    if not replication_vault:
        raise CLIError(
            f"No Replication Vault '{replication_vault_name}' found.")

    # Check if vault has managed identity, if not, enable it
    vault_identity = (
        replication_vault.get('identity') or
        replication_vault.get('properties', {}).get('identity')
    )
    if not vault_identity or not vault_identity.get('principalId'):
        print(
            f"Replication vault '{replication_vault_name}' does not "
            f"have a managed identity. "
            "Enabling system-assigned identity..."
        )

        # Update vault to enable system-assigned managed identity
        vault_update_body = {
            "identity": {
                "type": "SystemAssigned"
            }
        }

        replication_vault = create_or_update_resource(
            cmd, vault_uri, APIVersion.Microsoft_DataReplication.value,
            vault_update_body
        )

        # Wait for identity to be created
        time.sleep(30)

        # Refresh vault to get the identity
        replication_vault = get_resource_by_id(
            cmd, vault_uri, APIVersion.Microsoft_DataReplication.value)
        vault_identity = (
            replication_vault.get('identity') or
            replication_vault.get('properties', {}).get('identity')
        )

        if not vault_identity or not vault_identity.get('principalId'):
            raise CLIError(
                f"Failed to enable managed identity for replication "
                f"vault '{replication_vault_name}'")

        print(
            f"✓ Enabled system-assigned managed identity. "
            f"Principal ID: {vault_identity.get('principalId')}"
        )
    else:
        print(
            f"✓ Replication vault has managed identity. "
            f"Principal ID: {vault_identity.get('principalId')}")

    return replication_vault, replication_vault_name


def _store_appliance_site_mapping(app_map, appliance_name, site_id):
    """Store appliance name to site ID mapping in both lowercase and
    original case."""
    app_map[appliance_name.lower()] = site_id
    app_map[appliance_name] = site_id


def _process_v3_dict_map(app_map, app_map_v3):
    """Process V3 appliance map in dict format."""
    for appliance_name_key, site_info in app_map_v3.items():
        if isinstance(site_info, dict) and 'SiteId' in site_info:
            _store_appliance_site_mapping(
                app_map, appliance_name_key, site_info['SiteId'])
        elif isinstance(site_info, str):
            _store_appliance_site_mapping(
                app_map, appliance_name_key, site_info)


def _process_v3_list_item(app_map, item):
    """Process a single item from V3 appliance list."""
    if not isinstance(item, dict):
        return

    # Check if it has ApplianceName/SiteId structure
    if 'ApplianceName' in item and 'SiteId' in item:
        _store_appliance_site_mapping(
            app_map, item['ApplianceName'], item['SiteId'])
        return

    # Or it might be a single key-value pair
    for key, value in item.items():
        if isinstance(value, dict) and 'SiteId' in value:
            _store_appliance_site_mapping(
                app_map, key, value['SiteId'])
        elif isinstance(value, str):
            _store_appliance_site_mapping(app_map, key, value)


def _process_v3_appliance_map(app_map, app_map_v3):
    """Process V3 appliance map data structure."""
    if isinstance(app_map_v3, dict):
        _process_v3_dict_map(app_map, app_map_v3)
    elif isinstance(app_map_v3, list):
        for item in app_map_v3:
            _process_v3_list_item(app_map, item)


def parse_appliance_mappings(discovery_solution):
    """Parse appliance name to site ID mappings from discovery solution."""
    app_map = {}
    extended_details = (discovery_solution.get('properties', {})
                        .get('details', {})
                        .get('extendedDetails', {}))

    # Process applianceNameToSiteIdMapV2
    if 'applianceNameToSiteIdMapV2' in extended_details:
        try:
            app_map_v2 = json.loads(
                extended_details['applianceNameToSiteIdMapV2'])
            if isinstance(app_map_v2, list):
                for item in app_map_v2:
                    if (isinstance(item, dict) and
                            'ApplianceName' in item and
                            'SiteId' in item):
                        # Store both lowercase and original case
                        app_map[item['ApplianceName'].lower()] = (
                            item['SiteId'])
                        app_map[item['ApplianceName']] = item['SiteId']
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            get_logger(__name__).warning(
                "Failed to parse applianceNameToSiteIdMapV2: %s", str(e))

    # Process applianceNameToSiteIdMapV3
    if 'applianceNameToSiteIdMapV3' in extended_details:
        try:
            app_map_v3 = json.loads(
                extended_details['applianceNameToSiteIdMapV3'])
            _process_v3_appliance_map(app_map, app_map_v3)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            get_logger(__name__).warning(
                "Failed to parse applianceNameToSiteIdMapV3: %s", str(e))

    if not app_map:
        raise CLIError(
            "Server Discovery Solution missing Appliance Details. "
            "Invalid Solution.")

    return app_map


def validate_and_get_site_ids(app_map, source_appliance_name,
                              target_appliance_name):
    """Validate appliance names and get their site IDs."""
    # Validate SourceApplianceName & TargetApplianceName - try both
    # original and lowercase
    source_site_id = (app_map.get(source_appliance_name) or
                      app_map.get(source_appliance_name.lower()))
    target_site_id = (app_map.get(target_appliance_name) or
                      app_map.get(target_appliance_name.lower()))

    if not source_site_id:
        # Provide helpful error message with available appliances
        # (filter out duplicates)
        available_appliances = list(set(k for k in app_map
                                        if k not in app_map or
                                        not k.islower()))
        if not available_appliances:
            # If all keys are lowercase, show them
            available_appliances = list(set(app_map.keys()))
        raise CLIError(
            f"Source appliance '{source_appliance_name}' not in "
            f"discovery solution. "
            f"Available appliances: {','.join(available_appliances)}"
        )
    if not target_site_id:
        # Provide helpful error message with available appliances
        # (filter out duplicates)
        available_appliances = list(set(k for k in app_map
                                        if k not in app_map or
                                        not k.islower()))
        if not available_appliances:
            # If all keys are lowercase, show them
            available_appliances = list(set(app_map.keys()))
        raise CLIError(
            f"Target appliance '{target_appliance_name}' not in "
            f"discovery solution. "
            f"Available appliances: {','.join(available_appliances)}"
        )

    return source_site_id, target_site_id


def determine_instance_types(source_site_id, target_site_id,
                             source_appliance_name,
                             target_appliance_name):
    """Determine instance types based on site IDs."""
    hyperv_site_pattern = "/Microsoft.OffAzure/HyperVSites/"
    vmware_site_pattern = "/Microsoft.OffAzure/VMwareSites/"

    if (hyperv_site_pattern in source_site_id and
            hyperv_site_pattern in target_site_id):
        instance_type = AzLocalInstanceTypes.HyperVToAzLocal.value
        fabric_instance_type = FabricInstanceTypes.HyperVInstance.value
    elif (vmware_site_pattern in source_site_id and
          hyperv_site_pattern in target_site_id):
        instance_type = AzLocalInstanceTypes.VMwareToAzLocal.value
        fabric_instance_type = FabricInstanceTypes.VMwareInstance.value
    else:
        src_type = (
            'VMware' if vmware_site_pattern in source_site_id
            else 'HyperV' if hyperv_site_pattern in source_site_id
            else 'Unknown'
        )
        tgt_type = (
            'VMware' if vmware_site_pattern in target_site_id
            else 'HyperV' if hyperv_site_pattern in target_site_id
            else 'Unknown'
        )
        raise CLIError(
            f"Error matching source '{source_appliance_name}' and target "
            f"'{target_appliance_name}' appliances. Source is {src_type}, "
            f"Target is {tgt_type}"
        )

    return instance_type, fabric_instance_type


def find_fabric(all_fabrics, appliance_name, fabric_instance_type,
                amh_solution, is_source=True):
    """Find and validate a fabric for the given appliance."""
    logger = get_logger(__name__)
    fabric = None
    fabric_candidates = []

    for candidate in all_fabrics:
        props = candidate.get('properties', {})
        custom_props = props.get('customProperties', {})
        fabric_name = candidate.get('name', '')

        # Check if this fabric matches our criteria
        is_succeeded = (props.get('provisioningState') ==
                        ProvisioningState.Succeeded.value)

        # Check solution ID match - handle case differences and trailing
        # slashes
        fabric_solution_id = (custom_props.get('migrationSolutionId', '')
                              .rstrip('/'))
        expected_solution_id = amh_solution.get('id', '').rstrip('/')
        is_correct_solution = (fabric_solution_id.lower() ==
                               expected_solution_id.lower())

        is_correct_instance = (custom_props.get('instanceType') ==
                               fabric_instance_type)

        # Check if fabric name contains appliance name or vice versa
        name_matches = (
            fabric_name.lower().startswith(appliance_name.lower()) or
            appliance_name.lower() in fabric_name.lower() or
            fabric_name.lower() in appliance_name.lower() or
            f"{appliance_name.lower()}-" in fabric_name.lower()
        )

        # Collect potential candidates even if they don't fully match
        if custom_props.get('instanceType') == fabric_instance_type:
            fabric_candidates.append({
                'name': fabric_name,
                'state': props.get('provisioningState'),
                'solution_match': is_correct_solution,
                'name_match': name_matches
            })

        if is_succeeded and is_correct_instance and name_matches:
            # If solution doesn't match, log warning but still consider it
            if not is_correct_solution:
                logger.warning(
                    "Fabric '%s' matches name and type but has "
                    "different solution ID", fabric_name)
            fabric = candidate
            break

    if not fabric:
        appliance_type_label = "source" if is_source else "target"
        error_msg = (
            f"Couldn't find connected {appliance_type_label} appliance "
            f"'{appliance_name}'.\n")

        if fabric_candidates:
            error_msg += (
                f"Found {len(fabric_candidates)} fabric(s) with "
                f"matching type '{fabric_instance_type}': \n")
            for candidate in fabric_candidates:
                error_msg += (
                    f" - {candidate['name']} "
                    f"(state: {candidate['state']}, "
                    f"solution_match: {candidate['solution_match']}, "
                    f"name_match: {candidate['name_match']})\n")
            error_msg += "\nPlease verify:\n"
            error_msg += "1. The appliance name matches exactly\n"
            error_msg += "2. The fabric is in 'Succeeded' state\n"
            error_msg += (
                "3. The fabric belongs to the correct migration solution")
        else:
            error_msg += (
                f"No fabrics found with instance type "
                f"'{fabric_instance_type}'.\n")
            error_msg += "\nThis usually means:\n"
            error_msg += (
                f"1. The {appliance_type_label} appliance "
                f"'{appliance_name}' is not properly configured\n")
            if (fabric_instance_type ==
                    FabricInstanceTypes.VMwareInstance.value):
                appliance_type = 'VMware'
            elif (fabric_instance_type ==
                    FabricInstanceTypes.HyperVInstance.value):
                appliance_type = 'HyperV'
            else:
                appliance_type = 'Azure Local'
            error_msg += (
                f"2. The appliance type doesn't match "
                f"(expecting {appliance_type})\n")
            error_msg += (
                "3. The fabric creation is still in progress - "
                "wait a few minutes and retry")

            if all_fabrics:
                error_msg += "\n\nAvailable fabrics in resource group:\n"
                for fab in all_fabrics:
                    props = fab.get('properties', {})
                    custom_props = props.get('customProperties', {})
                    error_msg += (
                        f" - {fab.get('name')} "
                        f"(type: {custom_props.get('instanceType')})\n")

        raise CLIError(error_msg)

    return fabric


def get_fabric_agent(cmd, replication_fabrics_uri, fabric, appliance_name,
                     fabric_instance_type):
    """Get and validate fabric agent (DRA) for the given fabric."""
    fabric_name = fabric.get('name')
    dras_uri = (
        f"{replication_fabrics_uri}/{fabric_name}"
        f"/fabricAgents?api-version="
        f"{APIVersion.Microsoft_DataReplication.value}"
    )
    dras_response = send_get_request(cmd, dras_uri)
    dras = dras_response.json().get('value', [])

    dra = None
    for candidate in dras:
        props = candidate.get('properties', {})
        custom_props = props.get('customProperties', {})
        if (props.get('machineName') == appliance_name and
                custom_props.get('instanceType') == fabric_instance_type and
                bool(props.get('isResponsive'))):
            dra = candidate
            break

    if not dra:
        raise CLIError(
            f"The appliance '{appliance_name}' is in a disconnected state."
        )

    return dra


def setup_replication_policy(cmd,
                             rg_uri,
                             replication_vault_name,
                             instance_type):
    """Setup or validate replication policy."""
    policy_name = f"{replication_vault_name}{instance_type}policy"
    policy_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults"
        f"/{replication_vault_name}/replicationPolicies/{policy_name}"
    )

    # Try to get existing policy, handle not found gracefully
    try:
        policy = get_resource_by_id(
            cmd, policy_uri, APIVersion.Microsoft_DataReplication.value
        )
    except CLIError as e:
        error_str = str(e)
        if ("ResourceNotFound" in error_str or "404" in error_str or
                "Not Found" in error_str):
            # Policy doesn't exist, this is expected for new setups
            print(f"Policy '{policy_name}' does not exist, will create it.")
            policy = None
        else:
            # Some other error occurred, re-raise it
            raise

    # Handle existing policy states
    if policy:
        provisioning_state = (
            policy
            .get('properties', {})
            .get('provisioningState')
        )

        # Wait for creating/updating to complete
        if provisioning_state in [ProvisioningState.Creating.value,
                                  ProvisioningState.Updating.value]:
            print(
                f"Policy '{policy_name}' found in Provisioning State "
                f"'{provisioning_state}'."
            )
            for i in range(20):
                time.sleep(30)
                policy = get_resource_by_id(
                    cmd, policy_uri,
                    APIVersion.Microsoft_DataReplication.value
                )
                if policy:
                    provisioning_state = (
                        policy.get('properties', {}).get('provisioningState')
                    )
                    if provisioning_state not in [
                            ProvisioningState.Creating.value,
                            ProvisioningState.Updating.value]:
                        break

        # Remove policy if in bad state
        if provisioning_state in [ProvisioningState.Canceled.value,
                                  ProvisioningState.Failed.value]:
            print(
                f"Policy '{policy_name}' found in unusable state "
                f"'{provisioning_state}'. Removing..."
            )
            delete_resource(
                cmd, policy_uri, APIVersion.Microsoft_DataReplication.value
            )
            time.sleep(30)
            policy = None

    # Create policy if needed
    if not policy or (
            policy and
            policy.get('properties', {}).get('provisioningState') ==
            ProvisioningState.Deleted.value):
        print(f"Creating Policy '{policy_name}'...")

        recoveryPoint = (
            ReplicationPolicyDetails.RecoveryPointHistoryInMinutes
        )
        crashConsistentFreq = (
            ReplicationPolicyDetails.CrashConsistentFrequencyInMinutes
        )
        appConsistentFreq = (
            ReplicationPolicyDetails.AppConsistentFrequencyInMinutes
        )

        policy_body = {
            "properties": {
                "customProperties": {
                    "instanceType": instance_type,
                    "recoveryPointHistoryInMinutes": recoveryPoint,
                    "crashConsistentFrequencyInMinutes": crashConsistentFreq,
                    "appConsistentFrequencyInMinutes": appConsistentFreq
                }
            }
        }

        create_or_update_resource(
            cmd,
            policy_uri,
            APIVersion.Microsoft_DataReplication.value,
            policy_body,
        )

        # Wait for policy creation
        for i in range(20):
            time.sleep(30)
            try:
                policy = get_resource_by_id(
                    cmd, policy_uri,
                    APIVersion.Microsoft_DataReplication.value
                )
            except Exception as poll_error:
                # During creation, it might still return 404 initially
                if ("ResourceNotFound" in str(poll_error) or
                        "404" in str(poll_error)):
                    print(f"Policy creation in progress... ({i + 1}/20)")
                    continue
                raise

            if policy:
                provisioning_state = (
                    policy.get('properties', {}).get('provisioningState')
                )
                print(f"Policy state: {provisioning_state}")
                if provisioning_state in [
                        ProvisioningState.Succeeded.value,
                        ProvisioningState.Failed.value,
                        ProvisioningState.Canceled.value,
                        ProvisioningState.Deleted.value]:
                    break

    if not policy or (
            policy.get('properties', {}).get('provisioningState') !=
            ProvisioningState.Succeeded.value):
        raise CLIError(f"Policy '{policy_name}' is not in Succeeded state.")

    return policy


def setup_cache_storage_account(cmd, rg_uri, amh_solution,
                                cache_storage_account_id,
                                source_site_id, source_appliance_name,
                                migrate_project, project_name):
    """Setup or validate cache storage account."""
    logger = get_logger(__name__)

    amh_stored_storage_account_id = (
        amh_solution.get('properties', {})
        .get('details', {})
        .get('extendedDetails', {})
        .get('replicationStorageAccountId')
    )
    cache_storage_account = None

    if amh_stored_storage_account_id:
        # Check existing storage account
        storage_account_name = amh_stored_storage_account_id.split("/")[8]
        storage_uri = (
            f"{rg_uri}/providers/Microsoft.Storage/storageAccounts"
            f"/{storage_account_name}"
        )
        storage_account = get_resource_by_id(
            cmd, storage_uri, APIVersion.Microsoft_Storage.value
        )

        if storage_account and (
            storage_account
            .get('properties', {})
            .get('provisioningState') ==
                StorageAccountProvisioningState.Succeeded.value
        ):
            cache_storage_account = storage_account
            if (cache_storage_account_id and
                    cache_storage_account['id'] !=
                    cache_storage_account_id):
                warning_msg = (
                    f"A Cache Storage Account '{storage_account_name}' is "
                    f"already linked. "
                )
                warning_msg += "Ignoring provided -cache_storage_account_id."
                logger.warning(warning_msg)

    # Use user-provided storage account if no existing one
    if not cache_storage_account and cache_storage_account_id:
        storage_account_name = cache_storage_account_id.split("/")[8].lower()
        storage_uri = (
            f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/"
            f"{storage_account_name}"
        )
        user_storage_account = get_resource_by_id(
            cmd, storage_uri, APIVersion.Microsoft_Storage.value
        )

        if user_storage_account and (
            user_storage_account
            .get('properties', {})
            .get('provisioningState') ==
                StorageAccountProvisioningState.Succeeded.value
        ):
            cache_storage_account = user_storage_account
        else:
            error_msg = (
                f"Cache Storage Account with Id "
                f"'{cache_storage_account_id}' not found "
            )
            error_msg += "or not in valid state."
            raise CLIError(error_msg)

    # Create new storage account if needed
    if not cache_storage_account:
        artifact = f"{source_site_id}/{source_appliance_name}"
        suffix_hash = generate_hash_for_artifact(artifact)
        if len(suffix_hash) > 14:
            suffix_hash = suffix_hash[:14]
        storage_account_name = f"migratersa{suffix_hash}"

        print(f"Creating Cache Storage Account '{storage_account_name}'...")

        storage_body = {
            "location": migrate_project.get('location'),
            "tags": {"Migrate Project": project_name},
            "sku": {"name": "Standard_LRS"},
            "kind": "StorageV2",
            "properties": {
                "allowBlobPublicAccess": False,
                "allowCrossTenantReplication": True,
                "minimumTlsVersion": "TLS1_2",
                "networkAcls": {
                    "defaultAction": "Allow"
                },
                "encryption": {
                    "services": {
                        "blob": {"enabled": True},
                        "file": {"enabled": True}
                    },
                    "keySource": "Microsoft.Storage"
                },
                "accessTier": "Hot"
            }
        }

        storage_uri = (
            f"{rg_uri}/providers/Microsoft.Storage/storageAccounts"
            f"/{storage_account_name}"
        )
        cache_storage_account = create_or_update_resource(
            cmd,
            storage_uri,
            APIVersion.Microsoft_Storage.value,
            storage_body
        )

        for _ in range(20):
            time.sleep(30)
            cache_storage_account = get_resource_by_id(
                cmd,
                storage_uri,
                APIVersion.Microsoft_Storage.value
            )
            if cache_storage_account and (
                cache_storage_account
                .get('properties', {})
                .get('provisioningState') ==
                    StorageAccountProvisioningState.Succeeded.value
            ):
                break

    if not cache_storage_account or (
        cache_storage_account
        .get('properties', {})
        .get('provisioningState') !=
            StorageAccountProvisioningState.Succeeded.value
    ):
        raise CLIError("Failed to setup Cache Storage Account.")

    return cache_storage_account


def verify_storage_account_network_settings(cmd,
                                            rg_uri,
                                            cache_storage_account):
    """Verify and update storage account network settings if needed."""
    storage_account_id = cache_storage_account['id']

    # Verify storage account network settings
    print("Verifying storage account network configuration...")
    network_acls = (
        cache_storage_account.get('properties', {}).get('networkAcls', {})
    )
    default_action = network_acls.get('defaultAction', 'Allow')

    if default_action != 'Allow':
        print(
            f"WARNING: Storage account network defaultAction is "
            f"'{default_action}'. "
            "This may cause permission issues."
        )
        print(
            "Updating storage account to allow public network access..."
        )

        # Update storage account to allow public access
        storage_account_name = storage_account_id.split("/")[-1]
        storage_uri = (
            f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/"
            f"{storage_account_name}"
        )

        update_body = {
            "properties": {
                "networkAcls": {
                    "defaultAction": "Allow"
                }
            }
        }

        create_or_update_resource(
            cmd, storage_uri, APIVersion.Microsoft_Storage.value,
            update_body
        )

        # Wait for network update to propagate
        time.sleep(30)


def get_all_fabrics(cmd, rg_uri, resource_group_name,
                    source_appliance_name,
                    target_appliance_name, project_name):
    """Get all replication fabrics in the resource group."""
    replication_fabrics_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication/replicationFabrics"
    )
    fabrics_uri = (
        f"{replication_fabrics_uri}?api-version="
        f"{APIVersion.Microsoft_DataReplication.value}"
    )
    fabrics_response = send_get_request(cmd, fabrics_uri)
    all_fabrics = fabrics_response.json().get('value', [])

    # If no fabrics exist at all, provide helpful message
    if not all_fabrics:
        raise CLIError(
            f"No replication fabrics found in resource group "
            f"'{resource_group_name}'. "
            f"Please ensure that: \n"
            f"1. The source appliance '{source_appliance_name}' is deployed "
            f"and connected\n"
            f"2. The target appliance '{target_appliance_name}' is deployed "
            f"and connected\n"
            f"3. Both appliances are registered with the Azure Migrate "
            f"project '{project_name}'"
        )

    return all_fabrics, replication_fabrics_uri


def _get_role_name(role_def_id):
    """Get role name from role definition ID."""
    return ("Contributor" if role_def_id == RoleDefinitionIds.ContributorId
            else "Storage Blob Data Contributor")


def _assign_role_to_principal(auth_client, storage_account_id,
                              subscription_id,
                              principal_id, role_def_id,
                              principal_type_name):
    """Assign a role to a principal if not already assigned."""
    from uuid import uuid4
    from azure.mgmt.authorization.models import (
        RoleAssignmentCreateParameters, PrincipalType
    )

    role_name = _get_role_name(role_def_id)

    # Check if assignment exists
    assignments = auth_client.role_assignments.list_for_scope(
        scope=storage_account_id,
        filter=f"principalId eq '{principal_id}'"
    )

    roles = [a.role_definition_id.endswith(role_def_id) for a in assignments]
    has_role = any(roles)

    if not has_role:
        role_assignment_params = RoleAssignmentCreateParameters(
            role_definition_id=(
                f"/subscriptions/{subscription_id}/providers"
                f"/Microsoft.Authorization/roleDefinitions/{role_def_id}"
            ),
            principal_id=principal_id,
            principal_type=PrincipalType.SERVICE_PRINCIPAL
        )
        auth_client.role_assignments.create(
            scope=storage_account_id,
            role_assignment_name=str(uuid4()),
            parameters=role_assignment_params
        )
        print(
            f"  ✓ Created {role_name} role for {principal_type_name} "
            f"{principal_id[:8]}..."
        )
        return f"{principal_id[:8]} - {role_name}", False
    print(
        f"  ✓ {role_name} role already exists for {principal_type_name} "
        f"{principal_id[:8]}"
    )
    return f"{principal_id[:8]} - {role_name} (existing)", True


def _verify_role_assignments(auth_client, storage_account_id,
                             expected_principal_ids):
    """Verify that role assignments were created successfully."""
    print("Verifying role assignments...")
    all_assignments = list(
        auth_client.role_assignments.list_for_scope(
            scope=storage_account_id
        )
    )
    verified_principals = set()

    for assignment in all_assignments:
        principal_id = assignment.principal_id
        if principal_id in expected_principal_ids:
            verified_principals.add(principal_id)
            role_id = assignment.role_definition_id.split('/')[-1]
            role_display = _get_role_name(role_id)
            print(
                f"  ✓ Verified {role_display} for principal "
                f"{principal_id[:8]}"
            )

    missing_principals = set(expected_principal_ids) - verified_principals
    if missing_principals:
        print(
            f"WARNING: {len(missing_principals)} principal(s) missing role "
            f"assignments: "
        )
        for principal in missing_principals:
            print(f" - {principal}")


def grant_storage_permissions(cmd, storage_account_id, source_dra,
                              target_dra, replication_vault, subscription_id):
    """Grant role assignments for DRAs and vault identity to storage acct."""
    from azure.mgmt.authorization import AuthorizationManagementClient

    # Get role assignment client
    from azure.cli.core.commands.client_factory import (
        get_mgmt_service_client
    )
    auth_client = get_mgmt_service_client(
        cmd.cli_ctx, AuthorizationManagementClient
    )

    source_dra_object_id = (
        source_dra.get('properties', {})
        .get('resourceAccessIdentity', {}).get('objectId')
    )
    target_dra_object_id = (
        target_dra.get('properties', {})
        .get('resourceAccessIdentity', {}).get('objectId')
    )

    # Get vault identity from either root level or properties level
    vault_identity = (
        replication_vault.get('identity') or
        replication_vault.get('properties', {}).get('identity')
    )
    vault_identity_id = (
        vault_identity.get('principalId') if vault_identity else None
    )

    print("Granting permissions to the storage account...")
    print(f"  Source DRA Principal ID: {source_dra_object_id}")
    print(f"  Target DRA Principal ID: {target_dra_object_id}")
    print(f"  Vault Identity Principal ID: {vault_identity_id}")

    successful_assignments = []
    failed_assignments = []

    # Create role assignments for source and target DRAs
    for object_id in [source_dra_object_id, target_dra_object_id]:
        if object_id:
            for role_def_id in [
                RoleDefinitionIds.ContributorId,
                RoleDefinitionIds.StorageBlobDataContributorId
            ]:
                try:
                    assignment_msg, _ = _assign_role_to_principal(
                        auth_client, storage_account_id, subscription_id,
                        object_id, role_def_id, "DRA"
                    )
                    successful_assignments.append(assignment_msg)
                except CLIError as e:
                    role_name = _get_role_name(role_def_id)
                    error_msg = f"{object_id[:8]} - {role_name}: {str(e)}"
                    failed_assignments.append(error_msg)

    # Grant vault identity permissions if exists
    if vault_identity_id:
        for role_def_id in [RoleDefinitionIds.ContributorId,
                            RoleDefinitionIds.StorageBlobDataContributorId]:
            try:
                assignment_msg, _ = _assign_role_to_principal(
                    auth_client, storage_account_id, subscription_id,
                    vault_identity_id, role_def_id, "vault"
                )
                successful_assignments.append(assignment_msg)
            except CLIError as e:
                role_name = _get_role_name(role_def_id)
                error_msg = f"{vault_identity_id[:8]} - {role_name}: {str(e)}"
                failed_assignments.append(error_msg)

    # Report role assignment status
    print("\nRole Assignment Summary:")
    print(f"  Successful: {len(successful_assignments)}")
    if failed_assignments:
        print(f"  Failed: {len(failed_assignments)}")
        for failure in failed_assignments:
            print(f" - {failure}")

    # If there are failures, raise an error
    if failed_assignments:
        raise CLIError(
            f"Failed to create {len(failed_assignments)} role "
            f"assignment(s). "
            "The storage account may not have proper permissions."
        )

    # Add a wait after role assignments to ensure propagation
    time.sleep(120)

    # Verify role assignments were successful
    expected_principal_ids = [
        source_dra_object_id, target_dra_object_id, vault_identity_id
    ]
    _verify_role_assignments(
        auth_client, storage_account_id, expected_principal_ids
    )


def update_amh_solution_storage(cmd,
                                project_uri,
                                amh_solution,
                                storage_account_id):
    """Update AMH solution with storage account ID if needed."""
    amh_solution_uri = (
        f"{project_uri}/solutions/"
        f"Servers-Migration-ServerMigration_DataReplication"
    )

    if (amh_solution
        .get('properties', {})
        .get('details', {})
        .get('extendedDetails', {})
            .get('replicationStorageAccountId')) != storage_account_id:
        extended_details = (amh_solution
                            .get('properties', {})
                            .get('details', {})
                            .get('extendedDetails', {}))
        extended_details['replicationStorageAccountId'] = (
            storage_account_id
        )

        solution_body = {
            "properties": {
                "details": {
                    "extendedDetails": extended_details
                }
            }
        }

        create_or_update_resource(
            cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value,
            solution_body
        )

        # Wait for the AMH solution update to fully propagate
        time.sleep(60)

    return amh_solution_uri


def get_or_check_existing_extension(cmd, extension_uri,
                                    replication_extension_name,
                                    storage_account_id):
    """Get existing extension and check if it's in a good state."""
    # Try to get existing extension, handle not found gracefully
    try:
        replication_extension = get_resource_by_id(
            cmd, extension_uri, APIVersion.Microsoft_DataReplication.value
        )
    except CLIError as e:
        error_str = str(e)
        if ("ResourceNotFound" in error_str or "404" in error_str or
                "Not Found" in error_str):
            # Extension doesn't exist, this is expected for new setups
            print(
                f"Extension '{replication_extension_name}' does not exist, "
                f"will create it."
            )
            return None, False
        # Some other error occurred, re-raise it
        raise

    # Check if extension exists and is in good state
    if replication_extension:
        existing_state = (
            replication_extension.get('properties', {})
            .get('provisioningState')
        )
        existing_storage_id = (replication_extension
                               .get('properties', {})
                               .get('customProperties', {})
                               .get('storageAccountId'))

        print(
            f"Found existing extension '{replication_extension_name}' in "
            f"state: {existing_state}"
        )

        # If it's succeeded with the correct storage account, we're done
        if (existing_state == ProvisioningState.Succeeded.value and
                existing_storage_id == storage_account_id):
            print(
                "Replication Extension already exists with correct "
                "configuration."
            )
            print("Successfully initialized replication infrastructure")
            return None, True  # Signal that we're done

        # If it's in a bad state or has wrong storage account, delete it
        if (existing_state in [ProvisioningState.Failed.value,
                               ProvisioningState.Canceled.value] or
                existing_storage_id != storage_account_id):
            print(f"Removing existing extension (state: {existing_state})")
            delete_resource(
                cmd, extension_uri, APIVersion.Microsoft_DataReplication.value
            )
            time.sleep(120)
            return None, False

    return replication_extension, False


def verify_extension_prerequisites(cmd, rg_uri, replication_vault_name,
                                   instance_type, storage_account_id,
                                   amh_solution_uri, source_fabric_id,
                                   target_fabric_id):
    """Verify all prerequisites before creating extension."""
    print("\nVerifying prerequisites before creating extension...")

    # 1. Verify policy is succeeded
    policy_name = f"{replication_vault_name}{instance_type}policy"
    policy_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults"
        f"/{replication_vault_name}/replicationPolicies/{policy_name}"
    )
    policy_check = get_resource_by_id(
        cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
    if (policy_check.get('properties', {}).get('provisioningState') !=
            ProvisioningState.Succeeded.value):
        raise CLIError(
            "Policy is not in Succeeded state: {}".format(
                policy_check.get('properties', {}).get('provisioningState')))

    # 2. Verify storage account is succeeded
    storage_account_name = storage_account_id.split("/")[-1]
    storage_uri = (
        f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/"
        f"{storage_account_name}")
    storage_check = get_resource_by_id(
        cmd, storage_uri, APIVersion.Microsoft_Storage.value)
    if (storage_check
            .get('properties', {})
            .get('provisioningState') !=
            StorageAccountProvisioningState.Succeeded.value):
        raise CLIError(
            "Storage account is not in Succeeded state: {}".format(
                storage_check.get('properties', {}).get(
                    'provisioningState')))

    # 3. Verify AMH solution has storage account
    solution_check = get_resource_by_id(
        cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value)
    if (solution_check
            .get('properties', {})
            .get('details', {})
            .get('extendedDetails', {})
            .get('replicationStorageAccountId') != storage_account_id):
        raise CLIError(
            "AMH solution doesn't have the correct storage account ID")

    # 4. Verify fabrics are responsive
    source_fabric_check = get_resource_by_id(
        cmd, source_fabric_id, APIVersion.Microsoft_DataReplication.value)
    if (source_fabric_check.get('properties', {}).get('provisioningState') !=
            ProvisioningState.Succeeded.value):
        raise CLIError("Source fabric is not in Succeeded state")

    target_fabric_check = get_resource_by_id(
        cmd, target_fabric_id, APIVersion.Microsoft_DataReplication.value)
    if (target_fabric_check.get('properties', {}).get('provisioningState') !=
            ProvisioningState.Succeeded.value):
        raise CLIError("Target fabric is not in Succeeded state")

    print("All prerequisites verified successfully!")
    time.sleep(30)


def list_existing_extensions(cmd, rg_uri, replication_vault_name):
    """List existing extensions for informational purposes."""
    existing_extensions_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication"
        f"/replicationVaults/{replication_vault_name}"
        f"/replicationExtensions"
        f"?api-version={APIVersion.Microsoft_DataReplication.value}"
    )
    try:
        existing_extensions_response = send_get_request(
            cmd, existing_extensions_uri)
        existing_extensions = (
            existing_extensions_response.json().get('value', []))
        if existing_extensions:
            print(f"Found {len(existing_extensions)} existing "
                  f"extension(s): ")
            for ext in existing_extensions:
                ext_name = ext.get('name')
                ext_state = (
                    ext.get('properties', {}).get('provisioningState'))
                ext_type = (ext.get('properties', {})
                            .get('customProperties', {})
                            .get('instanceType'))
                print(f" - {ext_name}: state={ext_state}, "
                      f"type={ext_type}")
        else:
            print("No existing extensions found")
    except CLIError as list_error:
        # If listing fails, it might mean no extensions exist at all
        print(f"Could not list extensions (this is normal for new "
              f"projects): {str(list_error)}")


def build_extension_body(instance_type, source_fabric_id,
                         target_fabric_id, storage_account_id):
    """Build the extension body based on instance type."""
    print("\n=== Creating extension for replication infrastructure ===")
    print(f"Instance Type: {instance_type}")
    print(f"Source Fabric ID: {source_fabric_id}")
    print(f"Target Fabric ID: {target_fabric_id}")
    print(f"Storage Account ID: {storage_account_id}")

    # Build the extension body with properties in the exact order from
    # the working API call
    if instance_type == AzLocalInstanceTypes.VMwareToAzLocal.value:
        # Match exact property order from working call for VMware
        extension_body = {
            "properties": {
                "customProperties": {
                    "azStackHciFabricArmId": target_fabric_id,
                    "storageAccountId": storage_account_id,
                    "storageAccountSasSecretName": None,
                    "instanceType": instance_type,
                    "vmwareFabricArmId": source_fabric_id
                }
            }
        }
    elif instance_type == AzLocalInstanceTypes.HyperVToAzLocal.value:
        # For HyperV, use similar order but with hyperVFabricArmId
        extension_body = {
            "properties": {
                "customProperties": {
                    "azStackHciFabricArmId": target_fabric_id,
                    "storageAccountId": storage_account_id,
                    "storageAccountSasSecretName": None,
                    "instanceType": instance_type,
                    "hyperVFabricArmId": source_fabric_id
                }
            }
        }
    else:
        raise CLIError(f"Unsupported instance type: {instance_type}")

    # Debug: Print the exact body being sent
    body_str = json.dumps(extension_body, indent=2)
    print(f"Extension body being sent: \n{body_str}")

    return extension_body


def _wait_for_extension_creation(cmd, extension_uri):
    """Wait for extension creation to complete."""
    for i in range(20):
        time.sleep(30)
        try:
            api_version = APIVersion.Microsoft_DataReplication.value
            replication_extension = get_resource_by_id(
                cmd, extension_uri, api_version)
            if replication_extension:
                ext_state = replication_extension.get(
                    'properties', {}).get('provisioningState')
                print(f"Extension state: {ext_state}")
                if ext_state in [ProvisioningState.Succeeded.value,
                                 ProvisioningState.Failed.value,
                                 ProvisioningState.Canceled.value]:
                    break
        except CLIError:
            print(f"Waiting for extension... ({i + 1}/20)")


def _handle_extension_creation_error(cmd, extension_uri, create_error):
    """Handle errors during extension creation."""
    error_str = str(create_error)
    print(f"Error during extension creation: {error_str}")

    # Check if extension was created despite the error
    time.sleep(30)
    try:
        api_version = APIVersion.Microsoft_DataReplication.value
        replication_extension = get_resource_by_id(
            cmd, extension_uri, api_version)
        if replication_extension:
            print(
                f"Extension exists despite error, "
                f"state: {replication_extension.get('properties', {}).get(
                    'provisioningState')}"
            )
    except CLIError:
        replication_extension = None

    if not replication_extension:
        raise CLIError(
            f"Failed to create replication extension: "
            f"{str(create_error)}") from create_error


def create_replication_extension(cmd, extension_uri, extension_body):
    """Create the replication extension and wait for it to complete."""
    try:
        result = create_or_update_resource(
            cmd, extension_uri,
            APIVersion.Microsoft_DataReplication.value,
            extension_body)
        if result:
            print("Extension creation initiated successfully")
            # Wait for the extension to be created
            print("Waiting for extension creation to complete...")
            _wait_for_extension_creation(cmd, extension_uri)
    except CLIError as create_error:
        _handle_extension_creation_error(cmd, extension_uri, create_error)


def setup_replication_extension(cmd, rg_uri, replication_vault_name,
                                source_fabric, target_fabric,
                                instance_type, storage_account_id,
                                amh_solution_uri, pass_thru):
    """Setup replication extension - main orchestration function."""
    # Setup Replication Extension
    source_fabric_id = source_fabric['id']
    target_fabric_id = target_fabric['id']
    source_fabric_short_name = source_fabric_id.split('/')[-1]
    target_fabric_short_name = target_fabric_id.split('/')[-1]
    replication_extension_name = (
        f"{source_fabric_short_name}-{target_fabric_short_name}-"
        f"MigReplicationExtn")

    extension_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication/"
        f"replicationVaults/{replication_vault_name}/"
        f"replicationExtensions/{replication_extension_name}"
    )

    # Get or check existing extension
    replication_extension, is_complete = get_or_check_existing_extension(
        cmd, extension_uri, replication_extension_name,
        storage_account_id
    )

    if is_complete:
        return True if pass_thru else None

    # Verify prerequisites
    verify_extension_prerequisites(
        cmd, rg_uri, replication_vault_name, instance_type,
        storage_account_id, amh_solution_uri, source_fabric_id,
        target_fabric_id
    )

    # Create extension if needed
    if not replication_extension:
        print(
            f"Creating Replication Extension "
            f"'{replication_extension_name}'...")

        # List existing extensions for context
        list_existing_extensions(cmd, rg_uri, replication_vault_name)

        # Build extension body
        extension_body = build_extension_body(
            instance_type, source_fabric_id, target_fabric_id,
            storage_account_id
        )

        # Create the extension
        create_replication_extension(cmd, extension_uri, extension_body)

    print("Successfully initialized replication infrastructure")
    return True if pass_thru else None


def setup_project_and_solutions(cmd,
                                subscription_id,
                                resource_group_name,
                                project_name):
    """Setup and retrieve project and solutions."""
    rg_uri = get_and_validate_resource_group(
        cmd, subscription_id, resource_group_name)
    project_uri = (f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/"
                   f"{project_name}")
    migrate_project = get_migrate_project(cmd, project_uri, project_name)
    amh_solution = get_data_replication_solution(cmd, project_uri)
    discovery_solution = get_discovery_solution(cmd, project_uri)

    return (
        rg_uri,
        project_uri,
        migrate_project,
        amh_solution,
        discovery_solution
    )


def setup_appliances_and_types(discovery_solution,
                               source_appliance_name,
                               target_appliance_name):
    """Parse appliance mappings and determine instance types."""
    app_map = parse_appliance_mappings(discovery_solution)
    source_site_id, target_site_id = validate_and_get_site_ids(
        app_map, source_appliance_name, target_appliance_name
    )
    result = determine_instance_types(
        source_site_id, target_site_id, source_appliance_name,
        target_appliance_name
    )
    instance_type, fabric_instance_type = result
    return (
        source_site_id,
        instance_type,
        fabric_instance_type
    )


def setup_fabrics_and_dras(cmd, rg_uri, resource_group_name,
                           source_appliance_name, target_appliance_name,
                           project_name, fabric_instance_type,
                           amh_solution):
    """Get all fabrics and set up DRAs."""
    all_fabrics, replication_fabrics_uri = get_all_fabrics(
        cmd, rg_uri, resource_group_name, source_appliance_name,
        target_appliance_name, project_name
    )

    source_fabric = find_fabric(
        all_fabrics, source_appliance_name, fabric_instance_type,
        amh_solution, is_source=True)
    target_fabric_instance_type = FabricInstanceTypes.AzLocalInstance.value
    target_fabric = find_fabric(
        all_fabrics, target_appliance_name, target_fabric_instance_type,
        amh_solution, is_source=False)

    source_dra = get_fabric_agent(
        cmd, replication_fabrics_uri, source_fabric,
        source_appliance_name, fabric_instance_type)
    target_dra = get_fabric_agent(
        cmd, replication_fabrics_uri, target_fabric,
        target_appliance_name, target_fabric_instance_type)

    return source_fabric, target_fabric, source_dra, target_dra


def setup_storage_and_permissions(cmd, rg_uri, amh_solution,
                                  cache_storage_account_id, source_site_id,
                                  source_appliance_name, migrate_project,
                                  project_name, source_dra, target_dra,
                                  replication_vault, subscription_id):
    """Setup storage account and grant permissions."""
    cache_storage_account = setup_cache_storage_account(
        cmd, rg_uri, amh_solution, cache_storage_account_id,
        source_site_id, source_appliance_name, migrate_project, project_name
    )

    storage_account_id = cache_storage_account['id']
    verify_storage_account_network_settings(
        cmd, rg_uri, cache_storage_account)
    grant_storage_permissions(
        cmd, storage_account_id, source_dra, target_dra,
        replication_vault, subscription_id)

    return storage_account_id


def initialize_infrastructure_components(cmd, rg_uri, project_uri,
                                         amh_solution,
                                         replication_vault_name,
                                         instance_type, migrate_project,
                                         project_name,
                                         cache_storage_account_id,
                                         source_site_id,
                                         source_appliance_name, source_dra,
                                         target_dra, replication_vault,
                                         subscription_id):
    """Initialize policy, storage, and AMH solution."""
    setup_replication_policy(
        cmd, rg_uri, replication_vault_name, instance_type)

    storage_account_id = setup_storage_and_permissions(
        cmd, rg_uri, amh_solution, cache_storage_account_id,
        source_site_id, source_appliance_name, migrate_project, project_name,
        source_dra, target_dra, replication_vault, subscription_id
    )

    amh_solution_uri = update_amh_solution_storage(
        cmd, project_uri, amh_solution, storage_account_id)

    return storage_account_id, amh_solution_uri


def execute_replication_infrastructure_setup(cmd, subscription_id,
                                             resource_group_name,
                                             project_name,
                                             source_appliance_name,
                                             target_appliance_name,
                                             cache_storage_account_id,
                                             pass_thru):
    """Execute the complete replication infrastructure setup workflow."""
    # Setup project and solutions
    (rg_uri, project_uri, migrate_project, amh_solution,
     discovery_solution) = setup_project_and_solutions(
        cmd, subscription_id, resource_group_name, project_name
    )

    # Get and setup replication vault
    (replication_vault,
     replication_vault_name) = get_and_setup_replication_vault(
        cmd, amh_solution, rg_uri)

    # Setup appliances and determine types
    (source_site_id, instance_type,
     fabric_instance_type) = setup_appliances_and_types(
        discovery_solution, source_appliance_name, target_appliance_name
    )

    # Setup fabrics and DRAs
    (source_fabric, target_fabric, source_dra,
     target_dra) = setup_fabrics_and_dras(
        cmd, rg_uri, resource_group_name, source_appliance_name,
        target_appliance_name, project_name, fabric_instance_type,
        amh_solution
    )

    # Initialize policy, storage, and AMH solution
    (storage_account_id,
     amh_solution_uri) = initialize_infrastructure_components(
        cmd, rg_uri, project_uri, amh_solution, replication_vault_name,
        instance_type, migrate_project, project_name,
        cache_storage_account_id, source_site_id, source_appliance_name,
        source_dra, target_dra, replication_vault, subscription_id
    )

    # Setup Replication Extension
    return setup_replication_extension(
        cmd, rg_uri, replication_vault_name, source_fabric,
        target_fabric, instance_type, storage_account_id,
        amh_solution_uri, pass_thru
    )
