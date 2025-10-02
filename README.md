# AWS AI Concierge

An intelligent AI assistant for AWS resource management and monitoring through natural language interactions. Built with Amazon Bedrock, AWS Lambda, and CDK.

## 🎯 Overview

The AWS AI Concierge translates natural language queries into AWS API calls, providing intelligent insights about your cloud infrastructure. Ask questions like "What are my AWS costs this month?" or "Show me idle EC2 instances" and get actionable responses.

### Key Features

- 💰 **Cost Analysis**: Analyze spending patterns and identify optimization opportunities
- 🔍 **Resource Discovery**: Inventory and monitor AWS resources across regions
- 🛡️ **Security Assessment**: Identify security vulnerabilities and compliance issues
- 🤖 **Natural Language Interface**: Interact using plain English queries
- 📊 **Comprehensive Logging**: Complete audit trail for compliance
- ⚡ **Serverless Architecture**: Pay-per-use with automatic scaling

## 🏗️ Architecture

```
User Query → API Gateway → Lambda Functions → AWS APIs
     ↓
Amazon Bedrock Agent (Claude 3 Haiku) → OpenAPI Tools → Formatted Response
```

### Components

- **Amazon Bedrock Agent**: Natural language processing with Claude 3 Haiku
- **AWS Lambda**: Serverless functions for AWS API interactions
- **API Gateway**: RESTful API endpoints for tool invocation
- **S3**: OpenAPI specification storage
- **CloudWatch**: Logging and monitoring
- **IAM**: Read-only permissions with principle of least privilege

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Node.js 18+ and npm
- AWS CDK CLI (`npm install -g aws-cdk`)
- PowerShell (for Windows) or Bash (for Linux/macOS)

### 1. Deploy Infrastructure

```powershell
# Navigate to CDK directory
cd aws-ai-concierge-cdk

# Install dependencies and deploy
npm install
npm run build
.\scripts\deploy.ps1 -Environment dev
```

### 2. Create Bedrock Agent

```powershell
# Create the AI agent
.\scripts\create-bedrock-agent.ps1 -Environment dev
```

### 3. Fix Bedrock Permissions

```powershell
# Fix permissions to prevent 403 errors (use your actual Agent ID)
.\scripts\fix-bedrock-permissions.ps1 -Environment dev -AgentId YOUR_AGENT_ID
```

### 4. Test Your AI Concierge

**Option 1: AWS Console (Recommended)**
1. Go to AWS Console → Amazon Bedrock → Agents
2. Find your agent: `aws-ai-concierge-dev`
3. Click "Test" and try queries like:
   - "What are my AWS costs this month?"
   - "Show me idle EC2 instances"
   - "What security issues should I be concerned about?"

**Option 2: Integration Tests**
```powershell
cd integration-tests
python simple_test_runner.py --environment dev
```

## 💰 Cost Management

### 🚨 Important: POC Cost Control

This project uses pay-per-use AWS services. **Bedrock is the primary cost driver** (~$0.01-0.05 per query).

### Quick Cleanup (Recommended for POC)

```powershell
# Delete all resources to avoid ongoing costs
cd aws-ai-concierge-cdk
.\scripts\cleanup-environment.ps1 -Environment dev
```

### Cost Estimation

```powershell
# View detailed cost breakdown
.\scripts\estimate-costs.ps1 -Environment dev
```

### POC Workflow

1. **Deploy when testing**: `.\scripts\deploy.ps1 -Environment dev`
2. **Test your queries**: Use AWS Console or integration tests
3. **Clean up after testing**: `.\scripts\cleanup-environment.ps1 -Environment dev`
4. **Redeploy for demos**: Takes only 5-10 minutes

### Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| **Bedrock (Claude 3 Haiku)** | ~$0.01-0.05/query | **Main cost driver** |
| Lambda | Pay-per-invocation | Usually within free tier |
| API Gateway | Pay-per-request | Usually within free tier |
| S3 Storage | <$0.01/month | OpenAPI spec storage |
| CloudWatch Logs | <$1/month | Within free tier for POC |
| IAM Roles | **FREE** | No cost when not in use |

**Estimated POC costs**: $3-16/month for light usage (10 queries/day)

## 🛠️ Available Scripts

### Deployment
- `.\scripts\deploy.ps1` - Deploy CDK infrastructure
- `.\scripts\create-bedrock-agent.ps1` - Create Bedrock Agent
- `.\scripts\validate-deployment.ps1` - Validate deployment

### Cost Management
- `.\scripts\cleanup-environment.ps1` - **Delete all resources**
- `.\scripts\estimate-costs.ps1` - View cost breakdown

