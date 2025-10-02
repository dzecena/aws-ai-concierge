# Comprehensive Bedrock Agent Permissions Diagnostic and Fix
param(
    [string]$AgentId = "3REQDYQGXU",
    [string]$Environment = "dev"
)

Write-Host "🔍 Diagnosing Bedrock Agent Permissions" -ForegroundColor Blue
Write-Host "Agent ID: $AgentId" -ForegroundColor Blue
Write-Host ""

# Get current account and region
$Account = (aws sts get-caller-identity --query Account --output text)
$Region = (aws configure get region)
if (-not $Region) { $Region = "us-east-1" }

Write-Host "Account: $Account" -ForegroundColor Blue
Write-Host "Region: $Region" -ForegroundColor Blue
Write-Host ""

# 1. Check if Claude 3 Haiku is available in the region
Write-Host "1. Checking available foundation models..." -ForegroundColor Yellow
try {
    $AvailableModels = aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'claude-3')].[modelId,modelName]" --output text
    if ($AvailableModels) {
        Write-Host "✅ Claude 3 models available:" -ForegroundColor Green
        Write-Host $AvailableModels -ForegroundColor Blue
    } else {
        Write-Host "❌ No Claude 3 models found in region $Region" -ForegroundColor Red
        Write-Host "💡 You may need to enable Claude 3 models in the Bedrock console" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to list foundation models" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# 2. Check agent details
Write-Host "2. Checking agent configuration..." -ForegroundColor Yellow
try {
    $AgentDetails = aws bedrock-agent get-agent --agent-id $AgentId --output json | ConvertFrom-Json
    $AgentStatus = $AgentDetails.agent.agentStatus
    $AgentRole = $AgentDetails.agent.agentResourceRoleArn
    $FoundationModel = $AgentDetails.agent.foundationModel
    
    Write-Host "Agent Status: $AgentStatus" -ForegroundColor Blue
    Write-Host "Agent Role: $AgentRole" -ForegroundColor Blue
    Write-Host "Foundation Model: $FoundationModel" -ForegroundColor Blue
    
    if ($AgentStatus -ne "PREPARED") {
        Write-Host "⚠️  Agent is not in PREPARED state" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Agent is prepared" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Failed to get agent details" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# 3. Check role permissions
Write-Host "3. Checking role permissions..." -ForegroundColor Yellow
$RoleName = $AgentRole.Split('/')[-1]
Write-Host "Role Name: $RoleName" -ForegroundColor Blue

try {
    $RolePolicies = aws iam list-role-policies --role-name $RoleName --query "PolicyNames" --output text
    Write-Host "Attached Policies: $RolePolicies" -ForegroundColor Blue
    
    # Check if BedrockModelInvokePolicy exists
    if ($RolePolicies -like "*BedrockModelInvokePolicy*") {
        Write-Host "✅ BedrockModelInvokePolicy found" -ForegroundColor Green
        
        # Get the policy document
        $PolicyDoc = aws iam get-role-policy --role-name $RoleName --policy-name BedrockModelInvokePolicy --query "PolicyDocument" --output json
        Write-Host "Policy Document:" -ForegroundColor Blue
        Write-Host $PolicyDoc -ForegroundColor Gray
    } else {
        Write-Host "❌ BedrockModelInvokePolicy not found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to check role policies" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# 4. Check Lambda function permissions
Write-Host "4. Checking Lambda function permissions..." -ForegroundColor Yellow
$LambdaFunctionName = "aws-ai-concierge-tools-$Environment"

try {
    $LambdaPolicy = aws lambda get-policy --function-name $LambdaFunctionName --query "Policy" --output text 2>$null
    if ($LambdaPolicy) {
        Write-Host "✅ Lambda function has resource-based policy" -ForegroundColor Green
        
        # Check if Bedrock can invoke it
        if ($LambdaPolicy -like "*bedrock.amazonaws.com*") {
            Write-Host "✅ Bedrock has permission to invoke Lambda" -ForegroundColor Green
        } else {
            Write-Host "❌ Bedrock does not have permission to invoke Lambda" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Lambda function has no resource-based policy" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to check Lambda permissions" -ForegroundColor Red
}

Write-Host ""

# 5. Apply comprehensive fix
Write-Host "5. Applying comprehensive permission fix..." -ForegroundColor Yellow

# Create the most permissive Bedrock policy for troubleshooting
$BedrockPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:GetFoundationModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
"@

# Create Lambda invoke policy
$LambdaArn = aws lambda get-function --function-name $LambdaFunctionName --query "Configuration.FunctionArn" --output text
$LambdaPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "$LambdaArn"
      ]
    }
  ]
}
"@

try {
    # Write policies to temporary files
    $BedrockPolicy | Out-File -FilePath "bedrock-temp-policy.json" -Encoding UTF8
    $LambdaPolicy | Out-File -FilePath "lambda-temp-policy.json" -Encoding UTF8
    
    # Apply policies
    Write-Host "Applying Bedrock model policy..." -ForegroundColor Blue
    aws iam put-role-policy --role-name $RoleName --policy-name "BedrockModelInvokePolicy" --policy-document file://bedrock-temp-policy.json
    
    Write-Host "Applying Lambda invoke policy..." -ForegroundColor Blue
    aws iam put-role-policy --role-name $RoleName --policy-name "LambdaInvokePolicy" --policy-document file://lambda-temp-policy.json
    
    # Add Lambda permission for Bedrock
    Write-Host "Adding Lambda permission for Bedrock..." -ForegroundColor Blue
    aws lambda add-permission --function-name $LambdaFunctionName --statement-id "bedrock-agent-invoke-$Environment" --action "lambda:InvokeFunction" --principal "bedrock.amazonaws.com" --source-arn "arn:aws:bedrock:${Region}:${Account}:agent/$AgentId" 2>$null
    
    # Clean up temporary files
    Remove-Item "bedrock-temp-policy.json" -Force -ErrorAction SilentlyContinue
    Remove-Item "lambda-temp-policy.json" -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ Policies applied successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to apply policies" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 6. Re-prepare the agent
Write-Host ""
Write-Host "6. Re-preparing agent..." -ForegroundColor Yellow
try {
    aws bedrock-agent prepare-agent --agent-id $AgentId | Out-Null
    Write-Host "✅ Agent preparation initiated" -ForegroundColor Green
    
    # Wait for preparation
    $timeout = 60
    $elapsed = 0
    
    do {
        Start-Sleep 5
        $elapsed += 5
        
        $AgentStatus = aws bedrock-agent get-agent --agent-id $AgentId --query "agent.agentStatus" --output text
        Write-Host "Status: $AgentStatus (${elapsed}s)" -ForegroundColor Blue
        
        if ($AgentStatus -eq "PREPARED") {
            Write-Host "✅ Agent is ready!" -ForegroundColor Green
            break
        }
        
    } while ($elapsed -lt $timeout)
    
} catch {
    Write-Host "❌ Failed to prepare agent" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Diagnostic and fix completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. If Claude 3 models are not available, enable them in Bedrock console:" -ForegroundColor Yellow
Write-Host "   - Go to AWS Console → Bedrock → Model access" -ForegroundColor Yellow
Write-Host "   - Request access to Claude 3 Haiku model" -ForegroundColor Yellow
Write-Host "2. Wait 2-3 minutes for permissions to propagate" -ForegroundColor Yellow
Write-Host "3. Test the agent in AWS Console → Bedrock → Agents" -ForegroundColor Yellow
Write-Host "4. If still failing, check CloudWatch logs for detailed errors" -ForegroundColor Yellow