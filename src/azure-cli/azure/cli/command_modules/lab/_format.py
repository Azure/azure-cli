# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def export_artifacts(formula):
    """ Exports artifacts from the given formula. This method removes some of the properties of the
        artifact model as they do not play important part for users in create or read context.
    """
    artifacts = []
    if formula and formula.get('formulaContent') and formula['formulaContent'].get('artifacts'):
        artifacts = formula['formulaContent']['artifacts']
        for artifact in formula['formulaContent']['artifacts']:
            artifact.pop('status', None)
            artifact.pop('deploymentStatusMessage', None)
            artifact.pop('vmExtensionStatusMessage', None)
            artifact.pop('installTime', None)
    return artifacts


def transform_artifact_source_list(artifact_source_list):
    return [transform_artifact_source(v) for v in artifact_source_list]


def transform_artifact_source(result):
    from collections import OrderedDict
    return OrderedDict([('name', result['name']),
                        ('sourceType', result['sourceType']),
                        ('status', result.get('status')),
                        ('uri', result.get('uri'))])


def transform_arm_template_list(arm_template_list):
    return [transform_arm_template(v) for v in arm_template_list]


def transform_arm_template(result):
    from collections import OrderedDict
    return OrderedDict([('name', result['name']),
                        ('resourceGroup', result['resourceGroup']),
                        ('publisher', result.get('publisher'))])


def transform_vm_list(vm_list):
    return [_transform_vm_dict(v) for v in vm_list]


def _transform_vm_dict(result):
    from collections import OrderedDict
    return OrderedDict([('name', result['name']),
                        ('location', result['location']),
                        ('osType', result['osType'])])


def transform_vm(result):
    from collections import OrderedDict
    return OrderedDict([('name', result.name),
                        ('location', result.location),
                        ('osType', result.os_type)])
