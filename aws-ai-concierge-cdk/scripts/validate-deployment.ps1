# AWS AI Concierge Deployment Validation Script
# Usage: .\scripts\validate-deployment.ps1 [environment]

param(
    [string]$Environment = "dev"
)

$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🔍 AWS AI Concierge Deployment Validation" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host ""

$StackName = "AwsAiConcierge-$Environment"
$ValidationResults = @()

# Function to add validation result
function Add-ValidationResult {
    param($Test, $Status, $Message)
    $ValidationResults += [PSCustomObject]@{
        Test = $Test
        Status = $Status
        Message = $Message
    }
}

# Test 1: Check if CDK stack exists
Write-Host "1️⃣ Checking CDK stack existence..." -ForegroundColor $Yellow
try {
    $stack = aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0]' --output json | ConvertFrom-Json
    if ($stack.StackStatus -eq "CREATE_COMPLETE" -or $stack.StackStatus -eq "UPDATE_COMPLETE") {
        Write-Host "✅ Stack exists and is in good state" -ForegroundColor $Green
        Add-ValidationResult "Stack Existence" "PASS" "Stack $StackName exists and is healthy"
    } else {
        Write-Host "⚠️  Stack exists but status is: $($stack.StackStatus)" -ForegroundColor $Yellow
        Add-ValidationResult "Stack Existence" "WARNING" "Stack status: $($stack.StackStatus)"
    }
} catch {
    Write-Host "❌ Stack not found or error occurred" -ForegroundColor $Red
    Add-ValidationResult "Stack Existence" "FAIL" "Stack $StackName not found"
    Write-Host "Deployment validation cannot continue without the stack" -ForegroundColor $Red
    exit 1
}

# Test 2: Check Lambda function
Write-Host "2️⃣ Checking Lambda function..." -ForegroundColor $Yellow
try {
    $functionName = "aws-ai-concierge-tools-$Environment"
    $lambdaFunction = aws lambda get-function --function-name $functionName --query 'Configuration' --output json | ConvertFrom-Json
    if ($lambdaFunction.State -eq "Active") {
        Write-Host "✅ Lambda function is active" -ForegroundColor $Green
        Add-ValidationResult "Lambda Function" "PASS" "Function $functionName is active"
    } else {
        Write-Host "⚠️  Lambda function state: $($lambdaFunction.State)" -ForegroundColor $Yellow
        Add-ValidationResult "Lambda Function" "WARNING" "Function state: $($lambdaFunction.State)"
    }
} catch {
    Write-Host "❌ Lambda function not found or error occurred" -ForegroundColor $Red
    Add-ValidationResult "Lambda Function" "FAIL" "Lambda function not accessible"
}

# Test 3: Check S3 bucket
Write-Host "3️⃣ Checking S3 bucket..." -ForegroundColor $Yellow
try {
    $account = aws sts get-caller-identity --query Account --output text
    $region = aws configure get region
    if (-not $region) { $region = "us-east-1" }
    
    $bucketName = "aws-ai-concierge-openapi-$Environment-$account-$region"
    $bucket = aws s3api head-bucket --bucket $bucketName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ S3 bucket exists and is accessible" -ForegroundColor $Green
        Add-ValidationResult "S3 Bucket" "PASS" "Bucket $bucketName is accessible"
    } else {
        Write-Host "❌ S3 bucket not accessible" -ForegroundColor $Red
        Add-ValidationResult "S3 Bucket" "FAIL" "Bucket $bucketName not accessible"
    }
} catch {
    Write-Host "❌ Error checking S3 bucket" -ForegroundColor $Red
    Add-ValidationResult "S3 Bucket" "FAIL" "Error checking S3 bucket"
}

# Test 4: Check API Gateway
Write-Host "4️⃣ Checking API Gateway..." -ForegroundColor $Yellow
try {
    $apis = aws apigateway get-rest-apis --query "items[?contains(name, 'AWS AI Concierge API')]" --output json | ConvertFrom-Json
    if ($apis.Count -gt 0) {
        $api = $apis[0]
        Write-Host "✅ API Gateway found: $($api.name)" -ForegroundColor $Green
        Add-ValidationResult "API Gateway" "PASS" "API Gateway $($api.name) exists"
        
        # Test API endpoint
        $apiUrl = "https://$($api.id).execute-api.$region.amazonaws.com/$Environment"
        Write-Host "   API URL: $apiUrl" -ForegroundColor $Blue
    } else {
        Write-Host "❌ API Gateway not found" -ForegroundColor $Red
        Add-ValidationResult "API Gateway" "FAIL" "API Gateway not found"
    }
} catch {
    Write-Host "❌ Error checking API Gateway" -ForegroundColor $Red
    Add-ValidationResult "API Gateway" "FAIL" "Error checking API Gateway"
}

