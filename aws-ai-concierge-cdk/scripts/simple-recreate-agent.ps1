# Simple script to recreate Bedrock Agent with function-based configuration
param([string]$Environment = "dev")

Write-Host "Recreating Bedrock Agent with Function-Based Configuration"
Write-Host "Environment: $Environment"

# Get stack outputs
$StackName = "AwsAiConcierge-$Environment"
$StackOutputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json

$LambdaArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "LambdaFunctionArn" }).OutputValue
$BedrockRoleArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "BedrockAgentRoleArn" }).OutputValue

Write-Host "Lambda ARN: $LambdaArn"
Write-Host "Bedrock Role ARN: $BedrockRoleArn"

# Delete existing agent if it exists
$AgentName = "aws-ai-concierge-$Environment"
try {
    $ExistingAgents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
    $ExistingAgent = $ExistingAgents.agentSummaries | Where-Object { $_.agentName -eq $AgentName }
    
    if ($ExistingAgent) {
        $AgentId = $ExistingAgent.agentId
        Write-Host "Deleting existing agent: $AgentId"
        aws bedrock-agent delete-agent --agent-id $AgentId --skip-resource-in-use-check
        Start-Sleep -Seconds 10
    }
} catch {
    Write-Host "No existing agent to delete"
}

# Create new agent
Write-Host "Creating new function-based agent..."

$Instruction = "You are an AWS Cloud Concierge assistant for AWS resource management and monitoring. Help users understand and optimize their AWS infrastructure. Use clear, business-friendly language and always prioritize security and cost optimization."

$CreateAgentResult = aws bedrock-agent create-agent --agent-name $AgentName --description "AWS AI Concierge - Function-based assistant" --agent-resource-role-arn $BedrockRoleArn --foundation-model "anthropic.claude-3-haiku-20240307-v1:0" --instruction $Instruction --idle-session-ttl-in-seconds 1800 --output json

$Agent = $CreateAgentResult | ConvertFrom-Json
$AgentId = $Agent.agent.agentId

Write-Host "Agent created with ID: $AgentId"

# Create function-based action group
Write-Host "Creating function-based action group..."

$FunctionSchemaJson = '{"functions": [{"name": "getCostAnalysis", "description": "Analyze AWS costs and spending patterns", "parameters": {"time_period": {"type": "string", "description": "Time period for cost analysis", "required": true}}}]}'

$CreateActionGroupResult = aws bedrock-agent create-agent-action-group --agent-id $AgentId --agent-version "DRAFT" --action-group-name "aws-ai-concierge-tools" --description "Function-based tools for AWS analysis" --action-group-executor "lambda=$LambdaArn" --function-schema $FunctionSchemaJson --action-group-state "ENABLED" --output json

Write-Host "Action group created successfully"

# Prepare agent
Write-Host "Preparing agent..."
aws bedrock-agent prepare-agent --agent-id $AgentId --output json

# Create alias
Write-Host "Creating agent alias..."
$CreateAliasResult = aws bedrock-agent create-agent-alias --agent-id $AgentId --agent-alias-name $Environment --description "Alias for function-based AWS AI Concierge Agent" --output json

$Alias = $CreateAliasResult | ConvertFrom-Json
$AliasId = $Alias.agentAlias.agentAliasId

Write-Host "SUCCESS! Function-based Bedrock Agent created:"
Write-Host "Agent ID: $AgentId"
Write-Host "Alias ID: $AliasId"
Write-Host "Configuration: Function-Based (Direct Lambda calls)"
Write-Host ""
Write-Host "Now test with: What are my AWS costs?"