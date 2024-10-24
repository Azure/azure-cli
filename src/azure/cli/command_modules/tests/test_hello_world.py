import pytest
from azure.cli.command_modules.hello_world import hello_world

def test_hello_world():
    assert hello_world() == "Hello, World!"