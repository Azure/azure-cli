# coding=utf-8
# --------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from .vss_json_collection_wrapper_base import VssJsonCollectionWrapperBase


class VssJsonCollectionWrapper(VssJsonCollectionWrapperBase):
    """VssJsonCollectionWrapper.

    :param count:
    :type count: int
    :param value:
    :type value: object
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'value': {'key': 'value', 'type': 'object'}
    }

    def __init__(self, count=None, value=None):
        super(VssJsonCollectionWrapper, self).__init__(count=count)
        self.value = value
