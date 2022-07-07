# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class AAZUndefinedValueError(AttributeError, KeyError):

    def __init__(self, model, name):
        super().__init__(f"'{model.__class__.__name__}' has no value for field '{name}'.")


class AAZUnknownFieldError(AttributeError, KeyError):

    def __init__(self, model, name):
        super().__init__(
            f"Model '{model.__class__.__name__}' has no field named '{name}'"
        )


class AAZInvalidFieldError(KeyError, AttributeError):

    def __init__(self, model, name, msg):
        super().__init__(
            f"Model '{model.__class__.__name__}' has invalid field named '{name}': {msg}"
        )


class AAZConflictFieldDefinitionError(KeyError, AttributeError):

    def __init__(self, model, name, msg):
        super().__init__(
            f"Model '{model.__class__.__name__}' has conflict defined field '{name}': {msg}"
        )


class AAZValuePrecisionLossError(ValueError):

    def __init__(self, old, value):
        super().__init__(
            f"Precision Loss from '{old}'({type(old)}) to '{value}'({type(value)})"
        )


class AAZInvalidShorthandSyntaxError(ValueError):

    def __init__(self, error_data, error_at, error_range, msg):
        super().__init__()
        self.error_data = error_data
        self.error_at = error_at
        self.error_range = error_range
        self.msg = msg

    def __str__(self):
        return f"Shorthand Syntax Error: {self.msg}:" \
               f"\n\t{self.error_data[:self.error_at + self.error_range]}" \
               f"\n\t{' ' * self.error_at}{'^' * self.error_range}"


class AAZInvalidValueError(ValueError):
    pass


class AAZInvalidArgValueError(ValueError):

    def __init__(self, msg, indexes=None):
        super().__init__()
        self.msg = msg
        self.indexes = indexes or []

    def __str__(self):
        if self.indexes:
            idx = self.indexes[0]
            for i in self.indexes[1:]:
                if not i.startswith('['):
                    idx += '.'
                idx += i
            return f"Argument Value Error: {idx}: {self.msg}"
        return f"Argument Value Error: {self.msg}"
