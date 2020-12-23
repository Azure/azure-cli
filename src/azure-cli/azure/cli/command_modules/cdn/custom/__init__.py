# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .custom import default_content_types  # pylint: disable=unused-import
from .custom import list_profiles          # pylint: disable=unused-import
from .custom import update_endpoint        # pylint: disable=unused-import
from .custom import create_condition       # pylint: disable=unused-import
from .custom import create_action          # pylint: disable=unused-import
from .custom import add_rule               # pylint: disable=unused-import
from .custom import add_condition          # pylint: disable=unused-import
from .custom import add_action             # pylint: disable=unused-import
from .custom import remove_rule            # pylint: disable=unused-import
from .custom import remove_condition       # pylint: disable=unused-import
from .custom import remove_action          # pylint: disable=unused-import
from .custom import create_endpoint        # pylint: disable=unused-import
from .custom import create_custom_domain   # pylint: disable=unused-import
from .custom import enable_custom_https    # pylint: disable=unused-import
from .custom import update_origin          # pylint: disable=unused-import
from .custom import create_origin          # pylint: disable=unused-import
from .custom import update_profile         # pylint: disable=unused-import
from .custom import create_profile         # pylint: disable=unused-import
from .custom import create_origin_group    # pylint: disable=unused-import
from .custom import update_origin_group    # pylint: disable=unused-import

from .custom_waf import show_endpoint_waf_policy_link                 # pylint: disable=unused-import
from .custom_waf import set_endpoint_waf_policy_link                  # pylint: disable=unused-import
from .custom_waf import remove_endpoint_waf_policy_link               # pylint: disable=unused-import
from .custom_waf import list_waf_managed_rule_set                     # pylint: disable=unused-import
from .custom_waf import list_waf_managed_rule_groups                  # pylint: disable=unused-import
from .custom_waf import set_waf_policy                                # pylint: disable=unused-import
from .custom_waf import add_waf_policy_managed_rule_set               # pylint: disable=unused-import
from .custom_waf import remove_waf_policy_managed_rule_set            # pylint: disable=unused-import
from .custom_waf import list_waf_policy_managed_rule_sets             # pylint: disable=unused-import
from .custom_waf import show_waf_policy_managed_rule_set              # pylint: disable=unused-import
from .custom_waf import set_waf_managed_rule_group_override           # pylint: disable=unused-import
from .custom_waf import delete_waf_managed_rule_group_override        # pylint: disable=unused-import
from .custom_waf import list_waf_policy_managed_rule_group_overrides  # pylint: disable=unused-import
from .custom_waf import show_waf_managed_rule_group_override          # pylint: disable=unused-import
from .custom_waf import set_waf_custom_rule                           # pylint: disable=unused-import
from .custom_waf import delete_waf_custom_rule                        # pylint: disable=unused-import
from .custom_waf import show_waf_custom_rule                          # pylint: disable=unused-import
from .custom_waf import list_waf_custom_rules                         # pylint: disable=unused-import
from .custom_waf import set_waf_rate_limit_rule                       # pylint: disable=unused-import
from .custom_waf import delete_waf_rate_limit_rule                    # pylint: disable=unused-import
from .custom_waf import show_waf_rate_limit_rule                      # pylint: disable=unused-import
from .custom_waf import list_waf_rate_limit_rules                     # pylint: disable=unused-import
