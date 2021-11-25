

class AAZUndefinedValueError(AttributeError, KeyError):

    def __init__(self, model, name):
        super().__init__(f"'{model.__class__.__name__}' has no value for field '{name}'.")


class AAZUnknownFieldError(KeyError):

    def __init__(self, model, name):
        super().__init__(
            f"Model '{model.__class__.__name__}' has no field named '{name}'"
        )


class AAZConflictFieldDefinitionError(KeyError, AttributeError):

    def __init__(self, name):
        super().__init__(
            f"Model has conflict defined field '{name}'"
        )


class AAZValuePrecisionLossError(ValueError):

    def __init__(self, old, value):
        super().__init__(
            f"Precision Loss from '{old}'({type(old)}) to '{value}'({type(value)})"
        )
