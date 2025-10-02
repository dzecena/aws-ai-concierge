# Create Bedrock Agent manually
# Usage: .\scripts\create-bedrock-agent.ps1 [environment]

param(
    [string]$Environment = "dev"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🤖 Creating Bedrock Agent" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host ""

# Get stack outputs
$StackName = "AwsAiConcierge-$Environment"
try {
    $StackOutputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
    
    $LambdaArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "LambdaFunctionArn" }).OutputValue
    $BedrockRoleArn = ($StackOutputs | Where-Object { $_.OutputKey -eq "BedrockAgentRoleArn" }).OutputValue
    $S3BucketName = ($StackOutputs | Where-Object { $_.OutputKey -eq "OpenApiBucketName" }).OutputValue
    
    Write-Host "✅ Retrieved stack outputs" -ForegroundColor $Green
    Write-Host "  Lambda ARN: $LambdaArn" -ForegroundColor $Blue
    Write-Host "  Bedrock Role ARN: $BedrockRoleArn" -ForegroundColor $Blue
    Write-Host "  S3 Bucket: $S3BucketName" -ForegroundColor $Blue
    
} catch {
    Write-Host "❌ Failed to get stack outputs" -ForegroundColor $Red
    exit 1
}

# Create Bedrock Agent
Write-Host ""
Write-Host "🤖 Creating Bedrock Agent..." -ForegroundColor $Yellow

$AgentName = "aws-ai-concierge-$Environment"
$Instruction = @"
You are an AWS Cloud Concierge, an expert assistant for Amazon Web Services management and monitoring. Your primary goal is to help users understand, monitor, and optimize their AWS infrastructure through natural language interactions.

CORE CAPABILITIES:
- Analyze AWS costs and identify optimization opportunities
- Monitor and discover AWS resources across regions
- Provide security and compliance insights
- Translate technical AWS concepts into business-friendly language

TOOL USAGE GUIDELINES:
- Always use the most specific tool available for the user's request
- When multiple regions are involved, clearly specify which regions you're analyzing
- For cost queries, always include the time period and currency in your response
- When security issues are found, prioritize them by risk level
- If a tool returns no results, clearly state this and suggest alternative approaches

RESPONSE FORMAT:
- Use clear, business-friendly language while maintaining technical accuracy
- Always cite the specific AWS region(s) in your responses
- Provide actionable recommendations when possible
- Include relevant timestamps and metadata for context
- Format large datasets in tables or bullet points for readability

ERROR HANDLING:
- If AWS API calls fail, explain the issue in user-friendly terms
- When permissions are insufficient, specify what permissions are needed
- If services are unavailable, provide status information and alternatives
- For ambiguous requests, ask clarifying questions before proceeding

SECURITY PRINCIPLES:
- Never perform write operations without explicit user confirmation
- Always operate with read-only permissions by default
- Respect regional compliance and data residency requirements
- Log all operations for audit purposes

Remember to be helpful, accurate, and always prioritize the user's AWS environment security and cost optimization.
"@

try {
    $CreateAgentResult = aws bedrock-agent create-agent `
        --agent-name $AgentName `
        --description "AWS AI Concierge - Intelligent assistant for AWS resource management and monitoring ($Environment)" `
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

# Create Action Group
Write-Host ""
Write-Host "🔧 Creating Action Group..." -ForegroundColor $Yellow

try {
    $ApiSchemaParam = "s3=`{s3BucketName=$S3BucketName,s3ObjectKey=aws-ai-concierge-tools-simple.yaml`}"
    $CreateActionGroupResult = aws bedrock-agent create-agent-action-group `
        --agent-id $AgentId `
        --agent-version "DRAFT" `
        --action-group-name "aws-ai-concierge-tools" `
        --description "Tools for AWS cost analysis, resource discovery, and security assessment" `
        --action-group-executor "lambda=$LambdaArn" `
        --api-schema $ApiSchemaParam `
        --action-group-state "ENABLED" `
        --output json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create action group"
    }
    
    Write-Host "✅ Action Group created successfully" -ForegroundColor $Green
    
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
        --description "$($Environment.Substring(0,1).ToUpper() + $Environment.Substring(1)) alias for AWS AI Concierge Agent" `
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
Write-Host "🎉 Bedrock Agent setup completed successfully!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Agent Details:" -ForegroundColor $Blue
Write-Host "  Agent Name: $AgentName" -ForegroundColor $Blue
Write-Host "  Agent ID: $AgentId" -ForegroundColor $Blue
Write-Host "  Alias ID: $AliasId" -ForegroundColor $Blue
Write-Host "  Environment: $Environment" -ForegroundColor $Blue
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor $Yellow
Write-Host "  1. Test the agent with: .\scripts\test-bedrock-agent.ps1" -ForegroundColor $Yellow
Write-Host "  2. Try queries like 'What are my AWS costs this month?'" -ForegroundColor $Yellow
Write-Host "  3. Use the AWS Console to interact with the agent" -ForegroundColor $Yellow