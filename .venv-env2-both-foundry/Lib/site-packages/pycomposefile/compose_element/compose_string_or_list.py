from .compose_datatype_transformer import ComposeDataTypeTransformer


class ComposeStringOrListElement(ComposeDataTypeTransformer, list):
    def __init__(self, config, key=None, compose_path=None,):
        if compose_path is not None:
            self.compose_path = f"{compose_path}/{key}"

        if isinstance(config, list):
            for v in config:
                if isinstance(v, str):
                    v = v.strip("[]").rstrip().lstrip().strip("'")
                    self.append_transform(v)
                else:
                    self.append_transform(v, key, compose_path)
        else:
            self.append_transform(config, key, compose_path)

    def append(self, __object) -> None:
        if isinstance(__object, list):
            for element in __object:
                super().append(element)
        else:
            super().append(__object)

    def append_transform(self, config_value, key=None, compose_path=None):
        if isinstance(config_value, str) or isinstance(config_value, int):
            self.append(self.transform_supported_data(config_value))
        else:
            self.append(self.transform(config_value, key, compose_path))
