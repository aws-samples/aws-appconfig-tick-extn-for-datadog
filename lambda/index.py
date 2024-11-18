# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os

import boto3

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.model.monitor_overall_states import MonitorOverallStates

SECRET_ARN = os.environ["DD_SECRET"]

sm = boto3.client("secretsmanager")
dd_secret = json.loads(sm.get_secret_value(SecretId=SECRET_ARN)["SecretString"])

config = Configuration()
config.api_key["apiKeyAuth"] = dd_secret["DD_API_KEY"]
config.api_key["appKeyAuth"] = dd_secret["DD_APP_KEY"]
config.server_variables["site"] = dd_secret.get("DD_SITE", "datadoghq.com")
datadog = ApiClient(config)
monitors = MonitorsApi(datadog)


def check(monitor_ids: list[int]) -> int:
    """Check that the given monitors are in the OK state.

    Returns the id of a failed monitor, or 0 if all OK.
    """
    for monitor_id in monitor_ids:
        print(f"Checking monitor {monitor_id}")
        response = monitors.get_monitor(monitor_id=monitor_id)
        if response["overall_state"] != MonitorOverallStates.OK:
            print(f"oh no! Monitor {monitor_id} is {response['overall_state']}")
            return monitor_id
    print("All monitors OK")
    return 0


def lambda_handler(event, _):
    monitor_string = event["Parameters"]["MONITOR_IDS"]
    monitors = [int(m) for m in monitor_string.split(",")]
    if len(monitors) == 0:
        return {"Directive": "CONTINUE"}
    print(f"Tick: checking state of monitor(s) {monitors}")
    if failed := check(monitors):
        return {
            "Directive": "ROLL_BACK",
            "Description": f"Monitor id {failed} is not OK",
        }
    return {"Directive": "CONTINUE"}


if __name__ == "__main__":
    lambda_handler(None, None)
