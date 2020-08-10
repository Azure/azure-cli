# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphGlobalExtendedPropertyBatch(Model):
    """GraphGlobalExtendedPropertyBatch.

    :param property_name_filters:
    :type property_name_filters: list of str
    :param subject_descriptors:
    :type subject_descriptors: list of :class:`str <graph.v4_1.models.str>`
    """

    _attribute_map = {
        'property_name_filters': {'key': 'propertyNameFilters', 'type': '[str]'},
        'subject_descriptors': {'key': 'subjectDescriptors', 'type': '[str]'}
    }

    def __init__(self, property_name_filters=None, subject_descriptors=None):
        super(GraphGlobalExtendedPropertyBatch, self).__init__()
        self.property_name_filters = property_name_filters
        self.subject_descriptors = subject_descriptors
