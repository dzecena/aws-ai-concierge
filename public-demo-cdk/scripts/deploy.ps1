#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy the Public Demo Interface infrastructure
.DESCRIPTION
    This script deploys the AWS CDK infrastructure for the Public Demo Interface
.PARAMETER Environment
    The environment to deploy to (dev, staging, prod)
.PARAMETER Region
    The AWS region to deploy to (default: us-east-1)
.PARAMETER Account
    The AWS account ID (optional, will use default)
.EXAMPLE
    .\scripts\deploy.ps1 -Environment dev
.EXAMPLE
    .\scripts\deploy.ps1 -Environment prod -Region us-west-2 -Account 123456789012
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Account
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Public Demo Interface CDK Deployment" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow

try {
    # Check if AWS CLI is configured
    Write-Host "Checking AWS CLI configuration..." -ForegroundColor Blue
    $awsIdentity = aws sts get-caller-identity --output json | ConvertFrom-Json
    if (-not $awsIdentity) {
        throw "AWS CLI not configured. Please run 'aws configure' first."
    }
    Write-Host "✅ AWS CLI configured for account: $($awsIdentity.Account)" -ForegroundColor Green

    # Set account if not provided
    if (-not $Account) {
        $Account = $awsIdentity.Account
    }

    # Check if CDK is bootstrapped
    Write-Host "✅ Checking CDK bootstrap status..." -ForegroundColor Blue
    try {
        aws cloudformation describe-stacks --stack-name CDKToolkit --region $Region --output table | Out-Null
        Write-Host "✅ CDK already bootstrapped in $Region" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ CDK not bootstrapped. Bootstrapping now..." -ForegroundColor Yellow
        cdk bootstrap aws://$Account/$Region
        if ($LASTEXITCODE -ne 0) {
            throw "CDK bootstrap failed"
        }
        Write-Host "✅ CDK bootstrapped successfully" -ForegroundColor Green
    }

    # Install dependencies
    Write-Host "📦 Installing dependencies..." -ForegroundColor Blue
    npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed"
    }

    # Build the project
    Write-Host "🔨 Building project..." -ForegroundColor Blue
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }

    # Deploy the CDK stack
    Write-Host "🚀 Deploying CDK stack..." -ForegroundColor Blue
    $deployStart = Get-Date
    
    cdk deploy PublicDemo-$Environment --context environment=$Environment --require-approval never
    if ($LASTEXITCODE -ne 0) {
        throw "CDK deployment failed"
    }

    $deployEnd = Get-Date
    $deployDuration = ($deployEnd - $deployStart).TotalSeconds

    Write-Host "✨ Deployment time: $([math]::Round($deployDuration, 2))s" -ForegroundColor Green

    # Get stack outputs
    Write-Host "📋 Stack Outputs:" -ForegroundColor Blue
    aws cloudformation describe-stacks --stack-name PublicDemo-$Environment --region $Region --query "Stacks[0].Outputs" --output table

    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Create judge accounts in Cognito User Pool" -ForegroundColor White
    Write-Host "2. Deploy the React frontend to S3" -ForegroundColor White
    Write-Host "3. Deploy Lambda functions for backend API" -ForegroundColor White
    Write-Host "4. Test the complete system" -ForegroundColor White

}
catch {
    Write-Host "ERROR: Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}