# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""The programming interfaces which 3rd party applcation can depend on."""

# pylint: disable=unused-import

from ._environment import get_config_dir
from ._profile import load_subscriptions

from ._completers import get_subscription_id_list
