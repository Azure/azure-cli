from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.migrate._helpers import (
    send_get_request,
    get_resource_by_id,
    create_or_update_resource,
    APIVersion,
    ProvisioningState,
    AzLocalInstanceTypes,
    FabricInstanceTypes,
    SiteTypes,
    VMNicSelection,
    validate_arm_id_format,
    IdFormats
)
import re
import json
from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def _process_v2_dict(extended_details, app_map):
    try:
        app_map_v2 = json.loads(
            extended_details['applianceNameToSiteIdMapV2'])
        if isinstance(app_map_v2, list):
            for item in app_map_v2:
                if (isinstance(item, dict) and
                        'ApplianceName' in item and
                        'SiteId' in item):
                    # Store both lowercase and original case
                    app_map[item['ApplianceName'].lower()] = item['SiteId']
                    app_map[item['ApplianceName']] = item['SiteId']
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return app_map


def _process_v3_dict_map(app_map_v3, app_map):
    for appliance_name_key, site_info in app_map_v3.items():
        if isinstance(site_info, dict) and 'SiteId' in site_info:
            app_map[appliance_name_key.lower()] = site_info['SiteId']
            app_map[appliance_name_key] = site_info['SiteId']
        elif isinstance(site_info, str):
            app_map[appliance_name_key.lower()] = site_info
            app_map[appliance_name_key] = site_info
    return app_map


def _process_v3_dict_list(app_map_v3, app_map):
    # V3 might also be in list format
    for item in app_map_v3:
        if isinstance(item, dict):
            # Check if it has ApplianceName/SiteId structure
            if 'ApplianceName' in item and 'SiteId' in item:
                app_map[item['ApplianceName'].lower()] = item['SiteId']
                app_map[item['ApplianceName']] = item['SiteId']
            else:
                # Or it might be a single key-value pair
                for key, value in item.items():
                    if isinstance(value, dict) and 'SiteId' in value:
                        app_map[key.lower()] = value['SiteId']
                        app_map[key] = value['SiteId']
                    elif isinstance(value, str):
                        app_map[key.lower()] = value
                        app_map[key] = value
    return app_map


def _process_v3_dict(extended_details, app_map):
    try:
        app_map_v3 = json.loads(extended_details['applianceNameToSiteIdMapV3'])
        if isinstance(app_map_v3, dict):
            app_map = _process_v3_dict_map(app_map_v3, app_map)
        elif isinstance(app_map_v3, list):
            app_map = _process_v3_dict_list(app_map_v3, app_map)
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return app_map


def validate_server_parameters(
        cmd,
        machine_id,
        machine_index,
        project_name,
        resource_group_name,
        source_appliance_name,
        subscription_id):
    # Validate that either machine_id or machine_index is provided
    if not machine_id and not machine_index:
        raise CLIError(
            "Either machine_id or machine_index must be provided.")
    if machine_id and machine_index:
        raise CLIError(
            "Only one of machine_id or machine_index should be "
            "provided, not both.")

    if not subscription_id:
        subscription_id = get_subscription_id(cmd.cli_ctx)

    if machine_index:
        if not project_name:
            raise CLIError(
                "project_name is required when using machine_index.")
        if not resource_group_name:
            raise CLIError(
                "resource_group_name is required when using "
                "machine_index.")

        if not isinstance(machine_index, int) or machine_index < 1:
            raise CLIError(
                "machine_index must be a positive integer "
                "(1-based index).")

        rg_uri = (
            f"/subscriptions/{subscription_id}/"
            f"resourceGroups/{resource_group_name}")
        discovery_solution_name = "Servers-Discovery-ServerDiscovery"
        discovery_solution_uri = (
            f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects"
            f"/{project_name}/solutions/{discovery_solution_name}"
        )
        discovery_solution = get_resource_by_id(
            cmd, discovery_solution_uri, APIVersion.Microsoft_Migrate.value)

        if not discovery_solution:
            raise CLIError(
                f"Server Discovery Solution '{discovery_solution_name}' "
                f"not in project '{project_name}'.")

        # Get appliance mapping to determine site type
        app_map = {}
        extended_details = (
            discovery_solution.get('properties', {})
            .get('details', {})
            .get('extendedDetails', {}))

        # Process applianceNameToSiteIdMapV2 and V3
        if 'applianceNameToSiteIdMapV2' in extended_details:
            app_map = _process_v2_dict(extended_details, app_map)

        if 'applianceNameToSiteIdMapV3' in extended_details:
            app_map = _process_v3_dict(extended_details, app_map)

        # Get source site ID - try both original and lowercase
        source_site_id = (
            app_map.get(source_appliance_name) or
            app_map.get(source_appliance_name.lower()))
        if not source_site_id:
            raise CLIError(
                f"Source appliance '{source_appliance_name}' "
                f"not in discovery solution.")

        # Determine site type from source site ID
        hyperv_site_pattern = "/Microsoft.OffAzure/HyperVSites/"
        vmware_site_pattern = "/Microsoft.OffAzure/VMwareSites/"

        if hyperv_site_pattern in source_site_id:
            site_name = source_site_id.split('/')[-1]
            machines_uri = (
                f"{rg_uri}/providers/Microsoft.OffAzure/"
                f"HyperVSites/{site_name}/machines")
        elif vmware_site_pattern in source_site_id:
            site_name = source_site_id.split('/')[-1]
            machines_uri = (
                f"{rg_uri}/providers/Microsoft.OffAzure/"
                f"VMwareSites/{site_name}/machines")
        else:
            raise CLIError(
                f"Unable to determine site type for source appliance "
                f"'{source_appliance_name}'.")

        # Get all machines from the site
        request_uri = (
            f"{cmd.cli_ctx.cloud.endpoints.resource_manager}"
            f"{machines_uri}?api-version={APIVersion.Microsoft_OffAzure.value}"
        )

        response = send_get_request(cmd, request_uri)
        machines_data = response.json()
        machines = machines_data.get('value', [])

        # Fetch all pages if there are more
        while machines_data.get('nextLink'):
            response = send_get_request(cmd, machines_data.get('nextLink'))
            machines_data = response.json()
            machines.extend(machines_data.get('value', []))

        # Check if the index is valid
        if machine_index > len(machines):
            raise CLIError(
                f"Invalid machine_index {machine_index}. "
                f"Only {len(machines)} machines found in site '{site_name}'.")

        # Get the machine at the specified index (convert 1-based to 0-based)
        selected_machine = machines[machine_index - 1]
        machine_id = selected_machine.get('id')
    return rg_uri


