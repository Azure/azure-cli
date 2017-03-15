# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_complex_argument_processor(expanded_arguments, assigned_arg, model_type):
    """
    Return a validator which will aggregate multiple arguments to one complex argument.
    """
    def _expansion_validator_impl(namespace):
        """
        The validator create a argument of a given type from a specific set of arguments from CLI
        command.
        :param namespace: The argparse namespace represents the CLI arguments.
        :return: The argument of specific type.
        """
        ns = vars(namespace)
        kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))

        setattr(namespace, assigned_arg, model_type(**kwargs))

    return _expansion_validator_impl
