# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument, too-many-statements, too-many-branches, too-many-locals
from knack.log import get_logger

from ..aaz.latest.vmss import (ListInstances as _VMSSListInstances,
                               Start as _Start,
                               Create as _VMSSCreate,
                               Show as _VMSSShow)
from azure.cli.core.aaz import AAZUndefined, has_value

logger = get_logger(__name__)


class VMSSListInstances(_VMSSListInstances):
    def _output(self, *args, **kwargs):
        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        for value in self.ctx.vars.instance.value:
            if has_value(value.resources):
                for resource in value.resources:
                    if has_value(resource.type):
                        resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


class VMSSStart(_Start):

    def pre_operations(self):
        args = self.ctx.args

        if not has_value(args.instance_ids):
            # if instance id is not provide, override with '*'
            args.instance_ids = ["*"]


class VMSSCreate(_VMSSCreate):
    def _output(self, *args, **kwargs):
        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.properties.virtual_machine_profile.extension_profile.extensions):
            for extension in self.ctx.vars.instance.properties.virtual_machine_profile.extension_profile.extensions:
                if has_value(extension.type):
                    extension.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VMSSShow(_VMSSShow):

    def _output(self, *args, **kwargs):
        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.properties.virtual_machine_profile.extension_profile.extensions):
            for extension in self.ctx.vars.instance.properties.virtual_machine_profile.extension_profile.extensions:
                if has_value(extension.type):
                    extension.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


