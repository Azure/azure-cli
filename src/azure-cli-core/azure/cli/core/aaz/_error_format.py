from azure.mgmt.core.exceptions import ARMErrorFormat


registered_error_formats = {}


def register_error_format(name):
    def decorator(cls):
        if name in registered_error_formats:
            assert registered_error_formats[name] == cls
        else:
            registered_error_formats[name] = cls
        return cls
    return decorator


@register_error_format("MgmtErrorFormat")
class AAZMgmtErrorFormat(ARMErrorFormat):
    pass