### Testing
- `.\scripts\test-bedrock-agent.ps1` - Test agent functionality
- `python integration-tests/simple_test_runner.py` - Run integration tests

## 🤖 Example Queries

### Cost Analysis
- "What are my AWS costs this month?"
- "Show me costs by service"
- "Which resources are costing me the most?"
- "Find idle EC2 instances"

### Resource Discovery
- "List all my EC2 instances"
- "What S3 buckets do I have?"
- "Show me resources in us-east-1"
- "What Lambda functions are running?"

### Security Assessment
- "Are there any security issues?"
- "Which resources are publicly accessible?"
- "Check encryption status of my S3 buckets"
- "Show me security group misconfigurations"

## 📁 Project Structure

```
aws-ai-concierge/
├── aws-ai-concierge-cdk/          # CDK infrastructure code
│   ├── lib/                       # CDK stack definitions
│   ├── scripts/                   # Deployment and management scripts
│   └── config/                    # Environment configurations
├── lambda-src/                    # Lambda function source code
│   ├── tools/                     # AWS API integration tools
│   ├── utils/                     # Utilities and helpers
│   └── tests/                     # Unit tests
├── openapi-spec/                  # OpenAPI specifications
├── integration-tests/             # End-to-end tests
├── monitoring/                    # CloudWatch dashboards
└── docs/                         # Additional documentation
```

## 🔧 Configuration

### Environment Settings

Edit `aws-ai-concierge-cdk/config/environments.json`:

```json
{
  "dev": {
    "logRetentionDays": 7,
    "lambdaMemorySize": 512,
    "lambdaTimeout": 180,
    "enableDetailedMonitoring": false
  },
  "prod": {
    "logRetentionDays": 90,
    "lambdaMemorySize": 1024,
    "lambdaTimeout": 300,
    "enableDetailedMonitoring": true
  }
}
```

### Supported Environments
- `dev` - Development (lower costs, shorter retention)
- `staging` - Staging environment
- `prod` - Production (enhanced monitoring, longer retention)

## 🧪 Testing

### Unit Tests
```bash
cd lambda-src
python -m pytest tests/ -v
```

### Integration Tests
```bash
cd integration-tests
python run_integration_tests.py --environment dev
```

### Performance Tests
```bash
python performance_benchmark.py --environment dev
```

## 📊 Monitoring

### CloudWatch Dashboards
```bash
cd monitoring
python cloudwatch_dashboards.py --environment dev
```

### Key Metrics
- Lambda execution duration and errors
- API Gateway request count and latency
- Bedrock token usage and costs
- S3 storage utilization

## 🔒 Security

### IAM Permissions
- **Read-only by default**: All AWS API calls use read-only permissions
- **Principle of least privilege**: Minimal required permissions only
- **No data persistence**: No user data stored beyond session context
- **Audit logging**: Complete audit trail in CloudWatch

### Compliance Features
- Structured JSON logging for regulatory compliance
- Request ID tracking for complete audit trails
- Parameter sanitization for sensitive data protection
- Regional compliance validation

## 🚨 Important Notes

### Before Committing to Git
1. **Clean up AWS resources**: `.\scripts\cleanup-environment.ps1 -Environment dev`
2. **Remove any sensitive data** from configuration files
3. **Verify no hardcoded credentials** in the codebase

### Production Considerations
- Set up billing alerts in AWS Console
- Configure CloudWatch alarms for error rates
- Implement proper CI/CD pipelines
- Use AWS Secrets Manager for sensitive configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Clean up AWS resources after testing
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Deployment fails with "CloudWatch Logs role ARN must be set"**
- Solution: The CDK stack disables API Gateway logging to avoid this issue

**Bedrock Agent creation fails with OpenAPI parsing error**
- Solution: Use the function schema approach in `create-bedrock-agent.ps1`

**High costs appearing**
- Solution: Run `.\scripts\cleanup-environment.ps1 -Environment dev` immediately

### Getting Help

1. Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)
2. Review the [cost management guide](docs/COST_MANAGEMENT.md)
3. Review CloudWatch logs for detailed error information
4. Use the validation script: `.\scripts\validate-deployment.ps1`
5. Check AWS service status at https://status.aws.amazon.com/

## 🎯 Roadmap

- [ ] Support for write operations (with confirmation prompts)
- [ ] Multi-account support
- [ ] Custom dashboard creation
- [ ] Slack/Teams integration
- [ ] Advanced cost forecasting
- [ ] Automated remediation suggestions

---

**⚠️ Remember**: Always run `.\scripts\cleanup-environment.ps1` after testing to avoid unnecessary AWS charges!