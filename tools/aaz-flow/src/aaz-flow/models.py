# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from dataclasses import dataclass


@dataclass
class AAZRequest:
    name: str
    swagger_module_path: str
    resource_provider: str
    swagger_tag: str
