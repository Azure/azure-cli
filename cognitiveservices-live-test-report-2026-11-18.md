# Cognitive Services live-test report

- **Started:** 2026-11-18 19:33:04 UTC-08:00
- **Duration:** 1 hour, 2 minutes, 14 seconds
- **Environment:** Windows, Python 3.14.3, `azure-mgmt-cognitiveservices` 15.1.0b1
- **Scope:** Cognitive Services tests under `src\azure-cli\azure\cli\command_modules\cognitiveservices\tests\latest`, with `AZURE_TEST_RUN_LIVE=true`
- **Results:** 167 passed, 19 failed, 8 skipped; 221 additional subtests passed.
- **Live-only:** 15 tests have `@live_only()` on the method, its class, or both: 2 passed, 12 failed, 1 skipped.

The 194 listed test cases include unit tests as well as live scenarios. The JUnit
suite total is 415 because it also counts the 221 passing subtests; individual
subtest names were not retained in the saved results.

Immediately after the run, 22 recording files had been added or changed for
passing tests, and 18 partial recordings had been added or changed for failed
tests. Not every passing test produces a recording.

Detailed failure output is available locally in
`.venv\cognitiveservices-live-results-20261118.xml`. The identifiers below are
relative to the test directory above. A class-level `@live_only()` applies to
each test in that class.

## Failed tests (19)

| Test | Failure type | `@live_only()` |
| --- | --- | --- |
| `test_account_connections.py::CognitiveServicesAccountConnectionsTests::test_account_connections_from_file` | `InvalidArgumentValueError` | - |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_basic` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_complete` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_from_source` | `FileOperationError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_environment_variables` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_registry` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_resources` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_scaling` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_logs_show_basic` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_logs_show_with_options` | `AzureResponseError` | method |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_start_with_show_logs` | `AzureResponseError` | method |
| `test_byox.py::CognitiveServicesByoxTests::test_cognitiveservices_user_owned_storage` | `HttpResponseError` | - |
| `test_cognitiveservices_softdelete.py::CognitiveServicesDeleteTests::test_cognitiveservices_softdelete` | `ValueError` | - |
| `test_compute.py::CognitiveServicesComputeScenarioTests::test_cognitiveservices_compute_create_show_delete` | `HttpResponseError` | class |
| `test_compute.py::CognitiveServicesComputeScenarioTests::test_cognitiveservices_compute_list_empty` | `HttpResponseError` | class |
| `test_costcontrol.py::CognitiveServicesCostControlScenarioTests::test_cognitiveservices_project_costcontrol_crud` | `HttpResponseError` | - |
| `test_deployment.py::CognitiveServicesDeploymentTests::test_cognitiveservices_deployment` | `HttpResponseError` | - |
| `test_model.py::CognitiveServicesModelTests::test_cognitiveservices_model` | `HttpResponseError` | - |
| `test_project_connections.py::CognitiveServicesProjectConnectionsTests::test_project_connections_from_file` | `HttpResponseError` | - |

## Skipped tests (8)

| Test | Reason | `@live_only()` |
| --- | --- | --- |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentScenarioTests::test_adapter_deployment_create_show_list_delete` | Requires pre-provisioned adapter resources and `CLITEST_ADAPTER_*` settings. | method + class |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_managed_network_crud` | Pending service fix. | - |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_managed_network_provision` | Pending service fix. | - |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_outbound_rule_bulk_set_json` | Pending service fix. | - |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_outbound_rule_bulk_set_yaml` | Pending service fix. | - |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_outbound_rule_fqdn` | Pending service fix. | - |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_outbound_rule_private_endpoint` | Pending service fix. | - |
| `test_managed_network.py::CognitiveServicesManagedNetworkTests::test_outbound_rule_service_tag` | Pending service fix. | - |

## Passed tests (167)

