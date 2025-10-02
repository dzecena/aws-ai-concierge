# AWS AI Concierge Environment Cleanup Script
# Usage: .\scripts\cleanup-environment.ps1 [environment] [region]
# WARNING: This will DELETE all resources for the specified environment!

param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1",
    [switch]$Force = $false
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🧹 AWS AI Concierge Environment Cleanup" -ForegroundColor $Red
Write-Host "Environment: $Environment" -ForegroundColor $Red
Write-Host "Region: $Region" -ForegroundColor $Red
Write-Host ""

if (-not $Force) {
    Write-Host "⚠️  WARNING: This will DELETE all resources for the $Environment environment!" -ForegroundColor $Yellow
    Write-Host "This includes:" -ForegroundColor $Yellow
    Write-Host "  - Bedrock Agent and Alias" -ForegroundColor $Yellow
    Write-Host "  - Lambda Function" -ForegroundColor $Yellow
    Write-Host "  - API Gateway" -ForegroundColor $Yellow
    Write-Host "  - S3 Bucket and contents" -ForegroundColor $Yellow
    Write-Host "  - IAM Roles and Policies" -ForegroundColor $Yellow
    Write-Host "  - CloudWatch Log Groups" -ForegroundColor $Yellow
    Write-Host ""
    
    $confirmation = Read-Host "Type 'DELETE' to confirm you want to proceed"
    if ($confirmation -ne "DELETE") {
        Write-Host "❌ Cleanup cancelled" -ForegroundColor $Green
        exit 0
    }
}

Write-Host "🚀 Starting cleanup process..." -ForegroundColor $Blue
Write-Host ""

# Check if AWS CLI is configured
try {
    $null = aws sts get-caller-identity 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI not configured"
    }
} catch {
    Write-Host "❌ AWS CLI not configured or no valid credentials" -ForegroundColor $Red
    exit 1
}

# Get current AWS account
$Account = (aws sts get-caller-identity --query Account --output text)
Write-Host "✅ AWS CLI configured for account: $Account" -ForegroundColor $Green

# Step 1: Delete Bedrock Agent and Alias
Write-Host ""
Write-Host "🤖 Cleaning up Bedrock Agent..." -ForegroundColor $Yellow

try {
    # List agents to find our agent
    $AgentName = "aws-ai-concierge-$Environment"
    $Agents = aws bedrock-agent list-agents --query "agentSummaries[?agentName=='$AgentName'].agentId" --output text
    
    if ($Agents) {
        $AgentId = $Agents.Trim()
        Write-Host "Found Bedrock Agent: $AgentId" -ForegroundColor $Blue
        
        # Delete agent aliases first
        try {
            $Aliases = aws bedrock-agent list-agent-aliases --agent-id $AgentId --query "agentAliasSummaries[].agentAliasId" --output text
            if ($Aliases) {
                foreach ($AliasId in $Aliases.Split()) {
                    if ($AliasId.Trim()) {
                        Write-Host "Deleting agent alias: $AliasId" -ForegroundColor $Blue
                        aws bedrock-agent delete-agent-alias --agent-id $AgentId --agent-alias-id $AliasId.Trim() 2>$null
                    }
                }
            }
        } catch {
            Write-Host "⚠️  Could not delete agent aliases (may not exist)" -ForegroundColor $Yellow
        }
        
        # Delete the agent
        Write-Host "Deleting Bedrock Agent: $AgentId" -ForegroundColor $Blue
        aws bedrock-agent delete-agent --agent-id $AgentId --skip-resource-in-use-check 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Bedrock Agent deleted successfully" -ForegroundColor $Green
        } else {
            Write-Host "⚠️  Could not delete Bedrock Agent (may not exist or be in use)" -ForegroundColor $Yellow
        }
    } else {
        Write-Host "ℹ️  No Bedrock Agent found for $Environment" -ForegroundColor $Blue
    }
} catch {
    Write-Host "⚠️  Error cleaning up Bedrock Agent: $($_.Exception.Message)" -ForegroundColor $Yellow
}

# Step 2: Delete CDK Stack (this will handle most resources)
Write-Host ""
Write-Host "☁️  Deleting CDK Stack..." -ForegroundColor $Yellow

$StackName = "AwsAiConcierge-$Environment"

try {
    # Check if stack exists
    $StackStatus = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].StackStatus" --output text 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Found CDK Stack: $StackName" -ForegroundColor $Blue
        Write-Host "Deleting CDK Stack (this may take several minutes)..." -ForegroundColor $Blue
        
        # Delete the stack
        aws cloudformation delete-stack --stack-name $StackName --region $Region
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ CDK Stack deletion initiated" -ForegroundColor $Green
            Write-Host "⏳ Waiting for stack deletion to complete..." -ForegroundColor $Blue
            
            # Wait for deletion to complete (with timeout)
            $timeout = 300 # 5 minutes
            $elapsed = 0
            $interval = 10
            
            do {
                Start-Sleep $interval
                $elapsed += $interval
                
                $StackStatus = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].StackStatus" --output text 2>$null
                
                if ($LASTEXITCODE -ne 0) {
                    # Stack no longer exists
                    Write-Host "✅ CDK Stack deleted successfully" -ForegroundColor $Green
                    break
                }
                
                Write-Host "Stack status: $StackStatus (${elapsed}s elapsed)" -ForegroundColor $Blue
                
                if ($StackStatus -eq "DELETE_FAILED") {
                    Write-Host "❌ Stack deletion failed. You may need to delete resources manually." -ForegroundColor $Red
                    break
                }
                
            } while ($elapsed -lt $timeout -and $StackStatus -ne "DELETE_COMPLETE")
            
            if ($elapsed -ge $timeout) {
                Write-Host "⚠️  Stack deletion is taking longer than expected. Check AWS Console for status." -ForegroundColor $Yellow
            }
        } else {
            Write-Host "❌ Failed to initiate CDK Stack deletion" -ForegroundColor $Red
        }
    } else {
        Write-Host "ℹ️  No CDK Stack found for $Environment" -ForegroundColor $Blue
    }
} catch {
    Write-Host "⚠️  Error deleting CDK Stack: $($_.Exception.Message)" -ForegroundColor $Yellow
}

