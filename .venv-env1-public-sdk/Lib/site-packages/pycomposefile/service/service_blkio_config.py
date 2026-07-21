
from pycomposefile.compose_element import ComposeElement, ComposeStringOrListElement


class IoConfig(ComposeElement):
    element_keys = {
        "path": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_read_bps-device_write_bps"),
        "rate": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_read_bps-device_write_bps"),
    }


class IoConfigList(ComposeStringOrListElement):
    transform = IoConfig.from_parsed_yaml


class WeightDevice(ComposeElement):
    element_keys = {
        "path": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#weight_device"),
        "weight": ((int, [10, 1000]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#weight_device"),
    }


class WeightDeviceList(ComposeStringOrListElement):
    transform = WeightDevice.from_parsed_yaml


class BlkioConfig(ComposeElement):
    element_keys = {
        "device_read_bps": (IoConfigList, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_read_bps-device_write_bps"),
        "device_write_bps": (IoConfigList, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_read_bps-device_write_bps"),
        "device_read_iops": (IoConfigList, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_read_iops-device_write_iops"),
        "device_write_iops": (IoConfigList, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_read_iops-device_write_iops"),
        "weight": ((int, [10, 1000]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#weight"),
        "weight_device": (WeightDeviceList, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#weight_device"),
    }