# Test 5: Check Bedrock Agent
Write-Host "5️⃣ Checking Bedrock Agent..." -ForegroundColor $Yellow
try {
    $agents = aws bedrock-agent list-agents --query "agentSummaries[?contains(agentName, 'aws-ai-concierge')]" --output json | ConvertFrom-Json
    if ($agents.Count -gt 0) {
        $agent = $agents[0]
        Write-Host "✅ Bedrock Agent found: $($agent.agentName)" -ForegroundColor $Green
        Add-ValidationResult "Bedrock Agent" "PASS" "Bedrock Agent $($agent.agentName) exists"
        Write-Host "   Agent ID: $($agent.agentId)" -ForegroundColor $Blue
        Write-Host "   Agent Status: $($agent.agentStatus)" -ForegroundColor $Blue
    } else {
        Write-Host "❌ Bedrock Agent not found" -ForegroundColor $Red
        Add-ValidationResult "Bedrock Agent" "FAIL" "Bedrock Agent not found"
    }
} catch {
    Write-Host "⚠️  Error checking Bedrock Agent (may not be available in this region)" -ForegroundColor $Yellow
    Add-ValidationResult "Bedrock Agent" "WARNING" "Bedrock Agent check failed - may not be available in region"
}

# Test 6: Check CloudWatch Log Groups
Write-Host "6️⃣ Checking CloudWatch Log Groups..." -ForegroundColor $Yellow
try {
    $logGroupName = "/aws/lambda/aws-ai-concierge-tools-$Environment"
    $logGroup = aws logs describe-log-groups --log-group-name-prefix $logGroupName --query 'logGroups[0]' --output json | ConvertFrom-Json
    if ($logGroup) {
        Write-Host "✅ CloudWatch Log Group exists" -ForegroundColor $Green
        Add-ValidationResult "CloudWatch Logs" "PASS" "Log group $logGroupName exists"
    } else {
        Write-Host "❌ CloudWatch Log Group not found" -ForegroundColor $Red
        Add-ValidationResult "CloudWatch Logs" "FAIL" "Log group not found"
    }
} catch {
    Write-Host "❌ Error checking CloudWatch Log Groups" -ForegroundColor $Red
    Add-ValidationResult "CloudWatch Logs" "FAIL" "Error checking log groups"
}

# Test 7: Test Lambda function invocation
Write-Host "7️⃣ Testing Lambda function invocation..." -ForegroundColor $Yellow
try {
    $functionName = "aws-ai-concierge-tools-$Environment"
    $testPayload = @{
        httpMethod = "POST"
        path = "/cost-analysis"
        body = '{"time_period": "MONTHLY"}'
    } | ConvertTo-Json -Compress
    
    $response = aws lambda invoke --function-name $functionName --payload $testPayload --cli-binary-format raw-in-base64-out response.json 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path "response.json")) {
        $responseContent = Get-Content "response.json" | ConvertFrom-Json
        if ($responseContent.statusCode) {
            Write-Host "✅ Lambda function responds to invocation" -ForegroundColor $Green
            Add-ValidationResult "Lambda Invocation" "PASS" "Lambda function responds correctly"
        } else {
            Write-Host "⚠️  Lambda function responded but format unexpected" -ForegroundColor $Yellow
            Add-ValidationResult "Lambda Invocation" "WARNING" "Lambda response format unexpected"
        }
        Remove-Item "response.json" -ErrorAction SilentlyContinue
    } else {
        Write-Host "❌ Lambda function invocation failed" -ForegroundColor $Red
        Add-ValidationResult "Lambda Invocation" "FAIL" "Lambda invocation failed"
    }
} catch {
    Write-Host "❌ Error testing Lambda function" -ForegroundColor $Red
    Add-ValidationResult "Lambda Invocation" "FAIL" "Error testing Lambda function"
}

# Summary
Write-Host ""
Write-Host "📊 Validation Summary:" -ForegroundColor $Blue
Write-Host "=====================" -ForegroundColor $Blue

$passCount = ($ValidationResults | Where-Object { $_.Status -eq "PASS" }).Count
$warningCount = ($ValidationResults | Where-Object { $_.Status -eq "WARNING" }).Count
$failCount = ($ValidationResults | Where-Object { $_.Status -eq "FAIL" }).Count

foreach ($result in $ValidationResults) {
    $color = switch ($result.Status) {
        "PASS" { $Green }
        "WARNING" { $Yellow }
        "FAIL" { $Red }
    }
    Write-Host "$($result.Status.PadRight(8)) $($result.Test): $($result.Message)" -ForegroundColor $color
}

Write-Host ""
Write-Host "Results: $passCount passed, $warningCount warnings, $failCount failed" -ForegroundColor $Blue

if ($failCount -eq 0) {
    Write-Host ""
    Write-Host "🎉 Deployment validation completed successfully!" -ForegroundColor $Green
    Write-Host "Your AWS AI Concierge is ready to use." -ForegroundColor $Green
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Deployment validation found issues that need attention." -ForegroundColor $Red
    Write-Host "Please review the failed tests and redeploy if necessary." -ForegroundColor $Yellow
    exit 1
}