def convert_show_result_to_snake_case(result):
    new_result = {}
    if "extendedLocation" in result:
        new_result["extended_location"] = result["extendedLocation"]
    if "identity" in result:
        new_result["identity"] = result["identity"]
    if "location" in result:
        new_result["location"] = result["location"]
    if "placement" in result:
        new_result["placement"] = result["placement"]
    if "plan" in result:
        new_result["plan"] = result["plan"]
    if "sku" in result:
        new_result["sku"] = result["sku"]
    if "tags" in result:
        new_result["tags"] = result["tags"]
    if "zones" in result:
        new_result["zones"] = result["zones"]

    identity = new_result.get("identity", {}) or {}
    if "userAssignedIdentities" in identity:
        identity["user_assigned_identities"] = identity["userAssignedIdentities"]
        identity.pop("userAssignedIdentities")

    placement = new_result.get("placement", {}) or {}
    if "excludeZones" in placement:
        placement["exclude_zones"] = placement["excludeZones"]
        placement.pop("excludeZones")
    if "includeZones" in placement:
        placement["include_zones"] = placement["includeZones"]
        placement.pop("includeZones")
    if "zonePlacementPolicy" in placement:
        placement["zone_placement_policy"] = placement["zonePlacementPolicy"]
        placement.pop("zonePlacementPolicy")

    plan = new_result.get("plan", {}) or {}
    if "promotionCode" in plan:
        plan["promotion_code"] = plan["promotionCode"]
        plan.pop("promotionCode")

    if "additionalCapabilities" in result:
        new_result["additional_capabilities"] = result["additionalCapabilities"]
    if "automaticRepairsPolicy" in result:
        new_result["automatic_repairs_policy"] = result["automaticRepairsPolicy"]
    if "constrainedMaximumCapacity" in result:
        new_result["constrained_maximum_capacity"] = result["constrainedMaximumCapacity"]
    if "doNotRunExtensionsOnOverprovisionedVMs" in result:
        new_result["do_not_run_extensions_on_overprovisioned_v_ms"] = result["doNotRunExtensionsOnOverprovisionedVMs"]
    if "highSpeedInterconnectPlacement" in result:
        new_result["high_speed_interconnect_placement"] = result["highSpeedInterconnectPlacement"]
    if "hostGroup" in result:
        new_result["host_group"] = result["hostGroup"]
    if "orchestrationMode" in result:
        new_result["orchestration_mode"] = result["orchestrationMode"]
    if "overprovision" in result:
        new_result["overprovision"] = result["overprovision"]
    if "platformFaultDomainCount" in result:
        new_result["platform_fault_domain_count"] = result["platformFaultDomainCount"]
    if "priorityMixPolicy" in result:
        new_result["priority_mix_policy"] = result["priorityMixPolicy"]
    if "proximityPlacementGroup" in result:
        new_result["proximity_placement_group"] = result["proximityPlacementGroup"]
    if "resiliencyPolicy" in result:
        new_result["resiliency_policy"] = result["resiliencyPolicy"]
    if "scaleInPolicy" in result:
        new_result["scale_in_policy"] = result["scaleInPolicy"]
    if "scheduledEventsPolicy" in result:
        new_result["scheduled_events_policy"] = result["scheduledEventsPolicy"]
    if "singlePlacementGroup" in result:
        new_result["single_placement_group"] = result["singlePlacementGroup"]
    if "skuProfile" in result:
        new_result["sku_profile"] = result["skuProfile"]
    if "spotRestorePolicy" in result:
        new_result["spot_restore_policy"] = result["spotRestorePolicy"]
    if "upgradePolicy" in result:
        new_result["upgrade_policy"] = result["upgradePolicy"]
    if "virtualMachineProfile" in result:
        new_result["virtual_machine_profile"] = result["virtualMachineProfile"]
    if "zonalPlatformFaultDomainAlignMode" in result:
        new_result["zonal_platform_fault_domain_align_mode"] = result["zonalPlatformFaultDomainAlignMode"]
    if "zoneBalance" in result:
        new_result["zone_balance"] = result["zoneBalance"]

    additional_capabilities = new_result.get("additional_capabilities", {}) or {}
    if "enableFips1403Encryption" in additional_capabilities:
        additional_capabilities["enable_fips1403_encryption"] = additional_capabilities["enableFips1403Encryption"]
        additional_capabilities.pop("enableFips1403Encryption")
    if "hibernationEnabled" in additional_capabilities:
        additional_capabilities["hibernation_enabled"] = additional_capabilities["hibernationEnabled"]
        additional_capabilities.pop("hibernationEnabled")
    if "ultraSSDEnabled" in additional_capabilities:
        additional_capabilities["ultra_ssd_enabled"] = additional_capabilities["ultraSSDEnabled"]
        additional_capabilities.pop("ultraSSDEnabled")

    automatic_repairs_policy = new_result.get("automatic_repairs_policy", {}) or {}
    if "gracePeriod" in automatic_repairs_policy:
        automatic_repairs_policy["grace_period"] = automatic_repairs_policy["gracePeriod"]
        automatic_repairs_policy.pop("gracePeriod")
    if "repairAction" in automatic_repairs_policy:
        automatic_repairs_policy["repair_action"] = automatic_repairs_policy["repairAction"]
        automatic_repairs_policy.pop("repairAction")

    priority_mix_policy = new_result.get("priority_mix_policy", {}) or {}
    if "baseRegularPriorityCount" in priority_mix_policy:
        priority_mix_policy["base_regular_priority_count"] = priority_mix_policy["baseRegularPriorityCount"]
        priority_mix_policy.pop("baseRegularPriorityCount")
    if "regularPriorityPercentageAboveBase" in priority_mix_policy:
        priority_mix_policy["regular_priority_percentage_above_base"] = priority_mix_policy["regularPriorityPercentageAboveBase"]
        priority_mix_policy.pop("regularPriorityPercentageAboveBase")

    resiliency_policy = new_result.get("resiliency_policy", {}) or {}
    if "automaticZoneRebalancingPolicy" in resiliency_policy:
        resiliency_policy["automatic_zone_rebalancing_policy"] = resiliency_policy["automaticZoneRebalancingPolicy"]
        resiliency_policy.pop("automaticZoneRebalancingPolicy")
    if "resilientVMCreationPolicy" in resiliency_policy:
        resiliency_policy["resilient_vm_creation_policy"] = resiliency_policy["resilientVMCreationPolicy"]
        resiliency_policy.pop("resilientVMCreationPolicy")
    if "resilientVMDeletionPolicy" in resiliency_policy:
        resiliency_policy["resilient_vm_deletion_policy"] = resiliency_policy["resilientVMDeletionPolicy"]
        resiliency_policy.pop("resilientVMDeletionPolicy")
    if "zoneAllocationPolicy" in resiliency_policy:
        resiliency_policy["zone_allocation_policy"] = resiliency_policy["zoneAllocationPolicy"]
        resiliency_policy.pop("zoneAllocationPolicy")

    automatic_zone_rebalancing_policy = resiliency_policy.get("automatic_zone_rebalancing_policy", {}) or {}
    if "rebalanceBehavior" in automatic_zone_rebalancing_policy:
        automatic_zone_rebalancing_policy["rebalance_behavior"] = automatic_zone_rebalancing_policy["rebalanceBehavior"]
        automatic_zone_rebalancing_policy.pop("rebalanceBehavior")
    if "rebalanceStrategy" in automatic_zone_rebalancing_policy:
        automatic_zone_rebalancing_policy["rebalance_strategy"] = automatic_zone_rebalancing_policy["rebalanceStrategy"]
        automatic_zone_rebalancing_policy.pop("rebalanceStrategy")

    zone_allocation_policy = resiliency_policy.get("zone_allocation_policy", {}) or {}
    if "maxInstancePercentPerZonePolicy" in zone_allocation_policy:
        zone_allocation_policy["max_instance_percent_per_zone_policy"] = zone_allocation_policy["maxInstancePercentPerZonePolicy"]
        zone_allocation_policy.pop("maxInstancePercentPerZonePolicy")
    if "maxZoneCount" in zone_allocation_policy:
        zone_allocation_policy["max_zone_count"] = zone_allocation_policy["maxZoneCount"]
        zone_allocation_policy.pop("maxZoneCount")

    scale_in_policy = new_result.get("scale_in_policy", {}) or {}
    if "forceDeletion" in scale_in_policy:
        scale_in_policy["force_deletion"] = scale_in_policy["forceDeletion"]
        scale_in_policy.pop("forceDeletion")
    if "prioritizeUnhealthyVMs" in scale_in_policy:
        scale_in_policy["prioritize_unhealthy_v_ms"] = scale_in_policy["prioritizeUnhealthyVMs"]
        scale_in_policy.pop("prioritizeUnhealthyVMs")

    scheduled_events_policy = new_result.get("scheduled_events_policy", {}) or {}
    if "allInstancesDown" in scheduled_events_policy:
        scheduled_events_policy["all_instances_down"] = scheduled_events_policy["allInstancesDown"]
        scheduled_events_policy.pop("allInstancesDown")
    if "scheduledEventsAdditionalPublishingTargets" in scheduled_events_policy:
        scheduled_events_policy["scheduled_events_additional_publishing_targets"] = scheduled_events_policy[
            "scheduledEventsAdditionalPublishingTargets"]
        scheduled_events_policy.pop("scheduledEventsAdditionalPublishingTargets")
    if "userInitiatedReboot" in scheduled_events_policy:
        scheduled_events_policy["user_initiated_reboot"] = scheduled_events_policy["userInitiatedReboot"]
        scheduled_events_policy.pop("userInitiatedReboot")
    if "userInitiatedRedeploy" in scheduled_events_policy:
        scheduled_events_policy["user_initiated_redeploy"] = scheduled_events_policy["userInitiatedRedeploy"]
        scheduled_events_policy.pop("userInitiatedRedeploy")

    all_instances_down = scheduled_events_policy.get("all_instances_down", {}) or {}
    if "automaticallyApprove" in all_instances_down:
        all_instances_down["automatically_approve"] = all_instances_down["automaticallyApprove"]
        all_instances_down.pop("automaticallyApprove")

    scheduled_events_additional_publishing_targets = scheduled_events_policy.get("scheduled_events_additional_publishing_targets", {}) or {}
    if "eventGridAndResourceGraph" in scheduled_events_additional_publishing_targets:
        scheduled_events_additional_publishing_targets["event_grid_and_resource_graph"] = scheduled_events_additional_publishing_targets["eventGridAndResourceGraph"]
        scheduled_events_additional_publishing_targets.pop("eventGridAndResourceGraph")

    event_grid_and_resource_graph = scheduled_events_additional_publishing_targets.get("event_grid_and_resource_graph", {}) or {}
    if "scheduledEventsApiVersion" in event_grid_and_resource_graph:
        event_grid_and_resource_graph["scheduled_events_api_version"] = event_grid_and_resource_graph["scheduledEventsApiVersion"]
        event_grid_and_resource_graph.pop("scheduledEventsApiVersion")

    user_initiated_reboot = scheduled_events_policy.get("user_initiated_reboot", {}) or {}
    if "automaticallyApprove" in user_initiated_reboot:
        user_initiated_reboot["automatically_approve"] = user_initiated_reboot["automaticallyApprove"]
        user_initiated_reboot.pop("automaticallyApprove")

    user_initiated_redeploy = scheduled_events_policy.get("user_initiated_redeploy", {}) or {}
    if "automaticallyApprove" in user_initiated_redeploy:
        user_initiated_redeploy["automatically_approve"] = user_initiated_redeploy["automaticallyApprove"]
        user_initiated_redeploy.pop("automaticallyApprove")

    sku_profile = new_result.get("sku_profile", {}) or {}
    if "allocationStrategy" in sku_profile:
        sku_profile["allocation_strategy"] = sku_profile["allocationStrategy"]
        sku_profile.pop("allocationStrategy")
    if "vmSizes" in sku_profile:
        sku_profile["vm_sizes"] = sku_profile["vmSizes"]
        sku_profile.pop("vmSizes")

    spot_restore_policy = new_result.get("spot_restore_policy", {}) or {}
    if "restoreTimeout" in spot_restore_policy:
        spot_restore_policy["restore_timeout"] = spot_restore_policy["restoreTimeout"]
        spot_restore_policy.pop("restoreTimeout")

    upgrade_policy = new_result.get("upgrade_policy", {}) or {}
    if "automaticOSUpgradePolicy" in upgrade_policy:
        upgrade_policy["automatic_os_upgrade_policy"] = upgrade_policy["automaticOSUpgradePolicy"]
        upgrade_policy.pop("automaticOSUpgradePolicy")
    if "rollingUpgradePolicy" in upgrade_policy:
        upgrade_policy["rolling_upgrade_policy"] = upgrade_policy["rollingUpgradePolicy"]
        upgrade_policy.pop("rollingUpgradePolicy")

    automatic_os_upgrade_policy = upgrade_policy.get("automatic_os_upgrade_policy", {}) or {}
    if "disableAutomaticRollback" in automatic_os_upgrade_policy:
        automatic_os_upgrade_policy["disable_automatic_rollback"] = automatic_os_upgrade_policy["disableAutomaticRollback"]
        automatic_os_upgrade_policy.pop("disableAutomaticRollback")
    if "enableAutomaticOSUpgrade" in automatic_os_upgrade_policy:
        automatic_os_upgrade_policy["enable_automatic_os_upgrade"] = automatic_os_upgrade_policy["enableAutomaticOSUpgrade"]
        automatic_os_upgrade_policy.pop("enableAutomaticOSUpgrade")
    if "osRollingUpgradeDeferral" in automatic_os_upgrade_policy:
        automatic_os_upgrade_policy["os_rolling_upgrade_deferral"] = automatic_os_upgrade_policy["osRollingUpgradeDeferral"]
        automatic_os_upgrade_policy.pop("osRollingUpgradeDeferral")
    if "useRollingUpgradePolicy" in automatic_os_upgrade_policy:
        automatic_os_upgrade_policy["use_rolling_upgrade_policy"] = automatic_os_upgrade_policy["useRollingUpgradePolicy"]
        automatic_os_upgrade_policy.pop("useRollingUpgradePolicy")

    rolling_upgrade_policy = upgrade_policy.get("rolling_upgrade_policy", {}) or {}
    if "enableCrossZoneUpgrade" in rolling_upgrade_policy:
        rolling_upgrade_policy["enable_cross_zone_upgrade"] = rolling_upgrade_policy["enableCrossZoneUpgrade"]
        rolling_upgrade_policy.pop("enableCrossZoneUpgrade")
    if "maxBatchInstancePercent" in rolling_upgrade_policy:
        rolling_upgrade_policy["max_batch_instance_percent"] = rolling_upgrade_policy["maxBatchInstancePercent"]
        rolling_upgrade_policy.pop("maxBatchInstancePercent")
    if "maxSurge" in rolling_upgrade_policy:
        rolling_upgrade_policy["max_surge"] = rolling_upgrade_policy["maxSurge"]
        rolling_upgrade_policy.pop("maxSurge")
    if "maxUnhealthyInstancePercent" in rolling_upgrade_policy:
        rolling_upgrade_policy["max_unhealthy_instance_percent"] = rolling_upgrade_policy["maxUnhealthyInstancePercent"]
        rolling_upgrade_policy.pop("maxUnhealthyInstancePercent")
    if "maxUnhealthyUpgradedInstancePercent" in rolling_upgrade_policy:
        rolling_upgrade_policy["max_unhealthy_upgraded_instance_percent"] = rolling_upgrade_policy["maxUnhealthyUpgradedInstancePercent"]
        rolling_upgrade_policy.pop("maxUnhealthyUpgradedInstancePercent")
    if "pauseTimeBetweenBatches" in rolling_upgrade_policy:
        rolling_upgrade_policy["pause_time_between_batches"] = rolling_upgrade_policy["pauseTimeBetweenBatches"]
        rolling_upgrade_policy.pop("pauseTimeBetweenBatches")
    if "prioritizeUnhealthyInstances" in rolling_upgrade_policy:
        rolling_upgrade_policy["prioritize_unhealthy_instances"] = rolling_upgrade_policy["prioritizeUnhealthyInstances"]
        rolling_upgrade_policy.pop("prioritizeUnhealthyInstances")
    if "rollbackFailedInstancesOnPolicyBreach" in rolling_upgrade_policy:
        rolling_upgrade_policy["rollback_failed_instances_on_policy_breach"] = rolling_upgrade_policy["rollbackFailedInstancesOnPolicyBreach"]
        rolling_upgrade_policy.pop("rollbackFailedInstancesOnPolicyBreach")

    virtual_machine_profile = new_result.get("virtual_machine_profile", {}) or {}
    if "applicationProfile" in virtual_machine_profile:
        virtual_machine_profile["application_profile"] = virtual_machine_profile["applicationProfile"]
        virtual_machine_profile.pop("applicationProfile")
    if "billingProfile" in virtual_machine_profile:
        virtual_machine_profile["billing_profile"] = virtual_machine_profile["billingProfile"]
        virtual_machine_profile.pop("billingProfile")
    if "capacityReservation" in virtual_machine_profile:
        virtual_machine_profile["capacity_reservation"] = virtual_machine_profile["capacityReservation"]
        virtual_machine_profile.pop("capacityReservation")
    if "diagnosticsProfile" in virtual_machine_profile:
        virtual_machine_profile["diagnostics_profile"] = virtual_machine_profile["diagnosticsProfile"]
        virtual_machine_profile.pop("diagnosticsProfile")
    if "evictionPolicy" in virtual_machine_profile:
        virtual_machine_profile["eviction_policy"] = virtual_machine_profile["evictionPolicy"]
        virtual_machine_profile.pop("evictionPolicy")
    if "extensionProfile" in virtual_machine_profile:
        virtual_machine_profile["extension_profile"] = virtual_machine_profile["extensionProfile"]
        virtual_machine_profile.pop("extensionProfile")
    if "hardwareProfile" in virtual_machine_profile:
        virtual_machine_profile["hardware_profile"] = virtual_machine_profile["hardwareProfile"]
        virtual_machine_profile.pop("hardwareProfile")
    if "licenseType" in virtual_machine_profile:
        virtual_machine_profile["license_type"] = virtual_machine_profile["licenseType"]
        virtual_machine_profile.pop("licenseType")
    if "networkProfile" in virtual_machine_profile:
        virtual_machine_profile["network_profile"] = virtual_machine_profile["networkProfile"]
        virtual_machine_profile.pop("networkProfile")
    if "osProfile" in virtual_machine_profile:
        virtual_machine_profile["os_profile"] = virtual_machine_profile["osProfile"]
        virtual_machine_profile.pop("osProfile")
    if "scheduledEventsProfile" in virtual_machine_profile:
        virtual_machine_profile["scheduled_events_profile"] = virtual_machine_profile["scheduledEventsProfile"]
        virtual_machine_profile.pop("scheduledEventsProfile")
    if "securityPostureReference" in virtual_machine_profile:
        virtual_machine_profile["security_posture_reference"] = virtual_machine_profile["securityPostureReference"]
        virtual_machine_profile.pop("securityPostureReference")
    if "securityProfile" in virtual_machine_profile:
        virtual_machine_profile["security_profile"] = virtual_machine_profile["securityProfile"]
        virtual_machine_profile.pop("securityProfile")
    if "serviceArtifactReference" in virtual_machine_profile:
        virtual_machine_profile["service_artifact_reference"] = virtual_machine_profile["serviceArtifactReference"]
        virtual_machine_profile.pop("serviceArtifactReference")
    if "storageProfile" in virtual_machine_profile:
        virtual_machine_profile["storage_profile"] = virtual_machine_profile["storageProfile"]
        virtual_machine_profile.pop("storageProfile")
    if "userData" in virtual_machine_profile:
        virtual_machine_profile["user_data"] = virtual_machine_profile["userData"]
        virtual_machine_profile.pop("userData")

    application_profile = virtual_machine_profile.get("application_profile", {}) or {}
    if "galleryApplications" in application_profile:
        application_profile["gallery_applications"] = application_profile["galleryApplications"]
        application_profile.pop("galleryApplications")

    gallery_applications = application_profile.get("gallery_applications", []) or []
    for gallery_application in gallery_applications:
        if "configurationReference" in gallery_application:
            gallery_application["configuration_reference"] = gallery_application["configurationReference"]
            gallery_application.pop("configurationReference")
        if "enableAutomaticUpgrade" in gallery_application:
            gallery_application["enable_automatic_upgrade"] = gallery_application["enableAutomaticUpgrade"]
            gallery_application.pop("enableAutomaticUpgrade")
        if "packageReferenceId" in gallery_application:
            gallery_application["package_reference_id"] = gallery_application["packageReferenceId"]
            gallery_application.pop("packageReferenceId")
        if "treatFailureAsDeploymentFailure" in gallery_application:
            gallery_application["treat_failure_as_deployment_failure"] = gallery_application["treatFailureAsDeploymentFailure"]
            gallery_application.pop("treatFailureAsDeploymentFailure")

    billing_profile = virtual_machine_profile.get("billing_profile", {}) or {}
    if "maxPrice" in billing_profile:
        billing_profile["max_price"] = billing_profile["maxPrice"]
        billing_profile.pop("maxPrice")

    capacity_reservation = virtual_machine_profile.get("capacity_reservation", {}) or {}
    if "capacityReservationGroup" in capacity_reservation:
        capacity_reservation["capacity_reservation_group"] = capacity_reservation["capacityReservationGroup"]
        capacity_reservation.pop("capacityReservationGroup")

    diagnostics_profile = virtual_machine_profile.get("diagnostics_profile", {}) or {}
    if "bootDiagnostics" in diagnostics_profile:
        diagnostics_profile["boot_diagnostics"] = diagnostics_profile["bootDiagnostics"]
        diagnostics_profile.pop("bootDiagnostics")

    boot_diagnostics = diagnostics_profile.get("boot_diagnostics", {}) or {}
    if "storageUri" in boot_diagnostics:
        boot_diagnostics["storage_uri"] = boot_diagnostics["storageUri"]
        boot_diagnostics.pop("storageUri")

    extension_profile = virtual_machine_profile.get("extension_profile", {}) or {}
    if "extensionsTimeBudget" in extension_profile:
        extension_profile["extensions_time_budget"] = extension_profile["extensionsTimeBudget"]
        extension_profile.pop("extensionsTimeBudget")

    extensions = extension_profile.get("extensions", []) or []
    for extension in extensions:
        if "autoUpgradeMinorVersion" in extension:
            extension["auto_upgrade_minor_version"] = extension["autoUpgradeMinorVersion"]
            extension.pop("autoUpgradeMinorVersion")
        if "enableAutomaticUpgrade" in extension:
            extension["enable_automatic_upgrade"] = extension["enableAutomaticUpgrade"]
            extension.pop("enableAutomaticUpgrade")
        if "forceUpdateTag" in extension:
            extension["force_update_tag"] = extension["forceUpdateTag"]
            extension.pop("forceUpdateTag")
        if "protectedSettings" in extension:
            extension["protected_settings"] = extension["protectedSettings"]
            extension.pop("protectedSettings")
        if "protectedSettingsFromKeyVault" in extension:
            extension["protected_settings_from_key_vault"] = extension["protectedSettingsFromKeyVault"]
            extension.pop("protectedSettingsFromKeyVault")
        if "provisionAfterExtensions" in extension:
            extension["provision_after_extensions"] = extension["provisionAfterExtensions"]
            extension.pop("provisionAfterExtensions")
        if "suppressFailures" in extension:
            extension["suppress_failures"] = extension["suppressFailures"]
            extension.pop("suppressFailures")
        if "typeHandlerVersion" in extension:
            extension["type_handler_version"] = extension["typeHandlerVersion"]
            extension.pop("typeHandlerVersion")

        protected_settings_from_key_vault = extension.get("protected_settings_from_key_vault", {}) or {}
        if "secretUrl" in protected_settings_from_key_vault:
            protected_settings_from_key_vault["secret_url"] = protected_settings_from_key_vault["secretUrl"]
            protected_settings_from_key_vault.pop("secretUrl")
        if "sourceVault" in protected_settings_from_key_vault:
            protected_settings_from_key_vault["source_vault"] = protected_settings_from_key_vault["sourceVault"]
            protected_settings_from_key_vault.pop("sourceVault")

    hardware_profile = virtual_machine_profile.get("hardware_profile", {}) or {}
    if "vmSizeProperties" in hardware_profile:
        hardware_profile["vm_size_properties"] = hardware_profile["vmSizeProperties"]
        hardware_profile.pop("vmSizeProperties")

    vm_size_properties = hardware_profile.get("vm_size_properties", {}) or {}
    if "vCPUsAvailable" in vm_size_properties:
        vm_size_properties["v_cp_us_available"] = vm_size_properties["vCPUsAvailable"]
        vm_size_properties.pop("vCPUsAvailable")
    if "vCPUsPerCore" in vm_size_properties:
        vm_size_properties["v_cp_us_per_core"] = vm_size_properties["vCPUsPerCore"]
        vm_size_properties.pop("vCPUsPerCore")

    network_profile = virtual_machine_profile.get("network_profile", {}) or {}
    if "healthProbe" in network_profile:
        network_profile["health_probe"] = network_profile["healthProbe"]
        network_profile.pop("healthProbe")
    if "networkApiVersion" in network_profile:
        network_profile["network_api_version"] = network_profile["networkApiVersion"]
        network_profile.pop("networkApiVersion")
    if "networkInterfaceConfigurations" in network_profile:
        network_profile["network_interface_configurations"] = network_profile["networkInterfaceConfigurations"]
        network_profile.pop("networkInterfaceConfigurations")

    network_interface_configurations = network_profile.get("network_interface_configurations", []) or []
    for network_interface_configuration in network_interface_configurations:
        if "auxiliaryMode" in network_interface_configuration:
            network_interface_configuration["auxiliary_mode"] = network_interface_configuration["auxiliaryMode"]
            network_interface_configuration.pop("auxiliaryMode")
        if "auxiliarySku" in network_interface_configuration:
            network_interface_configuration["auxiliary_sku"] = network_interface_configuration["auxiliarySku"]
            network_interface_configuration.pop("auxiliarySku")
        if "deleteOption" in network_interface_configuration:
            network_interface_configuration["delete_option"] = network_interface_configuration["deleteOption"]
            network_interface_configuration.pop("deleteOption")
        if "disableTcpStateTracking" in network_interface_configuration:
            network_interface_configuration["disable_tcp_state_tracking"] = network_interface_configuration["disableTcpStateTracking"]
            network_interface_configuration.pop("disableTcpStateTracking")
        if "dnsSettings" in network_interface_configuration:
            network_interface_configuration["dns_settings"] = network_interface_configuration["dnsSettings"]
            network_interface_configuration.pop("dnsSettings")
        if "enableAcceleratedNetworking" in network_interface_configuration:
            network_interface_configuration["enable_accelerated_networking"] = network_interface_configuration["enableAcceleratedNetworking"]
            network_interface_configuration.pop("enableAcceleratedNetworking")
        if "enableFpga" in network_interface_configuration:
            network_interface_configuration["enable_fpga"] = network_interface_configuration["enableFpga"]
            network_interface_configuration.pop("enableFpga")
        if "enableIPForwarding" in network_interface_configuration:
            network_interface_configuration["enable_ip_forwarding"] = network_interface_configuration["enableIPForwarding"]
            network_interface_configuration.pop("enableIPForwarding")
        if "ipConfigurations" in network_interface_configuration:
            network_interface_configuration["ip_configurations"] = network_interface_configuration["ipConfigurations"]
            network_interface_configuration.pop("ipConfigurations")
        if "networkSecurityGroup" in network_interface_configuration:
            network_interface_configuration["network_security_group"] = network_interface_configuration["networkSecurityGroup"]
            network_interface_configuration.pop("networkSecurityGroup")

        dns_settings = network_interface_configuration.get("dns_settings", {}) or {}
        if "dnsServers" in dns_settings:
            dns_settings["dns_servers"] = dns_settings["dnsServers"]
            dns_settings.pop("dnsServers")

        ip_configurations = network_interface_configuration.get("ip_configurations", []) or []
        for ip_configuration in ip_configurations:
            if "applicationGatewayBackendAddressPools" in ip_configuration:
                ip_configuration["application_gateway_backend_address_pools"] = ip_configuration["applicationGatewayBackendAddressPools"]
                ip_configuration.pop("applicationGatewayBackendAddressPools")
            if "applicationSecurityGroups" in ip_configuration:
                ip_configuration["application_security_groups"] = ip_configuration["applicationSecurityGroups"]
                ip_configuration.pop("applicationSecurityGroups")
            if "loadBalancerBackendAddressPools" in ip_configuration:
                ip_configuration["load_balancer_backend_address_pools"] = ip_configuration["loadBalancerBackendAddressPools"]
                ip_configuration.pop("loadBalancerBackendAddressPools")
            if "loadBalancerInboundNatPools" in ip_configuration:
                ip_configuration["load_balancer_inbound_nat_pools"] = ip_configuration["loadBalancerInboundNatPools"]
                ip_configuration.pop("loadBalancerInboundNatPools")
            if "privateIPAddressVersion" in ip_configuration:
                ip_configuration["private_ip_address_version"] = ip_configuration["privateIPAddressVersion"]
                ip_configuration.pop("privateIPAddressVersion")
            if "publicIPAddressConfiguration" in ip_configuration:
                ip_configuration["public_ip_address_configuration"] = ip_configuration["publicIPAddressConfiguration"]
                ip_configuration.pop("publicIPAddressConfiguration")

            public_ip_address_configuration = ip_configuration.get("public_ip_address_configuration", {}) or {}
            if "deleteOption" in public_ip_address_configuration:
                public_ip_address_configuration["delete_option"] = public_ip_address_configuration["deleteOption"]
                public_ip_address_configuration.pop("deleteOption")
            if "dnsSettings" in public_ip_address_configuration:
                public_ip_address_configuration["dns_settings"] = public_ip_address_configuration["dnsSettings"]
                public_ip_address_configuration.pop("dnsSettings")
            if "idleTimeoutInMinutes" in public_ip_address_configuration:
                public_ip_address_configuration["idle_timeout_in_minutes"] = public_ip_address_configuration[
                    "idleTimeoutInMinutes"]
                public_ip_address_configuration.pop("idleTimeoutInMinutes")
            if "ipTags" in public_ip_address_configuration:
                public_ip_address_configuration["ip_tags"] = public_ip_address_configuration["ipTags"]
                public_ip_address_configuration.pop("ipTags")
            if "publicIPAddressVersion" in public_ip_address_configuration:
                public_ip_address_configuration["public_ip_address_version"] = public_ip_address_configuration["publicIPAddressVersion"]
                public_ip_address_configuration.pop("publicIPAddressVersion")
            if "publicIPPrefix" in public_ip_address_configuration:
                public_ip_address_configuration["public_ip_prefix"] = public_ip_address_configuration["publicIPPrefix"]
                public_ip_address_configuration.pop("publicIPPrefix")

            dns_settings = public_ip_address_configuration.get("dns_settings", {}) or {}
            if "domainNameLabel" in dns_settings:
                dns_settings["domain_name_label"] = dns_settings["domainNameLabel"]
                dns_settings.pop("domainNameLabel")
            if "domainNameLabelScope" in dns_settings:
                dns_settings["domain_name_label_scope"] = dns_settings["domainNameLabelScope"]
                dns_settings.pop("domainNameLabelScope")

            ip_tags = public_ip_address_configuration.get("ip_tags", []) or []
            for ip_tag in ip_tags:
                if "ipTagType" in ip_tag:
                    ip_tag["ip_tag_type"] = ip_tag["ipTagType"]
                    ip_tag.pop("ipTagType")

    os_profile = virtual_machine_profile.get("os_profile", {}) or {}
    if "adminPassword" in os_profile:
        os_profile["admin_password"] = os_profile["adminPassword"]
        os_profile.pop("adminPassword")
    if "adminUsername" in os_profile:
        os_profile["admin_username"] = os_profile["adminUsername"]
        os_profile.pop("adminUsername")
    if "allowExtensionOperations" in os_profile:
        os_profile["allow_extension_operations"] = os_profile["allowExtensionOperations"]
        os_profile.pop("allowExtensionOperations")
    if "computerNamePrefix" in os_profile:
        os_profile["computer_name_prefix"] = os_profile["computerNamePrefix"]
        os_profile.pop("computerNamePrefix")
    if "customData" in os_profile:
        os_profile["custom_data"] = os_profile["customData"]
        os_profile.pop("customData")
    if "linuxConfiguration" in os_profile:
        os_profile["linux_configuration"] = os_profile["linuxConfiguration"]
        os_profile.pop("linuxConfiguration")
    if "requireGuestProvisionSignal" in os_profile:
        os_profile["require_guest_provision_signal"] = os_profile["requireGuestProvisionSignal"]
        os_profile.pop("requireGuestProvisionSignal")
    if "windowsConfiguration" in os_profile:
        os_profile["windows_configuration"] = os_profile["windowsConfiguration"]
        os_profile.pop("windowsConfiguration")

    linux_configuration = os_profile.get("linux_configuration", {}) or {}
    if "disablePasswordAuthentication" in linux_configuration:
        linux_configuration["disable_password_authentication"] = linux_configuration[
            "disablePasswordAuthentication"]
        linux_configuration.pop("disablePasswordAuthentication")
    if "enableVMAgentPlatformUpdates" in linux_configuration:
        linux_configuration["enable_vm_agent_platform_updates"] = linux_configuration[
            "enableVMAgentPlatformUpdates"]
        linux_configuration.pop("enableVMAgentPlatformUpdates")
    if "patchSettings" in linux_configuration:
        linux_configuration["patch_settings"] = linux_configuration["patchSettings"]
        linux_configuration.pop("patchSettings")
    if "provisionVMAgent" in linux_configuration:
        linux_configuration["provision_vm_agent"] = linux_configuration["provisionVMAgent"]
        linux_configuration.pop("provisionVMAgent")

    patch_settings = linux_configuration.get("patch_settings", {}) or {}
    if "assessmentMode" in patch_settings:
        patch_settings["assessment_mode"] = patch_settings["assessmentMode"]
        patch_settings.pop("assessmentMode")
    if "automaticByPlatformSettings" in patch_settings:
        patch_settings["automatic_by_platform_settings"] = patch_settings["automaticByPlatformSettings"]
        patch_settings.pop("automaticByPlatformSettings")
    if "patchMode" in patch_settings:
        patch_settings["patch_mode"] = patch_settings["patchMode"]
        patch_settings.pop("patchMode")

    automatic_by_platform_settings = patch_settings.get("automatic_by_platform_settings", {}) or {}
    if "bypassPlatformSafetyChecksOnUserSchedule" in automatic_by_platform_settings:
        automatic_by_platform_settings["bypass_platform_safety_checks_on_user_schedule"] = automatic_by_platform_settings["bypassPlatformSafetyChecksOnUserSchedule"]
        automatic_by_platform_settings.pop("bypassPlatformSafetyChecksOnUserSchedule")
    if "rebootSetting" in automatic_by_platform_settings:
        automatic_by_platform_settings["reboot_setting"] = automatic_by_platform_settings["rebootSetting"]
        automatic_by_platform_settings.pop("rebootSetting")

    ssh = linux_configuration.get("ssh", {}) or {}
    if "publicKeys" in ssh:
        ssh["public_keys"] = ssh["publicKeys"]
        ssh.pop("publicKeys")

    public_keys = ssh.get("public_keys", []) or []
    for public_key in public_keys:
        if "keyData" in public_key:
            public_key["key_data"] = public_key["keyData"]
            public_key.pop("keyData")

    secrets = os_profile.get("secrets", []) or []
    for secret in secrets:
        if "sourceVault" in secret:
            secret["source_vault"] = secret["sourceVault"]
            secret.pop("sourceVault")
        if "vaultCertificates" in secret:
            secret["vault_certificates"] = secret["vaultCertificates"]
            secret.pop("vaultCertificates")

        vault_certificates = secret.get("vault_certificates", []) or []
        for vault_certificate in vault_certificates:
            if "certificateStore" in vault_certificate:
                vault_certificate["certificate_store"] = vault_certificate["certificateStore"]
                vault_certificate.pop("certificateStore")
            if "certificateUrl" in vault_certificate:
                vault_certificate["certificate_url"] = vault_certificate["certificateUrl"]
                vault_certificate.pop("certificateUrl")

    windows_configuration = os_profile.get("windows_configuration", {}) or {}
    if "additionalUnattendContent" in windows_configuration:
        windows_configuration["additional_unattend_content"] = windows_configuration["additionalUnattendContent"]
        windows_configuration.pop("additionalUnattendContent")
    if "enableAutomaticUpdates" in windows_configuration:
        windows_configuration["enable_automatic_updates"] = windows_configuration["enableAutomaticUpdates"]
        windows_configuration.pop("enableAutomaticUpdates")
    if "patchSettings" in windows_configuration:
        windows_configuration["patch_settings"] = windows_configuration["patchSettings"]
        windows_configuration.pop("patchSettings")
    if "provisionVMAgent" in windows_configuration:
        windows_configuration["provision_vm_agent"] = windows_configuration["provisionVMAgent"]
        windows_configuration.pop("provisionVMAgent")
    if "timeZone" in windows_configuration:
        windows_configuration["time_zone"] = windows_configuration["timeZone"]
        windows_configuration.pop("timeZone")
    if "winRM" in windows_configuration:
        windows_configuration["win_rm"] = windows_configuration["winRM"]
        windows_configuration.pop("winRM")

    additional_unattend_content = windows_configuration.get("additional_unattend_content", []) or []
    for ele in additional_unattend_content:
        if "componentName" in ele:
            ele["component_name"] = ele["componentName"]
            ele.pop("componentName")
        if "passName" in ele:
            ele["pass_name"] = ele["passName"]
            ele.pop("passName")
        if "settingName" in ele:
            ele["setting_name"] = ele["settingName"]
            ele.pop("settingName")

    patch_settings = windows_configuration.get("patch_settings", {}) or {}
    if "assessmentMode" in patch_settings:
        patch_settings["assessment_mode"] = patch_settings["assessmentMode"]
        patch_settings.pop("assessmentMode")
    if "automaticByPlatformSettings" in patch_settings:
        patch_settings["automatic_by_platform_settings"] = patch_settings["automaticByPlatformSettings"]
        patch_settings.pop("automaticByPlatformSettings")
    if "enableHotpatching" in patch_settings:
        patch_settings["enable_hotpatching"] = patch_settings["enableHotpatching"]
        patch_settings.pop("enableHotpatching")
    if "patchMode" in patch_settings:
        patch_settings["patch_mode"] = patch_settings["patchMode"]
        patch_settings.pop("patchMode")

    automatic_by_platform_settings = patch_settings.get("automatic_by_platform_settings", {}) or {}
    if "bypassPlatformSafetyChecksOnUserSchedule" in automatic_by_platform_settings:
        automatic_by_platform_settings["bypass_platform_safety_checks_on_user_schedule"] = automatic_by_platform_settings["bypassPlatformSafetyChecksOnUserSchedule"]
        automatic_by_platform_settings.pop("bypassPlatformSafetyChecksOnUserSchedule")
    if "rebootSetting" in automatic_by_platform_settings:
        automatic_by_platform_settings["reboot_setting"] = automatic_by_platform_settings["rebootSetting"]
        automatic_by_platform_settings.pop("rebootSetting")

    win_rm = windows_configuration.get("win_rm", {}) or {}
    listeners = win_rm.get("listeners", []) or []
    for listener in listeners:
        if "certificateUrl" in listener:
            listener["certificate_url"] = listener["certificateUrl"]
            listener.pop("certificateUrl")

    scheduled_events_profile = virtual_machine_profile.get("scheduled_events_profile", {}) or {}
    if "osImageNotificationProfile" in scheduled_events_profile:
        scheduled_events_profile["os_image_notification_profile"] = scheduled_events_profile["osImageNotificationProfile"]
        scheduled_events_profile.pop("osImageNotificationProfile")
    if "terminateNotificationProfile" in scheduled_events_profile:
        scheduled_events_profile["terminate_notification_profile"] = scheduled_events_profile["terminateNotificationProfile"]
        scheduled_events_profile.pop("terminateNotificationProfile")

    os_image_notification_profile = scheduled_events_profile.get("os_image_notification_profile", {}) or {}
    if "notBeforeTimeout" in os_image_notification_profile:
        os_image_notification_profile["not_before_timeout"] = os_image_notification_profile["notBeforeTimeout"]
        os_image_notification_profile.pop("notBeforeTimeout")

    terminate_notification_profile = scheduled_events_profile.get("terminate_notification_profile", {}) or {}
    if "notBeforeTimeout" in terminate_notification_profile:
        terminate_notification_profile["not_before_timeout"] = terminate_notification_profile["notBeforeTimeout"]
        terminate_notification_profile.pop("notBeforeTimeout")

    security_posture_reference = virtual_machine_profile.get("security_posture_reference", {}) or {}
    if "excludeExtensions" in security_posture_reference:
        security_posture_reference["exclude_extensions"] = security_posture_reference["excludeExtensions"]
        security_posture_reference.pop("excludeExtensions")
    if "isOverridable" in security_posture_reference:
        security_posture_reference["is_overridable"] = security_posture_reference["isOverridable"]
        security_posture_reference.pop("isOverridable")

    security_profile = virtual_machine_profile.get("security_profile", {}) or {}
    if "encryptionAtHost" in security_profile:
        security_profile["encryption_at_host"] = security_profile["encryptionAtHost"]
        security_profile.pop("encryptionAtHost")
    if "encryptionIdentity" in security_profile:
        security_profile["encryption_identity"] = security_profile["encryptionIdentity"]
        security_profile.pop("encryptionIdentity")
    if "proxyAgentSettings" in security_profile:
        security_profile["proxy_agent_settings"] = security_profile["proxyAgentSettings"]
        security_profile.pop("proxyAgentSettings")
    if "securityType" in security_profile:
        security_profile["security_type"] = security_profile["securityType"]
        security_profile.pop("securityType")
    if "uefiSettings" in security_profile:
        security_profile["uefi_settings"] = security_profile["uefiSettings"]
        security_profile.pop("uefiSettings")

    encryption_identity = security_profile.get("encryption_identity", {}) or {}
    if "userAssignedIdentityResourceId" in encryption_identity:
        encryption_identity["user_assigned_identity_resource_id"] = encryption_identity["userAssignedIdentityResourceId"]
        encryption_identity.pop("userAssignedIdentityResourceId")

    proxy_agent_settings = security_profile.get("proxy_agent_settings", {}) or {}
    if "addProxyAgentExtension" in proxy_agent_settings:
        proxy_agent_settings["add_proxy_agent_extension"] = proxy_agent_settings["addProxyAgentExtension"]
        proxy_agent_settings.pop("addProxyAgentExtension")
    if "keyIncarnationId" in proxy_agent_settings:
        proxy_agent_settings["key_incarnation_id"] = proxy_agent_settings["keyIncarnationId"]
        proxy_agent_settings.pop("keyIncarnationId")
    if "wireServer" in proxy_agent_settings:
        proxy_agent_settings["wire_server"] = proxy_agent_settings["wireServer"]
        proxy_agent_settings.pop("wireServer")

    imds = proxy_agent_settings.get("imds", {}) or {}
    if "inVMAccessControlProfileReferenceId" in imds:
        imds["in_vm_access_control_profile_reference_id"] = imds["inVMAccessControlProfileReferenceId"]
        imds.pop("inVMAccessControlProfileReferenceId")

    wire_server = proxy_agent_settings.get("wire_server", {}) or {}
    if "inVMAccessControlProfileReferenceId" in wire_server:
        wire_server["in_vm_access_control_profile_reference_id"] = wire_server["inVMAccessControlProfileReferenceId"]
        wire_server.pop("inVMAccessControlProfileReferenceId")

    uefi_settings = security_profile.get("uefi_settings", {}) or {}
    if "secureBootEnabled" in uefi_settings:
        uefi_settings["secure_boot_enabled"] = uefi_settings["secureBootEnabled"]
        uefi_settings.pop("secureBootEnabled")
    if "vTpmEnabled" in uefi_settings:
        uefi_settings["v_tpm_enabled"] = uefi_settings["vTpmEnabled"]
        uefi_settings.pop("vTpmEnabled")

    storage_profile = virtual_machine_profile.get("storage_profile", {}) or {}
    if "dataDisks" in storage_profile:
        storage_profile["data_disks"] = storage_profile["dataDisks"]
        storage_profile.pop("dataDisks")
    if "diskControllerType" in storage_profile:
        storage_profile["disk_controller_type"] = storage_profile["diskControllerType"]
        storage_profile.pop("diskControllerType")
    if "imageReference" in storage_profile:
        storage_profile["image_reference"] = storage_profile["imageReference"]
        storage_profile.pop("imageReference")
    if "osDisk" in storage_profile:
        storage_profile["os_disk"] = storage_profile["osDisk"]
        storage_profile.pop("osDisk")

    data_disks = storage_profile.get("data_disks", []) or []
    for data_disk in data_disks:
        if "createOption" in data_disk:
            data_disk["create_option"] = data_disk["createOption"]
            data_disk.pop("createOption")
        if "deleteOption" in data_disk:
            data_disk["delete_option"] = data_disk["deleteOption"]
            data_disk.pop("deleteOption")
        if "diskIOPSReadWrite" in data_disk:
            data_disk["disk_iops_read_write"] = data_disk["diskIOPSReadWrite"]
            data_disk.pop("diskIOPSReadWrite")
        if "diskMBpsReadWrite" in data_disk:
            data_disk["disk_m_bps_read_write"] = data_disk["diskMBpsReadWrite"]
            data_disk.pop("diskMBpsReadWrite")
        if "diskSizeGB" in data_disk:
            data_disk["disk_size_gb"] = data_disk["diskSizeGB"]
            data_disk.pop("diskSizeGB")
        if "managedDisk" in data_disk:
            data_disk["managed_disk"] = data_disk["managedDisk"]
            data_disk.pop("managedDisk")
        if "writeAcceleratorEnabled" in data_disk:
            data_disk["write_accelerator_enabled"] = data_disk["writeAcceleratorEnabled"]
            data_disk.pop("writeAcceleratorEnabled")

        managed_disk = data_disk.get("managed_disk", {}) or {}
        if "diskEncryptionSet" in managed_disk:
            managed_disk["disk_encryption_set"] = managed_disk["diskEncryptionSet"]
            managed_disk.pop("diskEncryptionSet")
        if "securityProfile" in managed_disk:
            managed_disk["security_profile"] = managed_disk["securityProfile"]
            managed_disk.pop("securityProfile")
        if "storageAccountType" in managed_disk:
            managed_disk["storage_account_type"] = managed_disk["storageAccountType"]
            managed_disk.pop("storageAccountType")

        security_profile = managed_disk.get("security_profile", {}) or {}
        if "diskEncryptionSet" in security_profile:
            security_profile["disk_encryption_set"] = security_profile["diskEncryptionSet"]
            security_profile.pop("diskEncryptionSet")
        if "securityEncryptionType" in security_profile:
            security_profile["security_encryption_type"] = security_profile["securityEncryptionType"]
            security_profile.pop("securityEncryptionType")

    image_reference = storage_profile.get("image_reference", {}) or {}
    if "communityGalleryImageId" in image_reference:
        image_reference["community_gallery_image_id"] = image_reference["communityGalleryImageId"]
        image_reference.pop("communityGalleryImageId")
    if "sharedGalleryImageId" in image_reference:
        image_reference["shared_gallery_image_id"] = image_reference["sharedGalleryImageId"]
        image_reference.pop("sharedGalleryImageId")

    os_disk = storage_profile.get("os_disk", {}) or {}
    if "createOption" in os_disk:
        os_disk["create_option"] = os_disk["createOption"]
        os_disk.pop("createOption")
    if "deleteOption" in os_disk:
        os_disk["delete_option"] = os_disk["deleteOption"]
        os_disk.pop("deleteOption")
    if "diffDiskSettings" in os_disk:
        os_disk["diff_disk_settings"] = os_disk["diffDiskSettings"]
        os_disk.pop("diffDiskSettings")
    if "diskSizeGB" in os_disk:
        os_disk["disk_size_gb"] = os_disk["diskSizeGB"]
        os_disk.pop("diskSizeGB")
    if "managedDisk" in os_disk:
        os_disk["managed_disk"] = os_disk["managedDisk"]
        os_disk.pop("managedDisk")
    if "osType" in os_disk:
        os_disk["os_type"] = os_disk["osType"]
        os_disk.pop("osType")
    if "vhdContainers" in os_disk:
        os_disk["vhd_containers"] = os_disk["vhdContainers"]
        os_disk.pop("vhdContainers")
    if "writeAcceleratorEnabled" in os_disk:
        os_disk["write_accelerator_enabled"] = os_disk["writeAcceleratorEnabled"]
        os_disk.pop("writeAcceleratorEnabled")

    managed_disk = os_disk.get("managed_disk", {}) or {}
    if "diskEncryptionSet" in managed_disk:
        managed_disk["disk_encryption_set"] = managed_disk["diskEncryptionSet"]
        managed_disk.pop("diskEncryptionSet")
    if "securityProfile" in managed_disk:
        managed_disk["security_profile"] = managed_disk["securityProfile"]
        managed_disk.pop("securityProfile")
    if "storageAccountType" in managed_disk:
        managed_disk["storage_account_type"] = managed_disk["storageAccountType"]
        managed_disk.pop("storageAccountType")

    security_profile = managed_disk.get("security_profile", {}) or {}
    if "diskEncryptionSet" in security_profile:
        security_profile["disk_encryption_set"] = security_profile["diskEncryptionSet"]
        security_profile.pop("diskEncryptionSet")
    if "securityEncryptionType" in security_profile:
        security_profile["security_encryption_type"] = security_profile["securityEncryptionType"]
        security_profile.pop("securityEncryptionType")

    return new_result
