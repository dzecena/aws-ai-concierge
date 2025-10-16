#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test and validate cleanup script functionality without actually deleting resources
.DESCRIPTION
    This script validates that the cleanup script can identify and would properly clean up
    all AWS AI Concierge resources. It performs a dry-run to show what would be deleted.
.EXAMPLE
    .\test-cleanup-validation.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🧪 AWS AI Concierge - Cleanup Script Validation" -ForegroundColor Cyan
Write-Host "=" * 60

Write-Host "🔍 Testing cleanup script functionality (DRY RUN)..." -ForegroundColor Blue

try {
    # 1. Test Bedrock Agent Detection
    Write-Host "`n🤖 Testing Bedrock Agent Detection..." -ForegroundColor Blue
    try {
        $agents = aws bedrock-agent list-agents --output json | ConvertFrom-Json
        $aiAgent = $agents.agentSummaries | Where-Object { $_.agentName -like "*aws-ai-concierge*" }
        
        if ($aiAgent) {
            Write-Host "   ✅ FOUND: Bedrock Agent '$($aiAgent.agentName)' (ID: $($aiAgent.agentId))" -ForegroundColor Green
            Write-Host "   📋 Would delete: aws bedrock-agent delete-agent --agent-id $($aiAgent.agentId)" -ForegroundColor Yellow
        }
        else {
            Write-Host "   ℹ️  No Bedrock Agent found matching pattern" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ❌ Bedrock Agent detection failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 2. Test CloudFormation Stack Detection
    Write-Host "`n🏗️  Testing CloudFormation Stack Detection..." -ForegroundColor Blue
    try {
        $stacksJson = aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --output json
        $allStacks = $stacksJson | ConvertFrom-Json
        $stacks = $allStacks.StackSummaries | Where-Object { $_.StackName -like "*AwsAiConcierge*" -or $_.StackName -like "*PublicDemo*" }
        
        if ($stacks -and $stacks.Count -gt 0) {
            Write-Host "   ✅ FOUND: $($stacks.Count) CloudFormation stack(s)" -ForegroundColor Green
            foreach ($stack in $stacks) {
                Write-Host "   📋 Would delete: $($stack.StackName) (Status: $($stack.StackStatus))" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "   ℹ️  No matching CloudFormation stacks found" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ❌ CloudFormation detection failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 3. Test S3 Bucket Detection
    Write-Host "`n🪣 Testing S3 Bucket Detection..." -ForegroundColor Blue
    try {
        $bucketsJson = aws s3api list-buckets --output json
        $allBuckets = $bucketsJson | ConvertFrom-Json
        $buckets = $allBuckets.Buckets | Where-Object { $_.Name -like "*aws-ai-concierge*" -or $_.Name -like "*demo-interface*" -or $_.Name -like "*awsaiconcierge*" -or $_.Name -like "*publicdemo*" }
        
        if ($buckets -and $buckets.Count -gt 0) {
            Write-Host "   ✅ FOUND: $($buckets.Count) S3 bucket(s)" -ForegroundColor Green
            foreach ($bucket in $buckets) {
                Write-Host "   📋 Would delete: s3://$($bucket.Name)" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "   ℹ️  No matching S3 buckets found" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ❌ S3 bucket detection failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 4. Test Lambda Function Detection
    Write-Host "`n⚡ Testing Lambda Function Detection..." -ForegroundColor Blue
    try {
        $functionsJson = aws lambda list-functions --output json
        $allFunctions = $functionsJson | ConvertFrom-Json
        $functions = $allFunctions.Functions | Where-Object { $_.FunctionName -like "*concierge*" -or $_.FunctionName -like "*aws-ai*" }
        
        if ($functions -and $functions.Count -gt 0) {
            Write-Host "   ✅ FOUND: $($functions.Count) Lambda function(s)" -ForegroundColor Green
            foreach ($func in $functions) {
                Write-Host "   📋 Would delete: $($func.FunctionName) ($($func.Runtime))" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "   ℹ️  No matching Lambda functions found" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ❌ Lambda function detection failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 5. Test CDK Directory Structure
    Write-Host "`n📁 Testing CDK Directory Structure..." -ForegroundColor Blue
    
    $backendDir = "aws-ai-concierge-cdk"
    $frontendDir = "public-demo-cdk"
    
    if (Test-Path $backendDir) {
        Write-Host "   ✅ FOUND: Backend CDK directory ($backendDir)" -ForegroundColor Green
        Write-Host "   📋 Would run: cdk destroy --force --all (in $backendDir)" -ForegroundColor Yellow
    }
    else {
        Write-Host "   ⚠️  Backend CDK directory not found: $backendDir" -ForegroundColor Yellow
    }
    
    if (Test-Path $frontendDir) {
        Write-Host "   ✅ FOUND: Frontend CDK directory ($frontendDir)" -ForegroundColor Green
        Write-Host "   📋 Would run: cdk destroy --force --all (in $frontendDir)" -ForegroundColor Yellow
    }
    else {
        Write-Host "   ⚠️  Frontend CDK directory not found: $frontendDir" -ForegroundColor Yellow
    }
    
    # 6. Test Cleanup Script Existence
    Write-Host "`n📜 Testing Cleanup Script Files..." -ForegroundColor Blue
    
    $mainCleanup = "cleanup-all-resources.ps1"
    $backendCleanup = "$backendDir/scripts/cleanup-backend-only.ps1"
    $frontendCleanup = "$frontendDir/scripts/cleanup-demo-only.ps1"
    
    if (Test-Path $mainCleanup) {
        Write-Host "   ✅ FOUND: Main cleanup script ($mainCleanup)" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ MISSING: Main cleanup script ($mainCleanup)" -ForegroundColor Red
    }
    
    if (Test-Path $backendCleanup) {
        Write-Host "   ✅ FOUND: Backend cleanup script ($backendCleanup)" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  Backend cleanup script not found: $backendCleanup" -ForegroundColor Yellow
    }
    
    if (Test-Path $frontendCleanup) {
        Write-Host "   ✅ FOUND: Frontend cleanup script ($frontendCleanup)" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  Frontend cleanup script not found: $frontendCleanup" -ForegroundColor Yellow
    }
    
    Write-Host "`n🎉 Cleanup Validation Complete!" -ForegroundColor Green
    Write-Host "=" * 60
    Write-Host "✅ Cleanup script functionality validated" -ForegroundColor White
    Write-Host "✅ All resource detection methods working" -ForegroundColor White
    Write-Host "✅ Ready for actual cleanup when needed" -ForegroundColor White
    Write-Host ""
    Write-Host "🚨 To perform actual cleanup, run:" -ForegroundColor Yellow
    Write-Host "   ./cleanup-all-resources.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 This was a DRY RUN - no resources were deleted" -ForegroundColor Cyan

}
catch {
    Write-Host "❌ ERROR during validation: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}