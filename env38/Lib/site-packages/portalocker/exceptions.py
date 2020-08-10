class BaseLockException(Exception):
    # Error codes:
    LOCK_FAILED = 1


class LockException(BaseLockException):
    pass


class AlreadyLocked(BaseLockException):
    pass


class FileToLarge(BaseLockException):
    pass
