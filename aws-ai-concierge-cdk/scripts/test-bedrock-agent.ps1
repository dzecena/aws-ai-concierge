# Test Bedrock Agent Integration
# Usage: .\scripts\test-bedrock-agent.ps1 [environment] [region]

param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🤖 Testing Bedrock Agent Integration" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host "Region: $Region" -ForegroundColor $Blue
Write-Host ""

# Check if AWS CLI is configured
try {
    $null = aws sts get-caller-identity 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI not configured"
    }
} catch {
    Write-Host "❌ AWS CLI not configured or no valid credentials" -ForegroundColor $Red
    exit 1
}

# Get stack outputs to find Bedrock Agent ID
Write-Host "🔍 Getting Bedrock Agent information..." -ForegroundColor $Yellow
$StackName = "AwsAiConcierge-$Environment"

try {
    $StackOutputs = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
    
    $AgentId = ($StackOutputs | Where-Object { $_.OutputKey -eq "BedrockAgentId" }).OutputValue
    $AgentAliasId = ($StackOutputs | Where-Object { $_.OutputKey -eq "BedrockAgentAliasId" }).OutputValue
    
    if (-not $AgentId) {
        throw "Bedrock Agent ID not found in stack outputs"
    }
    
    Write-Host "✅ Found Bedrock Agent" -ForegroundColor $Green
    Write-Host "  Agent ID: $AgentId" -ForegroundColor $Blue
    Write-Host "  Alias ID: $AgentAliasId" -ForegroundColor $Blue
    
} catch {
    Write-Host "❌ Failed to get Bedrock Agent information" -ForegroundColor $Red
    Write-Host "Make sure the CDK stack is deployed: $StackName" -ForegroundColor $Yellow
    exit 1
}

# Test simple query
Write-Host ""
Write-Host "🧪 Testing simple cost analysis query..." -ForegroundColor $Yellow
$TestQuery = "What are my AWS costs for this month?"

try {
    # Create a temporary JSON file for the request
    $RequestFile = "bedrock-test-request.json"
    $ResponseFile = "bedrock-test-response.json"
    
    $RequestBody = @{
        inputText = $TestQuery
        sessionId = "test-session-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    } | ConvertTo-Json
    
    $RequestBody | Out-File -FilePath $RequestFile -Encoding UTF8
    
    # Invoke Bedrock Agent
    aws bedrock-agent-runtime invoke-agent `
        --agent-id $AgentId `
        --agent-alias-id $AgentAliasId `
        --session-id "test-session-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
        --input-text $TestQuery `
        --region $Region `
        $ResponseFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Bedrock Agent responded successfully" -ForegroundColor $Green
        
        # Try to read and display response
        if (Test-Path $ResponseFile) {
            Write-Host ""
            Write-Host "📋 Agent Response:" -ForegroundColor $Blue
            Write-Host "==================" -ForegroundColor $Blue
            
            # The response is in a streaming format, so we'll just show it exists
            $ResponseSize = (Get-Item $ResponseFile).Length
            Write-Host "Response received ($ResponseSize bytes)" -ForegroundColor $Green
            Write-Host "Note: Response is in streaming format. Check $ResponseFile for details." -ForegroundColor $Yellow
        }
        
        Write-Host ""
        Write-Host "🎉 Bedrock Agent test completed successfully!" -ForegroundColor $Green
        
    } else {
        throw "Bedrock Agent invocation failed"
    }
    
} catch {
    Write-Host "❌ Bedrock Agent test failed" -ForegroundColor $Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor $Yellow
    
    # Check common issues
    Write-Host ""
    Write-Host "🔍 Troubleshooting checklist:" -ForegroundColor $Yellow
    Write-Host "  1. Is the OpenAPI specification uploaded to S3?" -ForegroundColor $Yellow
    Write-Host "  2. Is the Lambda function deployed and accessible?" -ForegroundColor $Yellow
    Write-Host "  3. Does the Bedrock Agent have proper IAM permissions?" -ForegroundColor $Yellow
    Write-Host "  4. Is the Bedrock Agent in PREPARED state?" -ForegroundColor $Yellow
    
    exit 1
    
} finally {
    # Clean up temporary files
    if (Test-Path $RequestFile) { Remove-Item $RequestFile -Force }
}

Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor $Yellow
Write-Host "  1. Try more complex queries to test different tools" -ForegroundColor $Yellow
Write-Host "  2. Run the full integration test suite" -ForegroundColor $Yellow
Write-Host "  3. Test from the AWS Console Bedrock Agent interface" -ForegroundColor $Yellow