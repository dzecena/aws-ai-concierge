# AWS AI Concierge - Deployment Guide

## 🎯 Overview

This guide walks you through deploying the AWS AI Concierge from scratch to a working AI assistant that can answer questions about your AWS infrastructure.

## ⚡ Quick Start (5 Minutes)

### Prerequisites Check
```powershell
# Verify AWS CLI
aws sts get-caller-identity

# Verify Node.js
node --version  # Should be 18+

# Verify CDK
cdk --version
```

### One-Command Deploy
```powershell
cd aws-ai-concierge-cdk
.\scripts\deploy.ps1 -Environment dev && .\scripts\create-bedrock-agent.ps1 -Environment dev
```

### Test Your AI Concierge
1. Go to AWS Console → Amazon Bedrock → Agents
2. Find `aws-ai-concierge-dev`
3. Click "Test" and ask: "What are my AWS costs this month?"

## 📋 Detailed Deployment Steps

### Step 1: Environment Setup

#### Install Prerequisites
```powershell
# Install Node.js (if not installed)
# Download from: https://nodejs.org/

# Install AWS CDK
npm install -g aws-cdk

# Configure AWS CLI (if not configured)
aws configure
```

#### Verify Permissions
Your AWS user/role needs these permissions:
- CloudFormation (full access)
- Lambda (full access)
- API Gateway (full access)
- S3 (full access)
- IAM (full access)
- Bedrock (full access)
- CloudWatch Logs (full access)

### Step 2: Deploy Infrastructure

#### Navigate to CDK Directory
```powershell
cd aws-ai-concierge-cdk
```

#### Install Dependencies
```powershell
npm install
```

#### Build Project
```powershell
npm run build
```

#### Bootstrap CDK (First Time Only)
```powershell
# Replace with your account ID and region
cdk bootstrap aws://123456789012/us-east-1
```

#### Deploy CDK Stack
```powershell
.\scripts\deploy.ps1 -Environment dev
```

**Expected Output:**
```
🚀 AWS AI Concierge CDK Deployment
Environment: dev
Region: us-east-1

✅ AWS CLI configured
✅ CDK already bootstrapped
📦 Installing dependencies...
🔨 Building project...
🚀 Deploying CDK stack...

✨ Deployment time: 111.94s

Outputs:
AwsAiConcierge-dev.ApiGatewayUrl = https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/
AwsAiConcierge-dev.LambdaFunctionName = aws-ai-concierge-tools-dev
...

🎉 Deployment completed successfully!
```

### Step 3: Create Bedrock Agent

#### Run Agent Creation Script
```powershell
.\scripts\create-bedrock-agent.ps1 -Environment dev
```

**Expected Output:**
```
🤖 Creating Bedrock Agent
Environment: dev

✅ Retrieved stack outputs
✅ Bedrock Agent created successfully
  Agent ID: XXXXXXXXXX
✅ Action Group created successfully
✅ Agent prepared successfully
✅ Agent Alias created successfully

🎉 Bedrock Agent setup completed successfully!
```

### Step 4: Validate Deployment

#### Run Validation Script
```powershell
.\scripts\validate-deployment.ps1 -Environment dev
```

#### Test Lambda Function Directly
```powershell
# Test via API Gateway
Invoke-RestMethod -Uri "https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/cost-analysis" -Method POST -ContentType "application/json" -Body '{"time_period":"MONTHLY"}'
```

**Expected Response:**
```json
{
  "success": true,
  "operation": "getCostAnalysis",
  "data": {
    "total_cost": 0.0,
    "currency": "USD",
    "time_period": "MONTHLY"
  }
}
```

### Step 5: Test Bedrock Agent

#### Option 1: AWS Console (Recommended)
1. Go to AWS Console → Amazon Bedrock → Agents
2. Find your agent: `aws-ai-concierge-dev`
3. Click "Test"
4. Try these queries:
   - "What are my AWS costs this month?"
   - "Show me my EC2 instances"
   - "Are there any security issues?"

#### Option 2: Command Line
```powershell
aws bedrock-agent-runtime invoke-agent \
  --agent-id YOUR_AGENT_ID \
  --agent-alias-id dev \
  --session-id test-session \
  --input-text "What are my AWS costs this month?" \
  response.json
```

#### Option 3: Integration Tests
```powershell
cd ../integration-tests
python simple_test_runner.py --environment dev
```

## 🌍 Multi-Environment Deployment

### Environment Configuration

Edit `config/environments.json`:
```json
{
  "dev": {
    "logRetentionDays": 7,
    "lambdaMemorySize": 512,
    "lambdaTimeout": 180,
    "enableDetailedMonitoring": false,
    "enableXRayTracing": false,
    "removalPolicy": "DESTROY"
  },
  "staging": {
    "logRetentionDays": 30,
    "lambdaMemorySize": 768,
    "lambdaTimeout": 240,
    "enableDetailedMonitoring": true,
    "enableXRayTracing": true,
    "removalPolicy": "RETAIN"
  },
  "prod": {
    "logRetentionDays": 90,
    "lambdaMemorySize": 1024,
    "lambdaTimeout": 300,
    "enableDetailedMonitoring": true,
    "enableXRayTracing": true,
    "removalPolicy": "RETAIN"
  }
}
```

### Deploy to Different Environments

#### Development
```powershell
.\scripts\deploy.ps1 -Environment dev
.\scripts\create-bedrock-agent.ps1 -Environment dev
```

