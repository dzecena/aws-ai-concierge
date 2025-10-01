# AWS AI Concierge - CDK Deployment Guide

This guide provides comprehensive instructions for deploying the AWS AI Concierge infrastructure using AWS CDK.

## 📋 Prerequisites

### Required Tools
- **Node.js** (v18 or later)
- **AWS CLI** (v2.x)
- **AWS CDK** (v2.x)
- **PowerShell** (for Windows deployment scripts)

### AWS Requirements
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Sufficient permissions for:
  - CloudFormation stack operations
  - Lambda function management
  - IAM role and policy management
  - S3 bucket operations
  - API Gateway management
  - Bedrock service access (if available in region)
  - CloudWatch logs and monitoring

### Installation Commands
```bash
# Install Node.js dependencies
npm install

# Install AWS CDK globally (if not already installed)
npm install -g aws-cdk

# Verify installations
node --version
aws --version
cdk --version
```

## 🏗️ Architecture Overview

The CDK stack deploys the following resources:

### Core Infrastructure
- **Lambda Function**: Main AI Concierge tools handler
- **IAM Roles**: Execution roles for Lambda and Bedrock Agent
- **S3 Bucket**: OpenAPI specification storage
- **CloudWatch Log Groups**: Centralized logging

### API Layer
- **API Gateway**: REST API for tool invocation
- **Bedrock Agent**: AI assistant with Claude 3 Haiku model
- **Bedrock Agent Alias**: Environment-specific agent alias

### Monitoring (Production)
- **CloudWatch Alarms**: Error rate and performance monitoring
- **X-Ray Tracing**: Distributed tracing (production environments)
- **Detailed Monitoring**: Enhanced metrics collection

## 🌍 Environment Configuration

The deployment supports three environments with different configurations:

### Development (`dev`)
- **Purpose**: Development and testing
- **Log Retention**: 7 days
- **Lambda Memory**: 512 MB
- **Lambda Timeout**: 3 minutes
- **Monitoring**: Basic
- **X-Ray Tracing**: Disabled
- **Removal Policy**: DESTROY (resources deleted on stack deletion)

### Staging (`staging`)
- **Purpose**: Pre-production testing
- **Log Retention**: 30 days
- **Lambda Memory**: 768 MB
- **Lambda Timeout**: 4 minutes
- **Monitoring**: Enhanced
- **X-Ray Tracing**: Enabled
- **Removal Policy**: RETAIN (resources preserved on stack deletion)

### Production (`prod`)
- **Purpose**: Live workloads
- **Log Retention**: 90 days
- **Lambda Memory**: 1024 MB
- **Lambda Timeout**: 5 minutes
- **Monitoring**: Full monitoring with alarms
- **X-Ray Tracing**: Enabled
- **Removal Policy**: RETAIN (resources preserved on stack deletion)

## 🚀 Deployment Instructions

### Method 1: Using PowerShell Script (Recommended for Windows)

```powershell
# Deploy to development environment
.\scripts\deploy.ps1 -Environment dev

# Deploy to staging environment
.\scripts\deploy.ps1 -Environment staging -Region us-east-1

# Deploy to production environment
.\scripts\deploy.ps1 -Environment prod -Region us-east-1 -Account 123456789012
```

### Method 2: Using Bash Script (Linux/macOS)

```bash
# Make script executable
chmod +x scripts/deploy.sh

# Deploy to development environment
./scripts/deploy.sh dev

# Deploy to staging environment
./scripts/deploy.sh staging us-east-1

# Deploy to production environment
./scripts/deploy.sh prod us-east-1 123456789012
```

