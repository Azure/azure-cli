def pytest_runtest_logreport(report):
    report.nodeid = "..." + report.nodeid[report.nodeid.rfind("::"):]


def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 5:
        session.exitstatus = 0  # assume to be succeeded if no tests found
