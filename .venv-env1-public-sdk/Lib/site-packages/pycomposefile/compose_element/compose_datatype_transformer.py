import re
import os


class EmptyOrUnsetException(Exception):
    def __init__(self, variable_name, *args: object) -> None:
        self.variable_name = variable_name
        super().__init__(*args)

    def __str__(self) -> str:
        return f"Failed to evaluate mandatory variable {self.variable_name}"


class ComposeDataTypeTransformer:
    transform = str
    valid_values = None

    def transform_supported_data(self, value):
        if self.valid_values is not None:
            value = self.transform_and_validate_supported_data(value)
        else:
            value = self.transform(self.replace_environment_variables(value))
        return value

    def test_valid_string(self, value):
        if isinstance(value, str):
            return value in self.valid_values
        return False

    def test_valid_int(self, value):
        if isinstance(value, int):
            return self.valid_values[0] <= value <= self.valid_values[1]
        return False

    def transform_and_validate_supported_data(self, value):
        # TODO: if the data is an integer or decimal, should there be a "between" check?
        transformed = self.transform(self.replace_environment_variables(value))
        if self.test_valid_string(transformed) or self.test_valid_int(transformed):
            return transformed
        else:
            # TODO: Should this return None or should this raise?
            return None

    def replace_environment_variables(self, value):
        value = str(value)
        value = self.replace_environment_variables_with_braces(value)
        value = self.replace_environment_variables_without_braces(value)
        value = self.replace_environment_variables_with_empty_unset(value)
        value = self.replace_environment_variables_with_unset(value)
        value = self.replace_mandatory_variables_with_empty_or_unset(value)
        value = self.replace_mandatory_variables_with_unset(value)
        value = self.do_not_replace_variables(value)

        return value

    def update_value_with_resolved_environment(self, env_variable_name, env_variable_value, source_string):
        if env_variable_value is None:
            env_variable_value = ""
        return re.sub(env_variable_name, env_variable_value, source_string)

    def replace_environment_variables_with_empty_unset(self, value):
        capture = re.compile(r"(\$+)\{(?P<variablename>\w+)\:-(?P<defaultvalue>[^$]*?)\}")
        matches = capture.search(value)
        if matches is not None and matches[1] == "$$":
            return value
        while matches:
            env_var = os.environ.get(matches.group("variablename"))
            default_value = matches.group("defaultvalue")
            if env_var is None or len(env_var) == 0:
                env_var = default_value
            escaped = re.sub(r"([*+?{}])", r"\\\1", matches[0])  # escape special characters
            value = self.update_value_with_resolved_environment(f"\\{escaped}", env_var, value)
            matches = capture.search(value)
        return value

    def replace_environment_variables_with_unset(self, value):
        capture = re.compile(r"(\$+)\{(?P<variablename>\w+)-(?P<defaultvalue>.+)\}")
        matches = capture.search(value)
        if matches is not None and matches[1] == "$$":
            return value
        while matches:
            env_var = os.environ.get(matches.group("variablename"))
            default_value = matches.group("defaultvalue")
            if env_var is None:
                env_var = default_value
            value = self.update_value_with_resolved_environment(f"{matches[0]}", env_var, value)
            matches = capture.search(value)
        return value

    def replace_mandatory_variables_with_empty_or_unset(self, value):
        capture = re.compile(r"(\$+)\{(?P<variablename>\w+)\:\?(err)\}")
        matches = capture.search(value)
        if matches is not None and matches[1] == "$$":
            return value
        while matches:
            env_var = os.environ.get(matches.group("variablename"))
            if env_var is None or len(env_var) == 0:
                raise EmptyOrUnsetException(matches.group("variablename"))
            to_be_replaced = r"\$\{" + matches.group('variablename') + r"\:\?err\}"
            value = self.update_value_with_resolved_environment(to_be_replaced, env_var, value)
            matches = capture.search(value)
        return value

    def replace_mandatory_variables_with_unset(self, value):
        capture = re.compile(r"(\$+)\{(?P<variablename>\w+)\?(err)\}")
        matches = capture.search(value)
        if matches is not None and matches[1] == "$$":
            return value
        while matches:
            env_var = os.environ.get(matches.group("variablename"))
            if env_var is None:
                raise EmptyOrUnsetException(matches.group("variablename"))
            to_be_replaced = r"\$\{" + matches.group('variablename') + r"\?err\}"
            value = self.update_value_with_resolved_environment(to_be_replaced, env_var, value)
            matches = capture.search(value)
        return value

    def replace_environment_variables_with_braces(self, value):
        capture = re.compile(r"\$\{(?P<variablename>\w+)\}")
        matches = capture.search(value)
        if matches is not None and matches[1] == "$$":
            return value
        while matches:
            env_var = os.environ.get(matches.group("variablename"))
            value = self.update_value_with_resolved_environment(f"\\{matches[0]}", env_var, value)
            matches = capture.search(value)
        return value

    def do_not_replace_variables(self, value):
        value = re.sub(r"\$\$", "$", value)
        return value

    def replace_environment_variables_without_braces(self, value):
        capture = re.compile(r"(\$+)(?P<variablename>\w+)")
        matches = capture.search(value)
        if matches is not None and matches[1] == "$$":
            return value
        while matches:
            env_var = os.environ.get(matches.group("variablename"))
            value = self.update_value_with_resolved_environment(f"\\{matches[0]}", env_var, value)
            matches = capture.search(value)
        return value