### Method 3: Manual CDK Commands

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy with environment context
cdk deploy --context environment=dev --context region=us-east-1
```

## 🔍 Deployment Validation

After deployment, validate the infrastructure:

```powershell
# Validate deployment
.\scripts\validate-deployment.ps1 -Environment dev
```

The validation script checks:
- ✅ CDK stack status
- ✅ Lambda function availability
- ✅ S3 bucket accessibility
- ✅ API Gateway configuration
- ✅ Bedrock Agent setup
- ✅ CloudWatch log groups
- ✅ Lambda function invocation test

## 📊 Stack Outputs

After successful deployment, the stack provides these outputs:

```json
{
  "Environment": "dev",
  "OpenApiBucketName": "aws-ai-concierge-openapi-dev-123456789012-us-east-1",
  "OpenApiSpecUrl": "https://aws-ai-concierge-openapi-dev-123456789012-us-east-1.s3.amazonaws.com/aws-ai-concierge-tools.yaml",
  "ApiGatewayUrl": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/",
  "BedrockAgentId": "ABCDEFGHIJ",
  "BedrockAgentAliasId": "KLMNOPQRST",
  "BedrockAgentArn": "arn:aws:bedrock:us-east-1:123456789012:agent/ABCDEFGHIJ",
  "LambdaFunctionName": "aws-ai-concierge-tools-dev",
  "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:aws-ai-concierge-tools-dev",
  "LambdaRoleArn": "arn:aws:iam::123456789012:role/aws-ai-concierge-lambda-role-dev",
  "BedrockAgentRoleArn": "arn:aws:iam::123456789012:role/aws-ai-concierge-bedrock-role-dev",
  "LogGroupName": "/aws/lambda/aws-ai-concierge-tools-dev"
}
```

## 🏷️ Resource Tagging

All resources are automatically tagged with:

### Common Tags
- **Environment**: dev/staging/prod
- **Project**: AWS-AI-Concierge
- **ManagedBy**: CDK
- **CostCenter**: Engineering-{Environment}
- **Owner**: DevOps-Team
- **DeployedAt**: ISO timestamp

### Resource-Specific Tags
- **ResourceType**: S3Bucket, LambdaFunction, IAMRole, etc.
- **Purpose**: Descriptive purpose of the resource

### Environment-Specific Tags
- **AutoShutdown**: true (dev only)
- **BackupRequired**: true (prod only)
- **Compliance**: SOC2 (prod only)

## 🔧 Configuration Management

### Environment Configuration File
The `config/environments.json` file contains environment-specific settings:

```json
{
  "dev": {
    "logRetentionDays": 7,
    "lambdaMemorySize": 512,
    "enableDetailedMonitoring": false,
    "tags": {
      "AutoShutdown": "true"
    }
  }
}
```

### CDK Context
Pass configuration via CDK context:

```bash
cdk deploy --context environment=prod --context region=us-east-1
```

## 📈 Monitoring and Alerting

### Production Monitoring
Production deployments include CloudWatch alarms for:

- **Lambda Error Rate**: Triggers when error rate exceeds 10 errors in 10 minutes
- **Lambda Duration**: Triggers when average duration exceeds 30 seconds
- **API Gateway 4XX Errors**: Triggers when 4XX errors exceed 50 in 10 minutes
- **API Gateway 5XX Errors**: Triggers when 5XX errors exceed 10 in 10 minutes

### Log Analysis
Structured logs are available in CloudWatch:
- **Request Logs**: `/aws/lambda/aws-ai-concierge-tools-{environment}`
- **Audit Logs**: Structured JSON logs for compliance
- **Performance Metrics**: Execution time and resource usage

## 🔒 Security Considerations

### IAM Permissions
- **Lambda Role**: Read-only AWS permissions for resource discovery
- **Bedrock Agent Role**: Limited to Lambda invocation and S3 access
- **Principle of Least Privilege**: All roles follow minimal permission requirements

### Network Security
- **S3 Bucket**: Block all public access
- **API Gateway**: CORS configured for controlled access
- **Lambda**: VPC deployment optional (configure if needed)

### Data Protection
- **Encryption**: S3 bucket uses server-side encryption
- **Audit Logging**: All operations logged for compliance
- **Parameter Sanitization**: Sensitive data redacted in logs

## 🛠️ Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Required
```
Error: Need to perform AWS CDK bootstrap
```
**Solution**: Run `cdk bootstrap aws://ACCOUNT/REGION`

#### 2. Insufficient Permissions
```
Error: User is not authorized to perform: iam:CreateRole
```
**Solution**: Ensure AWS credentials have sufficient permissions

#### 3. Bedrock Not Available
```
Error: Bedrock service not available in region
```
**Solution**: Deploy to a region where Bedrock is available (us-east-1, us-west-2, etc.)

#### 4. Lambda Package Too Large
```
Error: Unzipped size must be smaller than 262144000 bytes
```
**Solution**: Optimize Lambda package size or increase memory allocation

### Debugging Commands

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name AwsAiConcierge-dev

# View stack events
aws cloudformation describe-stack-events --stack-name AwsAiConcierge-dev

# Check Lambda function
aws lambda get-function --function-name aws-ai-concierge-tools-dev

# View Lambda logs
aws logs tail /aws/lambda/aws-ai-concierge-tools-dev --follow
```

## 🔄 Updates and Maintenance

### Updating the Stack
```bash
# Update with latest changes
npm run build
cdk deploy --context environment=prod
```

### Rolling Back
```bash
# View deployment history
aws cloudformation describe-stack-events --stack-name AwsAiConcierge-prod

# Rollback if needed (manual process)
# Redeploy previous version or use CloudFormation console
```

### Cleanup
```bash
# Destroy development environment
cdk destroy --context environment=dev

# Note: Production resources with RETAIN policy must be manually deleted
```

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review CloudFormation stack events
3. Check Lambda function logs
4. Validate AWS permissions
5. Ensure all prerequisites are met

## 🎯 Next Steps

After successful deployment:
1. **Upload OpenAPI Specification** to the S3 bucket
2. **Test Lambda Endpoints** using the API Gateway URL
3. **Configure Bedrock Agent** with the OpenAPI specification
4. **Set up Monitoring** dashboards and alerts
5. **Test End-to-End** functionality with sample queries