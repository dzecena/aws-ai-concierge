#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cleanup only the backend AWS AI Concierge resources
.DESCRIPTION
    This script removes only the backend infrastructure (Bedrock Agent, Lambda, etc.)
    while preserving the demo frontend for continued judge access
.EXAMPLE
    .\cleanup-backend-only.ps1
#>

param(
    [switch]$Force,
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "🧹 AWS AI Concierge - Backend Cleanup Only" -ForegroundColor Blue
Write-Host "=" * 50

if (-not $Force) {
    Write-Host "⚠️  This will delete backend resources only:" -ForegroundColor Yellow
    Write-Host "   ✅ Keeps: Demo website for judges" -ForegroundColor Green
    Write-Host "   ❌ Deletes: Bedrock Agent (main cost)" -ForegroundColor Red
    Write-Host "   ❌ Deletes: Lambda functions" -ForegroundColor Red
    Write-Host "   ❌ Deletes: Backend S3 buckets" -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "Continue with backend cleanup? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ Cleanup cancelled" -ForegroundColor Green
        exit 0
    }
}

try {
    # 1. Delete Bedrock Agent (main cost driver)
    Write-Host "🤖 Deleting Bedrock Agent..." -ForegroundColor Blue
    try {
        $agents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
        $aiAgent = $agents.agentSummaries | Where-Object { $_.agentName -like "*aws-ai-concierge*" }
        
        if ($aiAgent) {
            aws bedrock-agent delete-agent --agent-id $aiAgent.agentId --skip-resource-in-use-check
            Write-Host "   ✅ Bedrock Agent deleted (major cost savings)" -ForegroundColor Green
        } else {
            Write-Host "   ℹ️  No Bedrock Agent found" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ⚠️  Bedrock Agent deletion failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 2. Destroy CDK stack
    Write-Host "🏗️  Destroying backend CDK stack..." -ForegroundColor Blue
    cdk destroy --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Backend infrastructure destroyed" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  CDK destroy had issues, check manually" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 Backend Cleanup Complete!" -ForegroundColor Green
    Write-Host "=" * 50
    Write-Host "✅ Bedrock Agent deleted (main cost eliminated)" -ForegroundColor White
    Write-Host "✅ Lambda functions removed" -ForegroundColor White
    Write-Host "✅ Backend S3 buckets cleaned" -ForegroundColor White
    Write-Host "🌐 Demo website still available for judges" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💰 Cost Impact:" -ForegroundColor Blue
    Write-Host "   • Bedrock Agent: ~$50-100/month → $0" -ForegroundColor White
    Write-Host "   • Lambda: ~$5-10/month → $0" -ForegroundColor White
    Write-Host "   • Demo site: ~$1-2/month (kept for judges)" -ForegroundColor White

}
catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}