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


class CommandHead(CommandTree):
    """ represents the head of the tree, no data"""

    def __init__(self, children=None):
        CommandTree.__init__(self, None, children=children)


class CommandBranch(CommandTree):
    """ represents a branch of the tree """
    def __init__(self, data, children=None):
        CommandTree.__init__(self, data, children=children)


def generate_tree(commands):
    """ short cut to make a tree """
    data = commands.split()[::-1]
    first = True
    prev = None
    node = None
    for kid in data:
        node = CommandTree(kid)
        if first:
            first = False
            prev = node
        else:
            node.add_child(prev)
    return node


def in_tree(tree, cmd):
    """ if a command is in the tree """
    data = cmd.split(' ')
    if not data:
        return True
    try:
        for datum in data:
            tree = tree.get_child(datum)
    except ValueError:
        return False
    return True
