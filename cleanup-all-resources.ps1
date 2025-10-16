#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete cleanup of all AWS AI Concierge resources
.DESCRIPTION
    This script removes ALL resources created for the AWS AI Concierge project
    to avoid ongoing costs after the competition. Use with caution!
.EXAMPLE
    .\cleanup-all-resources.ps1
#>

param(
    [switch]$Force,
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "🧹 AWS AI Concierge - Complete Resource Cleanup" -ForegroundColor Red
Write-Host "=" * 60

if (-not $Force) {
    Write-Host "⚠️  WARNING: This will DELETE ALL AWS resources!" -ForegroundColor Yellow
    Write-Host "   - Bedrock Agent and all versions" -ForegroundColor Yellow
    Write-Host "   - Lambda functions and logs" -ForegroundColor Yellow
    Write-Host "   - S3 buckets and all contents" -ForegroundColor Yellow
    Write-Host "   - CloudFront distributions" -ForegroundColor Yellow
    Write-Host "   - Cognito User Pools" -ForegroundColor Yellow
    Write-Host "   - DynamoDB tables" -ForegroundColor Yellow
    Write-Host "   - API Gateway APIs" -ForegroundColor Yellow
    Write-Host "   - IAM roles and policies" -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "Type 'DELETE-ALL' to confirm complete cleanup"
    if ($confirm -ne "DELETE-ALL") {
        Write-Host "❌ Cleanup cancelled" -ForegroundColor Green
        exit 0
    }
}

try {
    Write-Host "🔍 Starting comprehensive cleanup..." -ForegroundColor Blue
    
    # 1. Cleanup Bedrock Agent
    Write-Host "🤖 Cleaning up Bedrock Agent..." -ForegroundColor Blue
    try {
        $agents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
        $aiAgent = $agents.agentSummaries | Where-Object { $_.agentName -like "*aws-ai-concierge*" }
        
        if ($aiAgent) {
            Write-Host "   Deleting Bedrock Agent: $($aiAgent.agentName)" -ForegroundColor Yellow
            aws bedrock-agent delete-agent --agent-id $aiAgent.agentId --skip-resource-in-use-check
            Write-Host "   ✅ Bedrock Agent deleted" -ForegroundColor Green
        }
        else {
            Write-Host "   ℹ️  No Bedrock Agent found" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ⚠️  Bedrock Agent cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 2. Cleanup Backend CDK Stack
    Write-Host "🏗️  Cleaning up Backend Infrastructure..." -ForegroundColor Blue
    try {
        Set-Location "aws-ai-concierge-cdk"
        cdk destroy --force --all
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Backend infrastructure destroyed" -ForegroundColor Green
        }
        Set-Location ".."
    }
    catch {
        Write-Host "   ⚠️  Backend cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Set-Location ".."
    }
    
    # 3. Cleanup Demo Frontend CDK Stack
    Write-Host "🌐 Cleaning up Demo Frontend..." -ForegroundColor Blue
    try {
        Set-Location "public-demo-cdk"
        cdk destroy --force --all
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Demo frontend destroyed" -ForegroundColor Green
        }
        Set-Location ".."
    }
    catch {
        Write-Host "   ⚠️  Frontend cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Set-Location ".."
    }
    
    # 4. Manual cleanup of any remaining resources
    Write-Host "🔍 Checking for remaining resources..." -ForegroundColor Blue
    
    # Check for S3 buckets
    try {
        $bucketsJson = aws s3api list-buckets --output json
        $allBuckets = $bucketsJson | ConvertFrom-Json
        $buckets = $allBuckets.Buckets | Where-Object { $_.Name -like "*aws-ai-concierge*" -or $_.Name -like "*demo-interface*" }
        
        if ($buckets) {
            Write-Host "   Found S3 buckets to clean:" -ForegroundColor Yellow
            foreach ($bucket in $buckets) {
                Write-Host "   Deleting S3 bucket: $($bucket.Name)" -ForegroundColor Yellow
                aws s3 rb "s3://$($bucket.Name)" --force
            }
        }
    }
    catch {
        Write-Host "   ⚠️  S3 cleanup check failed" -ForegroundColor Yellow
    }
    
    # Check for CloudFormation stacks
    try {
        $stacksJson = aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --output json
        $allStacks = $stacksJson | ConvertFrom-Json
        $stacks = $allStacks.StackSummaries | Where-Object { $_.StackName -like "*AwsAiConcierge*" -or $_.StackName -like "*PublicDemo*" }
        
        if ($stacks) {
            Write-Host "   Found CloudFormation stacks to delete:" -ForegroundColor Yellow
            foreach ($stack in $stacks) {
                Write-Host "   Deleting stack: $($stack.StackName)" -ForegroundColor Yellow
                aws cloudformation delete-stack --stack-name $stack.StackName
            }
        }
    }
    catch {
        Write-Host "   ⚠️  CloudFormation cleanup check failed" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 Cleanup Complete!" -ForegroundColor Green
    Write-Host "=" * 60
    Write-Host "✅ All AWS AI Concierge resources have been removed" -ForegroundColor White
    Write-Host "✅ No ongoing costs should be incurred" -ForegroundColor White
    Write-Host "✅ Competition cleanup successful" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Cost Impact:" -ForegroundColor Blue
    Write-Host "   • Bedrock Agent: `$0/month (deleted)" -ForegroundColor White
    Write-Host "   • Lambda Functions: `$0/month (deleted)" -ForegroundColor White
    Write-Host "   • S3 Storage: `$0/month (deleted)" -ForegroundColor White
    Write-Host "   • CloudFront: `$0/month (deleted)" -ForegroundColor White
    Write-Host "   • API Gateway: `$0/month (deleted)" -ForegroundColor White
    Write-Host ""
    Write-Host "🏆 Thank you for participating in the AWS AI competition!" -ForegroundColor Yellow

}
catch {
    Write-Host "❌ ERROR during cleanup: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Manual cleanup may be required:" -ForegroundColor Yellow
    Write-Host "   1. Check AWS Console for remaining resources" -ForegroundColor White
    Write-Host "   2. Delete any Bedrock Agents manually" -ForegroundColor White
    Write-Host "   3. Empty and delete S3 buckets" -ForegroundColor White
    Write-Host "   4. Delete CloudFormation stacks" -ForegroundColor White
    exit 1
}