---
title: "Python src Layout for AWS Lambdas"
publish: false
tags: ["aws", "python", "poetry", "lambda"]
license: "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
description: How to create AWS Lambdas with Poetry with the Python src layout
canonical_url: https://www.informediq.com/python-src-layout-for-aws-lambdas 
---

Over the last several years, the Python community has been moving towards a packaging layout format known as the `src layout` as the recommended way to organize directories and files for Python Packages.

The main takeaways of the `src layout` are:

* Your project has a `src` folder
  * The `src` folder only has sub folder[s]. Each sub folder
    * Is a Python Package
    * Its name is the name of the package
    * It contains an `__init__.py` (that's pretty much what makes it a Python Package)
  * All Python source code that makes up your appplication (other than tests or build utilities) for the project are in these sub folder[s]
* Modern Python tooling expects / works best with this layout
* Makes packaging easier and less prone to errors
* "editable" installs for development and regular installation for testing
* Generally no need for "import trickery"
* References at end of this article

We were looking for standards and best practices for organizing our Python AWS Lambda projects using [Poetry](https://python-poetry.org) in our monorepo and kept coming across the `src layout` as the recommended way to organize Python projects that had multiple modules. At the same time just about all examples of Python Lambda projects did not use `src layout` and in fact seemed to want to have the handler module at the top level of the project directory.  There just weren't many examples of this combination of `src layout` `Poetry` and AWS Lambdas.

Turns  out that it wasn't really difficult. The main "trick" is setting the Lambda `handler` name correctly.

> All this example code is available at  [Informed/blogpost-python-src-layout](https://github.com/Informed/blogpost-python-src-layout)
 
## Example src  layout for an AWS Lambda

Here's an example `src layout` suitable for AWS Lambda

* This is a section of what could be a regular or monorepo that shows one lambda project: `my_lambda`
  * You could have more lambda projects under services, each would be a separate subproject with the same layout
    * How to implement such a multi-project monorepo is left to a future blog post
  * The actual lambda code is in `src/my_lambda`
    * There is an  example of additional non-code files in `src/my_lambda/stuff` that might be used by the lambda or [lambda layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html) such as an [otel layer](https://aws-otel.github.io/docs/getting-started/lambda/lambda-python) that will be part of the deployed zip image.
      * This is not required, just showing an example of how you can easily bundle in additional non-code files
    * You can have additional Python modules in here like `utils.py` that are imported into the `handler.py` module
    * If your Lambda application is more complex you can have local Packages as subdirectories of `src/my_lambda`


```
blogpost-python-src-layout
├── LICENSE
├── README.md
├── doc
│   └── python_src_layout_for_aws_lambdas.md
└── services
    └── my_lambda
        ├── CHANGELOG.md
        ├── LICENSE
        ├── README.md
        ├── poetry.lock
        ├── pyproject.toml
        ├── src
        │   └── my_lambda
        │       ├── __init__.py
        │       ├── handler.py
        │       ├── stuff
        │       │   ├── config.yml
        │       │   └── data.csv
        │       └── utils.py
        └── tests
            └── test_my_handler.py
```

## Example  Poetry pyproject.toml

```toml
[tool.poetry]
name = "my_lambda"
version = "0.0.0"
description = "This is my lambda which is mine"
authors = ["Da Dev <daDev@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"
pyyaml = "6.0"

[tool.poetry.group.dev.dependencies]
coverage = {extras = ["toml"], version = "^6.5.0"}
pytest = "^7.2.0"
flake8 = "^6.0.0"
python-lambda-local = "^0.1.13"
boto3 = "1.20.32"

[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

Poetry expects a `src layout`. The fact that the `name` is the same as the directory name under `src` and that directory is a Python Package (i.e. it has an `__init__.py` and source code) means that Poetry will treat everything in `src/my_lambda` as the package it's going to build. Everything in `src/my_lambda` and any dependencies under `[tool.poetry.dependencies]`  will end up in the deployed zip image that will become the lambda function image. In this example we have the `pyyaml` package included.

The dependencies under `[tool.poetry.group.dev.dependencies]` will only be used for local builds, and not included in the zip image. You can put dependencies that are in the lambda runtime, like boto3 or any lambda layers (like Otel, or aws_powertools) in `[tool.poetry.group.dev.dependencies]` if you want them available for local testing.

There is also the option (and some folks recommend) to put a more up to date and fixed version of boto3 in `[tool.poetry.dependencies]` since AWS  can change the version used in the runtime at any time. The main downside of this is it makes your uploaded image larger.

The section '[tool.pytest.ini_options]' is recommended for all new packages that use [pytest](https://docs.pytest.org/en/7.2.x/explanation/goodpractices.html#tests-outside-application-code) for running their tests.

## Set the Lambda Handler to be the "two dot" format

The main thing that is different for configuring Lambdas when you use the `src layout` is that you must specify the handler as
```
<package_name>.<handler_module_name>.<handler_function_name>`
```
Also known as the [2 dot solution](https://gist.github.com/gene1wood/06a64ba80cf3fe886053f0ca6d375bc0) that specifies the handler like a package import path.

In our example that would be:
```python
my_lambda.handler.handler
```

## Example src/my_lambda/handler.py

This is just a very minimal lambda function that demonstrates:

* Importing the `PyYaml` package we specify as a dependency in the `pyproject.toml`
* Printing the `event` info passed in the handler
* Calling an imported function from the same lambda package (`utils.my_util`)
* Fetching and printing one of the non-source files in `src/my_lambda/stuff`

```python
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
```

## Building and deploying the Lambda

This is the basics of  building and deploying the lambda using Poetry. You may have more sophisticated CI/CD process.

These commands should be executed in the top level of the project (i.e. `my_repo/services/my_lambda`)

### Building the distribution

> Note: These command may not work for your actual application if it has dependencies that need to be compiled as part of the build process, particularly if you are building your application on a machine that is not the same architecture as your target Lambda (i.e. building on an M1 Macintosh and targeting an x86_64 lambda). In that case you need to use Docker to do your building which is beyond the scope of this post.
>
> These examples were only tested on an M1 Mac but should work on any modern Mac or *nix machine and will build zip images suitable for targeting Linux x86 Lambdas if you do not need to build binary dependencies.
> The `pip install` shown later uses the argument `--platform manylinux2014_x86_64` which forces the packaging to only include binary wheels built for Linux x86_64. The argument ` --only-binary :all:` ensures that it will not try to compile any source only dependencies and instead will emit an error letting you know that you must build the package in the native target environment (i.e. use a Docker build process). 


1) First we export the dependencies from Poetry so that we can later use `pip install` to create the files needed for the zip image.
```
poetry export -f requirements.txt --output requirements.txt  --without-hashes
```
2) Have Poetry build all the wheels and such
```
poetry build
```
This will result in a bunch of files in the directory `dist` the top level of your project.

3) Use pip to create the packages
```
poetry run pip install -r requirements.txt --upgrade --only-binary :all: --platform manylinux2014_x86_64 --target package dist/*.whl
```
This will generate all the wheels of all the dependencies in the `package` directory, suitable for zipping into the lambda image. 

4) Zip up the image
```
cd package
mkdir -p out
zip -r -q out/my-lambda.zip . -x '*.pyc' out
cd ..
```
This will result in a file in `my_repo/services/my_lambda/package/out/my-lambda.zip` that is suitable for uploading to AWS as the Lambda Function image.

### Create the Lambda function

You could do this in the AWS console or use the following AWS CLI Commands (If you use the AWS Console, it will create the execution role and trust policy automatically by default).

1) Create the [execution role and trust policy](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-awscli.html#with-userapp-walkthrough-custom-events-create-iam-role)

```
aws iam create-role --role-name my-lambda-ex --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
```

  * You should get a result like the following.
  * __Copy the arn from this output and you will use it for the next command__

```json
{
    "Role": {
        "Path": "/",
        "RoleName": "my-lambda-ex",
        "RoleId": "AROAWUWOOBVLDKY7ZE7P3",
        "Arn": "arn:aws:iam::1234567890123:role/my-lambda-ex",
        "CreateDate": "2023-01-12T06:08:22+00:00",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    }
}
```

2) Create the Lambda function

   * You have to set the `handler` to the 2 dot style `my_lambda.handler.handler`
   * Change the fake account-id (`1234567890123`) in the `role arn` to your AWS account-id
    ```shell
    aws lambda create-function --function-name my-lambda \
      --zip-file fileb://package/out/my-lambda.zip \
      --handler my_lambda.handler.handler --runtime python3.9 \
      --role arn:aws:iam::1234567890123:role/my-lambda-ex
    ```

