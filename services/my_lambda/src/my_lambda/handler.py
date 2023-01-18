import json
import os
from . import utils

# We're not using pyyaml, just showing that it's installed
import yaml

print("Loading function")


def handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    print("value1 = " + event["key1"])
    print("value2 = " + event["key2"])
    print("value3 = " + event["key3"])

    print(utils.my_util())
    print(f"cwd: {os.getcwd()}")
    with open("my_lambda/stuff/config.yml") as f:
        lines = f.readlines()
    print("File contents of my_lambda/stuff/config.yml:")
    print(lines)

    return event["key1"]  # Return the first key value
