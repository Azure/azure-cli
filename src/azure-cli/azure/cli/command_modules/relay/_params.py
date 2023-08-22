# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import tags_type, get_enum_type, resource_group_name_type, name_type, get_location_type, get_resource_name_completion_list, get_three_state_flag
from azure.cli.core.commands.validators import get_default_location_from_resource_group


def load_arguments(self, _):  # pylint: disable=unused-argument
    pass
