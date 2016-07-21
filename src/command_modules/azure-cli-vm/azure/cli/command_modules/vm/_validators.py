#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import random

def nsg_name_validator(namespace):
    namespace.network_security_group_name = namespace.network_security_group_name \
        or '{}NSG{}'.format(namespace.vm_name, random.randint(1, 999))
