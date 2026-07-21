from pycomposefile.compose_element import ComposeElement


class CredentialSpec(ComposeElement):
    element_keys = {
        "file": (str,
                 "https://github.com/compose-spec/compose-spec/blob/master/spec.md#credential_spec"),
        "registry": (str,
                     "https://github.com/compose-spec/compose-spec/blob/master/spec.md#credential_spec"),
        "config": (str,
                   "https://github.com/compose-spec/compose-spec/blob/master/spec.md#credential_spec")
    }