def validate_required_parameters(machine_id,
                                 target_storage_path_id,
                                 target_resource_group_id,
                                 target_vm_name,
                                 source_appliance_name,
                                 target_appliance_name,
                                 disk_to_include,
                                 nic_to_include,
                                 target_virtual_switch_id,
                                 os_disk_id,
                                 is_dynamic_memory_enabled):
    # Validate required parameters
    if not machine_id:
        raise CLIError("machine_id could not be determined.")
    if not target_storage_path_id:
        raise CLIError("target_storage_path_id is required.")
    if not target_resource_group_id:
        raise CLIError("target_resource_group_id is required.")
    if not target_vm_name:
        raise CLIError("target_vm_name is required.")
    if not source_appliance_name:
        raise CLIError("source_appliance_name is required.")
    if not target_appliance_name:
        raise CLIError("target_appliance_name is required.")

    # Validate parameter set requirements
    is_power_user_mode = (disk_to_include is not None or
                          nic_to_include is not None)
    is_default_user_mode = (target_virtual_switch_id is not None or
                            os_disk_id is not None)

    if is_power_user_mode and is_default_user_mode:
        raise CLIError(
            "Cannot mix default user mode parameters "
            "(target_virtual_switch_id, os_disk_id) with power user mode "
            "parameters (disk_to_include, nic_to_include).")

    if is_power_user_mode:
        # Power user mode validation
        if not disk_to_include:
            raise CLIError(
                "disk_to_include is required when using power user mode.")
        if not nic_to_include:
            raise CLIError(
                "nic_to_include is required when using power user mode.")
    else:
        # Default user mode validation
        if not target_virtual_switch_id:
            raise CLIError(
                "target_virtual_switch_id is required when using "
                "default user mode.")
        if not os_disk_id:
            raise CLIError(
                "os_disk_id is required when using default user mode.")

    is_dynamic_ram_enabled = None
    if is_dynamic_memory_enabled:
        if is_dynamic_memory_enabled not in ['true', 'false']:
            raise CLIError(
                "is_dynamic_memory_enabled must be either "
                "'true' or 'false'.")
        is_dynamic_ram_enabled = is_dynamic_memory_enabled == 'true'
    return is_dynamic_ram_enabled, is_power_user_mode


def validate_ARM_id_formats(machine_id,
                            target_storage_path_id,
                            target_resource_group_id,
                            target_virtual_switch_id,
                            target_test_virtual_switch_id):
    # Validate ARM ID formats
    if not validate_arm_id_format(
            machine_id,
            IdFormats.MachineArmIdTemplate):
        raise CLIError(
            f"Invalid -machine_id '{machine_id}'. "
            f"A valid machine ARM ID should follow the format "
            f"'{IdFormats.MachineArmIdTemplate}'.")

    if not validate_arm_id_format(
            target_storage_path_id,
            IdFormats.StoragePathArmIdTemplate):
        raise CLIError(
            f"Invalid -target_storage_path_id "
            f"'{target_storage_path_id}'. "
            f"A valid storage path ARM ID should follow the format "
            f"'{IdFormats.StoragePathArmIdTemplate}'.")

    if not validate_arm_id_format(
            target_resource_group_id,
            IdFormats.ResourceGroupArmIdTemplate):
        raise CLIError(
            f"Invalid -target_resource_group_id "
            f"'{target_resource_group_id}'. "
            f"A valid resource group ARM ID should follow the format "
            f"'{IdFormats.ResourceGroupArmIdTemplate}'.")

    if (target_virtual_switch_id and
            not validate_arm_id_format(
                target_virtual_switch_id,
                IdFormats.LogicalNetworkArmIdTemplate)):
        raise CLIError(
            f"Invalid -target_virtual_switch_id "
            f"'{target_virtual_switch_id}'. "
            f"A valid logical network ARM ID should follow the format "
            f"'{IdFormats.LogicalNetworkArmIdTemplate}'.")

    if (target_test_virtual_switch_id and
            not validate_arm_id_format(
                target_test_virtual_switch_id,
                IdFormats.LogicalNetworkArmIdTemplate)):
        raise CLIError(
            f"Invalid -target_test_virtual_switch_id "
            f"'{target_test_virtual_switch_id}'. "
            f"A valid logical network ARM ID should follow the format "
            f"'{IdFormats.LogicalNetworkArmIdTemplate}'.")

    machine_id_parts = machine_id.split("/")
    if len(machine_id_parts) < 11:
        raise CLIError(f"Invalid machine ARM ID format: '{machine_id}'")

    resource_group_name = machine_id_parts[4]
    site_type = machine_id_parts[7]
    site_name = machine_id_parts[8]
    machine_name = machine_id_parts[10]

    run_as_account_id = None
    instance_type = None
    return site_type, site_name, machine_name, run_as_account_id, instance_type, resource_group_name