#### Staging
```powershell
.\scripts\deploy.ps1 -Environment staging
.\scripts\create-bedrock-agent.ps1 -Environment staging
```

#### Production
```powershell
.\scripts\deploy.ps1 -Environment prod -Region us-east-1 -Account 123456789012
.\scripts\create-bedrock-agent.ps1 -Environment prod
```

## 🔧 Configuration Options

### Lambda Configuration
```json
{
  "lambdaMemorySize": 512,     // MB (128-10240)
  "lambdaTimeout": 180,        // seconds (1-900)
  "reservedConcurrency": 10    // concurrent executions
}
```

### Monitoring Configuration
```json
{
  "enableDetailedMonitoring": true,  // CloudWatch detailed metrics
  "enableXRayTracing": true,         // X-Ray distributed tracing
  "logRetentionDays": 30             // CloudWatch log retention
}
```

### Security Configuration
```json
{
  "removalPolicy": "RETAIN",  // DESTROY for dev, RETAIN for prod
  "enableEncryption": true,   // S3 bucket encryption
  "blockPublicAccess": true   // S3 public access blocking
}
```

## 🔍 Deployment Verification

### Check Resource Status
```powershell
# CloudFormation Stack
aws cloudformation describe-stacks --stack-name AwsAiConcierge-dev --query "Stacks[0].StackStatus"

# Lambda Function
aws lambda get-function --function-name aws-ai-concierge-tools-dev --query "Configuration.State"

# Bedrock Agent
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID --query "agent.agentStatus"

# S3 Bucket
aws s3 ls aws-ai-concierge-openapi-dev-ACCOUNT-REGION
```

### View Deployment Outputs
```powershell
# Get all stack outputs
aws cloudformation describe-stacks --stack-name AwsAiConcierge-dev --query "Stacks[0].Outputs"

# Get specific output
aws cloudformation describe-stacks --stack-name AwsAiConcierge-dev --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" --output text
```

## 🚨 Troubleshooting Deployment

### Common Issues

#### CDK Bootstrap Required
```
This stack uses assets, so the toolkit stack must be deployed
```
**Solution:**
```powershell
cdk bootstrap aws://ACCOUNT-ID/REGION
```

#### Insufficient Permissions
```
User is not authorized to perform: cloudformation:CreateStack
```
**Solution:** Add CloudFormation, Lambda, API Gateway, S3, IAM, and Bedrock permissions to your user/role.

#### Stack Already Exists
```
AwsAiConcierge-dev already exists
```
**Solution:**
```powershell
aws cloudformation delete-stack --stack-name AwsAiConcierge-dev
aws cloudformation wait stack-delete-complete --stack-name AwsAiConcierge-dev
```

#### Bedrock Agent Creation Fails
```
Failed to create OpenAPI 3 model from the JSON/YAML object
```
**Solution:** The script uses function schema instead of OpenAPI schema to avoid this issue.

### Deployment Logs
```powershell
# CDK deployment logs
cdk deploy --verbose

# CloudFormation events
aws cloudformation describe-stack-events --stack-name AwsAiConcierge-dev

# Lambda logs
aws logs tail /aws/lambda/aws-ai-concierge-tools-dev --follow
```

## 🔄 Update Deployment

### Update Infrastructure
```powershell
# Make changes to CDK code
# Then redeploy
npm run build
.\scripts\deploy.ps1 -Environment dev
```

### Update Lambda Code Only
```powershell
# Update Lambda function code
aws lambda update-function-code \
  --function-name aws-ai-concierge-tools-dev \
  --zip-file fileb://lambda-deployment-package.zip
```

### Update Bedrock Agent
```powershell
# Delete and recreate agent
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID --skip-resource-in-use-check
.\scripts\create-bedrock-agent.ps1 -Environment dev
```

## 🧹 Clean Up Deployment

### Complete Cleanup
```powershell
.\scripts\cleanup-environment.ps1 -Environment dev
```

### Selective Cleanup
```powershell
# Delete just the Bedrock agent
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID --skip-resource-in-use-check

# Delete just the CDK stack
aws cloudformation delete-stack --stack-name AwsAiConcierge-dev
```

## 📊 Post-Deployment Monitoring

### Set Up CloudWatch Alarms
```powershell
cd ../monitoring
python cloudwatch_dashboards.py --environment dev
```

### Monitor Costs
```powershell
.\scripts\estimate-costs.ps1 -Environment dev
```

### View Metrics
- Lambda function metrics in CloudWatch
- API Gateway metrics and logs
- Bedrock usage in CloudWatch
- S3 storage metrics

## 🎯 Next Steps After Deployment

1. **Test thoroughly**: Use the integration test suite
2. **Set up monitoring**: CloudWatch dashboards and alarms
3. **Configure cost alerts**: Billing alarms in AWS Console
4. **Document your queries**: Keep track of useful questions
5. **Plan for production**: Review security and compliance requirements

## 📋 Deployment Checklist

- [ ] Prerequisites installed (Node.js, AWS CLI, CDK)
- [ ] AWS credentials configured
- [ ] CDK bootstrapped
- [ ] Infrastructure deployed successfully
- [ ] Bedrock agent created and prepared
- [ ] Lambda function tested
- [ ] API Gateway endpoints working
- [ ] Integration tests passing
- [ ] Cost monitoring set up
- [ ] Documentation reviewed

**🎉 Congratulations! Your AWS AI Concierge is now ready to help manage your AWS infrastructure!**