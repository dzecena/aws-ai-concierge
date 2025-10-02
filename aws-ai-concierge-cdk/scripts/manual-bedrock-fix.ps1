# Manual Bedrock Permission Fix for User dzecena
# Run these commands one by one to fix the 403 Bedrock error

Write-Host "Manual Bedrock Permission Fix" -ForegroundColor Green
Write-Host "Run each command separately and check for errors" -ForegroundColor Yellow
Write-Host ""

# Variables
$AgentId = "3REQDYQGXU"
$Environment = "dev"
$RoleName = "aws-ai-concierge-bedrock-role-dev"
$LambdaFunctionName = "aws-ai-concierge-tools-dev"

Write-Host "=== STEP 1: Check Current Identity ===" -ForegroundColor Blue
Write-Host "aws sts get-caller-identity" -ForegroundColor Gray
Write-Host ""

Write-Host "=== STEP 2: Enable Claude 3 Model Access ===" -ForegroundColor Blue
Write-Host "IMPORTANT: You need to enable Claude 3 Haiku in the Bedrock console:" -ForegroundColor Red
Write-Host "1. Go to AWS Console → Amazon Bedrock → Model access" -ForegroundColor Yellow
Write-Host "2. Click 'Request model access'" -ForegroundColor Yellow
Write-Host "3. Find 'Claude 3 Haiku' and request access" -ForegroundColor Yellow
Write-Host "4. Wait for approval (usually instant for Claude 3 Haiku)" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== STEP 3: Add Bedrock Permissions to Role ===" -ForegroundColor Blue
Write-Host "Copy and paste this command:" -ForegroundColor Gray
Write-Host @"
aws iam put-role-policy --role-name $RoleName --policy-name BedrockModelInvokePolicy --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}'
"@ -ForegroundColor Cyan
Write-Host ""

Write-Host "=== STEP 4: Add Lambda Permissions ===" -ForegroundColor Blue
Write-Host "Copy and paste this command:" -ForegroundColor Gray
Write-Host @"
aws lambda add-permission --function-name $LambdaFunctionName --statement-id bedrock-agent-invoke-$Environment --action lambda:InvokeFunction --principal bedrock.amazonaws.com --source-arn "arn:aws:bedrock:us-east-1:296158189643:agent/$AgentId"
"@ -ForegroundColor Cyan
Write-Host ""

Write-Host "=== STEP 5: Re-prepare Agent ===" -ForegroundColor Blue
Write-Host "Copy and paste this command:" -ForegroundColor Gray
Write-Host "aws bedrock-agent prepare-agent --agent-id $AgentId" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== STEP 6: Check Agent Status ===" -ForegroundColor Blue
Write-Host "Copy and paste this command:" -ForegroundColor Gray
Write-Host "aws bedrock-agent get-agent --agent-id $AgentId --query agent.agentStatus --output text" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== STEP 7: Test in Console ===" -ForegroundColor Blue
Write-Host "1. Go to AWS Console → Amazon Bedrock → Agents" -ForegroundColor Yellow
Write-Host "2. Find agent: aws-ai-concierge-dev" -ForegroundColor Yellow
Write-Host "3. Click Test" -ForegroundColor Yellow
Write-Host "4. Ask: 'Hello, are you working?'" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== TROUBLESHOOTING ===" -ForegroundColor Red
Write-Host "If you still get 403 errors:" -ForegroundColor Yellow
Write-Host "1. Check that Claude 3 Haiku is enabled in Bedrock console" -ForegroundColor Yellow
Write-Host "2. Verify your user has Bedrock permissions" -ForegroundColor Yellow
Write-Host "3. Wait 5 minutes for permissions to propagate" -ForegroundColor Yellow
Write-Host "4. Try a different region (us-west-2)" -ForegroundColor Yellow