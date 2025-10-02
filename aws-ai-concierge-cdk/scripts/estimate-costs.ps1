# AWS AI Concierge Cost Estimation Script
# Usage: .\scripts\estimate-costs.ps1 [environment]

param(
    [string]$Environment = "dev"
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$Red = "Red"

Write-Host "💰 AWS AI Concierge Cost Estimation" -ForegroundColor $Blue
Write-Host "Environment: $Environment" -ForegroundColor $Blue
Write-Host ""

Write-Host "📊 Current Resource Costs (Pay-per-use):" -ForegroundColor $Blue
Write-Host ""

Write-Host "🔹 Lambda Function:" -ForegroundColor $Green
Write-Host "  • Cost: $0.0000166667 per GB-second" -ForegroundColor $Blue
Write-Host "  • Memory: 512 MB (configurable)" -ForegroundColor $Blue
Write-Host "  • Estimated cost per request: ~$0.000001 (1ms execution)" -ForegroundColor $Blue
Write-Host "  • Free tier: 1M requests/month + 400,000 GB-seconds" -ForegroundColor $Green
Write-Host ""

Write-Host "🔹 API Gateway:" -ForegroundColor $Green
Write-Host "  • Cost: $3.50 per million API calls" -ForegroundColor $Blue
Write-Host "  • Estimated cost per request: ~$0.0000035" -ForegroundColor $Blue
Write-Host "  • Free tier: 1M API calls/month (first 12 months)" -ForegroundColor $Green
Write-Host ""

Write-Host "🔹 Amazon Bedrock (Claude 3 Haiku):" -ForegroundColor $Green
Write-Host "  • Input tokens: $0.00025 per 1K tokens" -ForegroundColor $Blue
Write-Host "  • Output tokens: $0.00125 per 1K tokens" -ForegroundColor $Blue
Write-Host "  • Estimated cost per query: ~$0.01-0.05" -ForegroundColor $Blue
Write-Host "  • No free tier" -ForegroundColor $Yellow
Write-Host ""

Write-Host "🔹 S3 Storage:" -ForegroundColor $Green
Write-Host "  • Standard storage: $0.023 per GB/month" -ForegroundColor $Blue
Write-Host "  • OpenAPI spec: <1KB (~$0.00002/month)" -ForegroundColor $Blue
Write-Host "  • Free tier: 5GB for 12 months" -ForegroundColor $Green
Write-Host ""

Write-Host "🔹 CloudWatch Logs:" -ForegroundColor $Green
Write-Host "  • Ingestion: $0.50 per GB" -ForegroundColor $Blue
Write-Host "  • Storage: $0.03 per GB/month" -ForegroundColor $Blue
Write-Host "  • Estimated: <$1/month for typical usage" -ForegroundColor $Blue
Write-Host "  • Free tier: 5GB ingestion, 5GB storage" -ForegroundColor $Green
Write-Host ""

Write-Host "🔹 IAM Roles & Policies:" -ForegroundColor $Green
Write-Host "  • Cost: FREE" -ForegroundColor $Green
Write-Host ""

Write-Host "📈 Usage Scenarios:" -ForegroundColor $Blue
Write-Host ""

Write-Host "🟢 Light Usage (10 queries/day):" -ForegroundColor $Green
Write-Host "  • Bedrock: ~$3-15/month" -ForegroundColor $Blue
Write-Host "  • Lambda: FREE (within free tier)" -ForegroundColor $Green
Write-Host "  • API Gateway: FREE (within free tier)" -ForegroundColor $Green
Write-Host "  • Other services: <$1/month" -ForegroundColor $Blue
Write-Host "  • Total: ~$3-16/month" -ForegroundColor $Blue
Write-Host ""

Write-Host "🟡 Moderate Usage (100 queries/day):" -ForegroundColor $Yellow
Write-Host "  • Bedrock: ~$30-150/month" -ForegroundColor $Blue
Write-Host "  • Lambda: FREE (within free tier)" -ForegroundColor $Green
Write-Host "  • API Gateway: ~$0.35/month" -ForegroundColor $Blue
Write-Host "  • Other services: <$2/month" -ForegroundColor $Blue
Write-Host "  • Total: ~$32-152/month" -ForegroundColor $Blue
Write-Host ""

Write-Host "🔴 Heavy Usage (1000 queries/day):" -ForegroundColor $Red
Write-Host "  • Bedrock: ~$300-1500/month" -ForegroundColor $Blue
Write-Host "  • Lambda: ~$1-5/month" -ForegroundColor $Blue
Write-Host "  • API Gateway: ~$3.50/month" -ForegroundColor $Blue
Write-Host "  • Other services: ~$5/month" -ForegroundColor $Blue
Write-Host "  • Total: ~$309-1513/month" -ForegroundColor $Blue
Write-Host ""

Write-Host "💡 Cost Optimization Tips:" -ForegroundColor $Yellow
Write-Host ""
Write-Host "1. 🎯 Monitor Usage:" -ForegroundColor $Green
Write-Host "   • Set up CloudWatch billing alarms" -ForegroundColor $Blue
Write-Host "   • Use AWS Cost Explorer to track spending" -ForegroundColor $Blue
Write-Host ""
Write-Host "2. 🔧 Optimize Configuration:" -ForegroundColor $Green
Write-Host "   • Reduce Lambda memory if not needed (current: 512MB)" -ForegroundColor $Blue
Write-Host "   • Use shorter CloudWatch log retention (current: 7 days for dev)" -ForegroundColor $Blue
Write-Host ""
Write-Host "3. 🚫 For POC/Testing:" -ForegroundColor $Green
Write-Host "   • Delete resources when not in use: .\scripts\cleanup-environment.ps1" -ForegroundColor $Blue
Write-Host "   • Use dev environment for testing (lower resource allocation)" -ForegroundColor $Blue
Write-Host ""
Write-Host "4. 📊 Bedrock Cost Control:" -ForegroundColor $Green
Write-Host "   • Monitor token usage in CloudWatch" -ForegroundColor $Blue
Write-Host "   • Consider using shorter prompts" -ForegroundColor $Blue
Write-Host "   • Implement query caching for repeated questions" -ForegroundColor $Blue
Write-Host ""

Write-Host "⚠️  Important Notes:" -ForegroundColor $Yellow
Write-Host "• Bedrock is the primary cost driver (pay-per-token)" -ForegroundColor $Yellow
Write-Host "• Most other services are FREE or very low cost for POC usage" -ForegroundColor $Yellow
Write-Host "• Always clean up resources after POC to avoid ongoing charges" -ForegroundColor $Yellow
Write-Host ""

Write-Host "🧹 To clean up NOW and avoid costs:" -ForegroundColor $Red
Write-Host ".\scripts\cleanup-environment.ps1 -Environment $Environment" -ForegroundColor $Red