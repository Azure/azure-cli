# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import random


def generate_username():
    directory_path = os.path.dirname(__file__)
    adjectives, nouns = [], []
    with open(os.path.join(directory_path, 'adjectives.txt'), 'r') as file_adjective:
        with open(os.path.join(directory_path, 'nouns.txt'), 'r') as file_noun:
            for line in file_adjective:
                adjectives.append(line.strip())
            for line in file_noun:
                nouns.append(line.strip())
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    num = str(random.randrange(10))
    return adjective + noun + num