def process_site_type_hyperV(cmd,
                             rg_uri,
                             site_name,
                             machine_name,
                             subscription_id,
                             resource_group_name,
                             site_type):
    # Get HyperV machine
    machine_uri = (
        f"{rg_uri}/providers/Microsoft.OffAzure/HyperVSites"
        f"/{site_name}/machines/{machine_name}")
    machine = get_resource_by_id(
        cmd, machine_uri, APIVersion.Microsoft_OffAzure.value)
    if not machine:
        raise CLIError(
            f"Machine '{machine_name}' not in "
            f"resource group '{resource_group_name}' and "
            f"site '{site_name}'.")

    # Get HyperV site
    site_uri = (
        f"{rg_uri}/providers/Microsoft.OffAzure/HyperVSites/{site_name}")
    site_object = get_resource_by_id(
        cmd, site_uri, APIVersion.Microsoft_OffAzure.value)
    if not site_object:
        raise CLIError(
            f"Machine site '{site_name}' with Type '{site_type}' "
            f"not found.")

    # Get RunAsAccount
    properties = machine.get('properties', {})
    if properties.get('hostId'):
        # Machine is on a single HyperV host
        host_id_parts = properties['hostId'].split("/")
        if len(host_id_parts) < 11:
            raise CLIError(
                f"Invalid Hyper-V Host ARM ID '{properties['hostId']}'")

        host_resource_group = host_id_parts[4]
        host_site_name = host_id_parts[8]
        host_name = host_id_parts[10]

        host_uri = (
            f"/subscriptions/{subscription_id}/resourceGroups"
            f"/{host_resource_group}/providers/"
            f"Microsoft.OffAzure/HyperVSites"
            f"/{host_site_name}/hosts/{host_name}"
        )
        hyperv_host = get_resource_by_id(
            cmd, host_uri, APIVersion.Microsoft_OffAzure.value)
        if not hyperv_host:
            raise CLIError(
                f"Hyper-V host '{host_name}' not in "
                f"resource group '{host_resource_group}' and "
                f"site '{host_site_name}'.")

        run_as_account_id = (
            hyperv_host.get('properties', {}).get('runAsAccountId'))

    elif properties.get('clusterId'):
        # Machine is on a HyperV cluster
        cluster_id_parts = properties['clusterId'].split("/")
        if len(cluster_id_parts) < 11:
            raise CLIError(
                f"Invalid Hyper-V Cluster ARM ID "
                f"'{properties['clusterId']}'")

        cluster_resource_group = cluster_id_parts[4]
        cluster_site_name = cluster_id_parts[8]
        cluster_name = cluster_id_parts[10]

        cluster_uri = (
            f"/subscriptions/{subscription_id}/resourceGroups"
            f"/{cluster_resource_group}/providers/Microsoft.OffAzure"
            f"/HyperVSites/{cluster_site_name}/clusters/{cluster_name}"
        )
        hyperv_cluster = get_resource_by_id(
            cmd, cluster_uri, APIVersion.Microsoft_OffAzure.value)
        if not hyperv_cluster:
            raise CLIError(
                f"Hyper-V cluster '{cluster_name}' not in "
                f"resource group '{cluster_resource_group}' and "
                f"site '{cluster_site_name}'.")

        run_as_account_id = (
            hyperv_cluster.get('properties', {}).get('runAsAccountId'))
    return (run_as_account_id, machine, site_object,
            AzLocalInstanceTypes.HyperVToAzLocal.value)


def process_site_type_vmware(cmd,
                             rg_uri,
                             site_name,
                             machine_name,
                             subscription_id,
                             resource_group_name,
                             site_type):
    # Get VMware machine
    machine_uri = (
        f"{rg_uri}/providers/Microsoft.OffAzure/VMwareSites"
        f"/{site_name}/machines/{machine_name}")
    machine = get_resource_by_id(
        cmd, machine_uri, APIVersion.Microsoft_OffAzure.value)
    if not machine:
        raise CLIError(
            f"Machine '{machine_name}' not in "
            f"resource group '{resource_group_name}' and "
            f"site '{site_name}'.")

    # Get VMware site
    site_uri = (
        f"{rg_uri}/providers/Microsoft.OffAzure/VMwareSites/{site_name}")
    site_object = get_resource_by_id(
        cmd, site_uri, APIVersion.Microsoft_OffAzure.value)
    if not site_object:
        raise CLIError(
            f"Machine site '{site_name}' with Type '{site_type}' "
            f"not found.")

    # Get RunAsAccount
    properties = machine.get('properties', {})
    if properties.get('vCenterId'):
        vcenter_id_parts = properties['vCenterId'].split("/")
        if len(vcenter_id_parts) < 11:
            raise CLIError(
                f"Invalid VMware vCenter ARM ID "
                f"'{properties['vCenterId']}'")

        vcenter_resource_group = vcenter_id_parts[4]
        vcenter_site_name = vcenter_id_parts[8]
        vcenter_name = vcenter_id_parts[10]

        vcenter_uri = (
            f"/subscriptions/{subscription_id}/resourceGroups"
            f"/{vcenter_resource_group}/providers/Microsoft.OffAzure"
            f"/VMwareSites/{vcenter_site_name}/vCenters/{vcenter_name}"
        )
        vmware_vcenter = get_resource_by_id(
            cmd,
            vcenter_uri,
            APIVersion.Microsoft_OffAzure.value)
        if not vmware_vcenter:
            raise CLIError(
                f"VMware vCenter '{vcenter_name}' not in "
                f"resource group '{vcenter_resource_group}' and "
                f"site '{vcenter_site_name}'.")

        run_as_account_id = (
            vmware_vcenter.get('properties', {}).get('runAsAccountId'))
    return (run_as_account_id, machine, site_object,
            AzLocalInstanceTypes.VMwareToAzLocal.value)


def process_amh_solution(cmd,
                         machine,
                         site_object,
                         project_name,
                         resource_group_name,
                         machine_name,
                         rg_uri):
    # Validate the VM for replication
    machine_props = machine.get('properties', {})
    if machine_props.get('isDeleted'):
        raise CLIError(
            f"Cannot migrate machine '{machine_name}' as it is marked as "
            "deleted."
        )

    # Get project name from site
    discovery_solution_id = (
        site_object.get('properties', {}).get('discoverySolutionId', '')
    )
    if not discovery_solution_id:
        raise CLIError(
            "Unable to determine project from site. Invalid site "
            "configuration."
        )

    if not project_name:
        project_name = discovery_solution_id.split("/")[8]

    # Get the migrate project resource
    migrate_project_uri = (
        f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/"
        f"{project_name}"
    )
    migrate_project = get_resource_by_id(
        cmd, migrate_project_uri, APIVersion.Microsoft_Migrate.value
    )
    if not migrate_project:
        raise CLIError(f"Migrate project '{project_name}' not found.")

    # Get Data Replication Service (AMH solution)
    amh_solution_name = "Servers-Migration-ServerMigration_DataReplication"
    amh_solution_uri = (
        f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/"
        f"{project_name}/solutions/{amh_solution_name}"
    )
    amh_solution = get_resource_by_id(
        cmd,
        amh_solution_uri,
        APIVersion.Microsoft_Migrate.value
    )
    if not amh_solution:
        raise CLIError(
            f"No Data Replication Service Solution "
            f"'{amh_solution_name}' found in resource group "
            f"'{resource_group_name}' and project '{project_name}'. "
            "Please verify your appliance setup."
        )
    return amh_solution, migrate_project, machine_props


