# Track 2 Changes

## class name

* ManagedClusterIdentityUserAssignedIdentitiesValue -> Components1Umhcm8SchemasManagedclusteridentityPropertiesUserassignedidentitiesAdditionalproperties

## function name

* create_or_update -> begin_create_or_update
* reset_service_principal_profile -> begin_reset_service_principal_profile
* reset_aad_profile -> begin_reset_aad_profile
* upgrade_node_image_version -> begin_upgrade_node_image_version
* run_command -> begin_run_command
* rotate_cluster_certificates -> begin_rotate_cluster_certificates
* delete -> begin_delete
* stop -> begin_stop
* start -> begin_start

## parameter

* custom_headers -> headers

## property name

* adminGroupObjectIds -> adminGroupObjectIDs
* effectiveOutboundIps -> effectiveOutboundIPs
* outboundIpPrefixes -> outboundIpPrefixes
* outboundIps -> outboundIPs
* managedOutboundIps -> managedOutboundIPs
* authorizedIpRanges ->authorizedIPRanges
* managedOutboundIps -> managedOutboundIPs
* outboundIps -> outboundIPs

### NO CHANGE
* effectiveOutboundIps

## recording

### reason: ServicePrincipalNotFound(https://github.com/Azure/azure-cli/issues/9392)

* test test_aks_create_blb_vmas
* test_aks_create_with_ahub
* test_aks_nodepool_create_scale_delete
* test_aks_managed_identity_with_service_principal
* test_aks_nodepool_system_pool
