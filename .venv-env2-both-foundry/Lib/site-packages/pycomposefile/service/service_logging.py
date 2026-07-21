from pycomposefile.compose_element import ComposeElement, ComposeListOrMapElement


class Options(ComposeListOrMapElement):
    pass


class Logging(ComposeElement):
    element_keys = {
        "driver": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#logging"),
        "options": (Options, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#logging")
    }
