# Fix the function schema for the Bedrock Agent
param([string]$Environment = "dev")

Write-Host "Fixing Bedrock Agent function schema..."

# Get the agent ID
$AgentName = "aws-ai-concierge-$Environment"
$ExistingAgents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
$ExistingAgent = $ExistingAgents.agentSummaries | Where-Object { $_.agentName -eq $AgentName }

if (-not $ExistingAgent) {
    Write-Host "Agent not found!"
    exit 1
}

$AgentId = $ExistingAgent.agentId
Write-Host "Found agent: $AgentId"

# Get action groups
$ActionGroups = aws bedrock-agent list-agent-action-groups --agent-id $AgentId --agent-version "DRAFT" --output json | ConvertFrom-Json

if ($ActionGroups.actionGroupSummaries.Count -eq 0) {
    Write-Host "No action groups found!"
    exit 1
}

$ActionGroupId = $ActionGroups.actionGroupSummaries[0].actionGroupId
Write-Host "Found action group: $ActionGroupId"

# Get Lambda ARN
$StackName = "AwsAiConcierge-$Environment"
$StackOutputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$LambdaArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "LambdaFunctionArn" }).OutputValue

# Create proper function schema JSON file
$FunctionSchema = @{
    functions = @(
        @{
            name = "getCostAnalysis"
            description = "Analyze AWS costs and spending patterns"
            parameters = @{
                time_period = @{
                    type = "string"
                    description = "Time period for cost analysis"
                    required = $true
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

# Save to temp file
$TempFile = [System.IO.Path]::GetTempFileName()
$FunctionSchema | Out-File -FilePath $TempFile -Encoding UTF8

Write-Host "Function schema:"
Write-Host $FunctionSchema

# Update the action group with correct schema
Write-Host "Updating action group with correct function schema..."

try {
    $UpdateResult = aws bedrock-agent update-agent-action-group `
        --agent-id $AgentId `
        --agent-version "DRAFT" `
        --action-group-id $ActionGroupId `
        --action-group-name "aws-ai-concierge-tools" `
        --description "Function-based tools for AWS cost analysis" `
        --action-group-executor "lambda=$LambdaArn" `
        --function-schema "file://$TempFile" `
        --action-group-state "ENABLED" `
        --output json

    Write-Host "Action group updated successfully"
    
    # Prepare agent
    Write-Host "Preparing agent..."
    aws bedrock-agent prepare-agent --agent-id $AgentId --output json
    
    Write-Host "SUCCESS! Agent updated with correct function schema"
    
} catch {
    Write-Host "Error updating action group: $($_.Exception.Message)"
} finally {
    # Clean up temp file
    Remove-Item $TempFile -ErrorAction SilentlyContinue
}

Write-Host "Agent ID: $AgentId"
Write-Host "Test with: What are my AWS costs?"