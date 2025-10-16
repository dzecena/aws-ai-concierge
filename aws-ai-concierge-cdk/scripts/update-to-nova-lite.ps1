#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

Write-Host "Updating AWS AI Concierge to use Amazon Nova Lite" -ForegroundColor Green

try {
    # Get current agent
    Write-Host "Finding Bedrock Agent..." -ForegroundColor Blue
    $agents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
    $agent = $agents.agentSummaries | Where-Object { $_.agentName -like "*aws-ai-concierge*" } | Select-Object -First 1
    
    if (-not $agent) {
        throw "No AWS AI Concierge agent found"
    }
    
    $agentId = $agent.agentId
    Write-Host "Found agent: $($agent.agentName) (ID: $agentId)" -ForegroundColor Green
    
    # Get agent details
    Write-Host "Getting agent configuration..." -ForegroundColor Blue
    $agentDetails = aws bedrock-agent get-agent --agent-id $agentId --output json | ConvertFrom-Json
    $roleArn = $agentDetails.agent.agentResourceRoleArn
    
    Write-Host "Current model: $($agentDetails.agent.foundationModel)" -ForegroundColor Yellow
    
    # Update to Nova Lite
    Write-Host "Updating to Amazon Nova Lite..." -ForegroundColor Blue
    
    aws bedrock-agent update-agent `
        --agent-id $agentId `
        --agent-name $agent.agentName `
        --foundation-model "amazon.nova-lite-v1:0" `
        --description "AWS AI Concierge powered by Amazon Nova Lite - Fast and efficient AWS infrastructure assistant" `
        --instruction "You are an AWS AI Concierge powered by Amazon Nova Lite. Help users with AWS cost analysis, resource discovery, and security assessment using your available tools. Provide concise, accurate responses." `
        --agent-resource-role-arn $roleArn `
        --idle-session-ttl-in-seconds 1800
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update agent"
    }
    
    Write-Host "Agent updated to use Amazon Nova Lite!" -ForegroundColor Green
    
    # Prepare agent
    Write-Host "Preparing agent..." -ForegroundColor Blue
    aws bedrock-agent prepare-agent --agent-id $agentId
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to prepare agent"
    }
    
    Write-Host "Agent prepared successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "SUCCESS! AWS AI Concierge now uses Amazon Nova Lite" -ForegroundColor Green
    Write-Host "Model: Amazon Nova Lite (amazon.nova-lite-v1:0)" -ForegroundColor White
    Write-Host "Agent ID: $agentId" -ForegroundColor White
    
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}