def process_replication_vault(cmd,
                              amh_solution,
                              resource_group_name):
    # Validate replication vault
    vault_id = (
        amh_solution.get('properties', {})
        .get('details', {})
        .get('extendedDetails', {})
        .get('vaultId')
    )
    if not vault_id:
        raise CLIError(
            "No Replication Vault found. Please verify your Azure Migrate "
            "project setup."
        )

    replication_vault_name = vault_id.split("/")[8]
    replication_vault = get_resource_by_id(
        cmd, vault_id, APIVersion.Microsoft_DataReplication.value
    )
    if not replication_vault:
        raise CLIError(
            f"No Replication Vault '{replication_vault_name}' "
            f"found in Resource Group '{resource_group_name}'. "
            "Please verify your Azure Migrate project setup."
        )

    prov_state = replication_vault.get('properties', {})
    prov_state = prov_state.get('provisioningState')
    if prov_state != ProvisioningState.Succeeded.value:
        raise CLIError(
            f"The Replication Vault '{replication_vault_name}' is not in a "
            f"valid state. "
            f"The provisioning state is '{prov_state}'. "
            "Please verify your Azure Migrate project setup."
        )
    return replication_vault_name


def process_replication_policy(cmd,
                               replication_vault_name,
                               instance_type,
                               rg_uri):
    # Validate Policy
    policy_name = f"{replication_vault_name}{instance_type}policy"
    policy_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication"
        f"/replicationVaults/{replication_vault_name}"
        f"/replicationPolicies/{policy_name}"
    )
    policy = get_resource_by_id(
        cmd, policy_uri, APIVersion.Microsoft_DataReplication.value
    )

    if not policy:
        raise CLIError(
            f"The replication policy '{policy_name}' not found. "
            "The replication infrastructure is not initialized. "
            "Run the 'az migrate local-replication-infrastructure "
            "initialize' command."
        )
    prov_state = policy.get('properties', {}).get('provisioningState')
    if prov_state != ProvisioningState.Succeeded.value:
        raise CLIError(
            f"The replication policy '{policy_name}' is not in a valid "
            f"state. "
            f"The provisioning state is '{prov_state}'. "
            "Re-run the 'az migrate local-replication-infrastructure "
            "initialize' command."
        )
    return policy_name


def _validate_appliance_map_v3(app_map, app_map_v3):
    # V3 might also be in list format
    for item in app_map_v3:
        if isinstance(item, dict):
            # Check if it has ApplianceName/SiteId structure
            if 'ApplianceName' in item and 'SiteId' in item:
                app_map[item['ApplianceName'].lower()] = item['SiteId']
                app_map[item['ApplianceName']] = item['SiteId']
            else:
                # Or it might be a single key-value pair
                for key, value in item.items():
                    if isinstance(value, dict) and 'SiteId' in value:
                        app_map[key.lower()] = value['SiteId']
                        app_map[key] = value['SiteId']
                    elif isinstance(value, str):
                        app_map[key.lower()] = value
                        app_map[key] = value
    return app_map


def process_appliance_map(cmd, rg_uri, project_name):
    # Access Discovery Solution to get appliance mapping
    discovery_solution_name = "Servers-Discovery-ServerDiscovery"
    discovery_solution_uri = (
        f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/"
        f"{project_name}/solutions/{discovery_solution_name}"
    )
    discovery_solution = get_resource_by_id(
        cmd, discovery_solution_uri, APIVersion.Microsoft_Migrate.value
    )

    if not discovery_solution:
        raise CLIError(
            f"Server Discovery Solution '{discovery_solution_name}' not "
            "found."
        )

    # Get Appliances Mapping
    app_map = {}
    extended_details = (
        discovery_solution.get('properties', {})
        .get('details', {})
        .get('extendedDetails', {})
    )

    # Process applianceNameToSiteIdMapV2
    if 'applianceNameToSiteIdMapV2' in extended_details:
        try:
            app_map_v2 = json.loads(
                extended_details['applianceNameToSiteIdMapV2']
            )
            if isinstance(app_map_v2, list):
                for item in app_map_v2:
                    is_dict = isinstance(item, dict)
                    has_keys = ('ApplianceName' in item and
                                'SiteId' in item)
                    if is_dict and has_keys:
                        app_map[item['ApplianceName'].lower()] = (
                            item['SiteId']
                        )
                        app_map[item['ApplianceName']] = item['SiteId']
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(
                "Failed to parse applianceNameToSiteIdMapV2: %s", str(e)
            )

    # Process applianceNameToSiteIdMapV3
    if 'applianceNameToSiteIdMapV3' in extended_details:
        try:
            app_map_v3 = json.loads(
                extended_details['applianceNameToSiteIdMapV3']
            )
            if isinstance(app_map_v3, dict):
                for appliance_name_key, site_info in app_map_v3.items():
                    is_dict_w_site = (isinstance(site_info, dict) and
                                      'SiteId' in site_info)
                    if is_dict_w_site:
                        app_map[appliance_name_key.lower()] = (
                            site_info['SiteId']
                        )
                        app_map[appliance_name_key] = site_info['SiteId']
                    elif isinstance(site_info, str):
                        app_map[appliance_name_key.lower()] = site_info
                        app_map[appliance_name_key] = site_info
            elif isinstance(app_map_v3, list):
                app_map = _validate_appliance_map_v3(
                    app_map, app_map_v3
                )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(
                "Failed to parse applianceNameToSiteIdMapV3: %s", str(e)
            )
    return app_map


def _validate_site_ids(app_map,
                       source_appliance_name,
                       target_appliance_name):
    source_site_id = (
        app_map.get(source_appliance_name) or
        app_map.get(source_appliance_name.lower())
    )
    target_site_id = (
        app_map.get(target_appliance_name) or
        app_map.get(target_appliance_name.lower())
    )

    if not source_site_id:
        available_appliances = list(
            set(k for k in app_map if not k.islower())
        )
        if not available_appliances:
            available_appliances = list(set(app_map.keys()))
        raise CLIError(
            f"Source appliance '{source_appliance_name}' not in "
            "discovery solution. "
            f"Available appliances: {','.join(available_appliances)}"
        )

    if not target_site_id:
        available_appliances = list(
            set(k for k in app_map if not k.islower())
        )
        if not available_appliances:
            available_appliances = list(set(app_map.keys()))
        raise CLIError(
            f"Target appliance '{target_appliance_name}' not in "
            "discovery solution. "
            f"Available appliances: {','.join(available_appliances)}"
        )
    return source_site_id, target_site_id


