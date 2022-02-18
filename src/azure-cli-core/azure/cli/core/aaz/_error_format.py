import json
from azure.core.exceptions import ODataV4Format


registered_error_formats = {
    "ODataV4Format": ODataV4Format,
}


def register_error_format(name):
    def decorator(cls):
        if name in registered_error_formats:
            assert registered_error_formats[name] == cls
        else:
            registered_error_formats[name] = cls
        return cls
    return decorator


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
class AAZMgmtErrorFormat(ODataV4Format):
    """Describe error format from ARM, used at the base or inside "details" node.

    This format is compatible with ODataV4 format.
    https://github.com/Azure/azure-resource-manager-rpc/blob/master/v1.0/common-api-details.md#error-response-content
    """

    def __init__(self, json_object):
        # Parse the ODatav4 part
        super(AAZMgmtErrorFormat, self).__init__(json_object)
        if "error" in json_object:
            json_object = json_object["error"]

        # ARM specific annotations
        self.additional_info = [
            TypedErrorInfo(additional_info["type"], additional_info["info"])
            for additional_info in json_object.get("additionalInfo", [])
        ]

    def __str__(self):
        error_str = super(AAZMgmtErrorFormat, self).__str__()

        if self.additional_info:
            error_str += "\nAdditional Information:"
            for error_info in self.additional_info:
                error_str += str(error_info)

        return error_str
