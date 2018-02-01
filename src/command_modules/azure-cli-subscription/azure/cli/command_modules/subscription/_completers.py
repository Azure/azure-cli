# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer


@Completer
def get_offer_type_completion_list(cmd, prefix, namespace):  # pylint: disable=unused-argument
    return ['MS-AZR-0017P', 'MS-AZR-0148P'] 
