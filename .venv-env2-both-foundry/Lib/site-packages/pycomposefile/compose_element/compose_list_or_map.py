from .compose_datatype_transformer import ComposeDataTypeTransformer


class ComposeListOrMapElement(ComposeDataTypeTransformer, dict):
    def isValueEmpty(self, line):
        line = line.rstrip("=")
        if "=" not in line:
            return True
        else:
            return False

    def evaluate_from_string(self, source_string):
        source_string = self.replace_environment_variables(source_string)
        if self.isValueEmpty(source_string):
            value = None
            key = source_string.rstrip("=")
        else:
            key, value = source_string.split("=", 1)
        self[key] = value

    def evaluate_from_list(self, source_list):
        for line in source_list:
            self.evaluate_from_string(line)

    def evaluate_from_dict(self, config, compose_path):
        for key in config.keys():
            value = config[key]
            if value is None:
                pass
            elif isinstance(value, dict):
                value = self.transform(value, key, compose_path)
            elif isinstance(value, list):
                new_list = []
                for v in value:
                    new_list.append(self.replace_environment_variables(v))
                value = new_list
            else:
                value = self.replace_environment_variables(value)
            self[key] = value

    def __init__(self, config, key=None, compose_path=None,):
        if compose_path is not None:
            self.compose_path = f"{compose_path}/{key}"
        if config is None:
            pass
        else:
            if isinstance(config, dict):
                self.evaluate_from_dict(config, compose_path)
            elif isinstance(config, list):
                self.evaluate_from_list(config)
            elif isinstance(config, str):
                self.evaluate_from_string(config)