#### If you already have created the Lambda function

If you created the Lambda function some other way like via the Console or you want to update the Lambda function you created earlier, you can use the following command just to update it.

This mechanism loads the lambda from the S3 asset you uploaded earlier
```shell
aws lambda update-function-code --function-name my-lambda \
  --zip-file fileb://package/out/my-lambda.zip \
  --region us-west-2
```

### Test the Lambda

At this point your lambda should be ready to test. You can use the default test input in the AWS Lambda Console:

```json
{
  "key1": "value1",
  "key2": "value2",
  "key3": "value3"
}
```
You can run the default `Test` on the AWS Lambda console and you will see all the log output as well as the result which would look something like:

```
Test Event Name
basic

Response
"value1"

Function Logs
Loading function
START RequestId: 2f33f7b2-ddae-46df-a61b-1263ef404d6b Version: $LATEST
Received event: {
"key1": "value1",
"key2": "value2",
"key3": "value3"
}
value1 = value1
value2 = value2
value3 = value3
Hello from my_util
cwd: /var/task
File contents of my_lambda/stuff/config.yml:
['thing:\n', '  hand: manicure\n']
END RequestId: 2f33f7b2-ddae-46df-a61b-1263ef404d6b
REPORT RequestId: 2f33f7b2-ddae-46df-a61b-1263ef404d6b	Duration: 1.57 ms	Billed Duration: 2 ms	Memory Size: 128 MB	Max Memory Used: 40 MB	Init Duration: 172.83 ms
```

