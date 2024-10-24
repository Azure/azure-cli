# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_output_breaking_change, register_argument_deprecate

register_argument_deprecate('sql mi link create', '--target-database', '--databases')
register_argument_deprecate('sql mi link create', '--primary-availability-group-name',
                            '--partner-availability-group-name')
register_argument_deprecate('sql mi link create', '--secondary-availability-group-name',
                            '--instance-availability-group-name')
register_argument_deprecate('sql mi link create', '--source-endpoint', '--partner-endpoint')
register_output_breaking_change('sql mi link create',
                                description='Deprecated output properties: targetDatabase, '
                                            'primaryAvailabilityGroupName, secondaryAvailabilityGroupName'
                                            'sourceEndpoint, sourceReplicaId, targetReplicaId, '
                                            'linkState, lastHardenedLsn.'
                                            '\nNew output properties: databases, partnerAvailabilityGroupName,'
                                            ' instanceAvailabilityGroupName, partnerEndpoint,'
                                            ' distributedAvailabilityGroupName, instanceLinkRole,'
                                            ' partnerLinkRole, failoverMode, seedingMode.',
                                doc_link='aka.ms/mi-link-rest-api-create-or-update')

register_output_breaking_change('sql mi link show',
                                description='Deprecated output properties: targetDatabase, '
                                            'primaryAvailabilityGroupName, secondaryAvailabilityGroupName'
                                            'sourceEndpoint, sourceReplicaId, targetReplicaId, '
                                            'linkState, lastHardenedLsn.'
                                            '\nNew output properties: databases, partnerAvailabilityGroupName,'
                                            ' instanceAvailabilityGroupName, partnerEndpoint,'
                                            ' distributedAvailabilityGroupName, instanceLinkRole,'
                                            ' partnerLinkRole, failoverMode, seedingMode.',
                                doc_link='aka.ms/mi-link-rest-api-get')

register_output_breaking_change('sql mi link list',
                                description='Deprecated output properties: targetDatabase, '
                                            'primaryAvailabilityGroupName, secondaryAvailabilityGroupName'
                                            'sourceEndpoint, sourceReplicaId, targetReplicaId, '
                                            'linkState, lastHardenedLsn.'
                                            '\nNew output properties: databases, partnerAvailabilityGroupName,'
                                            ' instanceAvailabilityGroupName, partnerEndpoint,'
                                            ' distributedAvailabilityGroupName, instanceLinkRole,'
                                            ' partnerLinkRole, failoverMode, seedingMode.',
                                doc_link='aka.ms/mi-link-rest-api-list-by-instance')

register_output_breaking_change('sql mi link update',
                                description='Deprecated output properties: targetDatabase, '
                                            'primaryAvailabilityGroupName, secondaryAvailabilityGroupName'
                                            'sourceEndpoint, sourceReplicaId, targetReplicaId, '
                                            'linkState, lastHardenedLsn.'
                                            '\nNew output properties: databases, partnerAvailabilityGroupName,'
                                            ' instanceAvailabilityGroupName, partnerEndpoint,'
                                            ' distributedAvailabilityGroupName, instanceLinkRole,'
                                            ' partnerLinkRole, failoverMode, seedingMode.',
                                doc_link='aka.ms/mi-link-rest-api-create-or-update')
