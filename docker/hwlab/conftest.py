def pytest_addoption(parser):
    parser.addoption("--pkg", default="/work/pkg", help="package root inside the container")
