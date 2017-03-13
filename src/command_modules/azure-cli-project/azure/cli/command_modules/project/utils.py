import string
import random


def get_random_string(length=6):
    """
    Gets a random lowercase string made
    from ascii letters and digits
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for _ in range(length))
