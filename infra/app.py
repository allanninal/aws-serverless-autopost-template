#!/usr/bin/env python3
"""CDK app entry point for the autopost infrastructure stack."""

import aws_cdk as cdk

from stacks.autopost_stack import AutopostStack

app = cdk.App()

AutopostStack(
    app,
    "AutopostStack",
    env=cdk.Environment(
        # CUSTOMIZE: Set your AWS region
        # Common choices: us-east-1, eu-west-1, ap-southeast-1
        region="YOUR_AWS_REGION",
    ),
    tags={
        "Project": "YOUR_PROJECT_NAME",
        "App": "autopost",
        "Owner": "YOUR_NAME",
        "Environment": "production",
    },
)

app.synth()
