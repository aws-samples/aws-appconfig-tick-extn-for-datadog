# AWS AppConfig Deployment Tick Datadog Sample Extension

This is a sample AWS AppConfig extension to show integrating the
`AT_DEPLOYMENT_TICK` event with the Datadog API - that is, allowing AppConfig to
check the state of a 3rd party monitor as a deployment runs.

The Lambda function is invoked regularly by AWS AppConfig during a deployment
(including the baking period at the end), and calls the Datadog API to check
the status of one or more monitors. If any are not in the "OK" state, the
function tells AWS AppConfig to roll back the deployment.

If you wish to use this sample in your environments, please consider using a
customer-managed KMS key with Secrets Manager, as described in [the
documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html).

## Prerequisites

Please see the [AWS AppConfig
documentation](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html)
for details on configuring the service.

You will need a Datadog account with one or more monitors configured as
required to monitor your environment.

Ensure you have an up-to-date Python install available, and [AWS CDK
v2](https://docs.aws.amazon.com/cdk/v2/guide/home.html) installed.

You will need Docker installed and running for CDK to build the Lambda
function.

## Setting up

1. Clone this repo
2. In the cloned repo, create a Python virtual environment: `python -m venv .venv`
3. Activate your virtual environment: `source .venv/bin/activate`
4. Install the Python dependencies: `pip install -r requirements.txt`
5. Ensure you have suitable AWS credentials configured in your environment
6. If you have not bootstrapped this AWS account/region for CDK previously, run
   `cdk bootstrap`. (It's safe to rerun if you're not sure.)
7. Deploy this CDK app by running `cdk deploy`. You only need to deploy it once
   per AWS Account/Region.
8. Note the value of the `ddsecret` output from CDK as you'll need it in a
   moment. If you miss it, you can find it again by running this command or by
   looking at the Outputs for the `AppconfigTickExtnStack` in the
   CloudFormation console:
   ```bash
   aws cloudformation describe-stacks --stack-name AppconfigTickExtnStack --query 'Stacks[0].Outputs[?OutputKey==`ddsecret`].OutputValue' --output text
   ```
9. In your Datadog account, create (if needed) an [API key and an
   Application key](https://docs.datadoghq.com/account_management/api-app-keys/).
   The application key only needs the `monitors_read`
   [scope](https://docs.datadoghq.com/account_management/api-app-keys/#scopes),
   so you can configure this to follow the Principle of Least Privilege.
10. In your Datadog account, collect the Monitor Id(s) for the Monitor(s). The
    Id is shown on the "Properties" screen for the monitor, and is an integer.
11. In the AWS Console, navigate to AWS Secrets Manager (ensure you are working
    in the same region used for deploying the CDK app).
12. From the menu on the left, choose **Secrets**, then in the list of Secrets,
    choose the entry with the name you noted down in step 7.
13. Under the Overview tab, choose **Retrieve secret value**, then choose
    **Edit**
14. Replace the placeholder values for the API key and APP key with your keys
    from steps 8 and 9.
15. Replace the site placeholder with the name of your Datadog Site (for example
    `datadoghq.com`). See the [Datadoc docs](https://docs.datadoghq.com/getting_started/site/)
    for details.
16. Choose **Save**

NOTE: You should ensure that your IAM Policies in your account prevent
viewing/decryption of this secret by users who should not be able to access it.


## Usage

1. Navigate to the AppConfig console, then choose **Extensions**
2. Choose the **Sample Datadog Monitor Tick** extension, then choose **Add to
   resource**
3. Choose the **Resource Type** to associate the Extension with, and populate
   the following fields as required
4. Under **Parameters**, for **MONITOR_IDS**, enter the Ids of your monitors. You
   can enter more than one by separating the Ids with commas
5. Choose **Create Association to Resource**

You can now deploy a configuration (under a resource to which the extension is
attached) and your Datadog Monitors will be checked during the deployment to
make sure they are in the "OK" state.

If a monitor is not in the "OK" state when checked, the deployment will
automatically roll back.

You can find more details about the roll back by examining the event log for
the deployment. For example, using the AWS CLI:

```bash
aws appconfig get-deployment --application-id 123abc --environment-id 456def --query '[State,EventLog]' --deployment-number 1
```

## Cleaning up

1. Navigate to the AppConfig console, then choose **Extensions**
2. Choose the **Sample Datadog Monitor Tick** extension
3. For each entry under **Associated resources**, choose the radio button then
   choose **Remove association**, then choose **Delete**
4. Once you have removed all the Associated resources, you can run `cdk
   destroy` to remove all resources created by the app

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This sample is licensed under the MIT-0 License. See the LICENSE file.
