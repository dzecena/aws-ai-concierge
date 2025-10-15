#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cleanup only the demo frontend resources
.DESCRIPTION
    This script removes only the demo website infrastructure
    while preserving the backend Bedrock Agent
.EXAMPLE
    .\cleanup-demo-only.ps1
#>

param(
    [switch]$Force,
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "🧹 AWS AI Concierge - Demo Frontend Cleanup" -ForegroundColor Blue
Write-Host "=" * 50

if (-not $Force) {
    Write-Host "⚠️  This will delete demo frontend only:" -ForegroundColor Yellow
    Write-Host "   ✅ Keeps: Bedrock Agent for AWS Console testing" -ForegroundColor Green
    Write-Host "   ❌ Deletes: Demo website" -ForegroundColor Red
    Write-Host "   ❌ Deletes: CloudFront distribution" -ForegroundColor Red
    Write-Host "   ❌ Deletes: S3 hosting bucket" -ForegroundColor Red
    Write-Host "   ❌ Deletes: Cognito User Pool" -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "Continue with demo cleanup? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ Cleanup cancelled" -ForegroundColor Green
        exit 0
    }
}

try {
    Write-Host "🌐 Destroying demo frontend CDK stack..." -ForegroundColor Blue
    cdk destroy --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Demo frontend destroyed" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  CDK destroy had issues, check manually" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 Demo Cleanup Complete!" -ForegroundColor Green
    Write-Host "=" * 50
    Write-Host "✅ Demo website removed" -ForegroundColor White
    Write-Host "✅ CloudFront distribution deleted" -ForegroundColor White
    Write-Host "✅ S3 hosting bucket cleaned" -ForegroundColor White
    Write-Host "🤖 Bedrock Agent still available in AWS Console" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💰 Cost Impact:" -ForegroundColor Blue
    Write-Host "   • CloudFront: ~$1-2/month → $0" -ForegroundColor White
    Write-Host "   • S3 hosting: ~$0.50/month → $0" -ForegroundColor White
    Write-Host "   • Cognito: ~$0.10/month → $0" -ForegroundColor White

}
catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}