#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy the React frontend to S3
.DESCRIPTION
    This script builds the React app and deploys it to the S3 bucket
.EXAMPLE
    .\deploy.ps1
#>

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Building and Deploying React Frontend" -ForegroundColor Green

try {
    # Install dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Blue
    npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed"
    }

    # Build the project
    Write-Host "Building React app..." -ForegroundColor Blue
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }

    # Deploy to S3
    Write-Host "Deploying to S3..." -ForegroundColor Blue
    aws s3 sync dist/ s3://demo-interface-dev-296158189643-us-east-1 --delete
    if ($LASTEXITCODE -ne 0) {
        throw "S3 deployment failed"
    }

    # Invalidate CloudFront cache
    Write-Host "Invalidating CloudFront cache..." -ForegroundColor Blue
    aws cloudfront create-invalidation --distribution-id E3BGW0WO58I2LB --paths "/*"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "CloudFront invalidation failed, but deployment succeeded" -ForegroundColor Yellow
    }

    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend URL: https://d3sfryrdjx8e9t.cloudfront.net" -ForegroundColor Yellow
    Write-Host "Demo Credentials:" -ForegroundColor Yellow
    Write-Host "  Email: demo.judge@example.com" -ForegroundColor White
    Write-Host "  Password: OqN#ldMRn5TfA@Kw" -ForegroundColor White

}
catch {
    Write-Host "ERROR: Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}