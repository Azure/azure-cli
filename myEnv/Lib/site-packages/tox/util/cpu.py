import os


def cpu_count():
    return len(os.sched_getaffinity(0))


def auto_detect_cpus():
    try:
        n = cpu_count()
    except NotImplementedError:  # pragma: no cov
        n = None  # pragma: no cov
    return n if n else 1
