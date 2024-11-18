# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import cast
from aws_cdk import (
    CfnOutput,
    SecretValue,
    Stack,
    aws_appconfig,
    aws_lambda,
    aws_iam as iam,
    aws_lambda_python_alpha as aws_python,
    aws_secretsmanager,
)
from cdk_nag import NagSuppressions, NagPackSuppression
from constructs import Construct


class AppconfigTickExtnStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Secret for the user to populate with their values
        dd_secret = aws_secretsmanager.Secret(
            self,
            "tick_dd_secret",
            description="DataDog API credentials for AWS AppConfig Tick extension",
            secret_object_value={
                "DD_API_KEY": SecretValue.unsafe_plain_text("<some dd api key>"),
                "DD_APP_KEY": SecretValue.unsafe_plain_text("<some dd app key>"),
                "DD_SITE": SecretValue.unsafe_plain_text("<dd api endpoint>"),
            },
        )

        NagSuppressions.add_resource_suppressions(
            dd_secret,
            [
                NagPackSuppression(
                    id="AwsSolutions-SMG4",
                    reason="External secret and does not support rotation",
                )
            ],
        )

        function = aws_python.PythonFunction(
            self,
            "tick_fn",
            index="index.py",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler="lambda_handler",
            entry="lambda",
            bundling=aws_python.BundlingOptions(
                asset_excludes=[
                    ".venv",
                    ".mypy_cache",
                    ".ruff_cache",
                    "requirements-dev.txt",
                ]
            ),
            description="AppConfig Extension to handle deployment tick",
            architecture=aws_lambda.Architecture.ARM_64,
            environment={
                "DD_SECRET": dd_secret.secret_arn,
            },
            # up the mem size slightly to get more CPU
            # AppConfig will wait 3s for an extn so we need to hustle
            memory_size=256,
        )
        dd_secret.grant_read(function)

        NagSuppressions.add_resource_suppressions(
            function,
            [
                NagPackSuppression(
                    id="AwsSolutions-IAM4",
                    reason="Managed Policy just allows Lambda access to CWL",
                    applies_to=[
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                ),
            ],
            apply_to_children=True,
        )

        appconfig_svc_role = iam.Role(
            self,
            "appconfig_role",
            assumed_by=cast(
                iam.IPrincipal, iam.ServicePrincipal("appconfig.amazonaws.com")
            ),
        )
        function.grant_invoke(appconfig_svc_role)

        NagSuppressions.add_resource_suppressions(
            appconfig_svc_role,
            [
                NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Wildcard applies to function aliases and version; policy is restricted to function by arn",
                    applies_to=["Resource::<tickfnB386E70B.Arn>:*"],
                ),
            ],
            apply_to_children=True,
        )

        aws_appconfig.CfnExtension(
            self,
            "tick_extn",
            name="Sample Datadog Monitor Tick",
            description="A sample Extension to watch Datadog Monitors during a deployment and roll back if they are not OK.",
            actions={
                "AT_DEPLOYMENT_TICK": [
                    {
                        "Name": "Sample Datadog Monitor Tick Action",
                        "Description": "Deployment Tick action point",
                        "RoleArn": appconfig_svc_role.role_arn,
                        "Uri": function.function_arn,
                    }
                ]
            },
            parameters={
                "MONITOR_IDS": aws_appconfig.CfnExtension.ParameterProperty(
                    required=True,
                    description="Comma-separated list of Datadog monitor IDs",
                    dynamic=False,
                )
            },
        )

        CfnOutput(
            self,
            "dd_secret",
            value=dd_secret.secret_name,
            description="The Secrets Manager Secret which must be updated with Datadog API credentials",
        )
