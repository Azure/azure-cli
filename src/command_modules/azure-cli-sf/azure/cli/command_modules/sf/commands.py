# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import cli_command
from azure.cli.command_modules.sf._factory import cf_sf_client
from azure.cli.core.sdk.util import (
    create_service_adapter,
    ServiceGroup
)

custom_path = "azure.cli.command_modules.sf.custom#{}"
cluster_operations = create_service_adapter("azure.servicefabric",
                                            "ServiceFabricClientAPIs")

# Custom commands
# TODO: Fix custom commands to accept client as additional argument instead of
# generating
cli_command(__name__, "sf cluster select",
            "azure.cli.command_modules.sf.custom#sf_select")
cli_command(__name__, "sf application upload",
            "azure.cli.command_modules.sf.custom#sf_upload_app")
cli_command(__name__, "sf compose create",
            "azure.cli.command_modules.sf.custom#sf_create_compose_application")
cli_command(__name__, "sf service create",
            "azure.cli.command_modules.sf.custom#sf_create_service")
cli_command(__name__, "sf service update",
            "azure.cli.command_modules.sf.custom#sf_update_service")
cli_command(__name__, "sf service report-health",
            "azure.cli.command_modules.sf.custom#sf_report_svc_health")
cli_command(__name__, "sf application create",
            "azure.cli.command_modules.sf.custom#sf_create_app")
cli_command(__name__, "sf application report-health",
            "azure.cli.command_modules.sf.custom#sf_report_app_health")
cli_command(__name__, "sf application upgrade",
            "azure.cli.command_modules.sf.custom#sf_upgrade_app")
cli_command(__name__, "sf node report-health",
            "azure.cli.command_modules.sf.custom#sf_report_node_health")
cli_command(__name__, "sf node service-package-upload",
            "azure.cli.command_modules.sf.custom#sf_service_package_upload")
cli_command(__name__, "sf replica report-health",
            "azure.cli.command_modules.sf.custom#sf_report_replica_health")
cli_command(__name__, "sf chaos start",
            "azure.cli.command_modules.sf.custom#sf_start_chaos")
cli_command(__name__, "sf partition report-health",
            "azure.cli.command_modules.sf.custom#sf_report_partition_health")

# Standard commands
with ServiceGroup(__name__, cf_sf_client, cluster_operations,
                  custom_path) as sg:
    # Cluster level commands
    with sg.group("sf cluster") as cl_group:
        cl_group.command("manifest", "get_cluster_manifest")
        cl_group.command("code-version",
                         "get_provisioned_fabric_code_version_info_list")
        cl_group.command("config-version",
                         "get_provisioned_fabric_config_version_info_list")
        cl_group.command("health", "get_cluster_health")

    # Application level commands
    with sg.group("sf application") as app_group:
        app_group.command("health", "get_application_health")
        app_group.command("manifest", "get_application_manifest")
        app_group.command("provision", "provision_application_type")
        app_group.command("delete", "delete_application")
        app_group.command("unprovision", "unprovision_application_type")
        app_group.command("package-delete", "delete_image_store_content")
        app_group.command("type", "get_application_type_info_list")
        app_group.command("list", "get_application_info_list")

    # Service level commands
    with sg.group("sf service") as svc_group:
        svc_group.command("list", "get_service_info_list")
        svc_group.command("manifest", "get_service_manifest")
        svc_group.command("application-name", "get_application_name_info")
        svc_group.command("description", "get_service_description")
        svc_group.command("health", "get_service_health")
        svc_group.command("resolve", "resolve_service")

    # Partition level commands
    with sg.group("sf partition") as partition_group:
        partition_group.command("info", "get_partition_info")
        partition_group.command("service-name", "get_service_name_info")
        partition_group.command("health", "get_partition_health")

    # Replica level commands
    with sg.group("sf replica") as replica_group:
        replica_group.command("health", "get_replica_health")

    # Node level commands
    with sg.group("sf node") as node_group:
        node_group.command("list", "get_node_info_list")
        node_group.command("remove-state", "remove_node_state")
        node_group.command("stop", "stop_node")
        node_group.command("restart", "restart_node")
        node_group.command("start", "start_node")
        node_group.command("replica-list",
                           "get_deployed_service_replica_info_list")
        node_group.command("load", "get_node_load_info")
        node_group.command("service-package-list",
                           "get_deployed_service_package_info_list")
        node_group.command("service-package",
                           "get_deployed_service_package_info_list_by_name")
        node_group.command("service-type-list",
                           "get_deployed_service_type_info_list")
        node_group.command("service-type",
                           "get_deployed_service_type_info_by_name")
        node_group.command("code-package",
                           "get_deployed_code_package_info_list")

    # Docker Compose commands
    with sg.group("sf compose") as compose_group:
        compose_group.command("status", "get_compose_application_status")
        compose_group.command("list", "get_compose_application_status_list")
        compose_group.command("remove", "remove_compose_application")
