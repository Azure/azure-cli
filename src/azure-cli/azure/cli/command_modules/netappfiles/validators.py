# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from functools import reduce
from azure.cli.core.azclierror import ValidationError

from azure.cli.command_modules.netappfiles._client_factory import (
    volumes_mgmt_client_factory,
    volume_quota_rules_mgmt_client_factory)

from knack.log import get_logger
logger = get_logger(__name__)


def rgetattr(obj, attr, *args):
    """See https://stackoverflow.com/questions/31174295/getattr-and-setattr-on-nested-objects"""
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))


# Command validators
def validate_resync_quotarule(cmd, namespace):
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
    # Get volume params
    netAppVolumeClient = volumes_mgmt_client_factory(cmd.cli_ctx, None)
    netAppVolumeQuotaRuleClient = volume_quota_rules_mgmt_client_factory(cmd.cli_ctx, None)
    logger.debug("ANF validate_resync_quotarule:")
    volume = netAppVolumeClient.get(namespace.resource_group_name, namespace.account_name, namespace.pool_name,
                                    namespace.volume_name)
    logger.debug("ANF validate_resync_quotarule: get volume %s  ", volume.name)
    if volume.data_protection is not None and volume.data_protection.replication is not None:
        endpointType = rgetattr(volume, 'data_protection.replication.endpoint_type')
        remoteVolumeResourceId = rgetattr(volume, 'data_protection.replication.remote_volume_resource_id')
        logger.debug("ANF validate_resync_quotarule: get dataProtection endpointType: %s  ", endpointType)
        if endpointType is not None and endpointType == 'Src':
            logger.debug("ANF validate_resync_quotarule: Get dataprotection volume for volume %s RemoteVolumeResourceId\
                         %s:", namespace.volume_name, remoteVolumeResourceId)
            if is_valid_resource_id(remoteVolumeResourceId):
                resource_parts = parse_resource_id(remoteVolumeResourceId)
                logger.debug("ANF validate_resync_quotarule: Destination volume resourceID parts %s:", resource_parts)
                destGroupName = resource_parts['resource_group']
                destAccountName = resource_parts['name']
                destPoolName = resource_parts['child_name_1']
                destVolumeName = resource_parts['child_name_2']
                logger.debug("ANF validate_resync_quotarule: Get quota rules for volume %s:", destVolumeName)
                try:
                    destVol = netAppVolumeClient.get(destGroupName, destAccountName, destPoolName, destVolumeName)
                    if destVol is not None:
                        destVolumeQuotaRules = netAppVolumeQuotaRuleClient.list_by_volume(destGroupName,
                                                                                          destAccountName, destPoolName,
                                                                                          destVolumeName)
                        rules_list = list(destVolumeQuotaRules)

                except:
                    raise ValidationError("\nDestination volume not found check remote_volume_resource_id: '{}'."
                                          .format(remoteVolumeResourceId))
            else:
                logger.warning("ANF validate_resync_quotarule: The remote_volume_resource_id %s is not a valid\
                               resourceId:", remoteVolumeResourceId)
            if rules_list is not None and not rules_list:
                logger.debug("ANF validate_resync_quotarule: There are no quota rules for volume:")
            else:
                logger.debug("ANF validate_resync_quotarule: There are %s quota rules for this volume, show warning",
                             len(rules_list))
                logger.warning("\nIf any quota rules exists on destination volume they will be overwritten\
with source volume's quota rules.")
    else:
        logger.debug("ANF validate_resync_quotarule: Volume %s is not in a CRR relationship:", namespace.volume_name)
        raise ValueError("\nThis volume is not configured for CRR replication.")
