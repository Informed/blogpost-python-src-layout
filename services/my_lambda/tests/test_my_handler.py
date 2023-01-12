# write a test for your lambda handler
# this test will be run by pytest
import pytest
import os
from my_lambda.handler import handler

event = {"key1": "value1", "key2": "value2", "key3": "value3"}
context = {}


def test_my_handler():
    # Emulate running in the same directory context as the lambda would
    os.chdir("src")
    assert handler(event, context) == "value1"
