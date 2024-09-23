# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_group_deprecate, register_command_deprecate
register_command_group_deprecate('sf cluster setting', redirect='sf cluster update')
# Warning Message: This command group has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.

register_command_group_deprecate('sf cluster upgrade-type', redirect='sf cluster update')
# Warning Message: This command group has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.

register_command_deprecate('sf cluster durability', redirect='sf cluster update')
# Warning Message: This command has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.

register_command_deprecate('sf cluster reliability update', redirect='sf cluster update')
# Warning Message: This command has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.

register_command_deprecate('sf cluster setting remove', redirect='sf cluster update')
# Warning Message: This command has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.

register_command_deprecate('sf cluster setting set', redirect='sf cluster update')
# Warning Message: This command has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.

register_command_deprecate('sf cluster upgrade-type set', redirect='sf cluster update')
# Warning Message: This command has been deprecated and will be removed in next breaking change release. Use `sf cluster update` instead.
