# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument, too-many-statements, too-many-branches, too-many-locals
import json

from knack.log import get_logger

from azure.cli.core.aaz import AAZStrType
from ..aaz.latest.vm import (Show as _VMShow, ListSizes as _VMListSizes, Patch as _VMPatch,
                             Update as _VMUpdate, Capture as _VMCapture, Create as _VMCreate)
from .._vm_utils import IdentityType

logger = get_logger(__name__)


class VMUpdate(_VMUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZDictArg, AAZObjectArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.identity = AAZObjectArg(
            options=["--identity"],
            arg_group="Parameters",
            help="The identity of the virtual machine scale set, if configured.",
        )

        identity = args_schema.identity
        identity.type = AAZStrArg(
            options=["type"],
            help="The type of identity used for the virtual machine scale set. The type 'SystemAssigned, UserAssigned' includes both an implicitly created identity and a set of user assigned identities. The type 'None' will remove any identities from the virtual machine scale set.",
            enum={"None": "None", "SystemAssigned": "SystemAssigned",
                  "SystemAssigned, UserAssigned": "SystemAssigned, UserAssigned", "UserAssigned": "UserAssigned"},
        )
        identity.user_assigned_identities = AAZDictArg(
            options=["user-assigned-identities"],
            help="The list of user identities associated with the virtual machine scale set. The user identity dictionary key references will be ARM resource ids in the form: '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{identityName}'.",
        )
        user_assigned_identities = args_schema.identity.user_assigned_identities
        user_assigned_identities.Element = AAZObjectArg(
            blank={},
        )

        return args_schema

    class VirtualMachinesGet(_VMUpdate.VirtualMachinesGet):
        # Override to solve key conflict of _schema_on_200.resources.Element.properties.type when deserializing
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()

            del schema.resources.Element.properties._fields['type']
            schema.resources.Element.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.resources):
            for resource in self.ctx.vars.instance.resources:
                if has_value(resource.type):
                    resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VMShow(_VMShow):
    class VirtualMachinesGet(_VMShow.VirtualMachinesGet):
        # Override to solve key conflict of _schema_on_200.resources.Element.properties.type when deserializing
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()

            del schema.resources.Element.properties._fields['type']
            schema.resources.Element.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.resources):
            for resource in self.ctx.vars.instance.resources:
                if has_value(resource.type):
                    resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VMListSizes(_VMListSizes):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._id_part = None

        return args_schema


class VMCapture(_VMCapture):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        result = result.get('output', None) or result.get('resources', [None])[0]
        return result


