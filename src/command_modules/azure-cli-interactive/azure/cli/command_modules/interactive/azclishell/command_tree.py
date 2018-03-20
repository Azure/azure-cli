# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class CommandTree(object):
    """ a command tree """
    def __init__(self, data, children=None):
        self.data = data
        if not children:
            self.children = {}
        else:
            self.children = children

    def get_child(self, child_name):  # pylint: disable=no-self-use
        """ returns the object with the name supplied """
        child = self.children.get(child_name, None)
        if child:
            return child
        raise ValueError("Value {} not in this tree".format(child_name))

    def add_child(self, child):
        """ adds a child to this branch """
        # TODO allow adding child_name
        assert isinstance(child, CommandTree)
        self.children[child.data] = child

    def has_child(self, name):
        """ whether this has a child """
        return self.children.get(name, None) is not None

    def in_tree(self, cmd_args):
        """ if a command is in the tree """
        if not cmd_args:
            return True
        tree = self
        try:
            for datum in cmd_args:
                tree = tree.get_child(datum)
        except ValueError:
            return False
        return True

    def get_sub_tree(self, cmd_args):
        current_command = []
        leftover_args = []

        tree = self
        for arg in cmd_args:
            if tree.has_child(arg):
                current_command.append(arg)
                tree = tree.get_child(arg)
            else:
                leftover_args.append(arg)
        return tree, ' '.join(current_command), leftover_args


class CommandHead(CommandTree):
    """ represents the head of the tree, no data"""

    def __init__(self, children=None):
        CommandTree.__init__(self, None, children=children)


class CommandBranch(CommandTree):
    """ represents a branch of the tree """
    def __init__(self, data, children=None):
        CommandTree.__init__(self, data, children=children)