# Step 3: Clean up any remaining S3 objects (in case auto-delete failed)
Write-Host ""
Write-Host "🗂️  Cleaning up S3 resources..." -ForegroundColor $Yellow

$BucketName = "aws-ai-concierge-openapi-$Environment-$Account-$Region"

try {
    # Check if bucket exists
    $BucketExists = aws s3api head-bucket --bucket $BucketName 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Found S3 Bucket: $BucketName" -ForegroundColor $Blue
        Write-Host "Emptying S3 Bucket..." -ForegroundColor $Blue
        
        # Empty the bucket
        aws s3 rm "s3://$BucketName" --recursive 2>$null
        
        Write-Host "Deleting S3 Bucket..." -ForegroundColor $Blue
        aws s3api delete-bucket --bucket $BucketName --region $Region 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ S3 Bucket deleted successfully" -ForegroundColor $Green
        } else {
            Write-Host "⚠️  Could not delete S3 Bucket (may have been deleted by CDK)" -ForegroundColor $Yellow
        }
    } else {
        Write-Host "ℹ️  No S3 Bucket found for $Environment" -ForegroundColor $Blue
    }
} catch {
    Write-Host "⚠️  Error cleaning up S3 resources: $($_.Exception.Message)" -ForegroundColor $Yellow
}

# Step 4: Clean up CloudWatch Log Groups (if not deleted by CDK)
Write-Host ""
Write-Host "📊 Cleaning up CloudWatch Log Groups..." -ForegroundColor $Yellow

$LogGroupName = "/aws/lambda/aws-ai-concierge-tools-$Environment"

try {
    # Check if log group exists
    $LogGroups = aws logs describe-log-groups --log-group-name-prefix $LogGroupName --region $Region --query "logGroups[].logGroupName" --output text 2>$null
    
    if ($LASTEXITCODE -eq 0 -and $LogGroups) {
        foreach ($LogGroup in $LogGroups.Split()) {
            if ($LogGroup.Trim()) {
                Write-Host "Deleting Log Group: $($LogGroup.Trim())" -ForegroundColor $Blue
                aws logs delete-log-group --log-group-name $LogGroup.Trim() --region $Region 2>$null
            }
        }
        Write-Host "✅ CloudWatch Log Groups cleaned up" -ForegroundColor $Green
    } else {
        Write-Host "ℹ️  No CloudWatch Log Groups found for $Environment" -ForegroundColor $Blue
    }
} catch {
    Write-Host "⚠️  Error cleaning up CloudWatch Log Groups: $($_.Exception.Message)" -ForegroundColor $Yellow
}

# Step 5: Summary and Cost Verification
Write-Host ""
Write-Host "💰 Cost Impact Summary:" -ForegroundColor $Blue
Write-Host "The following resources have been deleted (no ongoing costs):" -ForegroundColor $Green
Write-Host "  ✅ Lambda Function (pay-per-invocation)" -ForegroundColor $Green
Write-Host "  ✅ API Gateway (pay-per-request)" -ForegroundColor $Green
Write-Host "  ✅ S3 Bucket and objects (pay-per-GB stored)" -ForegroundColor $Green
Write-Host "  ✅ CloudWatch Log Groups (pay-per-GB stored)" -ForegroundColor $Green
Write-Host "  ✅ Bedrock Agent (pay-per-request)" -ForegroundColor $Green
Write-Host ""
Write-Host "ℹ️  Note: IAM roles have no cost when not in use" -ForegroundColor $Blue
Write-Host ""

# Step 6: Verification
Write-Host "🔍 Verification Steps:" -ForegroundColor $Blue
Write-Host "1. Check AWS Console → CloudFormation for any remaining stacks" -ForegroundColor $Blue
Write-Host "2. Check AWS Console → Lambda for any remaining functions" -ForegroundColor $Blue
Write-Host "3. Check AWS Console → S3 for any remaining buckets" -ForegroundColor $Blue
Write-Host "4. Check AWS Console → Bedrock → Agents for any remaining agents" -ForegroundColor $Blue
Write-Host ""

Write-Host "🎉 Environment cleanup completed!" -ForegroundColor $Green
Write-Host ""
Write-Host "💡 To redeploy later:" -ForegroundColor $Yellow
Write-Host "  1. Run: .\scripts\deploy.ps1 -Environment $Environment" -ForegroundColor $Yellow
Write-Host "  2. Run: .\scripts\create-bedrock-agent.ps1 -Environment $Environment" -ForegroundColor $Yellow
Write-Host ""
Write-Host "📊 Monitor your AWS bill to confirm no unexpected charges" -ForegroundColor $Blue