| Test | `@live_only()` |
| --- | --- |
| `test_account_connections.py::CognitiveServicesConnectionLoadingTests::test_load_connections` | - |
| `test_account_properties.py::CognitiveServicesPropertiesTests::test_cognitiveservices_account_capabilities` | - |
| `test_account_properties.py::CognitiveServicesPropertiesTests::test_cognitiveservices_account_public_network_access` | - |
| `test_account_properties.py::CognitiveServicesPropertiesTests::test_cognitiveservices_aiservices` | - |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentScenarioTests::test_adapter_deployment_list_empty` | class |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentUnitTests::test_create_builds_expected_payload_shape` | - |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentUnitTests::test_create_omits_readonly_fields_from_payload` | - |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentUnitTests::test_create_returns_poller_directly` | - |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentUnitTests::test_delete_returns_poller_directly` | - |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentUnitTests::test_list_passes_through_to_client` | - |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentUnitTests::test_show_passes_through_to_client` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_agent_create_show_logs_parameter` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_agent_create_timeout_parameter_default` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_agent_logs_show_function_signature` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_agent_start_show_logs_parameter` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_build_ai_project_endpoint` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_build_ai_project_endpoint_rejects_invalid_resource_names` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_build_image_locally_uses_resolved_path` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_cf_ai_projects_rejects_invalid_account` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_cf_ai_projects_rejects_invalid_project` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_cf_ai_projects_requires_account_name` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_deploy_agent_version_show_logs_parameter` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_deploy_agent_version_timeout_parameter` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_environment_variables_type_invalid` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_environment_variables_type_valid` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_get_agent_container_status_builds_expected_request` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_has_dockerfile_custom_name` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_has_dockerfile_exists` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_has_dockerfile_invalid_dir` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_has_dockerfile_not_exists` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_is_docker_running_rejects_current_directory` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_is_docker_running_uses_resolved_path` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_is_fully_qualified_image` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_push_image_to_registry_uses_resolved_path` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_resolve_docker_command_preserves_launcher_symlink` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_stream_agent_logs_function_signature` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_validate_image_tag_invalid` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_validate_image_tag_valid` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_validate_path_for_subprocess_dangerous_chars` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_validate_path_for_subprocess_empty_path` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_validate_path_for_subprocess_null_bytes` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_validate_path_for_subprocess_valid_paths` | - |
| `test_agent.py::CognitiveServicesAgentHelperTests::test_wait_for_agent_deployment_ready_timeout_parameter` | - |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_errors` | method |
| `test_agent_hosting.py::CognitiveServicesAgentHostingScenarioTests::test_cognitiveservices_agent_hosting_flattened_arguments` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingScenarioTests::test_cognitiveservices_agent_hosting_identity_aliases` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_account_update_omits_configuration` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_builds_expected_payload` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_failed_preflight_does_not_submit_account` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_minimal_arguments_prepare_dependencies` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_non_byo_create_preserves_existing_payload` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_rejects_empty_and_non_string_arguments` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_rejects_invalid_resource_ids` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_requires_cluster_and_accepts_optional_dependencies` | - |
| `test_agent_hosting.py::CognitiveServicesAgentHostingUnitTests::test_agent_hosting_uses_user_assigned_identity_without_system_identity` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_account_cluster_and_storage_require_same_subscription` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_account_name_validation_precedes_dependency_queries` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_account_read_errors_are_not_treated_as_not_found` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_agent_pool_requirements_each_block_when_missing` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_all_eight_dependency_and_grant_branches` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_assignment_names_are_stable_across_retries` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_auto_storage_configuration` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_auto_storage_prefers_zrs_and_falls_back_to_lrs` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_automatic_cluster_is_rejected` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_autoscaling_does_not_replace_required_existing_agent_node` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_blob_validation_does_not_infer_data_access_from_owner` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_cluster_requirement_failures` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_command_validates_ids_once_and_passes_kind_and_domain` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_compatible_existing_grant_is_not_recreated` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_conditional_grants_are_not_unconditional_evidence` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_created_workload_identity_requires_all_three_metadata_fields` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_cross_subscription_workload_identity_is_allowed_in_same_tenant` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_cross_tenant_reference_blocks` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_dependency_creation_logs_are_descriptive` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_disabled_network_policy_fails_before_writes_even_with_overlay` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_documented_managed_network_policy_configurations_are_accepted` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_domain_api_error_is_preserved` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_entry_point_does_not_provision_after_failed_preflight` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_account_checks_changed_custom_domain` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_account_hosting_mismatch_fails_before_dependency_queries` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_account_location_mismatch_fails_before_dependency_queries` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_account_with_hosting_skips_dependency_preparation` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_account_without_hosting_is_rejected_before_dependency_queries` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_generated_dependencies_are_reused_without_updates` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_existing_workload_identity_requires_all_three_metadata_fields` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_explicit_azure_linux_3_os_sku_is_accepted` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_group_read_error_is_preserved` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_invalid_storage_configuration_blocks` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_kubenet_is_rejected_even_with_overlay` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_missing_group_blocks_before_any_dependency_write` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_missing_operator_authority_blocks_all_writes` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_missing_or_unrecognized_network_policy_evidence_blocks_preflight` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_missing_validation_permission_blocks_without_repair` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_missing_vm_size_sku_or_capacity_is_unverified` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_mixed_vm_sizes_pass_when_every_size_meets_capacity` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_new_account_allows_hosting_configuration` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_new_account_checks_actual_custom_domain_with_root_client` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_non_overlay_networking_is_rejected` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_operator_requirements_follow_request_intent_and_target_scope` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_other_role_assignment_errors_are_not_ignored` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_partial_custom_grants_must_cover_all_existing_requirements` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_preflight_returns_results_without_mutating_request` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_qualifying_requirements_cannot_be_combined_across_pools` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_resolved_management_and_workload_identity_cannot_be_same` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_restricted_storage_and_lrs_do_not_warn_or_block` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_role_assignment_conflict_must_match_principal_role_scope_and_condition` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_role_assignment_race_reuses_only_verified_identical_assignment` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_sandbox_label_requires_exact_lowercase_true` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_service_errors_are_preserved_with_visible_resource_context` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_smaller_manual_or_actual_vm_size_fails_pool_capacity` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_standard_aks_offering_does_not_restrict_pricing_tier` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_supplied_dependencies_need_no_grant_write_permission` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_supplied_storage_must_match_account_region` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_system_pool_must_be_succeeded` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_top_level_vm_size_capacity_still_passes` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unavailable_generated_storage_name_blocks_before_writes` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unavailable_or_unverified_domain_blocks_dependency_creation` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unknown_storage_public_network_state_blocks` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unreadable_assignment_authority_is_not_silently_skipped` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unreadable_caller_permissions_block_preflight` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unreadable_resources_are_unverified_not_absent` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_unverified_role_assignment_conflict_preserves_original_error` | - |
| `test_agent_hosting_preparation.py::AgentHostingPreparationTests::test_workload_identity_does_not_require_operator_assign_action` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_another_role_can_fill_only_the_missing_wildcard_actions` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_deterministic_account_based_names` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_excluded_or_conditional_grants_cannot_take_fast_path` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_image_baseline_accepts_only_same_series_at_or_above_minimum` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_resource_type_validation` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_wildcard_data_permissions_use_their_own_exclusions_and_grants` | - |
| `test_agent_hosting_preparation.py::AgentHostingValueTests::test_wildcard_requirements_do_not_bypass_write_or_delete_exclusions` | - |
| `test_api_properties.py::CognitiveServicesApiPropertiesTests::test_cognitiveservices_create_api_properties` | - |
| `test_byox.py::CognitiveServicesByoxTests::test_cognitiveservices_encryption` | - |
| `test_cognitiveservices_command.py::CognitiveServicesCommandTests::test_cognitiveservices_account_list_kinds` | - |
| `test_cognitiveservices_command.py::CognitiveServicesCommandTests::test_cognitiveservices_account_list_skus` | - |
| `test_cognitiveservices_command.py::CognitiveServicesCommandTests::test_cognitiveservices_account_list_skus_legacy` | - |
| `test_cognitiveservices_command.py::CognitiveServicesCommandTests::test_cognitiveservices_account_list_usage` | - |
| `test_cognitiveservices_command.py::CognitiveServicesCommandTests::test_cognitiveservices_crud` | - |
| `test_commitment_plan.py::CognitiveServicesCommitmentPlanTests::test_cognitiveservices_commitment_plan` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_create_builds_expected_payload_shape` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_create_omits_vm_priority_by_default` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_create_passes_vm_priority_when_provided` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_create_returns_poller_without_waiting` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_delete_returns_poller_without_waiting` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_list_passes_through_to_client` | - |
| `test_compute.py::CognitiveServicesComputeUnitTests::test_show_passes_through_to_client` | - |
| `test_costcontrol.py::CognitiveServicesCostControlScenarioTests::test_cognitiveservices_account_costcontrol_crud` | - |
| `test_custom_domain.py::CognitiveServicesCustomDomainTests::test_cognitiveservices_custom_domain` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentCliUnitTests::test_cognitiveservices_deployment_cli_help` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentCliUnitTests::test_cognitiveservices_deployment_cli_provider_arguments` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentCliUnitTests::test_cognitiveservices_deployment_cli_rejects_country_names` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentCliUnitTests::test_cognitiveservices_deployment_cli_requires_anthropic_provider_arguments` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_anthropic_format_casing` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_country_codes` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_empty_provider_fields` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_existing_options` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_invalid_country` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_missing_provider_fields` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_provider_data` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_provider_data_optional` | - |
| `test_deployment_unit.py::CognitiveServicesDeploymentUnitTests::test_cognitiveservices_deployment_sdk_serialization` | - |
| `test_identity.py::CognitiveServicesIdentityTests::test_cognitiveservices_identity` | - |
| `test_identity.py::CognitiveServicesIdentityTests::test_cognitiveservices_identity_assign_when_create` | - |
| `test_network_rules.py::CognitiveServicesNetworkRulesTests::test_cognitiveservices_network_rules` | - |
| `test_private_endpoint.py::CognitiveServicesPrivateEndpointTests::test_cognitiveservices_private_endpoint` | - |
| `test_private_endpoint.py::CognitiveServicesPrivateEndpointTests::test_cognitiveservices_private_endpoint_connection` | - |
| `test_subscription_level_apis.py::CognitiveServicesTests::test_cognitiveservices_list_models` | - |
| `test_subscription_level_apis.py::CognitiveServicesTests::test_cognitiveservices_list_usages` | - |

## Tests with `@live_only()` (15)

| Test | Result | Decorator location |
| --- | --- | --- |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentScenarioTests::test_adapter_deployment_create_show_list_delete` | skipped | method `test_adapter_deployment.py:196`, class `test_adapter_deployment.py:154` |
| `test_adapter_deployment.py::CognitiveServicesAdapterDeploymentScenarioTests::test_adapter_deployment_list_empty` | passed | class `test_adapter_deployment.py:154` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_basic` | failed | method `test_agent.py:562` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_complete` | failed | method `test_agent.py:817` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_errors` | passed | method `test_agent.py:975` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_from_source` | failed | method `test_agent.py:881` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_environment_variables` | failed | method `test_agent.py:717` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_registry` | failed | method `test_agent.py:619` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_resources` | failed | method `test_agent.py:668` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_create_with_scaling` | failed | method `test_agent.py:768` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_logs_show_basic` | failed | method `test_agent.py:1075` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_logs_show_with_options` | failed | method `test_agent.py:1121` |
| `test_agent.py::CognitiveServicesAgentTests::test_agent_start_with_show_logs` | failed | method `test_agent.py:1177` |
| `test_compute.py::CognitiveServicesComputeScenarioTests::test_cognitiveservices_compute_create_show_delete` | failed | class `test_compute.py:157` |
| `test_compute.py::CognitiveServicesComputeScenarioTests::test_cognitiveservices_compute_list_empty` | failed | class `test_compute.py:157` |
