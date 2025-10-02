# AWS AI Concierge - Troubleshooting Guide

## 🚨 Emergency: High AWS Costs

**If you see unexpected charges, run this immediately:**
```powershell
cd aws-ai-concierge-cdk
.\scripts\cleanup-environment.ps1 -Environment dev -Force
```

## 🔧 Common Deployment Issues

### CDK Deployment Fails

#### Error: "CloudWatch Logs role ARN must be set"
```
Resource handler returned message: "CloudWatch Logs role ARN must be set in account settings to enable logging"
```

**Solution**: The CDK stack has been configured to disable API Gateway logging to avoid this issue. If you still see this error:

```powershell
# Verify the CDK stack configuration
cat aws-ai-concierge-cdk/lib/aws-ai-concierge-cdk-stack.ts | grep -A 5 "loggingLevel"

# Should show: loggingLevel: apigateway.MethodLoggingLevel.OFF
```

#### Error: "Stack already exists"
```
AwsAiConcierge-dev already exists
```

**Solution**: Delete the existing stack first:
```powershell
aws cloudformation delete-stack --stack-name AwsAiConcierge-dev
aws cloudformation wait stack-delete-complete --stack-name AwsAiConcierge-dev
```

#### Error: "Bootstrap required"
```
This stack uses assets, so the toolkit stack must be deployed to the environment
```

**Solution**: Bootstrap CDK:
```powershell
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### Bedrock Agent Issues

#### Error: "Failed to create OpenAPI 3 model"
```
Failed to create OpenAPI 3 model from the JSON/YAML object that you provided
```

**Solution**: Use function schema instead of OpenAPI schema:
```powershell
# The create-bedrock-agent.ps1 script uses function schema by default
.\scripts\create-bedrock-agent.ps1 -Environment dev
```

#### Error: "Agent not found"
```
An error occurred (ResourceNotFoundException) when calling the GetAgent operation
```

**Solution**: Check if agent exists and get the correct ID:
```powershell
aws bedrock-agent list-agents --query "agentSummaries[?contains(agentName, 'aws-ai-concierge')]"
```

#### Error: "Agent is not in PREPARED state"
```
Agent must be in PREPARED state to create alias
```

**Solution**: Wait for agent preparation or prepare manually:
```powershell
aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID
```

## 🔍 Lambda Function Issues

### Lambda Function Not Working

#### Error: "Function not found"
```
The resource you requested does not exist
```

**Solution**: Verify function exists and check name:
```powershell
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aws-ai-concierge')]"
```

#### Error: "Access Denied" in Lambda logs
```
User: arn:aws:sts::ACCOUNT:assumed-role/aws-ai-concierge-lambda-role-dev is not authorized to perform: ce:GetCostAndUsage
```

**Solution**: Check IAM role permissions:
```powershell
aws iam get-role-policy --role-name aws-ai-concierge-lambda-role-dev --policy-name AWSReadOnlyAccess
```

#### Error: Lambda timeout
```
Task timed out after 180.00 seconds
```

**Solution**: Increase timeout in environment config:
```json
// aws-ai-concierge-cdk/config/environments.json
{
  "dev": {
    "lambdaTimeout": 300  // Increase from 180 to 300 seconds
  }
}
```

### API Gateway Issues

#### Error: "Internal Server Error" (500)
```
{"message": "Internal server error"}
```

**Solution**: Check Lambda function logs:
```powershell
aws logs tail /aws/lambda/aws-ai-concierge-tools-dev --follow
```

#### Error: "Forbidden" (403)
```
{"message": "Forbidden"}
```

**Solution**: Check API Gateway permissions and CORS:
```powershell
# Test direct Lambda invocation
aws lambda invoke --function-name aws-ai-concierge-tools-dev --payload '{"tool":"getCostAnalysis","parameters":{"time_period":"MONTHLY"}}' response.json
```

## 🧪 Testing Issues

### Integration Tests Failing

#### Error: "No module named 'boto3'"
```
ModuleNotFoundError: No module named 'boto3'
```

**Solution**: Install Python dependencies:
```bash
cd integration-tests
pip install -r requirements.txt
```

#### Error: "AWS credentials not found"
```
NoCredentialsError: Unable to locate credentials
```

**Solution**: Configure AWS CLI:
```powershell
aws configure
# Or set environment variables:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
```

#### Error: "Agent not responding"
```
Bedrock agent test failed: timeout
```

**Solution**: Check agent status and wait for preparation:
```powershell
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID --query "agent.agentStatus"
# Should return "PREPARED"
```

## 💰 Cost-Related Issues

### Unexpected High Costs

#### Issue: Bedrock charges higher than expected
**Investigation**:
```powershell
# Check CloudWatch logs for token usage
aws logs filter-log-events --log-group-name "/aws/lambda/aws-ai-concierge-tools-dev" --filter-pattern "bedrock"

