# Upload OpenAPI Specification to S3
# Usage: .\scripts\upload-openapi.ps1 [environment] [region]

param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "📤 Uploading OpenAPI Specification" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host "Region: $Region" -ForegroundColor $Blue
Write-Host ""

# Get current AWS account
try {
    $Account = (aws sts get-caller-identity --query Account --output text)
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to get account"
    }
} catch {
    Write-Host "❌ AWS CLI not configured or no valid credentials" -ForegroundColor $Red
    exit 1
}

# Construct bucket name (matches CDK stack naming)
$BucketName = "aws-ai-concierge-openapi-$Environment-$Account-$Region"
Write-Host "Target S3 Bucket: $BucketName" -ForegroundColor $Blue

# Check if bucket exists
try {
    $null = aws s3api head-bucket --bucket $BucketName 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Bucket not found"
    }
    Write-Host "✅ S3 bucket found" -ForegroundColor $Green
} catch {
    Write-Host "❌ S3 bucket not found: $BucketName" -ForegroundColor $Red
    Write-Host "Please deploy the CDK stack first" -ForegroundColor $Yellow
    exit 1
}

# Check if OpenAPI spec exists
$OpenApiPath = "..\openapi-spec\aws-ai-concierge-tools.yaml"
if (-not (Test-Path $OpenApiPath)) {
    Write-Host "❌ OpenAPI specification not found: $OpenApiPath" -ForegroundColor $Red
    exit 1
}

Write-Host "✅ OpenAPI specification found" -ForegroundColor $Green

# Upload OpenAPI specification
Write-Host "📤 Uploading OpenAPI specification..." -ForegroundColor $Yellow
try {
    aws s3 cp $OpenApiPath "s3://$BucketName/aws-ai-concierge-tools.yaml" --content-type "application/yaml"
    if ($LASTEXITCODE -ne 0) {
        throw "Upload failed"
    }
    Write-Host "✅ OpenAPI specification uploaded successfully" -ForegroundColor $Green
} catch {
    Write-Host "❌ Failed to upload OpenAPI specification" -ForegroundColor $Red
    exit 1
}

# Verify upload
Write-Host "🔍 Verifying upload..." -ForegroundColor $Yellow
try {
    $null = aws s3api head-object --bucket $BucketName --key "aws-ai-concierge-tools.yaml" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Verification failed"
    }
    Write-Host "✅ Upload verified" -ForegroundColor $Green
} catch {
    Write-Host "❌ Upload verification failed" -ForegroundColor $Red
    exit 1
}

Write-Host ""
Write-Host "🎉 OpenAPI specification upload completed!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Upload Summary:" -ForegroundColor $Blue
Write-Host "  S3 Bucket: $BucketName" -ForegroundColor $Blue
Write-Host "  S3 Key: aws-ai-concierge-tools.yaml" -ForegroundColor $Blue
Write-Host "  S3 URL: https://$BucketName.s3.amazonaws.com/aws-ai-concierge-tools.yaml" -ForegroundColor $Blue
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor $Yellow
Write-Host "  1. The Bedrock Agent should now be able to access the OpenAPI specification" -ForegroundColor $Yellow
Write-Host "  2. Test the Bedrock Agent with a simple query" -ForegroundColor $Yellow
Write-Host "  3. Run integration tests to verify functionality" -ForegroundColor $Yellow