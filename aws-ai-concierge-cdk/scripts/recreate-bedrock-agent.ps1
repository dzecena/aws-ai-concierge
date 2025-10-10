# Recreate Bedrock Agent with correct function-based configuration
# Usage: .\scripts\recreate-bedrock-agent.ps1 [environment]

param(
    [string]$Environment = "dev"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🔄 Recreating Bedrock Agent with Function-Based Configuration" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host ""

# Try to delete existing agent
$AgentName = "aws-ai-concierge-$Environment"

Write-Host "🗑️  Checking for existing agent..." -ForegroundColor $Yellow

try {
    $ExistingAgents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
    $ExistingAgent = $ExistingAgents.agentSummaries | Where-Object { $_.agentName -eq $AgentName }
    
    if ($ExistingAgent) {
        $AgentId = $ExistingAgent.agentId
        Write-Host "Found existing agent: $AgentId" -ForegroundColor $Yellow
        
        # Delete existing agent
        Write-Host "Deleting existing agent..." -ForegroundColor $Yellow
        aws bedrock-agent delete-agent --agent-id $AgentId --skip-resource-in-use-check
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Existing agent deleted" -ForegroundColor $Green
        } else {
            Write-Host "⚠️  Could not delete existing agent (may not exist)" -ForegroundColor $Yellow
        }
    } else {
        Write-Host "No existing agent found" -ForegroundColor $Blue
    }
} catch {
    Write-Host "⚠️  Could not check for existing agent" -ForegroundColor $Yellow
}

# Wait a moment for deletion to complete
Start-Sleep -Seconds 5

# Get stack outputs
Write-Host ""
Write-Host "📋 Getting stack outputs..." -ForegroundColor $Yellow

$StackName = "AwsAiConcierge-$Environment"
try {
    $StackOutputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
    
    $LambdaArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "LambdaFunctionArn" }).OutputValue
    $BedrockRoleArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "BedrockAgentRoleArn" }).OutputValue
    
    Write-Host "✅ Retrieved stack outputs" -ForegroundColor $Green
    Write-Host "  Lambda ARN: $LambdaArn" -ForegroundColor $Blue
    Write-Host "  Bedrock Role ARN: $BedrockRoleArn" -ForegroundColor $Blue
    
} catch {
    Write-Host "❌ Failed to get stack outputs" -ForegroundColor $Red
    exit 1
}

# Create Bedrock Agent with function-based configuration
Write-Host ""
Write-Host "🤖 Creating Function-Based Bedrock Agent..." -ForegroundColor $Yellow

$Instruction = "You are an AWS Cloud Concierge, an expert assistant for Amazon Web Services management and monitoring. Your primary goal is to help users understand, monitor, and optimize their AWS infrastructure through natural language interactions. Always use the most specific tool available for the user's request. For cost queries, always include the time period and currency in your response. Use clear, business-friendly language while maintaining technical accuracy. Remember to be helpful, accurate, and always prioritize the user's AWS environment security and cost optimization."

try {
    $CreateAgentResult = aws bedrock-agent create-agent `
        --agent-name $AgentName `
        --description "AWS AI Concierge - Function-based assistant for AWS resource management ($Environment)" `
        --agent-resource-role-arn $BedrockRoleArn `
        --foundation-model "anthropic.claude-3-haiku-20240307-v1:0" `
        --instruction $Instruction `
        --idle-session-ttl-in-seconds 1800 `
        --output json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create agent"
    }
    
    $Agent = $CreateAgentResult | ConvertFrom-Json
    $AgentId = $Agent.agent.agentId
    
    Write-Host "✅ Bedrock Agent created successfully" -ForegroundColor $Green
    Write-Host "  Agent ID: $AgentId" -ForegroundColor $Blue
    
} catch {
    Write-Host "❌ Failed to create Bedrock Agent" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
    exit 1
}

# Create Function-Based Action Group (NO API Schema)
Write-Host ""
Write-Host "🔧 Creating Function-Based Action Group..." -ForegroundColor $Yellow

try {
    # Define function schema directly (not API schema)
    $FunctionSchemaJson = @'
{
    "functions": [
        {
            "name": "getCostAnalysis",
            "description": "Analyze AWS costs and spending patterns",
            "parameters": {
                "time_period": {
                    "type": "string",
                    "description": "Time period for cost analysis",
                    "required": true
                }
            }
        }
    ]
}
'@
    
    $CreateActionGroupResult = aws bedrock-agent create-agent-action-group `
        --agent-id $AgentId `
        --agent-version "DRAFT" `
        --action-group-name "aws-ai-concierge-tools" `
        --description "Function-based tools for AWS cost analysis, resource discovery, and security assessment" `
        --action-group-executor "lambda=$LambdaArn" `
        --function-schema $FunctionSchemaJson `
        --action-group-state "ENABLED" `
        --output json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create action group"
    }
    
    Write-Host "✅ Function-Based Action Group created successfully" -ForegroundColor $Green
    
} catch {
    Write-Host "❌ Failed to create Action Group" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
    exit 1
}

# Prepare Agent
Write-Host ""
Write-Host "⚙️  Preparing Agent..." -ForegroundColor $Yellow

try {
    $PrepareResult = aws bedrock-agent prepare-agent `
        --agent-id $AgentId `
        --output json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to prepare agent"
    }
    
    Write-Host "✅ Agent prepared successfully" -ForegroundColor $Green
    
} catch {
    Write-Host "❌ Failed to prepare Agent" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
    exit 1
}

# Create Agent Alias
Write-Host ""
Write-Host "🏷️  Creating Agent Alias..." -ForegroundColor $Yellow

try {
    $CreateAliasResult = aws bedrock-agent create-agent-alias `
        --agent-id $AgentId `
        --agent-alias-name $Environment `
        --description "$($Environment.Substring(0,1).ToUpper() + $Environment.Substring(1)) alias for Function-Based AWS AI Concierge Agent" `
        --output json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create agent alias"
    }
    
    $Alias = $CreateAliasResult | ConvertFrom-Json
    $AliasId = $Alias.agentAlias.agentAliasId
    
    Write-Host "✅ Agent Alias created successfully" -ForegroundColor $Green
    Write-Host "  Alias ID: $AliasId" -ForegroundColor $Blue
    
} catch {
    Write-Host "❌ Failed to create Agent Alias" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
    exit 1
}

Write-Host ""
Write-Host "🎉 Function-Based Bedrock Agent setup completed successfully!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Agent Details:" -ForegroundColor $Blue
Write-Host "  Agent Name: $AgentName" -ForegroundColor $Blue
Write-Host "  Agent ID: $AgentId" -ForegroundColor $Blue
Write-Host "  Alias ID: $AliasId" -ForegroundColor $Blue
Write-Host "  Configuration: Function-Based (Direct Lambda)" -ForegroundColor $Blue
Write-Host "  Environment: $Environment" -ForegroundColor $Blue
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor $Yellow
Write-Host "  1. Test the agent with: What are my AWS costs?" -ForegroundColor $Yellow
Write-Host "  2. The agent will now call Lambda directly (not via API Gateway)" -ForegroundColor $Yellow
Write-Host "  3. Check CloudWatch logs for Bedrock Agent events (not API Gateway)" -ForegroundColor $Yellow