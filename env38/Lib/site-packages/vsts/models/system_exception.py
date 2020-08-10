# coding=utf-8
# --------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class SystemException(Model):
    """SystemException.
    :param class_name:
    :type class_name: str
    :param inner_exception:
    :type inner_exception: :class:`SystemException <vsts.models.SystemException>`
    :param message:
    :type message: str
    """

    _attribute_map = {
        'class_name': {'key': 'ClassName', 'type': 'str'},
        'message': {'key': 'Message', 'type': 'str'},
        'inner_exception': {'key': 'InnerException', 'type': 'SystemException'}
    }

    def __init__(self, class_name=None, message=None, inner_exception=None):
        super(SystemException, self).__init__()
        self.class_name = class_name
        self.message = message
        self.inner_exception = inner_exception
