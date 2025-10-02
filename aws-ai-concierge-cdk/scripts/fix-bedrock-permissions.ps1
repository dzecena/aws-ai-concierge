# Fix Bedrock Agent Permissions
# Usage: .\scripts\fix-bedrock-permissions.ps1 [environment] [agent-id]

param(
    [string]$Environment = "dev",
    [string]$AgentId = ""
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🔧 Fixing Bedrock Agent Permissions" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host ""

# Get stack outputs if AgentId not provided
if (-not $AgentId) {
    Write-Host "🔍 Getting Agent ID from Bedrock..." -ForegroundColor $Yellow
    try {
        $AgentName = "aws-ai-concierge-$Environment"
        $AgentId = aws bedrock-agent list-agents --query "agentSummaries[?agentName=='$AgentName'].agentId" --output text
        if (-not $AgentId) {
            throw "Agent not found"
        }
        $AgentId = $AgentId.Trim()
        Write-Host "Found Agent ID: $AgentId" -ForegroundColor $Green
    } catch {
        Write-Host "❌ Could not find Bedrock Agent" -ForegroundColor $Red
        exit 1
    }
}

# Get Lambda function ARN
Write-Host "🔍 Getting Lambda function details..." -ForegroundColor $Yellow
try {
    $LambdaFunctionName = "aws-ai-concierge-tools-$Environment"
    $LambdaArn = aws lambda get-function --function-name $LambdaFunctionName --query "Configuration.FunctionArn" --output text
    Write-Host "Lambda ARN: $LambdaArn" -ForegroundColor $Blue
} catch {
    Write-Host "❌ Could not find Lambda function" -ForegroundColor $Red
    exit 1
}

# Get current account and region
$Account = (aws sts get-caller-identity --query Account --output text)
$Region = (aws configure get region)
if (-not $Region) { $Region = "us-east-1" }

Write-Host "Account: $Account" -ForegroundColor $Blue
Write-Host "Region: $Region" -ForegroundColor $Blue
Write-Host ""

# 1. Add Lambda invoke permission for Bedrock Agent
Write-Host "🔐 Adding Lambda invoke permission for Bedrock Agent..." -ForegroundColor $Yellow
try {
    aws lambda add-permission `
        --function-name $LambdaFunctionName `
        --statement-id "bedrock-agent-invoke-$Environment" `
        --action "lambda:InvokeFunction" `
        --principal "bedrock.amazonaws.com" `
        --source-arn "arn:aws:bedrock:${Region}:${Account}:agent/$AgentId" 2>$null
    
    Write-Host "✅ Lambda permission added" -ForegroundColor $Green
} catch {
    Write-Host "⚠️  Lambda permission may already exist" -ForegroundColor $Yellow
}

# 2. Add Bedrock model invoke permissions to the role
Write-Host "🤖 Adding Bedrock model permissions to agent role..." -ForegroundColor $Yellow

$BedrockRoleName = "aws-ai-concierge-bedrock-role-$Environment"

# Create Bedrock model invoke policy
$BedrockPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:${Region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        "arn:aws:bedrock:${Region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    }
  ]
}
"@

# Create Lambda invoke policy
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
    
    # Add policies to the role
    aws iam put-role-policy --role-name $BedrockRoleName --policy-name "BedrockModelInvokePolicy" --policy-document file://bedrock-temp-policy.json
    aws iam put-role-policy --role-name $BedrockRoleName --policy-name "LambdaInvokePolicy" --policy-document file://lambda-temp-policy.json
    
    # Clean up temporary files
    Remove-Item "bedrock-temp-policy.json" -Force -ErrorAction SilentlyContinue
    Remove-Item "lambda-temp-policy.json" -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ Bedrock role permissions updated" -ForegroundColor $Green
} catch {
    Write-Host "❌ Failed to update Bedrock role permissions" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
}

# 3. Prepare the agent to pick up new permissions
Write-Host "⚙️  Preparing Bedrock Agent with new permissions..." -ForegroundColor $Yellow
try {
    aws bedrock-agent prepare-agent --agent-id $AgentId | Out-Null
    Write-Host "✅ Agent preparation initiated" -ForegroundColor $Green
    
    # Wait for preparation to complete
    Write-Host "⏳ Waiting for agent preparation..." -ForegroundColor $Blue
    $timeout = 60
    $elapsed = 0
    $interval = 5
    
    do {
        Start-Sleep $interval
        $elapsed += $interval
        
        $AgentStatus = aws bedrock-agent get-agent --agent-id $AgentId --query "agent.agentStatus" --output text
        Write-Host "Agent status: $AgentStatus (${elapsed}s elapsed)" -ForegroundColor $Blue
        
        if ($AgentStatus -eq "PREPARED") {
            Write-Host "✅ Agent is ready!" -ForegroundColor $Green
            break
        }
        
    } while ($elapsed -lt $timeout -and $AgentStatus -eq "PREPARING")
    
    if ($elapsed -ge $timeout) {
        Write-Host "⚠️  Agent preparation is taking longer than expected" -ForegroundColor $Yellow
    }
    
} catch {
    Write-Host "❌ Failed to prepare agent" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
}

Write-Host ""
Write-Host "🎉 Permission fix completed!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor $Blue
Write-Host "  Agent ID: $AgentId" -ForegroundColor $Blue
Write-Host "  Lambda Function: $LambdaFunctionName" -ForegroundColor $Blue
Write-Host "  Bedrock Role: $BedrockRoleName" -ForegroundColor $Blue
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor $Yellow
Write-Host "  1. Test the agent in AWS Console → Bedrock → Agents" -ForegroundColor $Yellow
Write-Host "  2. Try a query like 'What are my AWS costs this month?'" -ForegroundColor $Yellow
Write-Host "  3. If still having issues, wait 2-3 minutes for permissions to propagate" -ForegroundColor $Yellow