def _process_source_fabrics(all_fabrics,
                            source_appliance_name,
                            amh_solution,
                            fabric_instance_type):
    source_fabric = None
    source_fabric_candidates = []

    for fabric in all_fabrics:
        props = fabric.get('properties', {})
        custom_props = props.get('customProperties', {})
        fabric_name = fabric.get('name', '')
        prov_state = props.get('provisioningState')
        is_succeeded = prov_state == ProvisioningState.Succeeded.value

        fabric_solution_id = (
            custom_props.get('migrationSolutionId', '').rstrip('/')
        )
        expected_solution_id = amh_solution.get('id', '').rstrip('/')
        is_correct_solution = (
            fabric_solution_id.lower() == expected_solution_id.lower()
        )
        is_correct_instance = (
            custom_props.get('instanceType') == fabric_instance_type
        )

        name_matches = (
            fabric_name.lower().startswith(
                source_appliance_name.lower()
            ) or
            source_appliance_name.lower() in fabric_name.lower() or
            fabric_name.lower() in source_appliance_name.lower() or
            f"{source_appliance_name.lower()}-" in fabric_name.lower()
        )

        # Collect potential candidates even if they don't fully match
        if custom_props.get('instanceType') == fabric_instance_type:
            source_fabric_candidates.append({
                'name': fabric_name,
                'state': props.get('provisioningState'),
                'solution_match': is_correct_solution,
                'name_match': name_matches
            })

        if is_succeeded and is_correct_instance and name_matches:
            # If solution doesn't match, log warning but still consider it
            if not is_correct_solution:
                logger.warning(
                    "Fabric '%s' matches name and type but has different "
                    "solution ID",
                    fabric_name
                )
            source_fabric = fabric
            break
    return source_fabric, source_fabric_candidates


def _handle_no_source_fabric_error(source_appliance_name,
                                   source_fabric_candidates,
                                   fabric_instance_type,
                                   all_fabrics):
    error_msg = (
        f"Couldn't find connected source appliance "
        f"'{source_appliance_name}'.\n"
    )
    if source_fabric_candidates:
        error_msg += (
            f"Found {len(source_fabric_candidates)} fabric(s) with "
            f"matching type '{fabric_instance_type}': \n"
        )
        for candidate in source_fabric_candidates:
            error_msg += (
                f" - {candidate['name']} (state: "
                f"{candidate['state']}, "
            )
            error_msg += (
                f"solution_match: {candidate['solution_match']}, "
            )
            error_msg += f"name_match: {candidate['name_match']})\n"
        error_msg += "\nPlease verify:\n"
        error_msg += "1. The appliance name matches exactly\n"
        error_msg += "2. The fabric is in 'Succeeded' state\n"
        error_msg += (
            "3. The fabric belongs to the correct migration solution"
        )
    else:
        error_msg += (
            f"No fabrics found with instance type "
            f"'{fabric_instance_type}'.\n"
        )
        error_msg += "\nThis usually means:\n"
        error_msg += (
            f"1. The source appliance '{source_appliance_name}' is not "
            "properly configured\n"
        )
        if fabric_instance_type == FabricInstanceTypes.VMwareInstance.value:
            appliance_type = 'VMware'
        else:
            appliance_type = 'HyperV'
        error_msg += (
            f"2. The appliance type doesn't match (expecting "
            f"{appliance_type})\n"
        )
        error_msg += (
            "3. The fabric creation is still in progress - wait a few "
            "minutes and retry"
        )

        # List all available fabrics for debugging
        if all_fabrics:
            error_msg += "\n\nAvailable fabrics in resource group:\n"
            for fabric in all_fabrics:
                props = fabric.get('properties', {})
                custom_props = props.get('customProperties', {})
                error_msg += (
                    f" - {fabric.get('name')} "
                    f"(type: {custom_props.get('instanceType')})\n"
                )

    raise CLIError(error_msg)


def process_source_fabric(cmd,
                          rg_uri,
                          app_map,
                          source_appliance_name,
                          target_appliance_name,
                          amh_solution,
                          resource_group_name,
                          project_name):
    # Validate and get site IDs
    source_site_id, target_site_id = _validate_site_ids(
        app_map,
        source_appliance_name,
        target_appliance_name)

    # Determine instance types based on site IDs
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

    # Get healthy fabrics in the resource group
    fabrics_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication/"
        f"replicationFabrics"
        f"?api-version={APIVersion.Microsoft_DataReplication.value}"
    )
    fabrics_response = send_get_request(cmd, fabrics_uri)
    all_fabrics = fabrics_response.json().get('value', [])

    if not all_fabrics:
        raise CLIError(
            f"No replication fabrics found in resource group "
            f"'{resource_group_name}'. Please ensure that: \n"
            f"1. The source appliance '{source_appliance_name}' is "
            f"deployed and connected\n"
            f"2. The target appliance '{target_appliance_name}' is "
            f"deployed and connected\n"
            f"3. Both appliances are registered with the Azure Migrate "
            f"project '{project_name}'"
        )

    source_fabric, source_fabric_candidates = _process_source_fabrics(
        all_fabrics,
        source_appliance_name,
        amh_solution,
        fabric_instance_type)

    if not source_fabric:
        _handle_no_source_fabric_error(
            source_appliance_name,
            source_fabric_candidates,
            fabric_instance_type,
            all_fabrics)
    return source_fabric, fabric_instance_type, instance_type, all_fabrics


