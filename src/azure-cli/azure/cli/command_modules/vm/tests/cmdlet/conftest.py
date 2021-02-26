def pytest_runtest_logreport(report):
    report.nodeid = "..." + report.nodeid[report.nodeid.rfind("::"):]
