from enum import Enum


class RecordMode(str, Enum):
    """
    Configues when VCR will record to the cassette.

    Can be declared by either using the enumerated value (`vcr.mode.ONCE`)
    or by simply using the defined string (`once`).

    `ALL`: Every request is recorded.
    `ANY`: ?
    `NEW_EPISODES`: Any request not found in the cassette is recorded.
    `NONE`: No requests are recorded.
    `ONCE`:  First set of requests is recorded, all others are replayed.
    Attempting to add a new episode fails.
    """

    ALL = "all"
    ANY = "any"
    NEW_EPISODES = "new_episodes"
    NONE = "none"
    ONCE = "once"
