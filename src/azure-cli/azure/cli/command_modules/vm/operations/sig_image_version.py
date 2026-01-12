# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument, too-many-branches
from knack.log import get_logger

from ..aaz.latest.sig.image_version import Show as _SigImageVersionShow, ListShared as _SigImageVersionListShared

logger = get_logger(__name__)


def convert_show_result_to_snake_case(result):
    new_result = {}
    if "id" in result:
        new_result["id"] = result["id"]
    if "location" in result:
        new_result["location"] = result["location"]
    if "name" in result:
        new_result["name"] = result["name"]
    if "tags" in result:
        new_result["tags"] = result["tags"]
    if "type" in result:
        new_result["type"] = result["type"]
    if "provisioningState" in result:
        new_result["provisioning_state"] = result["provisioningState"]
    if "publishingProfile" in result:
        new_result["publishing_profile"] = result["publishingProfile"]
    if "replicationStatus" in result:
        new_result["replication_status"] = result["replicationStatus"]
    if "restore" in result:
        new_result["restore"] = result["restore"]
    if "safetyProfile" in result:
        new_result["safety_profile"] = result["safetyProfile"]
    if "securityProfile" in result:
        new_result["security_profile"] = result["securityProfile"]
    if "storageProfile" in result:
        new_result["storage_profile"] = result["storageProfile"]
    if "validationsProfile" in result:
        new_result["validations_profile"] = result["validationsProfile"]

    publishing_profile = new_result.get("publishing_profile", {}) or {}
    if "endOfLifeDate" in publishing_profile:
        publishing_profile["end_of_life_date"] = publishing_profile["endOfLifeDate"]
        publishing_profile.pop("endOfLifeDate")
    if "excludeFromLatest" in publishing_profile:
        publishing_profile["exclude_from_latest"] = publishing_profile["excludeFromLatest"]
        publishing_profile.pop("excludeFromLatest")
    if "publishedDate" in publishing_profile:
        publishing_profile["published_date"] = publishing_profile["publishedDate"]
        publishing_profile.pop("publishedDate")
    if "replicaCount" in publishing_profile:
        publishing_profile["replica_count"] = publishing_profile["replicaCount"]
        publishing_profile.pop("replicaCount")
    if "replicationMode" in publishing_profile:
        publishing_profile["replication_mode"] = publishing_profile["replicationMode"]
        publishing_profile.pop("replicationMode")
    if "storageAccountType" in publishing_profile:
        publishing_profile["storage_account_type"] = publishing_profile["storageAccountType"]
        publishing_profile.pop("storageAccountType")
    if "targetExtendedLocations" in publishing_profile:
        publishing_profile["target_extended_locations"] = publishing_profile["targetExtendedLocations"]
        publishing_profile.pop("targetExtendedLocations")
    if "targetRegions" in publishing_profile:
        publishing_profile["target_regions"] = publishing_profile["targetRegions"]
        publishing_profile.pop("targetRegions")

    target_extended_locations = publishing_profile.get("target_extended_locations", []) or []
    for target_extended_location in target_extended_locations:
        if "extendedLocation" in target_extended_location:
            target_extended_location["extended_location"] = target_extended_location["extendedLocation"]
            target_extended_location.pop("extendedLocation")
        if "extendedLocationReplicaCount" in target_extended_location:
            target_extended_location["extended_location_replica_count"] = target_extended_location[
                "extendedLocationReplicaCount"]
            target_extended_location.pop("extendedLocationReplicaCount")
        if "storageAccountType" in target_extended_location:
            target_extended_location["storage_account_type"] = target_extended_location["storageAccountType"]
            target_extended_location.pop("storageAccountType")

    target_regions = publishing_profile.get("target_regions", []) or []
    for target_region in target_regions:
        if "additionalReplicaSets" in target_region:
            target_region["additional_replica_sets"] = target_region["additionalReplicaSets"]
            target_region.pop("additionalReplicaSets")
        if "excludeFromLatest" in target_region:
            target_region["exclude_from_latest"] = target_region["excludeFromLatest"]
            target_region.pop("excludeFromLatest")
        if "regionalReplicaCount" in target_region:
            target_region["regional_replica_count"] = target_region["regionalReplicaCount"]
            target_region.pop("regionalReplicaCount")
        if "storageAccountType" in target_region:
            target_region["storage_account_type"] = target_region["storageAccountType"]
            target_region.pop("storageAccountType")

        additional_replica_sets = target_region.get("additional_replica_sets", []) or []
        for additional_replica_set in additional_replica_sets:
            if "regionalReplicaCount" in additional_replica_set:
                additional_replica_set["regional_replica_count"] = additional_replica_set["regionalReplicaCount"]
                additional_replica_set.pop("regionalReplicaCount")
            if "storageAccountType" in additional_replica_set:
                additional_replica_set["storage_account_type"] = additional_replica_set["storageAccountType"]
                additional_replica_set.pop("storageAccountType")

    replication_status = new_result.get("replication_status", {}) or {}
    if "aggregatedState" in replication_status:
        replication_status["aggregated_state"] = replication_status["aggregatedState"]
        replication_status.pop("aggregatedState")

    safety_profile = new_result.get("safety_profile", {}) or {}
    if "allowDeletionOfReplicatedLocations" in safety_profile:
        safety_profile["allow_deletion_of_replicated_locations"] = safety_profile["allowDeletionOfReplicatedLocations"]
        safety_profile.pop("allowDeletionOfReplicatedLocations")
    if "blockDeletionBeforeEndOfLife" in safety_profile:
        safety_profile["block_deletion_before_end_of_life"] = safety_profile["blockDeletionBeforeEndOfLife"]
        safety_profile.pop("blockDeletionBeforeEndOfLife")
    if "policyViolations" in safety_profile:
        safety_profile["policy_violations"] = safety_profile["policyViolations"]
        safety_profile.pop("policyViolations")
    if "reportedForPolicyViolation" in safety_profile:
        safety_profile["reported_for_policy_violation"] = safety_profile["reportedForPolicyViolation"]
        safety_profile.pop("reportedForPolicyViolation")

    security_profile = new_result.get("security_profile", {}) or {}
    if "uefiSettings" in security_profile:
        security_profile["uefi_settings"] = security_profile["uefiSettings"]
        security_profile.pop("uefiSettings")

    uefi_settings = security_profile.get("uefi_settings", {}) or {}
    if "additionalSignatures" in uefi_settings:
        uefi_settings["additional_signatures"] = uefi_settings["additionalSignatures"]
        uefi_settings.pop("additionalSignatures")
    if "signatureTemplateNames" in uefi_settings:
        uefi_settings["signature_template_names"] = uefi_settings["signatureTemplateNames"]
        uefi_settings.pop("signatureTemplateNames")

    storage_profile = new_result.get("storage_profile", {}) or {}
    if "dataDiskImages" in storage_profile:
        storage_profile["data_disk_images"] = storage_profile["dataDiskImages"]
        storage_profile.pop("dataDiskImages")
    if "osDiskImage" in storage_profile:
        storage_profile["os_disk_image"] = storage_profile["osDiskImage"]
        storage_profile.pop("osDiskImage")

    data_disk_images = storage_profile.get("data_disk_images", []) or []
    for data_disk_image in data_disk_images:
        if "hostCaching" in data_disk_image:
            data_disk_image["host_caching"] = data_disk_image["hostCaching"]
            data_disk_image.pop("hostCaching")
        if "sizeInGB" in data_disk_image:
            data_disk_image["size_in_gb"] = data_disk_image["sizeInGB"]
            data_disk_image.pop("sizeInGB")

    os_disk_image = storage_profile.get("os_disk_image", {}) or {}
    if "hostCaching" in os_disk_image:
        os_disk_image["host_caching"] = os_disk_image["hostCaching"]
        os_disk_image.pop("hostCaching")
    if "sizeInGB" in os_disk_image:
        os_disk_image["size_in_gb"] = os_disk_image["sizeInGB"]
        os_disk_image.pop("sizeInGB")

    source = storage_profile.get("source", {}) or {}
    if "communityGalleryImageId" in source:
        source["community_gallery_image_id"] = source["communityGalleryImageId"]
        source.pop("communityGalleryImageId")
    if "virtualMachineId" in source:
        source["virtual_machine_id"] = source["virtualMachineId"]
        source.pop("virtualMachineId")

    validations_profile = new_result.get("validations_profile", {}) or {}
    if "executedValidations" in validations_profile:
        validations_profile["executed_validations"] = validations_profile["executedValidations"]
        validations_profile.pop("executedValidations")
    if "platformAttributes" in validations_profile:
        validations_profile["platform_attributes"] = validations_profile["platformAttributes"]
        validations_profile.pop("platformAttributes")
    if "validationEtag" in validations_profile:
        validations_profile["validation_etag"] = validations_profile["validationEtag"]
        validations_profile.pop("validationEtag")

    executed_validations = validations_profile.get("executed_validations", {}) or {}
    for executed_validation in executed_validations:
        if "executionTime" in executed_validation:
            executed_validation["execution_time"] = executed_validation["executionTime"]
            executed_validation.pop("executionTime")

    return new_result


class SigImageVersionListShared(_SigImageVersionListShared):
    def pre_operations(self):
        from azure.cli.core.aaz import has_value
        args = self.ctx.args
        if has_value(args.shared_to) and args.shared_to == 'subscription':
            args.shared_to = None
