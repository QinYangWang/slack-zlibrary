# slack-zlibrary-bot-serverless

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build 
sam deploy --guided
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name zlib
```