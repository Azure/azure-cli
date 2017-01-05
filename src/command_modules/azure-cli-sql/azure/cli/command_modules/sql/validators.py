# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_expension_validator(expanded_arguments, model_type):
    def _expension_valiator_impl(namespace):
        ns = vars(namespace)
        kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))

        namespace.parameters = model_type(**kwargs)

    return _expension_valiator_impl
