# Simple Bedrock Agent Permissions Fix
param(
    [string]$AgentId = "3REQDYQGXU",
    [string]$Environment = "dev"
)

Write-Host "Fixing Bedrock Agent Permissions for Agent: $AgentId" -ForegroundColor Green

# Get current account and region
$Account = (aws sts get-caller-identity --query Account --output text)
$Region = (aws configure get region)
if (-not $Region) { $Region = "us-east-1" }

Write-Host "Account: $Account, Region: $Region" -ForegroundColor Blue

# Get Lambda function details
$LambdaFunctionName = "aws-ai-concierge-tools-$Environment"
$LambdaArn = aws lambda get-function --function-name $LambdaFunctionName --query "Configuration.FunctionArn" --output text

Write-Host "Lambda ARN: $LambdaArn" -ForegroundColor Blue

# 1. Add Lambda invoke permission for Bedrock Agent
Write-Host "Adding Lambda invoke permission..." -ForegroundColor Yellow
try {
    aws lambda add-permission --function-name $LambdaFunctionName --statement-id "bedrock-agent-invoke-$Environment" --action "lambda:InvokeFunction" --principal "bedrock.amazonaws.com" --source-arn "arn:aws:bedrock:${Region}:${Account}:agent/$AgentId" 2>$null
    Write-Host "Lambda permission added" -ForegroundColor Green
} catch {
    Write-Host "Lambda permission may already exist" -ForegroundColor Yellow
}

# 2. Get the Bedrock Agent role name
Write-Host "Getting Bedrock Agent role..." -ForegroundColor Yellow
$AgentDetails = aws bedrock-agent get-agent --agent-id $AgentId --output json | ConvertFrom-Json
$AgentRoleArn = $AgentDetails.agent.agentResourceRoleArn
$RoleName = $AgentRoleArn.Split('/')[-1]

Write-Host "Agent Role: $RoleName" -ForegroundColor Blue

# 3. Create Bedrock model invoke policy
Write-Host "Adding Bedrock model permissions..." -ForegroundColor Yellow

$BedrockPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            )
            Resource = @(
                "arn:aws:bedrock:${Region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:${Region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            )
        }
    )
} | ConvertTo-Json -Depth 10

$BedrockPolicy | Out-File -FilePath "bedrock-policy.json" -Encoding UTF8

# 4. Create Lambda invoke policy
$LambdaPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @("lambda:InvokeFunction")
            Resource = @($LambdaArn)
        }
    )
} | ConvertTo-Json -Depth 10

$LambdaPolicy | Out-File -FilePath "lambda-policy.json" -Encoding UTF8

# 5. Apply policies to the role
try {
    aws iam put-role-policy --role-name $RoleName --policy-name "BedrockModelInvokePolicy" --policy-document file://bedrock-policy.json
    aws iam put-role-policy --role-name $RoleName --policy-name "LambdaInvokePolicy" --policy-document file://lambda-policy.json
    
    Write-Host "Policies applied successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to apply policies: $($_.Exception.Message)" -ForegroundColor Red
}

# Clean up temporary files
Remove-Item "bedrock-policy.json" -Force -ErrorAction SilentlyContinue
Remove-Item "lambda-policy.json" -Force -ErrorAction SilentlyContinue

# 6. Prepare the agent
Write-Host "Preparing Bedrock Agent..." -ForegroundColor Yellow
try {
    aws bedrock-agent prepare-agent --agent-id $AgentId | Out-Null
    Write-Host "Agent preparation initiated" -ForegroundColor Green
    
    # Wait for preparation
    Write-Host "Waiting for agent preparation..." -ForegroundColor Blue
    $timeout = 60
    $elapsed = 0
    
    do {
        Start-Sleep 5
        $elapsed += 5
        
        $AgentStatus = aws bedrock-agent get-agent --agent-id $AgentId --query "agent.agentStatus" --output text
        Write-Host "Status: $AgentStatus (${elapsed}s)" -ForegroundColor Blue
        
        if ($AgentStatus -eq "PREPARED") {
            Write-Host "Agent is ready!" -ForegroundColor Green
            break
        }
        
    } while ($elapsed -lt $timeout)
    
} catch {
    Write-Host "Failed to prepare agent: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Permission fix completed!" -ForegroundColor Green
Write-Host "You can now test the agent in the AWS Console" -ForegroundColor Yellow