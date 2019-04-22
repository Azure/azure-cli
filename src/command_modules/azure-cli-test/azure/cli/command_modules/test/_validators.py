# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def example_validator(cmd, namespace):
    if not getattr(namespace, 'property', None):
        return

    # TODO: do something with namespace.property