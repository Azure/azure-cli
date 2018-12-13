# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def validate_component_version(namespace):
    if namespace.component_version:
        import re
        invalid_component_versions = [cv for cv in namespace.component_version if not re.match('^[^=]+=[^=]+$', cv)]
        if any(invalid_component_versions):
            raise ValueError('Component verions must be in the form component=version. '
                             'Invalid component version(s): {}'.format(', '.join(invalid_component_versions)))