# Check recent Bedrock API calls
aws logs filter-log-events --log-group-name "/aws/lambda/aws-ai-concierge-tools-dev" --start-time $(date -d "1 day ago" +%s)000
```

**Solution**: Clean up immediately and review usage patterns:
```powershell
.\scripts\cleanup-environment.ps1 -Environment dev -Force
.\scripts\estimate-costs.ps1 -Environment dev
```

#### Issue: Resources not cleaned up properly
**Investigation**:
```powershell
# Check for remaining resources
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
aws bedrock-agent list-agents
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aws-ai-concierge')]"
aws s3 ls | grep aws-ai-concierge
```

**Solution**: Manual cleanup:
```powershell
# Delete specific resources manually
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID --skip-resource-in-use-check
aws cloudformation delete-stack --stack-name AwsAiConcierge-dev
aws s3 rm s3://YOUR-BUCKET-NAME --recursive
aws s3api delete-bucket --bucket YOUR-BUCKET-NAME
```

## 🔐 Permission Issues

### IAM Permission Errors

#### Error: "User is not authorized to perform bedrock:CreateAgent"
```
An error occurred (AccessDeniedException) when calling the CreateAgent operation
```

**Solution**: Add Bedrock permissions to your user/role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Error: "User is not authorized to perform cloudformation:CreateStack"
```
User is not authorized to perform: cloudformation:CreateStack
```

**Solution**: Add CloudFormation permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "iam:*",
        "lambda:*",
        "apigateway:*",
        "s3:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🔧 Environment-Specific Issues

### Development Environment

#### Issue: Frequent timeouts during development
**Solution**: Increase timeouts for dev environment:
```json
// aws-ai-concierge-cdk/config/environments.json
{
  "dev": {
    "lambdaTimeout": 300,
    "lambdaMemorySize": 1024
  }
}
```

#### Issue: Logs filling up quickly
**Solution**: Reduce log retention:
```json
{
  "dev": {
    "logRetentionDays": 3  // Reduce from 7 to 3 days
  }
}
```

### Production Environment

#### Issue: Performance degradation
**Solution**: Increase resources:
```json
{
  "prod": {
    "lambdaMemorySize": 1024,
    "lambdaTimeout": 300,
    "enableDetailedMonitoring": true
  }
}
```

## 🔍 Debugging Commands

### Check Deployment Status
```powershell
# CDK Stack status
aws cloudformation describe-stacks --stack-name AwsAiConcierge-dev --query "Stacks[0].StackStatus"

# Lambda function status
aws lambda get-function --function-name aws-ai-concierge-tools-dev --query "Configuration.State"

# Bedrock agent status
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID --query "agent.agentStatus"
```

### View Recent Logs
```powershell
# Lambda logs (last 10 minutes)
aws logs tail /aws/lambda/aws-ai-concierge-tools-dev --since 10m

# CloudFormation events
aws cloudformation describe-stack-events --stack-name AwsAiConcierge-dev --query "StackEvents[0:10]"
```

### Test Individual Components
```powershell
# Test Lambda directly
aws lambda invoke --function-name aws-ai-concierge-tools-dev --payload '{"tool":"getCostAnalysis","parameters":{"time_period":"MONTHLY"}}' response.json

# Test API Gateway
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/cost-analysis -H "Content-Type: application/json" -d '{"time_period":"MONTHLY"}'

# Test Bedrock agent
aws bedrock-agent-runtime invoke-agent --agent-id YOUR_AGENT_ID --agent-alias-id dev --session-id test --input-text "What are my costs?" response.json
```

## 🆘 Getting Help

### Self-Service Debugging

1. **Check CloudWatch Logs**: Most issues show up in Lambda logs
2. **Verify Resource Status**: Use the debugging commands above
3. **Check AWS Service Health**: https://status.aws.amazon.com/
4. **Review Recent Changes**: What changed since it last worked?

### Escalation Path

1. **Clean up resources first**: `.\scripts\cleanup-environment.ps1 -Environment dev`
2. **Document the issue**: What were you trying to do? What error occurred?
3. **Gather logs**: Copy relevant CloudWatch logs
4. **Check costs**: Run `.\scripts\estimate-costs.ps1` to see financial impact

### Emergency Contacts

- **High AWS costs**: Run cleanup script immediately, then investigate
- **Production issues**: Check monitoring dashboards first
- **Security concerns**: Review IAM permissions and audit logs

## 📋 Troubleshooting Checklist

When something goes wrong:

- [ ] Run cleanup script to stop any ongoing costs
- [ ] Check CloudWatch logs for error details
- [ ] Verify AWS CLI credentials are working
- [ ] Check if resources exist where expected
- [ ] Review recent changes to code or configuration
- [ ] Test individual components in isolation
- [ ] Check AWS service status
- [ ] Review IAM permissions
- [ ] Verify environment configuration
- [ ] Check for resource limits or quotas

## 🔄 Recovery Procedures

### Complete Environment Reset
```powershell
# 1. Clean up everything
.\scripts\cleanup-environment.ps1 -Environment dev -Force

# 2. Wait for cleanup to complete
Start-Sleep 60

# 3. Redeploy from scratch
.\scripts\deploy.ps1 -Environment dev
.\scripts\create-bedrock-agent.ps1 -Environment dev

# 4. Validate deployment
.\scripts\validate-deployment.ps1 -Environment dev
```

### Partial Recovery (Keep infrastructure, recreate agent)
```powershell
# 1. Delete just the Bedrock agent
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID --skip-resource-in-use-check

# 2. Recreate the agent
.\scripts\create-bedrock-agent.ps1 -Environment dev
```

Remember: **When in doubt, clean up first to avoid costs, then investigate!**