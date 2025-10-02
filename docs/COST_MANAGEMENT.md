# AWS AI Concierge - Cost Management Guide

## 🚨 Critical: POC Cost Control

**The AWS AI Concierge uses pay-per-use services. Bedrock is the primary cost driver at ~$0.01-0.05 per query.**

This guide ensures you don't get surprise AWS bills during development and testing.

## 🧹 Quick Cleanup (Most Important)

### Emergency Stop - Delete Everything Now
```powershell
cd aws-ai-concierge-cdk
.\scripts\cleanup-environment.ps1 -Environment dev -Force
```

### Standard Cleanup (with confirmation)
```powershell
cd aws-ai-concierge-cdk
.\scripts\cleanup-environment.ps1 -Environment dev
```

**What gets deleted:**
- ✅ Bedrock Agent (main cost driver)
- ✅ Lambda Function
- ✅ API Gateway
- ✅ S3 Bucket and contents
- ✅ CloudWatch Log Groups
- ✅ IAM Roles and Policies

## 💰 Cost Breakdown

### Services That Cost Money

| Service | Cost Structure | Estimated Cost | Free Tier |
|---------|---------------|----------------|-----------|
| **Amazon Bedrock** | $0.00025/1K input tokens<br>$0.00125/1K output tokens | **$0.01-0.05 per query** | ❌ None |
| **AWS Lambda** | $0.0000166667 per GB-second | ~$0.000001 per request | ✅ 1M requests/month |
| **API Gateway** | $3.50 per million calls | ~$0.0000035 per request | ✅ 1M calls/month |
| **S3 Storage** | $0.023 per GB/month | <$0.00002/month | ✅ 5GB for 12 months |
| **CloudWatch Logs** | $0.50 per GB ingested | <$1/month typical | ✅ 5GB ingestion/month |

### Services That Are Free
- **IAM Roles & Policies**: Completely free
- **CloudFormation**: Free for stack management

## 📊 Usage Cost Scenarios

### 🟢 Light POC Usage (10 queries/day)
- **Bedrock**: $3-15/month
- **Other services**: FREE (within free tier)
- **Total**: **$3-16/month**

### 🟡 Moderate Testing (100 queries/day)
- **Bedrock**: $30-150/month
- **Lambda**: FREE (within free tier)
- **API Gateway**: $0.35/month
- **Other services**: <$2/month
- **Total**: **$32-152/month**

### 🔴 Heavy Usage (1000 queries/day)
- **Bedrock**: $300-1500/month
- **Lambda**: $1-5/month
- **API Gateway**: $3.50/month
- **Other services**: $5/month
- **Total**: **$309-1513/month**

## 🔄 Recommended POC Workflow

### Daily Development Cycle
```powershell
# 1. Deploy when you start working
.\scripts\deploy.ps1 -Environment dev
.\scripts\create-bedrock-agent.ps1 -Environment dev

# 2. Test and develop
# Use AWS Console or integration tests

# 3. Clean up when done for the day
.\scripts\cleanup-environment.ps1 -Environment dev
```

### Demo/Presentation Cycle
```powershell
# 1. Quick deploy before demo (5-10 minutes)
.\scripts\deploy.ps1 -Environment dev
.\scripts\create-bedrock-agent.ps1 -Environment dev

# 2. Run your demo

# 3. Clean up immediately after
.\scripts\cleanup-environment.ps1 -Environment dev
```

## 📈 Cost Monitoring Setup

### 1. AWS Billing Alerts
1. Go to AWS Console → Billing → Billing preferences
2. Enable "Receive Billing Alerts"
3. Set up CloudWatch billing alarm for $10-20/month

### 2. Service-Specific Monitoring
```powershell
# Check current costs
.\scripts\estimate-costs.ps1 -Environment dev

# Monitor Bedrock usage
aws logs filter-log-events --log-group-name "/aws/lambda/aws-ai-concierge-tools-dev" --filter-pattern "bedrock"
```

