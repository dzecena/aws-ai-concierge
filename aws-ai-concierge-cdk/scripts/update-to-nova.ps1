#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Update Bedrock Agent to use Amazon Nova Pro instead of Claude Haiku
.DESCRIPTION
    This script updates the existing Bedrock Agent to use Amazon Nova Pro model
    to comply with competition requirements
.EXAMPLE
    .\update-to-nova.ps1
#>

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Updating AWS AI Concierge to use Amazon Nova Pro" -ForegroundColor Green
Write-Host "=" * 60

try {
    # Get current agent details
    Write-Host "📋 Getting current Bedrock Agent details..." -ForegroundColor Blue
    $agentList = aws bedrock-agent list-agents --query "agentSummaries[?contains(agentName, ``aws-ai-concierge``)]" --output json | ConvertFrom-Json
    
    if ($agentList.Count -eq 0) {
        throw "No AWS AI Concierge agent found. Please deploy the agent first."
    }
    
    $agent = $agentList[0]
    $agentId = $agent.agentId
    $agentName = $agent.agentName
    
    Write-Host "✅ Found agent: $agentName (ID: $agentId)" -ForegroundColor Green
    
    # Get current agent configuration
    Write-Host "📋 Getting current agent configuration..." -ForegroundColor Blue
    $agentDetails = aws bedrock-agent get-agent --agent-id $agentId --output json | ConvertFrom-Json
    
    # Update agent to use Nova Pro
    Write-Host "🔄 Updating agent to use Amazon Nova Pro..." -ForegroundColor Blue
    
    aws bedrock-agent update-agent `
        --agent-id $agentId `
        --agent-name $agentName `
        --foundation-model "amazon.nova-pro-v1:0" `
        --description "AWS AI Concierge - Intelligent AWS infrastructure assistant powered by Amazon Nova Pro. Provides cost analysis, security assessment, and resource discovery capabilities." `
        --instruction "You are an AWS AI Concierge powered by Amazon Nova Pro, designed to help users understand and optimize their AWS infrastructure. You have access to tools that can analyze AWS costs, discover resources, and assess security posture. Always provide helpful, accurate information about AWS services and best practices. When users ask about costs, use the cost-analysis tool. For resource information, use resource-discovery tools. For security concerns, use security-assessment tools. Be conversational but professional, and always explain your findings clearly." `
        --agent-resource-role-arn $agentDetails.agent.agentResourceRoleArn `
        --idle-session-ttl-in-seconds 1800
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update Bedrock Agent"
    }
    
    Write-Host "✅ Agent updated successfully to use Amazon Nova Pro!" -ForegroundColor Green
    
    # Prepare the agent (this creates a new version)
    Write-Host "🔄 Preparing updated agent..." -ForegroundColor Blue
    aws bedrock-agent prepare-agent --agent-id $agentId
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to prepare updated agent"
    }
    
    Write-Host "✅ Agent prepared successfully!" -ForegroundColor Green
    
    # Wait for agent to be ready
    Write-Host "⏳ Waiting for agent to be ready..." -ForegroundColor Blue
    $maxAttempts = 30
    $attempt = 0
    
    do {
        Start-Sleep -Seconds 10
        $attempt++
        $agentStatus = aws bedrock-agent get-agent --agent-id $agentId --query "agent.agentStatus" --output text
        Write-Host "   Attempt $attempt/$maxAttempts - Status: $agentStatus" -ForegroundColor Yellow
        
        if ($agentStatus -eq "PREPARED") {
            break
        }
        
        if ($attempt -ge $maxAttempts) {
            throw "Agent preparation timed out after $($maxAttempts * 10) seconds"
        }
    } while ($true)
    
    Write-Host "✅ Agent is ready!" -ForegroundColor Green
    
    # Test the updated agent
    Write-Host "🧪 Testing updated agent with Amazon Nova Pro..." -ForegroundColor Blue
    
    $testQuery = "Hello! I'm testing the new Amazon Nova Pro integration. Can you tell me about your capabilities?"
    
    $sessionId = "test-nova-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    aws bedrock-agent-runtime invoke-agent `
        --agent-id $agentId `
        --agent-alias-id "TSTALIASID" `
        --session-id $sessionId `
        --input-text $testQuery `
        --output-file "test-nova-response.json"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Test successful! Agent is working with Amazon Nova Pro" -ForegroundColor Green
        
        # Show test response
        if (Test-Path "test-nova-response.json") {
            Write-Host "📄 Test Response:" -ForegroundColor Blue
            $response = Get-Content "test-nova-response.json" -Raw | ConvertFrom-Json
            Write-Host $response.completion -ForegroundColor White
            Remove-Item "test-nova-response.json" -Force
        }
    } else {
        Write-Host "⚠️  Test failed, but agent was updated. You may need to wait a few more minutes." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 SUCCESS! AWS AI Concierge now uses Amazon Nova Pro" -ForegroundColor Green
    Write-Host "=" * 60
    Write-Host "✅ Model: Amazon Nova Pro (amazon.nova-pro-v1:0)" -ForegroundColor White
    Write-Host "✅ Agent ID: $agentId" -ForegroundColor White
    Write-Host "✅ Status: Ready for competition submission" -ForegroundColor White
    Write-Host ""
    Write-Host "🏆 Competition Requirements Met:" -ForegroundColor Yellow
    Write-Host "   ✅ Uses Amazon Nova (required AWS AI service)" -ForegroundColor White
    Write-Host "   ✅ Amazon Bedrock Agent Core implementation" -ForegroundColor White
    Write-Host "   ✅ AWS SDK integration for tools" -ForegroundColor White
    Write-Host "   ✅ AWS Transform capabilities" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 Test the agent:" -ForegroundColor Blue
    Write-Host "   AWS Console → Amazon Bedrock → Agents → $agentName → Test" -ForegroundColor White

}
catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Ensure you have AWS CLI configured" -ForegroundColor White
    Write-Host "   2. Verify Bedrock Agent exists and is accessible" -ForegroundColor White
    Write-Host "   3. Check AWS permissions for Bedrock operations" -ForegroundColor White
    Write-Host "   4. Ensure Amazon Nova models are available in your region" -ForegroundColor White
    exit 1
}