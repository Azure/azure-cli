# coding=utf-8
# --------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class VssJsonCollectionWrapperBase(Model):
    """VssJsonCollectionWrapperBase.

    :param count:
    :type count: int
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'}
    }

    def __init__(self, count=None):
        super(VssJsonCollectionWrapperBase, self).__init__()
        self.count = count