def _process_target_fabrics(all_fabrics,
                            target_appliance_name,
                            amh_solution):
    # Filter for target fabric - make matching more flexible and diagnostic
    target_fabric_instance_type = FabricInstanceTypes.AzLocalInstance.value
    target_fabric = None
    target_fabric_candidates = []

    for fabric in all_fabrics:
        props = fabric.get('properties', {})
        custom_props = props.get('customProperties', {})
        fabric_name = fabric.get('name', '')
        is_succeeded = (props.get('provisioningState') ==
                        ProvisioningState.Succeeded.value)

        fabric_solution_id = (custom_props.get('migrationSolutionId', '')
                              .rstrip('/'))
        expected_solution_id = amh_solution.get('id', '').rstrip('/')
        is_correct_solution = (fabric_solution_id.lower() ==
                               expected_solution_id.lower())
        is_correct_instance = (custom_props.get('instanceType') ==
                               target_fabric_instance_type)

        name_matches = (
            fabric_name.lower().startswith(target_appliance_name.lower()) or
            target_appliance_name.lower() in fabric_name.lower() or
            fabric_name.lower() in target_appliance_name.lower() or
            f"{target_appliance_name.lower()}-" in fabric_name.lower()
        )

        # Collect potential candidates
        if (custom_props.get('instanceType') ==
                target_fabric_instance_type):
            target_fabric_candidates.append({
                'name': fabric_name,
                'state': props.get('provisioningState'),
                'solution_match': is_correct_solution,
                'name_match': name_matches
            })

        if is_succeeded and is_correct_instance and name_matches:
            if not is_correct_solution:
                logger.warning(
                    "Fabric '%s' matches name and type but has different "
                    "solution ID", fabric_name)
            target_fabric = fabric
            break
    return target_fabric, target_fabric_candidates, \
        target_fabric_instance_type


def _handle_no_target_fabric_error(target_appliance_name,
                                   target_fabric_candidates,
                                   target_fabric_instance_type):
    # Provide more detailed error message
    error_msg = (f"Couldn't find connected target appliance "
                 f"'{target_appliance_name}'.\n")

    if target_fabric_candidates:
        error_msg += (f"Found {len(target_fabric_candidates)} fabric(s) "
                      f"with matching type "
                      f"'{target_fabric_instance_type}': \n")
        for candidate in target_fabric_candidates:
            error_msg += (f" - {candidate['name']} "
                          f"(state: {candidate['state']}, ")
            error_msg += (f"solution_match: "
                          f"{candidate['solution_match']}, "
                          f"name_match: "
                          f"{candidate['name_match']})\n")
    else:
        error_msg += (f"No fabrics found with instance type "
                      f"'{target_fabric_instance_type}'.\n")
        error_msg += "\nThis usually means:\n"
        error_msg += (f"1. The target appliance '{target_appliance_name}' "
                      f"is not properly configured for Azure Local\n")
        error_msg += ("2. The fabric creation is still in progress - wait "
                      "a few minutes and retry\n")
        error_msg += ("3. The target appliance is not connected to the "
                      "Azure Local cluster")

    raise CLIError(error_msg)


def process_target_fabric(cmd,
                          rg_uri,
                          source_fabric,
                          fabric_instance_type,
                          all_fabrics,
                          source_appliance_name,
                          target_appliance_name,
                          amh_solution):
    # Get source fabric agent (DRA)
    source_fabric_name = source_fabric.get('name')
    dras_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication"
        f"/replicationFabrics/{source_fabric_name}/fabricAgents"
        f"?api-version={APIVersion.Microsoft_DataReplication.value}"
    )
    source_dras_response = send_get_request(cmd, dras_uri)
    source_dras = source_dras_response.json().get('value', [])

    source_dra = None
    for dra in source_dras:
        props = dra.get('properties', {})
        custom_props = props.get('customProperties', {})
        if (props.get('machineName') == source_appliance_name and
                custom_props.get('instanceType') == fabric_instance_type and
                bool(props.get('isResponsive'))):
            source_dra = dra
            break

    if not source_dra:
        raise CLIError(
            f"The source appliance '{source_appliance_name}' is in a "
            f"disconnected state.")

    target_fabric, target_fabric_candidates, \
        target_fabric_instance_type = _process_target_fabrics(
            all_fabrics,
            target_appliance_name,
            amh_solution)

    if not target_fabric:
        _handle_no_target_fabric_error(
            target_appliance_name,
            target_fabric_candidates,
            target_fabric_instance_type
        )

    # Get target fabric agent (DRA)
    target_fabric_name = target_fabric.get('name')
    target_dras_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication"
        f"/replicationFabrics/{target_fabric_name}/fabricAgents"
        f"?api-version={APIVersion.Microsoft_DataReplication.value}"
    )
    target_dras_response = send_get_request(cmd, target_dras_uri)
    target_dras = target_dras_response.json().get('value', [])

    target_dra = None
    for dra in target_dras:
        props = dra.get('properties', {})
        custom_props = props.get('customProperties', {})
        if (props.get('machineName') == target_appliance_name and
                custom_props.get('instanceType') ==
                target_fabric_instance_type and
                bool(props.get('isResponsive'))):
            target_dra = dra
            break

    if not target_dra:
        raise CLIError(
            f"The target appliance '{target_appliance_name}' is in a "
            f"disconnected state.")

    return target_fabric, source_dra, target_dra


def validate_replication_extension(cmd,
                                   rg_uri,
                                   source_fabric,
                                   target_fabric,
                                   replication_vault_name):
    source_fabric_id = source_fabric['id']
    target_fabric_id = target_fabric['id']
    source_fabric_short_name = source_fabric_id.split('/')[-1]
    target_fabric_short_name = target_fabric_id.split('/')[-1]
    replication_extension_name = (
        f"{source_fabric_short_name}-{target_fabric_short_name}-"
        f"MigReplicationExtn")
    extension_uri = (
        f"{rg_uri}/providers/Microsoft.DataReplication"
        f"/replicationVaults/{replication_vault_name}"
        f"/replicationExtensions/{replication_extension_name}"
    )
    replication_extension = get_resource_by_id(
        cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)

    if not replication_extension:
        raise CLIError(
            f"The replication extension '{replication_extension_name}' "
            f"not found. Run 'az migrate local replication init' first.")

    extension_state = (replication_extension.get('properties', {})
                       .get('provisioningState'))

    if extension_state != ProvisioningState.Succeeded.value:
        raise CLIError(
            f"The replication extension '{replication_extension_name}' "
            f"is not ready. State: '{extension_state}'")
    return replication_extension_name