### 3. Daily Cost Check
```bash
# Check yesterday's costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-02 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## 🎯 Cost Optimization Strategies

### 1. Development Best Practices
- **Use cleanup script religiously**: After every testing session
- **Test in batches**: Don't leave agent running between tests
- **Use dev environment**: Lower resource allocation than prod

### 2. Query Optimization
- **Keep prompts concise**: Fewer tokens = lower cost
- **Batch related questions**: Ask multiple things in one query
- **Cache common responses**: Avoid repeated identical queries

### 3. Resource Configuration
```json
// aws-ai-concierge-cdk/config/environments.json
{
  "dev": {
    "logRetentionDays": 7,        // Shorter retention = lower cost
    "lambdaMemorySize": 512,      // Lower memory = lower cost
    "lambdaTimeout": 180          // Shorter timeout = lower cost
  }
}
```

## 🚨 Emergency Procedures

### If You See Unexpected Charges

1. **Immediate Action**:
   ```powershell
   .\scripts\cleanup-environment.ps1 -Environment dev -Force
   ```

2. **Verify Cleanup**:
   ```powershell
   # Check for remaining resources
   aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
   aws bedrock-agent list-agents
   aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aws-ai-concierge')]"
   ```

3. **Check AWS Console**:
   - CloudFormation → Stacks
   - Bedrock → Agents
   - Lambda → Functions
   - S3 → Buckets

### If Cleanup Script Fails

Manual cleanup commands:
```powershell
# Delete Bedrock Agent (replace AGENT_ID)
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID --skip-resource-in-use-check

# Delete CloudFormation Stack
aws cloudformation delete-stack --stack-name AwsAiConcierge-dev

# Delete S3 Bucket (replace with your bucket name)
aws s3 rm s3://aws-ai-concierge-openapi-dev-ACCOUNT-REGION --recursive
aws s3api delete-bucket --bucket aws-ai-concierge-openapi-dev-ACCOUNT-REGION

# Delete CloudWatch Log Groups
aws logs delete-log-group --log-group-name /aws/lambda/aws-ai-concierge-tools-dev
```

## 📋 Pre-Commit Checklist

Before committing code or leaving for the day:

- [ ] Run cleanup script: `.\scripts\cleanup-environment.ps1 -Environment dev`
- [ ] Verify no active CloudFormation stacks
- [ ] Check no Bedrock agents are running
- [ ] Confirm no unexpected charges in AWS billing
- [ ] Remove any hardcoded credentials from code

## 🔍 Cost Verification Commands

### Check Current Deployment Status
```powershell
# Check if resources exist
aws cloudformation describe-stacks --stack-name AwsAiConcierge-dev 2>$null
aws bedrock-agent list-agents --query "agentSummaries[?contains(agentName, 'aws-ai-concierge')]"
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aws-ai-concierge')]"
```

### Estimate Current Month Costs
```powershell
# Get current month costs for key services
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter file://cost-filter.json
```

## 💡 Pro Tips

1. **Set Calendar Reminders**: Daily reminder to run cleanup script
2. **Use Billing Alerts**: Set up alerts for $5, $10, $20 thresholds
3. **Monitor Token Usage**: Check CloudWatch for Bedrock token consumption
4. **Batch Testing**: Do all your testing in one session, then clean up
5. **Document Costs**: Keep track of what each test session costs

## 🎯 Cost-Conscious Development

### Before Starting Development
```powershell
# Check if anything is already running
.\scripts\estimate-costs.ps1 -Environment dev
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE
```

### During Development
- Test efficiently - don't leave resources idle
- Use integration tests to validate functionality quickly
- Monitor CloudWatch logs for any unexpected activity

### After Development
```powershell
# Always clean up
.\scripts\cleanup-environment.ps1 -Environment dev

# Verify cleanup worked
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

## 📞 Support

If you're seeing unexpected costs:

1. **Immediate**: Run the cleanup script
2. **Investigate**: Check AWS Cost Explorer
3. **Prevent**: Set up billing alerts
4. **Document**: Note what caused the costs for future reference

Remember: **The cleanup script is your best friend for cost control!**

---

**⚠️ Final Reminder**: The most expensive mistake is forgetting to clean up after testing. Make it a habit to run the cleanup script every time you finish working with the AI Concierge.