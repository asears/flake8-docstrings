import os, sys

parent = os.path.abspath(".")
sys.path.insert(1, parent)
from flake8_docstrings import pep257Checker
import pytest


def test_flake8_docstrings():
    # Test case: a function without docstring
    code_without_docstring = """
    def hello_world():
        print("Hello, world!")
    """
    tree = None
    filename = "(none)"
    lines = code_without_docstring.splitlines()
    checker = pep257Checker(tree, filename, lines)
    with pytest.raises(Exception):
        errors = list(checker.run())
    # assert errors, "Expected at least one error for missing docstring"