def get_ARC_resource_bridge_info(target_fabric, migrate_project):
    target_fabric_custom_props = (
        target_fabric.get('properties', {}).get('customProperties', {}))
    target_cluster_id = (
        target_fabric_custom_props.get('cluster', {})
        .get('resourceName', ''))

    if not target_cluster_id:
        target_cluster_id = (target_fabric_custom_props
                             .get('azStackHciClusterName', ''))

    if not target_cluster_id:
        target_cluster_id = (target_fabric_custom_props
                             .get('clusterName', ''))

    # Extract custom location from target fabric
    custom_location_id = (target_fabric_custom_props
                          .get('customLocationRegion', ''))

    if not custom_location_id:
        custom_location_id = (target_fabric_custom_props
                              .get('customLocationId', ''))

    if not custom_location_id:
        if target_cluster_id:
            cluster_parts = target_cluster_id.split('/')
            if len(cluster_parts) >= 5:
                custom_location_region = (
                    migrate_project.get('location', 'eastus'))
                custom_location_id = (
                    f"/subscriptions/{cluster_parts[2]}/"
                    f"resourceGroups/{cluster_parts[4]}/providers/"
                    f"Microsoft.ExtendedLocation/customLocations/"
                    f"{cluster_parts[-1]}-customLocation"
                )
            else:
                custom_location_region = (
                    migrate_project.get('location', 'eastus'))
        else:
            custom_location_region = (
                migrate_project.get('location', 'eastus'))
    else:
        custom_location_region = migrate_project.get('location', 'eastus')
    return custom_location_id, custom_location_region, target_cluster_id


def validate_target_VM_name(target_vm_name):
    if len(target_vm_name) == 0 or len(target_vm_name) > 64:
        raise CLIError(
            "The target virtual machine name must be between 1 and 64 "
            "characters long.")

    vm_name_pattern = r"^[^_\W][a-zA-Z0-9\-]{0,63}(?<![-._])$"

    if not re.match(vm_name_pattern, target_vm_name):
        raise CLIError(
            "The target VM name must begin with a letter or number, "
            "contain only letters, numbers, or hyphens, and not end with "
            "'.' or '-'.")


def construct_disk_and_nic_mapping(is_power_user_mode,
                                   disk_to_include,
                                   nic_to_include,
                                   machine_props,
                                   site_type,
                                   os_disk_id,
                                   target_virtual_switch_id,
                                   target_test_virtual_switch_id):
    disks = []
    nics = []

    if is_power_user_mode:
        if not disk_to_include or len(disk_to_include) == 0:
            raise CLIError(
                "At least one disk must be included for replication.")

        # Validate that exactly one disk is marked as OS disk
        os_disks = [d for d in disk_to_include if d.get('isOSDisk', False)]
        if len(os_disks) != 1:
            raise CLIError(
                "Exactly one disk must be designated as the OS disk.")

        # Process disks
        for i, disk in enumerate(disk_to_include):
            disk_obj = {
                'diskId': disk.get('diskId'),
                'diskSizeGb': disk.get('diskSizeGb'),
                'diskFileFormat': disk.get('diskFileFormat', 'VHDX'),
                'isDynamic': disk.get('isDynamic', True),
                'isOSDisk': disk.get('isOSDisk', False)
            }
            disks.append(disk_obj)

        # Process NICs
        print(f"DEBUG: Processing {len(nic_to_include)} NICs in "
              f"power user mode")
        for i, nic in enumerate(nic_to_include):
            print(f"DEBUG: Processing NIC {i + 1}: ID={nic.get('nicId')}, "
                  f"Target={nic.get('targetNetworkId')}")
            nic_obj = {
                'nicId': nic.get('nicId'),
                'targetNetworkId': nic.get('targetNetworkId'),
                'testNetworkId': nic.get('testNetworkId',
                                         nic.get('targetNetworkId')),
                'selectionTypeForFailover': nic.get(
                    'selectionTypeForFailover',
                    VMNicSelection.SelectedByUser.value)
            }
            nics.append(nic_obj)
    else:
        machine_disks = machine_props.get('disks', [])
        machine_nics = machine_props.get('networkAdapters', [])

        # Find OS disk
        for i, disk in enumerate(machine_disks):
            if site_type == SiteTypes.HyperVSites.value:
                disk_id = disk.get('instanceId')
                disk_size = disk.get('maxSizeInBytes', 0)
            else:  # VMware
                disk_id = disk.get('uuid')
                disk_size = disk.get('maxSizeInBytes', 0)

            is_os_disk = disk_id == os_disk_id
            # Round up to GB
            disk_size_gb = (disk_size + (1024 ** 3 - 1)) // (1024 ** 3)
            disk_obj = {
                'diskId': disk_id,
                'diskSizeGb': disk_size_gb,
                'diskFileFormat': 'VHDX',
                'isDynamic': True,
                'isOSDisk': is_os_disk
            }
            disks.append(disk_obj)

        for i, nic in enumerate(machine_nics):
            nic_id = nic.get('nicId')
            test_network_id = (target_test_virtual_switch_id or
                               target_virtual_switch_id)

            nic_obj = {
                'nicId': nic_id,
                'targetNetworkId': target_virtual_switch_id,
                'testNetworkId': test_network_id,
                'selectionTypeForFailover': VMNicSelection.SelectedByUser.value
            }
            nics.append(nic_obj)
    return disks, nics


