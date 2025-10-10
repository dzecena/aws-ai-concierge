# Add action group to existing Bedrock Agent
param([string]$Environment = "dev")

Write-Host "Adding action group to Bedrock Agent..."

# Get agent ID
$AgentName = "aws-ai-concierge-$Environment"
$ExistingAgents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
$ExistingAgent = $ExistingAgents.agentSummaries | Where-Object { $_.agentName -eq $AgentName }

if (-not $ExistingAgent) {
    Write-Host "Agent not found!"
    exit 1
}

$AgentId = $ExistingAgent.agentId
Write-Host "Found agent: $AgentId"

# Get Lambda ARN
$StackName = "AwsAiConcierge-$Environment"
$StackOutputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$LambdaArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "LambdaFunctionArn" }).OutputValue

Write-Host "Lambda ARN: $LambdaArn"

# Create function schema file
$FunctionSchema = @'
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

$TempFile = [System.IO.Path]::GetTempFileName()
$FunctionSchema | Out-File -FilePath $TempFile -Encoding UTF8

Write-Host "Creating action group..."

try {
    $CreateResult = aws bedrock-agent create-agent-action-group `
        --agent-id $AgentId `
        --agent-version "DRAFT" `
        --action-group-name "aws-ai-concierge-tools" `
        --description "Function-based tools for AWS cost analysis" `
        --action-group-executor "lambda=$LambdaArn" `
        --function-schema "file://$TempFile" `
        --action-group-state "ENABLED" `
        --output json

    Write-Host "Action group created successfully"
    
    # Prepare agent
    Write-Host "Preparing agent..."
    aws bedrock-agent prepare-agent --agent-id $AgentId --output json
    
    Write-Host "SUCCESS! Action group added with correct function schema"
    
} catch {
    Write-Host "Error creating action group: $($_.Exception.Message)"
} finally {
    Remove-Item $TempFile -ErrorAction SilentlyContinue
}

Write-Host "Agent ID: $AgentId"
Write-Host "Test with: What are my AWS costs?"