class VMCreate(_VMCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZDictArg, AAZObjectArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.identity = AAZObjectArg(
            options=["--identity"],
            arg_group="Parameters",
            help="The identity of the virtual machine scale set, if configured.",
        )

        identity = args_schema.identity
        identity.type = AAZStrArg(
            options=["type"],
            help="The type of identity used for the virtual machine scale set. The type 'SystemAssigned, UserAssigned' includes both an implicitly created identity and a set of user assigned identities. The type 'None' will remove any identities from the virtual machine scale set.",
            enum={"None": "None", "SystemAssigned": "SystemAssigned",
                  "SystemAssigned, UserAssigned": "SystemAssigned, UserAssigned", "UserAssigned": "UserAssigned"},
        )
        identity.user_assigned_identities = AAZDictArg(
            options=["user-assigned-identities"],
            help="The list of user identities associated with the virtual machine scale set. The user identity dictionary key references will be ARM resource ids in the form: '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{identityName}'.",
        )
        user_assigned_identities = args_schema.identity.user_assigned_identities
        user_assigned_identities.Element = AAZObjectArg(
            blank={},
        )

        return args_schema

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.resources):
            for resource in self.ctx.vars.instance.resources:
                if has_value(resource.type):
                    resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VMPatch(_VMPatch):
    class VirtualMachinesUpdate(_VMPatch.VirtualMachinesUpdate):
        # Override to solve key conflict of _schema_on_200.resources.Element.properties.type when deserializing
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()

            del schema.resources.Element.properties._fields['type']
            schema.resources.Element.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.resources):
            for resource in self.ctx.vars.instance.resources:
                if has_value(resource.type):
                    resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VMIdentityRemove(_VMPatch):
    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.resources):
            for resource in self.ctx.vars.instance.resources:
                if has_value(resource.type):
                    resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)

        identity = result.get('identity')
        if not identity:
            return result

        if not identity.get('userAssignedIdentities'):
            identity['userAssignedIdentities'] = None

        return result

    class VirtualMachinesUpdate(_VMPatch.VirtualMachinesUpdate):
        # Override to solve key conflict of _schema_on_200.resources.Element.properties.type when deserializing
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()

            del schema.resources.Element.properties._fields['type']
            schema.resources.Element.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema

        def _format_content(self, content):
            if isinstance(content, str):
                content = json.loads(content)

            if not content.get('identity'):
                content['identity'] = {
                    'userAssignedIdentities': None,
                    'type': IdentityType.NONE.value
                }
                return json.dumps(content)

            identities = content.get('identity', {}).get('userAssignedIdentities')
            if identities:
                if 'UserAssigned' in identities.keys():
                    identities.pop('UserAssigned')

                for key in list(identities.keys()):
                    identities[key] = None

            if not content.get('identity', {}).get('userAssignedIdentities', {}):
                content['identity']['userAssignedIdentities'] = None

            return json.dumps(content)

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            request.data = self._format_content(request.data)
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200, 202]:
                return self.client.build_lro_polling(
                    self.ctx.args.no_wait,
                    session,
                    self.on_200,
                    self.on_error,
                    lro_options={"final-state-via": "azure-async-operation"},
                    path_format_arguments=self.url_parameters,
                )

            return self.on_error(session.http_response)