Or you could run it via the AWS CLI:
```
aws lambda invoke --cli-binary-format raw-in-base64-out \
  --function-name my-lambda \
  --payload '{ "key1": "value1", "key2": "value2", "key3": "value3"}' \
  outputfile.txt   --log-type Tail \
  --query 'LogResult' --output text |  base64 -d
```
This will print the log output (same as what  was shown above in example of running the Test in the AWS Console) 

You can see the returned value of the handler in `outputfile.txt`

## Running tests with `Pytest`

There is also a simple test example in `services/my_lambda/tests/test_my_handler.py`
```python
import pytest
import os
from my_lambda.handler import handler

event = {"key1": "value1", "key2": "value2", "key3": "value3"}
context = {}


def test_my_handler():
    # Emulate running in the same directory context as the lambda would
    os.chdir("src")
    assert handler(event, context) == "value1"
```

Before you run pytest for the first time in this project (or before you do any local development that needs  any of the packages in the `[tool.poetry.group.dev.dependencies]` section of `pyproject.toml`) you need to run at least once:
```shell
poetry install
```
This will install all the dependencies listed in your main `[tool.poetry.dependencies]` and in `[tool.poetry.group.dev.dependencies]` in the virtualenv that is managed by Poetry.

You can run the test from `services/my_lambda`:
```
poetry run pytest
```

## References on `src layout`

* PyPA Python Packaging User Guide [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/#src-layout-vs-flat-layout)
* [Pytest Good Integration Practices: Tests outside application code](https://docs.pytest.org/en/6.2.x/goodpractices.html#tests-outside-application-code)
* The post that pretty much started the movement: [Packaging a python library](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure) by [Ionel Cristian Mărieș](https://blog.ionelmc.ro/about/)
* Another early influential blog post [Testing & Packaging](https://hynek.me/articles/testing-packaging/) by [Hynek Schlawack](https://hynek.me/about/)
* [Organize Python code like a PRO](https://guicommits.com/organize-python-code-like-a-pro/)
* [Convert a Poetry package to the src layout](https://browniebroke.com/blog/convert-existing-poetry-to-src-layout/)
