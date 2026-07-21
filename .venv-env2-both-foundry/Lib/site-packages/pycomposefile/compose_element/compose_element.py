from decimal import Decimal
from .compose_datatype_transformer import ComposeDataTypeTransformer


class ComposeByteValue(ComposeDataTypeTransformer):
    compose_path = ""
    value = 0.0
    _conversions = {
        'gb': 1073741824,
        'g': 1073741824,
        'mb': 1048576,
        'kb': 1024,
        'm': 1048576,
        'k': 1024,
        'b': 1,
    }

    def convert_value(self, value_string):
        value_string = value_string.lower()
        for key in self._conversions.keys():
            if value_string.endswith(key):
                return Decimal(value_string.rstrip(key)) * self._conversions[key]
        return Decimal(value_string)

    def __init__(self, config, compose_path=None):
        if compose_path is not None:
            self.compose_path = compose_path
        self.value = self.convert_value(config)

    def as_gigabytes(self):
        return self.value / self._conversions['gb']


class ComposeElement(ComposeDataTypeTransformer):
    element_keys = {}

    def __init__(self, config, compose_path=""):
        self.compose_path = compose_path
        for key in self.element_keys.keys():
            config_element = config.pop(key, None)
            key_config = self.element_keys[key]
            self.set_supported_property_from_config(key, key_config, config_element, compose_path)
        for key in config.keys():
            # raise Exception(f"Failed to map {key} in {compose_path}")
            pass

    def set_supported_property_from_config(self, key, key_config, value, compose_path):
        if type(key_config[0]) is tuple:
            self.transform, self.valid_values = key_config[0]
        else:
            self.transform = key_config[0]
            self.valid_values = None

        if self.transform is not None:
            if isinstance(value, dict):
                value = self.transform(value, key, compose_path)
            elif isinstance(value, list):
                value = self.transform(value, key, compose_path)
            elif value is not None:
                value = self.transform_supported_data(value)
        else:
            # TODO: Logging message if value was not None
            value = None
        self.__setattr__(key, value)

    @classmethod
    def from_parsed_yaml(cls, config, name, compose_path):
        if config is None:
            return None
        compose_path = f"{compose_path}/{name}"
        return cls(config, compose_path)
