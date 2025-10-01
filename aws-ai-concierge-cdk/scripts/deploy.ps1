# AWS AI Concierge CDK Deployment Script (PowerShell)
# Usage: .\scripts\deploy.ps1 [environment] [region] [account]

param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1",
    [string]$Account = ""
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🚀 AWS AI Concierge CDK Deployment" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host "Region: $Region" -ForegroundColor $Blue
if ($Account) {
    Write-Host "Account: $Account" -ForegroundColor $Blue
}
Write-Host ""

# Validate environment
if ($Environment -notin @("dev", "staging", "prod")) {
    Write-Host "❌ Invalid environment: $Environment" -ForegroundColor $Red
    Write-Host "Valid environments: dev, staging, prod" -ForegroundColor $Yellow
    exit 1
}

# Check if AWS CLI is configured
try {
    $null = aws sts get-caller-identity 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI not configured"
    }
} catch {
    Write-Host "❌ AWS CLI not configured or no valid credentials" -ForegroundColor $Red
    Write-Host "Please run 'aws configure' or set up your AWS credentials" -ForegroundColor $Yellow
    exit 1
}

# Get current AWS account and region
$CurrentAccount = (aws sts get-caller-identity --query Account --output text)
$CurrentRegion = (aws configure get region)
if (-not $CurrentRegion) {
    $CurrentRegion = "us-east-1"
}

Write-Host "✅ AWS CLI configured" -ForegroundColor $Green
Write-Host "Current Account: $CurrentAccount" -ForegroundColor $Blue
Write-Host "Current Region: $CurrentRegion" -ForegroundColor $Blue
Write-Host ""

# Validate account if provided
if ($Account -and ($Account -ne $CurrentAccount)) {
    Write-Host "❌ Account mismatch: specified $Account but current account is $CurrentAccount" -ForegroundColor $Red
    exit 1
}

# Use current account if not specified
if (-not $Account) {
    $Account = $CurrentAccount
}

# Check if CDK is installed
try {
    $null = Get-Command cdk -ErrorAction Stop
    Write-Host "✅ AWS CDK found" -ForegroundColor $Green
} catch {
    Write-Host "❌ AWS CDK not found" -ForegroundColor $Red
    Write-Host "Please install CDK: npm install -g aws-cdk" -ForegroundColor $Yellow
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor $Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor $Red
    exit 1
}

# Build the project
Write-Host "🔨 Building project..." -ForegroundColor $Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build project" -ForegroundColor $Red
    exit 1
}

# Bootstrap CDK if needed
Write-Host "🏗️  Checking CDK bootstrap status..." -ForegroundColor $Yellow
try {
    $null = aws cloudformation describe-stacks --stack-name CDKToolkit --region $Region 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "CDK not bootstrapped"
    }
    Write-Host "✅ CDK already bootstrapped" -ForegroundColor $Green
} catch {
    Write-Host "🏗️  Bootstrapping CDK for account $Account in region $Region..." -ForegroundColor $Yellow
    cdk bootstrap "aws://$Account/$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to bootstrap CDK" -ForegroundColor $Red
        exit 1
    }
}

# Synthesize the stack
Write-Host "🔍 Synthesizing CDK stack..." -ForegroundColor $Yellow
cdk synth --context environment=$Environment --context region=$Region --context account=$Account
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to synthesize stack" -ForegroundColor $Red
    exit 1
}

# Deploy the stack
Write-Host "🚀 Deploying CDK stack..." -ForegroundColor $Yellow
cdk deploy --context environment=$Environment --context region=$Region --context account=$Account --require-approval never --outputs-file "cdk-outputs-$Environment.json"

# Check deployment status
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor $Green
    Write-Host ""
    Write-Host "📋 Deployment Summary:" -ForegroundColor $Blue
    Write-Host "  Environment: $Environment" -ForegroundColor $Blue
    Write-Host "  Region: $Region" -ForegroundColor $Blue
    Write-Host "  Account: $Account" -ForegroundColor $Blue
    Write-Host "  Stack Name: AwsAiConcierge-$Environment" -ForegroundColor $Blue
    Write-Host ""
    
    # Display outputs if file exists
    if (Test-Path "cdk-outputs-$Environment.json") {
        Write-Host "📊 Stack Outputs:" -ForegroundColor $Blue
        $outputs = Get-Content "cdk-outputs-$Environment.json" | ConvertFrom-Json
        foreach ($stack in $outputs.PSObject.Properties) {
            foreach ($output in $stack.Value.PSObject.Properties) {
                Write-Host "  $($output.Name): $($output.Value)" -ForegroundColor $Blue
            }
        }
        Write-Host ""
    }
    
    Write-Host "💡 Next Steps:" -ForegroundColor $Yellow
    Write-Host "  1. Upload OpenAPI specification to S3 bucket" -ForegroundColor $Yellow
    Write-Host "  2. Test Lambda function endpoints" -ForegroundColor $Yellow
    Write-Host "  3. Test Bedrock Agent integration" -ForegroundColor $Yellow
    Write-Host "  4. Set up monitoring and alerting" -ForegroundColor $Yellow
    
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor $Red
    Write-Host "Check the error messages above for details" -ForegroundColor $Yellow
    exit 1
}