from knack.help import (HelpParameter as KnackHelpParameter, HelpExample as KnackHelpExample)
from knack.help import HelpAuthoringException
from knack.util import CLIError

class CliHelpExample(KnackHelpExample):  # pylint: disable=too-few-public-methods

    def __init__(self, _data):
        _data['name'] = _data.get('name', '')
        _data['text'] = _data.get('text', '')
        super(CliHelpExample, self).__init__(_data)

        self.command = _data.get('command', '')
        self.description = _data.get('description', '')

        self.min_profile = _data.get('min_profile', '')
        self.max_profile = _data.get('max_profile', '')

        self.text = "{}\n{}".format(self.description, self.command) if self.description else self.command

class CliHelpParameter(KnackHelpParameter):  # pylint: disable=too-many-instance-attributes

    def __init__(self, **kwargs):
        super(CliHelpParameter, self).__init__(**kwargs)
        self.raw_value_sources = []

    def update_from_data(self, data):
        if self.name != data.get('name'):
            raise HelpAuthoringException(u"mismatched name {} vs. {}"
                                         .format(self.name,
                                                 data.get('name')))

        if data.get('summary'):
            self.short_summary = data.get('summary')

        if data.get('description'):
            self.long_summary = data.get('description')

        if data.get('value-source'): # todo: change to value-sources
            self.raw_value_sources = data.get('value-source')
            for value_source in self.raw_value_sources:
                val_str = self._raw_value_source_to_string(value_source)
                if val_str:
                    self.value_sources.append(val_str)

    @staticmethod
    def _raw_value_source_to_string(value_source):
        if "string" in value_source:
            return value_source["string"]
        elif "link" in value_source:
            link_text = ""
            if "url" in value_source["link"]:
                link_text = "url: {} ".format(value_source["link"]["url"])
            if "command" in value_source["link"]:
                link_text = "command: {} ".format(value_source["link"]["command"])
            return link_text
        return ""


def get_yaml_help_for_nouns(nouns, cmd_loader_map_ref, is_group):
    import inspect
    import os

    def _parse_yaml_from_string(text, help_file_path):
        import yaml

        dir_name, base_name = os.path.split(help_file_path)

        pretty_file_path = os.path.join(os.path.basename(dir_name), base_name)

        try:
            data = yaml.load(text)
            if not data:
                raise CLIError("Error: Help file {} is empty".format(pretty_file_path))
            return data
        except yaml.YAMLError as e:
            raise CLIError("Error parsing {}:\n\n{}".format(pretty_file_path, e))

    command_nouns = " ".join(nouns)
    loader = None
    if is_group:
        for k, v in cmd_loader_map_ref.items():
            if k.startswith(command_nouns):
                loader = v[0]
                break
    else:
        loader = cmd_loader_map_ref.get(command_nouns, [None])[0]

    if loader:
        loader_file_path = inspect.getfile(loader.__class__)
        dir_name = os.path.dirname(loader_file_path)
        files = os.listdir(dir_name)
        for file in files:
            if file.endswith((".yaml", ".yml")):
                help_file_path = os.path.join(dir_name, file)
                with open(help_file_path, "r") as f:
                    text = f.read()
                    return _parse_yaml_from_string(text, help_file_path)
    return None


def update_help_file(self, data, parser):

    def _name_is_equal(data, param):
        if data.get('name', None) == param.name:
            return True
        for name in param.name_source:
            if data.get("name") == name.lstrip("-"):
                return True
        return False

    content = data.get("content")
    info_type = None
    info = None
    for elem in content:
        for key, value in elem.items():
            # find the command / group's help text
            if value.get("name") == self.command:
                info_type = key
                info = value
                break
        if info:
            break
    # if a new command not found return old data object

    if not info:
        # if content does not have the desired command or command group, default to data in parser
        description = getattr(parser, 'description', None)
        try:
            self.short_summary = description[:description.index('.')]
            long_summary = description[description.index('.') + 1:].lstrip()
            self.long_summary = ' '.join(long_summary.splitlines())
        except (ValueError, AttributeError):
            self.short_summary = description
        return

    self.type = info_type
    if "summary" in info:
        self.short_summary = info["summary"]
    if "description" in info:
        self.long_summary = info["description"]
    if "examples" in info:
        ex_list = []
        self.examples=[]
        for item in info["examples"]:
            ex = {}
            ex["name"] = item.get("summary", "")
            ex["command"] = item.get("command", "")
            ex["description"] = item.get("description", "")
            ex["min_profile"] = item.get('min_profile', "")
            ex["max_profile"] = item.get('max_profile', "")
            ex_list.append(ex)
        for ex in ex_list:
            if self._should_include_example(ex):
                self.examples.append(CliHelpExample(ex))

    if "links" in info:
        self.links = info["links"]

    if "arguments" in info and hasattr(self, "parameters"):

        loaded_params = []
        for param in self.parameters:
            loaded_param = next((n for n in info['arguments'] if _name_is_equal(n, param)), None)
            if loaded_param and isinstance(param, KnackHelpParameter):
                loaded_param["name"] = param.name
                param.__class__ = CliHelpParameter # cast param to CliHelpParameter
                param.update_from_data(loaded_param)
            loaded_params.append(param)

        self.parameters = loaded_params




# new_data["long-summary"] = "{}\n{}".format(new_data["long-summary"], text) \
#     if new_data.get("long-summary") else text

# ex["text"] = "{}\n{}".format(ex["description"], ex["command"]) if ex["description"] else  ex["command"]

