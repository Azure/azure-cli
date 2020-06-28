import os

# The actual tests will execute the code anyhow so the following code can
# safely be ignored from the coverage tests
if os.name == 'nt':  # pragma: no cover
    import msvcrt

    LOCK_EX = 0x1
    LOCK_SH = 0x2
    LOCK_NB = 0x4
    LOCK_UN = msvcrt.LK_UNLCK

elif os.name == 'posix':  # pragma: no cover
    import fcntl

    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
    LOCK_UN = fcntl.LOCK_UN

else:  # pragma: no cover
    raise RuntimeError('PortaLocker only defined for nt and posix platforms')