def convert_show_result_to_snake_case(result):
    new_result = {}
    if "id" in result:
        new_result["id"] = result["id"]
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
    if "applicationProfile" in result:
        new_result["application_profile"] = result["applicationProfile"]
    if "availabilitySet" in result:
        new_result["availability_set"] = result["availabilitySet"]
    if "billingProfile" in result:
        new_result["billing_profile"] = result["billingProfile"]
    if "capacityReservation" in result:
        new_result["capacity_reservation"] = result["capacityReservation"]
    if "diagnosticsProfile" in result:
        new_result["diagnostics_profile"] = result["diagnosticsProfile"]
    if "evictionPolicy" in result:
        new_result["eviction_policy"] = result["evictionPolicy"]
    if "extensionsTimeBudget" in result:
        new_result["extensions_time_budget"] = result["extensionsTimeBudget"]
    if "hardwareProfile" in result:
        new_result["hardware_profile"] = result["hardwareProfile"]
    if "host" in result:
        new_result["host"] = result["host"]
    if "hostGroup" in result:
        new_result["host_group"] = result["hostGroup"]
    if "licenseType" in result:
        new_result["license_type"] = result["licenseType"]
    if "networkProfile" in result:
        new_result["network_profile"] = result["networkProfile"]
    if "osProfile" in result:
        new_result["os_profile"] = result["osProfile"]
    if "platformFaultDomain" in result:
        new_result["platform_fault_domain"] = result["platformFaultDomain"]
    if "priority" in result:
        new_result["priority"] = result["priority"]
    if "proximityPlacementGroup" in result:
        new_result["proximity_placement_group"] = result["proximityPlacementGroup"]
    if "scheduledEventsPolicy" in result:
        new_result["scheduled_events_policy"] = result["scheduledEventsPolicy"]
    if "scheduledEventsProfile" in result:
        new_result["scheduled_events_profile"] = result["scheduledEventsProfile"]
    if "securityProfile" in result:
        new_result["security_profile"] = result["securityProfile"]
    if "storageProfile" in result:
        new_result["storage_profile"] = result["storageProfile"]
    if "userData" in result:
        new_result["user_data"] = result["userData"]
    if "virtualMachineScaleSet" in result:
        new_result["virtual_machine_scale_set"] = result["virtualMachineScaleSet"]

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

    application_profile = new_result.get("application_profile", {}) or {}
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

    billing_profile = new_result.get("billing_profile", {}) or {}
    if "maxPrice" in billing_profile:
        billing_profile["max_price"] = billing_profile["maxPrice"]
        billing_profile.pop("maxPrice")

    capacity_reservation = new_result.get("capacity_reservation", {}) or {}
    if "capacityReservationGroup" in capacity_reservation:
        capacity_reservation["capacity_reservation_group"] = capacity_reservation["capacityReservationGroup"]
        capacity_reservation.pop("capacityReservationGroup")

    diagnostics_profile = new_result.get("diagnostics_profile", {}) or {}
    if "bootDiagnostics" in diagnostics_profile:
        diagnostics_profile["boot_diagnostics"] = diagnostics_profile["bootDiagnostics"]
        diagnostics_profile.pop("bootDiagnostics")

    boot_diagnostics = diagnostics_profile.get("boot_diagnostics", {}) or {}
    if "storageUri" in boot_diagnostics:
        boot_diagnostics["storage_uri"] = boot_diagnostics["storageUri"]
        boot_diagnostics.pop("storageUri")

    hardware_profile = new_result.get("hardware_profile", {}) or {}
    if "vmSize" in hardware_profile:
        hardware_profile["vm_size"] = hardware_profile["vmSize"]
        hardware_profile.pop("vmSize")
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

    network_profile = new_result.get("network_profile", {}) or {}
    if "networkApiVersion" in network_profile:
        network_profile["network_api_version"] = network_profile["networkApiVersion"]
        network_profile.pop("networkApiVersion")
    if "networkInterfaceConfigurations" in network_profile:
        network_profile["network_interface_configurations"] = network_profile["networkInterfaceConfigurations"]
        network_profile.pop("networkInterfaceConfigurations")
    if "networkInterfaces" in network_profile:
        network_profile["network_interfaces"] = network_profile["networkInterfaces"]
        network_profile.pop("networkInterfaces")

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
        if "dscpConfiguration" in network_interface_configuration:
            network_interface_configuration["dscp_configuration"] = network_interface_configuration["dscpConfiguration"]
            network_interface_configuration.pop("dscpConfiguration")
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
                public_ip_address_configuration["public_ip_address_version"] = public_ip_address_configuration[
                    "publicIPAddressVersion"]
                public_ip_address_configuration.pop("publicIPAddressVersion")
            if "publicIPAllocationMethod" in public_ip_address_configuration:
                public_ip_address_configuration["public_ip_allocation_method"] = public_ip_address_configuration[
                    "publicIPAllocationMethod"]
                public_ip_address_configuration.pop("publicIPAllocationMethod")
            if "publicIPPrefix" in public_ip_address_configuration:
                public_ip_address_configuration["public_ip_prefix"] = public_ip_address_configuration[
                    "publicIPPrefix"]
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

    network_interfaces = network_profile.get("network_interfaces", []) or []
    for network_interface in network_interfaces:
        if "deleteOption" in network_interface:
            network_interface["delete_option"] = network_interface["deleteOption"]
            network_interface.pop("deleteOption")

    os_profile = new_result.get("os_profile", {}) or {}
    if "adminPassword" in os_profile:
        os_profile["admin_password"] = os_profile["adminPassword"]
        os_profile.pop("adminPassword")
    if "adminUsername" in os_profile:
        os_profile["admin_username"] = os_profile["adminUsername"]
        os_profile.pop("adminUsername")
    if "allowExtensionOperations" in os_profile:
        os_profile["allow_extension_operations"] = os_profile["allowExtensionOperations"]
        os_profile.pop("allowExtensionOperations")
    if "computerName" in os_profile:
        os_profile["computer_name"] = os_profile["computerName"]
        os_profile.pop("computerName")
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
        linux_configuration["disable_password_authentication"] = linux_configuration["disablePasswordAuthentication"]
        linux_configuration.pop("disablePasswordAuthentication")
    if "enableVMAgentPlatformUpdates" in linux_configuration:
        linux_configuration["enable_vm_agent_platform_updates"] = linux_configuration["enableVMAgentPlatformUpdates"]
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

    scheduled_events_policy = new_result.get("scheduled_events_policy", {}) or {}
    if "allInstancesDown" in scheduled_events_policy:
        scheduled_events_policy["all_instances_down"] = scheduled_events_policy["allInstancesDown"]
        scheduled_events_policy.pop("allInstancesDown")
    if "scheduledEventsAdditionalPublishingTargets" in scheduled_events_policy:
        scheduled_events_policy["scheduled_events_additional_publishing_targets"] = scheduled_events_policy["scheduledEventsAdditionalPublishingTargets"]
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

    scheduled_events_profile = new_result.get("scheduled_events_profile", {}) or {}
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

    security_profile = new_result.get("security_profile", {}) or {}
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

    storage_profile = new_result.get("storage_profile", {}) or {}
    if "alignRegionalDisksToVMZone" in storage_profile:
        storage_profile["align_regional_disks_to_vm_zone"] = storage_profile["alignRegionalDisksToVMZone"]
        storage_profile.pop("alignRegionalDisksToVMZone")
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
        if "detachOption" in data_disk:
            data_disk["detach_option"] = data_disk["detachOption"]
            data_disk.pop("detachOption")
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
        if "sourceResource" in data_disk:
            data_disk["source_resource"] = data_disk["sourceResource"]
            data_disk.pop("sourceResource")
        if "toBeDetached" in data_disk:
            data_disk["to_be_detached"] = data_disk["toBeDetached"]
            data_disk.pop("toBeDetached")
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

        security_profile = managed_disk.get("security_profile", {})
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
    if "encryptionSettings" in os_disk:
        os_disk["encryption_settings"] = os_disk["encryptionSettings"]
        os_disk.pop("encryptionSettings")
    if "managedDisk" in os_disk:
        os_disk["managed_disk"] = os_disk["managedDisk"]
        os_disk.pop("managedDisk")
    if "osType" in os_disk:
        os_disk["os_type"] = os_disk["osType"]
        os_disk.pop("osType")
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

    security_profile = managed_disk.get("security_profile", {})
    if "diskEncryptionSet" in security_profile:
        security_profile["disk_encryption_set"] = security_profile["diskEncryptionSet"]
        security_profile.pop("diskEncryptionSet")
    if "securityEncryptionType" in security_profile:
        security_profile["security_encryption_type"] = security_profile["securityEncryptionType"]
        security_profile.pop("securityEncryptionType")

    encryption_settings = os_disk.get("encryption_settings", {}) or {}
    if "diskEncryptionKey" in encryption_settings:
        encryption_settings["disk_encryption_key"] = encryption_settings["diskEncryptionKey"]
        encryption_settings.pop("diskEncryptionKey")
    if "keyEncryptionKey" in encryption_settings:
        encryption_settings["key_encryption_key"] = encryption_settings["keyEncryptionKey"]
        encryption_settings.pop("keyEncryptionKey")

    disk_encryption_key = encryption_settings.get("disk_encryption_key", {}) or {}
    if "secretUrl" in disk_encryption_key:
        disk_encryption_key["secret_url"] = disk_encryption_key["secretUrl"]
        disk_encryption_key.pop("secretUrl")
    if "sourceVault" in disk_encryption_key:
        disk_encryption_key["source_vault"] = disk_encryption_key["sourceVault"]
        disk_encryption_key.pop("sourceVault")

    key_encryption_key = encryption_settings.get("key_encryption_key", {}) or {}
    if "keyUrl" in key_encryption_key:
        key_encryption_key["key_url"] = key_encryption_key["keyUrl"]
        key_encryption_key.pop("keyUrl")
    if "sourceVault" in key_encryption_key:
        key_encryption_key["source_vault"] = key_encryption_key["sourceVault"]
        key_encryption_key.pop("sourceVault")

    return new_result