def _handle_configuration_validation(cmd,
                                     subscription_id,
                                     resource_group_name,
                                     replication_vault_name,
                                     machine_name,
                                     machine_props,
                                     target_vm_cpu_core,
                                     target_vm_ram,
                                     site_type):
    protected_item_name = machine_name
    protected_item_uri = (
        f"subscriptions/{subscription_id}/resourceGroups"
        f"/{resource_group_name}/providers/Microsoft.DataReplication"
        f"/replicationVaults/{replication_vault_name}"
        f"/protectedItems/{protected_item_name}"
    )

    try:
        existing_item = get_resource_by_id(
            cmd,
            protected_item_uri,
            APIVersion.Microsoft_DataReplication.value)
        if existing_item:
            raise CLIError(
                f"A replication already exists for machine "
                f"'{machine_name}'. "
                "Remove it first before creating a new one.")
    except (CLIError, ValueError, KeyError, TypeError) as e:
        # Check if it's a 404 Not Found error - that's expected and fine
        error_str = str(e)
        if ("ResourceNotFound" in error_str or "404" in error_str or
                "Not Found" in error_str):
            existing_item = None
        else:
            # Some other error occurred, re-raise it
            raise

    # Determine Hyper-V generation
    if site_type == SiteTypes.HyperVSites.value:
        hyperv_generation = machine_props.get('generation', '1')
        is_source_dynamic_memory = machine_props.get(
            'isDynamicMemoryEnabled', False)
    else:  # VMware
        firmware = machine_props.get('firmware', 'BIOS')
        hyperv_generation = '2' if firmware != 'BIOS' else '1'
        is_source_dynamic_memory = False

    # Determine target CPU and RAM
    source_cpu_cores = machine_props.get('numberOfProcessorCore', 2)
    source_memory_mb = machine_props.get('allocatedMemoryInMB', 4096)

    if not target_vm_cpu_core:
        target_vm_cpu_core = source_cpu_cores

    if not target_vm_ram:
        target_vm_ram = max(source_memory_mb, 512)  # Minimum 512MB

    if target_vm_cpu_core < 1 or target_vm_cpu_core > 240:
        raise CLIError("Target VM CPU cores must be between 1 and 240.")

    if hyperv_generation == '1':
        if target_vm_ram < 512 or target_vm_ram > 1048576:  # 1TB
            raise CLIError(
                "Target VM RAM must be between 512 MB and 1048576 MB "
                "(1 TB) for Generation 1 VMs.")
    else:
        if target_vm_ram < 32 or target_vm_ram > 12582912:  # 12TB
            raise CLIError(
                "Target VM RAM must be between 32 MB and 12582912 MB "
                "(12 TB) for Generation 2 VMs.")

    return (hyperv_generation, source_cpu_cores, is_source_dynamic_memory,
            source_memory_mb, protected_item_uri)


def _build_custom_properties(instance_type, custom_location_id,
                             custom_location_region,
                             machine_id, disks, nics, target_vm_name,
                             target_resource_group_id,
                             target_storage_path_id, hyperv_generation,
                             target_vm_cpu_core,
                             source_cpu_cores, is_dynamic_ram_enabled,
                             is_source_dynamic_memory,
                             source_memory_mb, target_vm_ram, source_dra,
                             target_dra,
                             run_as_account_id, target_cluster_id):
    """Build custom properties for protected item creation."""
    return {
        "instanceType": instance_type,
        "targetArcClusterCustomLocationId": custom_location_id or "",
        "customLocationRegion": custom_location_region,
        "fabricDiscoveryMachineId": machine_id,
        "disksToInclude": [
            {
                "diskId": disk["diskId"],
                "diskSizeGB": disk["diskSizeGb"],
                "diskFileFormat": disk["diskFileFormat"],
                "isOsDisk": disk["isOSDisk"],
                "isDynamic": disk["isDynamic"],
                "diskPhysicalSectorSize": 512
            }
            for disk in disks
        ],
        "targetVmName": target_vm_name,
        "targetResourceGroupId": target_resource_group_id,
        "storageContainerId": target_storage_path_id,
        "hyperVGeneration": hyperv_generation,
        "targetCpuCores": target_vm_cpu_core,
        "sourceCpuCores": source_cpu_cores,
        "isDynamicRam": (is_dynamic_ram_enabled
                         if is_dynamic_ram_enabled is not None
                         else is_source_dynamic_memory),
        "sourceMemoryInMegaBytes": float(source_memory_mb),
        "targetMemoryInMegaBytes": int(target_vm_ram),
        "nicsToInclude": [
            {
                "nicId": nic["nicId"],
                "selectionTypeForFailover": nic["selectionTypeForFailover"],
                "targetNetworkId": nic["targetNetworkId"],
                "testNetworkId": nic.get("testNetworkId", "")
            }
            for nic in nics
        ],
        "dynamicMemoryConfig": {
            "maximumMemoryInMegaBytes": 1048576,  # Max for Gen 1
            "minimumMemoryInMegaBytes": 512,       # Min for Gen 1
            "targetMemoryBufferPercentage": 20
        },
        "sourceFabricAgentName": source_dra.get('name'),
        "targetFabricAgentName": target_dra.get('name'),
        "runAsAccountId": run_as_account_id,
        "targetHCIClusterId": target_cluster_id
    }


# pylint: disable=too-many-locals
def create_protected_item(cmd,
                          subscription_id,
                          resource_group_name,
                          replication_vault_name,
                          machine_name,
                          machine_props,
                          target_vm_cpu_core,
                          target_vm_ram,
                          custom_location_id,
                          custom_location_region,
                          site_type,
                          instance_type,
                          disks,
                          nics,
                          target_vm_name,
                          target_resource_group_id,
                          target_storage_path_id,
                          is_dynamic_ram_enabled,
                          source_dra,
                          target_dra,
                          policy_name,
                          replication_extension_name,
                          machine_id,
                          run_as_account_id,
                          target_cluster_id):

    config_result = _handle_configuration_validation(
        cmd,
        subscription_id,
        resource_group_name,
        replication_vault_name,
        machine_name,
        machine_props,
        target_vm_cpu_core,
        target_vm_ram,
        site_type
    )
    (hyperv_generation, source_cpu_cores, is_source_dynamic_memory,
     source_memory_mb, protected_item_uri) = config_result

    # Construct protected item properties with only the essential properties
    custom_properties = _build_custom_properties(
        instance_type, custom_location_id, custom_location_region,
        machine_id, disks, nics, target_vm_name, target_resource_group_id,
        target_storage_path_id, hyperv_generation, target_vm_cpu_core,
        source_cpu_cores, is_dynamic_ram_enabled, is_source_dynamic_memory,
        source_memory_mb, target_vm_ram, source_dra, target_dra,
        run_as_account_id, target_cluster_id
    )

    protected_item_body = {
        "properties": {
            "policyName": policy_name,
            "replicationExtensionName": replication_extension_name,
            "customProperties": custom_properties
        }
    }

    create_or_update_resource(
        cmd,
        protected_item_uri,
        APIVersion.Microsoft_DataReplication.value,
        protected_item_body)

    print(f"Successfully initiated replication for machine "
          f"'{machine_name}'.")
