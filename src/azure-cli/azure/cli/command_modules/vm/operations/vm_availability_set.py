# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.aaz import register_command, has_value, AAZStrArg
from ..aaz.latest.vm.availability_set import Update as _Update

logger = get_logger(__name__)

PPG_RID_TEMPLATE = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/proximityPlacementGroups/{}"


class AvailabilitySetUpdate(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ppg = AAZStrArg(
            options=["--ppg"],
            help="Name or ID of the proximity placement group that the availability set should be associated with."
        )
        args_schema.sku._registered = False
        args_schema.platform_fault_domain_count._registered = False
        args_schema.proximity_placement_group._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.ppg):
            ppg = args.ppg.to_serialized_data()
            args.proximity_placement_group.id = ppg if is_valid_resource_id(ppg) else PPG_RID_TEMPLATE.format(self.ctx.subscription_id, args.resource_group, ppg)


@register_command(
    'vm availability-set convert'
)
class AvailabilitySetConvert(_Update):
    """Convert an Azure Availability Set to contain VMs with managed disks.

    :example: Convert an availabiity set to use managed disks by name.
        az vm availability-set convert -g MyResourceGroup -n MyAvSet

    :example: Convert an availability set to use managed disks by ID.
        az vm availability-set convert --ids $(az vm availability-set list -g MyResourceGroup --query "[].id" -o tsv)
    """

    AZ_SUPPORT_GENERIC_UPDATE = False

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.sku._registered = False
        args_schema.platform_fault_domain_count._registered = False
        args_schema.proximity_placement_group._registered = False
        args_schema.additional_scheduled_events._registered = False
        args_schema.enable_user_reboot_scheduled_events._registered = False
        args_schema.enable_user_redeploy_scheduled_events._registered = False
        return args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.AvailabilitySetsGet(ctx=self.ctx)()
        if self.pre_instance_update(self.ctx.vars.instance):
            return
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.vars.instance)
        self.AvailabilitySetsCreateOrUpdate(ctx=self.ctx)()
        self.post_operations()

    def pre_instance_update(self, instance):
        # end the operation if the availability set is already configured for managed disks
        if instance.sku.name == 'Aligned':
            logger.warning("Availability set '%s' is already configured for managed disks.", instance.name)
            return True

        instance.sku.name = 'Aligned'

        # double check whether the existing FD number is supported
        from ..custom import list_skus
        skus = list_skus(self, instance.location)
        av_sku = next((s for s in skus if s['resourceType'] == 'availabilitySets' and s['name'] == 'Aligned'), None)
        if av_sku and av_sku['capabilities']:
            max_fd = int(next((c['value'] for c in av_sku['capabilities'] if c['name'] == 'MaximumPlatformFaultDomainCount'), '0'))
            if max_fd and max_fd < instance.properties.platform_fault_domain_count:
                logger.warning("The fault domain count will be adjusted from %s to %s so to stay within region's "
                               "limitation", instance.properties.platform_fault_domain_count, max_fd)
                instance.properties.platform_fault_domain_count = max_fd
