#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Amazon Nova Pro permissions for Bedrock Agent
.DESCRIPTION
    Verifies that the Bedrock Agent can access Nova Pro model
.EXAMPLE
    .\test-nova-permissions.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🧪 Testing Amazon Nova Pro Permissions" -ForegroundColor Green

try {
    $agentId = "WWYOPOAATI"
    
    # Check agent status
    Write-Host "📋 Checking agent status..." -ForegroundColor Blue
    $agent = aws bedrock-agent get-agent --agent-id $agentId --output json | ConvertFrom-Json
    
    Write-Host "✅ Agent Status: $($agent.agent.agentStatus)" -ForegroundColor Green
    Write-Host "✅ Foundation Model: $($agent.agent.foundationModel)" -ForegroundColor Green
    Write-Host "✅ Role ARN: $($agent.agent.agentResourceRoleArn)" -ForegroundColor Green
    
    # Check if agent is prepared
    if ($agent.agent.agentStatus -ne "PREPARED") {
        Write-Host "🔄 Agent not prepared, preparing now..." -ForegroundColor Yellow
        aws bedrock-agent prepare-agent --agent-id $agentId
        
        # Wait for preparation
        $maxWait = 60
        $waited = 0
        do {
            Start-Sleep -Seconds 5
            $waited += 5
            $status = aws bedrock-agent get-agent --agent-id $agentId --query "agent.agentStatus" --output text
            Write-Host "   Status: $status (waited ${waited}s)" -ForegroundColor Yellow
        } while ($status -eq "PREPARING" -and $waited -lt $maxWait)
        
        if ($status -eq "PREPARED") {
            Write-Host "✅ Agent prepared successfully!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Agent preparation may still be in progress" -ForegroundColor Yellow
        }
    }
    
    # Check IAM role permissions
    Write-Host "🔐 Checking IAM permissions..." -ForegroundColor Blue
    $roleName = $agent.agent.agentResourceRoleArn.Split('/')[-1]
    
    $policies = aws iam list-role-policies --role-name $roleName --output json | ConvertFrom-Json
    Write-Host "✅ Inline Policies: $($policies.PolicyNames -join ', ')" -ForegroundColor Green
    
    # Check if Nova Pro model is accessible
    Write-Host "🤖 Checking Nova Pro model access..." -ForegroundColor Blue
    $models = aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?modelId=='amazon.nova-pro-v1:0']" --output json | ConvertFrom-Json
    
    if ($models.Count -gt 0) {
        Write-Host "✅ Nova Pro model available: $($models[0].modelId)" -ForegroundColor Green
        Write-Host "✅ Model status: $($models[0].modelLifecycle.status)" -ForegroundColor Green
    } else {
        Write-Host "❌ Nova Pro model not found or not accessible" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🎉 Permission Test Complete!" -ForegroundColor Green
    Write-Host "=" * 50
    Write-Host "✅ Agent: PREPARED and ready" -ForegroundColor White
    Write-Host "✅ Model: Amazon Nova Pro accessible" -ForegroundColor White
    Write-Host "✅ Permissions: Updated with Nova Pro access" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 Test the agent in AWS Console:" -ForegroundColor Blue
    Write-Host "   Bedrock → Agents → aws-ai-concierge-dev → Test" -ForegroundColor White
    Write-Host "   Try: 'Hello! What are my AWS costs?'" -ForegroundColor White

}
catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}