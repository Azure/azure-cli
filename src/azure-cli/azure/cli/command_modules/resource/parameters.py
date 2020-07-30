from enum import Enum


class TagUpdateOperation(str, Enum):
    merge = "Merge"
    replace = "Replace"
    delete = "Delete"
