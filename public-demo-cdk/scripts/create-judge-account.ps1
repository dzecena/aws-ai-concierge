#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create a judge account in the Cognito User Pool
.DESCRIPTION
    This script creates a new judge account with a temporary password
.PARAMETER Environment
    The environment (dev, staging, prod)
.PARAMETER Email
    The judge's email address (will be used as username)
.PARAMETER Name
    The judge's full name
.PARAMETER SendEmail
    Whether to send a welcome email (default: false for demo)
.EXAMPLE
    .\scripts\create-judge-account.ps1 -Environment dev -Email judge1@example.com -Name "Judge Smith"
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Name,
    
    [Parameter(Mandatory=$false)]
    [bool]$SendEmail = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "👨‍⚖️ Creating Judge Account" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Email: $Email" -ForegroundColor Yellow
Write-Host "Name: $Name" -ForegroundColor Yellow

try {
    # Get the User Pool ID from CloudFormation outputs
    Write-Host "🔍 Getting User Pool ID..." -ForegroundColor Blue
    $stackOutputs = aws cloudformation describe-stacks --stack-name PublicDemo-$Environment --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
    $userPoolId = ($stackOutputs | Where-Object { $_.OutputKey -eq "UserPoolId" }).OutputValue
    
    if (-not $userPoolId) {
        throw "Could not find User Pool ID. Make sure the stack is deployed."
    }
    
    Write-Host "✅ User Pool ID: $userPoolId" -ForegroundColor Green

    # Generate a temporary password
    $tempPassword = -join ((65..90) + (97..122) + (48..57) + (33,35,37,42,43,45,61,63,64) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    
    # Create the user
    Write-Host "👤 Creating user account..." -ForegroundColor Blue
    
    $createUserCommand = @"
aws cognito-idp admin-create-user \
    --user-pool-id $userPoolId \
    --username $Email \
    --user-attributes Name=email,Value=$Email Name=name,Value="$Name" Name=custom:role,Value=judge \
    --temporary-password $tempPassword \
    --message-action $(if ($SendEmail) { "RESEND" } else { "SUPPRESS" })
"@

    Invoke-Expression $createUserCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create user account"
    }

    Write-Host "✅ Judge account created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Account Details:" -ForegroundColor Yellow
    Write-Host "Email/Username: $Email" -ForegroundColor White
    Write-Host "Temporary Password: $tempPassword" -ForegroundColor White
    Write-Host "Status: Must change password on first login" -ForegroundColor White
    Write-Host ""
    
    if (-not $SendEmail) {
        Write-Host "⚠️ No email sent. Please provide these credentials to the judge manually." -ForegroundColor Yellow
    }
    
    Write-Host "🔗 Demo URL will be available after frontend deployment" -ForegroundColor Blue

}
catch {
    Write-Host "❌ Failed to create judge account: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}