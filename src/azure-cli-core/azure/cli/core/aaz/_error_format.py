# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
# from azure.core.exceptions import ODataV4Format


registered_error_formats = {}


def register_error_format(name):
    def decorator(cls):
        if name in registered_error_formats:
            assert registered_error_formats[name] == cls
        else:
            registered_error_formats[name] = cls
        return cls
    return decorator


@register_error_format("ODataV4Format")
class AAZODataV4Format:
    ERROR_LABEL = "error"
    CODE_LABEL = "code"
    MESSAGE_LABEL = "message"
    TARGET_LABEL = "target"
    DETAILS_LABEL = "details"
    INNERERROR_LABEL = "innererror"

    @staticmethod
    def get_object_prop(obj, label, default=None):
        for key in obj:
            if key.lower() == label.lower():
                return obj[key]
        return default

    def __init__(self, json_object):
        json_object = self.get_object_prop(json_object, self.ERROR_LABEL, default=json_object)
        cls = self.__class__

        # Required fields, but assume they could be missing still to be robust
        self.code = self.get_object_prop(json_object, cls.CODE_LABEL)
        self.message = self.get_object_prop(json_object, cls.MESSAGE_LABEL)

        if not (self.code or self.message):
            raise ValueError("Impossible to extract code/message from received JSON:\n" + json.dumps(json_object))

        # Optional fields
        self.target = self.get_object_prop(json_object, cls.TARGET_LABEL)

        # details is recursive of this very format
        self.details = []
        for detail_node in self.get_object_prop(json_object, cls.DETAILS_LABEL) or []:
            try:
                self.details.append(self.__class__(detail_node))
            except Exception:  # pylint: disable=broad-except
                pass
        self.innererror = self.get_object_prop(json_object, cls.INNERERROR_LABEL) or {}

    @property
    def error(self):
        import warnings
        warnings.warn(
            "error.error from azure exceptions is deprecated, just simply use 'error' once",
            DeprecationWarning,
        )
        return self

    def __str__(self):
        return "({}) {}\n{}".format(
            self.code,
            self.message,
            self.message_details()
        )

    def message_details(self):
        """Return a detailled string of the error.
        """
        # () -> str
        error_str = "Code: {}".format(self.code)
        error_str += "\nMessage: {}".format(self.message)
        if self.target:
            error_str += "\nTarget: {}".format(self.target)

        if self.details:
            error_str += "\nException Details:"
            for error_obj in self.details:
                # Indent for visibility
                error_str += "\n".join("\t" + s for s in str(error_obj).splitlines())

        if self.innererror:
            error_str += "\nInner error: {}".format(
                json.dumps(self.innererror, indent=4)
            )
        return error_str


# pylint: disable=too-few-public-methods
class TypedErrorInfo:
    """Additional info class defined in ARM specification.

    https://github.com/Azure/azure-resource-manager-rpc/blob/master/v1.0/common-api-details.md#error-response-content
    """

    def __init__(self, type, info):  # pylint: disable=redefined-builtin
        self.type = type
        self.info = info

    def __str__(self):
        """Cloud error message."""
        error_str = "Type: {}".format(self.type)
        error_str += "\nInfo: {}".format(json.dumps(self.info, indent=4))
        return error_str


@register_error_format("MgmtErrorFormat")
class AAZMgmtErrorFormat(AAZODataV4Format):
    """Describe error format from ARM, used at the base or inside "details" node.

    This format is compatible with ODataV4 format.
    https://github.com/Azure/azure-resource-manager-rpc/blob/master/v1.0/common-api-details.md#error-response-content
    """

    ADDITIONALINFO_LABEL = "additionalInfo"

    def __init__(self, json_object):
        # Parse the ODatav4 part
        super().__init__(json_object)
        json_object = self.get_object_prop(json_object, self.ERROR_LABEL, default=json_object)

        # ARM specific annotations
        self.additional_info = [
            TypedErrorInfo(additional_info["type"], additional_info["info"])
            for additional_info in self.get_object_prop(json_object, self.ADDITIONALINFO_LABEL, [])
        ]

    def __str__(self):
        error_str = super().__str__()

        if self.additional_info:
            error_str += "\nAdditional Information:"
            for error_info in self.additional_info:
                error_str += str(error_info)

        return error_str
