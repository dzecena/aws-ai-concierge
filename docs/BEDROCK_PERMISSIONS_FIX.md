# Bedrock Agent Permissions Fix

## 🚨 Problem Description

When testing the Bedrock Agent in the AWS Console, users encounter a 403 "Access denied when calling Bedrock" error:

```json
{
  "failureCode": 403,
  "failureReason": "Access denied when calling Bedrock. Check your request permissions and retry the request."
}
```

## 🔍 Root Cause

The Bedrock Agent's execution role lacks the necessary permissions to:
1. Invoke Bedrock foundation models (Claude 3 Haiku/Sonnet)
2. Call the Lambda functions with proper authorization

## ✅ Solution

### Automated Fix (Recommended)

Run the permission fix script:

```powershell
cd aws-ai-concierge-cdk
.\scripts\fix-bedrock-permissions.ps1 -Environment dev -AgentId YOUR_AGENT_ID
```

### What the Script Does

1. **Adds Lambda Invoke Permission**
   - Grants Bedrock Agent permission to invoke the Lambda function
   - Sets proper source ARN restrictions for security

2. **Adds Bedrock Model Permissions**
   - Grants `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`
   - Specifically for Claude 3 Haiku and Sonnet models

3. **Updates Agent Role**
   - Applies policies to the agent's execution role
   - Re-prepares the agent to pick up new permissions

### Manual Fix (If Script Fails)

#### Step 1: Add Lambda Permission
```bash
aws lambda add-permission \
  --function-name aws-ai-concierge-tools-dev \
  --statement-id bedrock-agent-invoke-dev \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-east-1:ACCOUNT:agent/AGENT_ID"
```

#### Step 2: Add Bedrock Model Permissions
```bash
aws iam put-role-policy \
  --role-name aws-ai-concierge-bedrock-role-dev \
  --policy-name BedrockModelInvokePolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    }]
  }'
```

#### Step 3: Re-prepare Agent
```bash
aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID
```

## 🧪 Verification

### Check Agent Status
```bash
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID --query "agent.agentStatus"
# Should return: "PREPARED"
```

### Check Role Permissions
```bash
aws iam list-role-policies --role-name aws-ai-concierge-bedrock-role-dev
# Should include: BedrockModelInvokePolicy, LambdaInvokePolicy
```

### Test Agent
1. Go to AWS Console → Bedrock → Agents
2. Select your agent
3. Click "Test"
4. Ask: "What are my AWS costs this month?"
5. Should receive a proper response without 403 errors

## 📋 Required Permissions

### Bedrock Agent Role Needs:
- `bedrock:InvokeModel` - To call foundation models
- `bedrock:InvokeModelWithResponseStream` - For streaming responses
- `lambda:InvokeFunction` - To call Lambda functions

### Lambda Function Needs:
- Permission for `bedrock.amazonaws.com` principal to invoke it
- Proper source ARN restriction for security

### Foundation Models Required:
- `anthropic.claude-3-haiku-20240307-v1:0` (primary model)
- `anthropic.claude-3-sonnet-20240229-v1:0` (fallback model)

## 🔧 Integration with Deployment

### Updated Deployment Process

1. Deploy infrastructure: `.\scripts\deploy.ps1 -Environment dev`
2. Create Bedrock Agent: `.\scripts\create-bedrock-agent.ps1 -Environment dev`
3. **Fix permissions: `.\scripts\fix-bedrock-permissions.ps1 -Environment dev -AgentId YOUR_AGENT_ID`**
4. Test the agent in AWS Console

### Documentation Updates

- ✅ README.md - Updated quick start section
- ✅ DEPLOYMENT_GUIDE.md - Added permission fix step
- ✅ TROUBLESHOOTING.md - Added 403 error resolution
- ✅ Scripts - Created fix-bedrock-permissions.ps1

## 🚨 Common Issues

### Permission Propagation Delay
**Issue**: Permissions applied but still getting 403 errors
**Solution**: Wait 2-3 minutes for IAM changes to propagate

### Foundation Model Access
**Issue**: Model not available in region
**Solution**: Ensure Claude 3 Haiku is enabled in Bedrock console for your region

### Agent Not Prepared
**Issue**: Agent status is not "PREPARED"
**Solution**: Run `aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID`

### Script Syntax Errors
**Issue**: PowerShell script fails with syntax errors
**Solution**: Use the simplified script or manual commands above

## 📊 Impact Assessment

### Before Fix
- ❌ Agent returns 403 errors
- ❌ Cannot invoke foundation models
- ❌ Lambda functions not accessible
- ❌ Poor user experience

### After Fix
- ✅ Agent responds to queries
- ✅ Foundation models accessible
- ✅ Lambda functions working
- ✅ Complete functionality

## 🔄 Maintenance

### Regular Checks
- Verify agent status remains "PREPARED"
- Monitor CloudWatch logs for permission errors
- Test agent functionality after AWS updates

### Updates Required When:
- Adding new foundation models
- Changing Lambda function names
- Updating agent configuration
- Deploying to new regions

## 📝 Change Log

### Version 1.0 (Current)
- Initial permission fix implementation
- Automated script creation
- Documentation updates
- Integration with deployment process

### Future Enhancements
- Automatic permission detection and fixing
- Support for additional foundation models
- Cross-region permission management
- Enhanced error reporting

---

**Note**: This fix is now integrated into the standard deployment process and should be run after creating any new Bedrock Agent.