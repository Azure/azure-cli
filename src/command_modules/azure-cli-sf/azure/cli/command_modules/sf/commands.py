# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.sf._factory import cf_sf_client
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from azure.cli.core.sdk.util import (
    create_service_adapter,
    ServiceGroup
)

DEPRECATE_SFCTL_STRING = "az sf sfctl"

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    custom_path = "azure.cli.command_modules.sf.custom#{}"
    cluster_operations = create_service_adapter("azure.servicefabric",
                                                "ServiceFabricClientAPIs")

    # No client commands
    with ServiceGroup(__name__, None, None, custom_path) as sg:
        with sg.group("sf cluster") as g:
            g.custom_command("select", "sf_select", deprecate_info=DEPRECATE_SFCTL_STRING)
        with sg.group("sf application") as g:
            g.custom_command("upload", "sf_upload_app", deprecate_info=DEPRECATE_SFCTL_STRING)
        with sg.group("sf") as g:
            # Command for more information on sfctl
            g.custom_command("sfctl", "sfctl_info")

    # Standard commands
    with ServiceGroup(__name__, cf_sf_client, cluster_operations,
                      custom_path) as sg:
        # Cluster level commands
        with sg.group("sf cluster") as cl_group:
            cl_group.command("manifest", "get_cluster_manifest", deprecate_info=DEPRECATE_SFCTL_STRING)
            cl_group.command("code-version", "get_provisioned_fabric_code_version_info_list",
                             deprecate_info=DEPRECATE_SFCTL_STRING)
            cl_group.command("config-version", "get_provisioned_fabric_config_version_info_list",
                             deprecate_info=DEPRECATE_SFCTL_STRING)
            cl_group.command("health", "get_cluster_health", deprecate_info=DEPRECATE_SFCTL_STRING)

        # Application level commands
        with sg.group("sf application") as app_group:
            app_group.custom_command("create", "sf_create_app", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.custom_command("report-health", "sf_report_app_health", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.custom_command("upgrade", "sf_upgrade_app", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("health", "get_application_health", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("manifest", "get_application_manifest", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("provision", "provision_application_type", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("delete", "delete_application", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("unprovision", "unprovision_application_type", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("package-delete", "delete_image_store_content", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("type", "get_application_type_info_list", deprecate_info=DEPRECATE_SFCTL_STRING)
            app_group.command("list", "get_application_info_list", deprecate_info=DEPRECATE_SFCTL_STRING)

        # Service level commands
        with sg.group("sf service") as svc_group:
            svc_group.custom_command("create", "sf_create_service", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.custom_command("update", "sf_update_service", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.custom_command("report-health", "sf_report_svc_health", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.command("list", "get_service_info_list", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.command("manifest", "get_service_manifest", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.command("application-name", "get_application_name_info", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.command("description", "get_service_description", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.command("health", "get_service_health", deprecate_info=DEPRECATE_SFCTL_STRING)
            svc_group.command("resolve", "resolve_service", deprecate_info=DEPRECATE_SFCTL_STRING)

        # Partition level commands
        with sg.group("sf partition") as partition_group:
            partition_group.custom_command("report-health", "sf_report_partition_health",
                                           deprecate_info=DEPRECATE_SFCTL_STRING)
            partition_group.command("info", "get_partition_info", deprecate_info=DEPRECATE_SFCTL_STRING)
            partition_group.command("service-name", "get_service_name_info", deprecate_info=DEPRECATE_SFCTL_STRING)
            partition_group.command("health", "get_partition_health", deprecate_info=DEPRECATE_SFCTL_STRING)

        # Replica level commands
        with sg.group("sf replica") as replica_group:
            replica_group.custom_command("report-health", "sf_report_replica_health",
                                         deprecate_info=DEPRECATE_SFCTL_STRING)
            replica_group.command("health", "get_replica_health", deprecate_info=DEPRECATE_SFCTL_STRING)

        # Node level commands
        with sg.group("sf node") as node_group:
            node_group.custom_command("report-health", "sf_report_node_health", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.custom_command("service-package-upload", "sf_service_package_upload",
                                      deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("list", "get_node_info_list", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("remove-state", "remove_node_state", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("stop", "stop_node", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("restart", "restart_node", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("start", "start_node", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("replica-list", "get_deployed_service_replica_info_list",
                               deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("load", "get_node_load_info", deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("service-package-list", "get_deployed_service_package_info_list",
                               deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("service-package", "get_deployed_service_package_info_list_by_name",
                               deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("service-type-list", "get_deployed_service_type_info_list",
                               deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("service-type", "get_deployed_service_type_info_by_name",
                               deprecate_info=DEPRECATE_SFCTL_STRING)
            node_group.command("code-package", "get_deployed_code_package_info_list",
                               deprecate_info=DEPRECATE_SFCTL_STRING)

        # Docker Compose commands
        with sg.group("sf compose") as compose_group:
            compose_group.custom_command("create", "sf_create_compose_application",
                                         deprecate_info=DEPRECATE_SFCTL_STRING)
            compose_group.command("status", "get_compose_application_status", deprecate_info=DEPRECATE_SFCTL_STRING)
            compose_group.command("list", "get_compose_application_status_list",
                                  deprecate_info=DEPRECATE_SFCTL_STRING)
            compose_group.command("remove", "remove_compose_application", deprecate_info=DEPRECATE_SFCTL_STRING)

        # Chaos test commands
        with sg.group("sf chaos") as chaos_group:
            chaos_group.custom_command("start", "sf_start_chaos", deprecate_info=DEPRECATE_SFCTL_STRING)
