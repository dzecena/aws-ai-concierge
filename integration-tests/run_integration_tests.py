"""
AWS AI Concierge Integration Test Runner
Comprehensive test execution with reporting and validation
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_framework import IntegrationTestFramework
from test_scenarios import SpecificTestScenarios


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='AWS AI Concierge Integration Test Runner')
    parser.add_argument('--environment', '-e', default='dev', 
                       choices=['dev', 'staging', 'prod'],
                       help='Environment to test (default: dev)')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--outputs-file', '-o', 
                       help='CDK outputs file path (default: auto-detect)')
    parser.add_argument('--report-dir', '-d', default='reports',
                       help='Directory for test reports (default: reports)')
    parser.add_argument('--concurrent-users', '-c', type=int, default=10,
                       help='Number of concurrent users for load testing (default: 10)')
    parser.add_argument('--requests-per-user', '-u', type=int, default=5,
                       help='Requests per user for load testing (default: 5)')
    parser.add_argument('--skip-bedrock', action='store_true',
                       help='Skip Bedrock Agent tests')
    parser.add_argument('--skip-load', action='store_true',
                       help='Skip load testing')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create reports directory
    report_dir = Path(args.report_dir)
    report_dir.mkdir(exist_ok=True)
    
    print("🚀 AWS AI Concierge Integration Test Suite")
    print("=" * 60)
    print(f"Environment: {args.environment}")
    print(f"Region: {args.region}")
    print(f"Report Directory: {report_dir}")
    print(f"Concurrent Users: {args.concurrent_users}")
    print(f"Requests per User: {args.requests_per_user}")
    if args.skip_bedrock:
        print("⏭️  Skipping Bedrock Agent tests")
    if args.skip_load:
        print("⏭️  Skipping load tests")
    print("=" * 60)
    
    # Initialize test framework
    framework = IntegrationTestFramework(
        environment=args.environment,
        region=args.region
    )
    
    # Load stack outputs
    if args.outputs_file:
        framework.load_stack_outputs(args.outputs_file)
    else:
        framework.load_stack_outputs()
    
    # Initialize specific test scenarios
    scenarios = SpecificTestScenarios(framework)
    
    # Track overall test execution
    start_time = datetime.utcnow()
    overall_success = True
    
    try:
        print("\n🔍 Phase 1: Core Integration Tests")
        print("-" * 40)
        
        # Test Lambda direct invocation
        if not framework.test_lambda_direct_invocation():
            overall_success = False
        
        # Test API Gateway endpoints
        if not framework.test_api_gateway_endpoints():
            overall_success = False
        
        print("\n🔍 Phase 2: Functional Test Scenarios")
        print("-" * 40)
        
        # Run specific functional scenarios
        if not scenarios.run_all_scenarios():
            overall_success = False
        
        print("\n🔍 Phase 3: Performance Testing")
        print("-" * 40)
        
        # Test performance requirements
        if not framework.test_performance_requirements():
            overall_success = False
        
        # Load testing (if not skipped)
        if not args.skip_load:
            if not framework.test_concurrent_users(args.concurrent_users, args.requests_per_user):
                overall_success = False
        else:
            print("⏭️  Skipping load tests as requested")
        
        print("\n🔍 Phase 4: End-to-End Testing")
        print("-" * 40)
        
        # Bedrock Agent integration (if not skipped)
        if not args.skip_bedrock:
            if not framework.test_bedrock_agent_integration():
                overall_success = False
        else:
            print("⏭️  Skipping Bedrock Agent tests as requested")
        
        print("\n🔍 Phase 5: Compliance and Audit")
        print("-" * 40)
        
        # Test audit logging
        if not framework.test_audit_logging():
            overall_success = False
        
        # Generate comprehensive summary
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        summary = {
            "test_execution": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "execution_time_seconds": execution_time,
                "environment": args.environment,
                "region": args.region,
                "overall_success": overall_success
            },
            "test_configuration": {
                "concurrent_users": args.concurrent_users,
                "requests_per_user": args.requests_per_user,
                "skip_bedrock": args.skip_bedrock,
                "skip_load": args.skip_load
            }
        }
        
        # Get framework summary
        framework_summary = framework.run_all_tests()
        summary.update(framework_summary)
        
        # Generate reports
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # JSON report
        json_report_file = report_dir / f"integration-test-report-{args.environment}-{timestamp}.json"
        with open(json_report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # HTML report
        html_report_file = report_dir / f"integration-test-report-{args.environment}-{timestamp}.html"
        generate_html_report(summary, html_report_file)
        
        # Console summary
        print_test_summary(summary, json_report_file, html_report_file)
        
        # Exit with appropriate code
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def generate_html_report(summary: dict, output_file: Path):
    """Generate an HTML test report."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS AI Concierge Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .metric h3 {{ margin: 0 0 10px 0; color: #333; }}
        .metric .value {{ font-size: 24px; font-weight: bold; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .test-results {{ margin-top: 30px; }}
        .test-item {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #ddd; }}
        .test-item.passed {{ border-left-color: #28a745; }}
        .test-item.failed {{ border-left-color: #dc3545; }}
        .test-item.skipped {{ border-left-color: #ffc107; }}
        .test-name {{ font-weight: bold; margin-bottom: 5px; }}
        .test-details {{ font-size: 14px; color: #666; }}
        .performance-chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AWS AI Concierge Integration Test Report</h1>
            <p>Environment: <strong>{summary.get('environment', 'Unknown')}</strong> | 
               Region: <strong>{summary.get('region', 'Unknown')}</strong> | 
               Generated: <strong>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</strong></p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>Total Tests</h3>
                <div class="value">{summary.get('total_tests', 0)}</div>
            </div>
            <div class="metric">
                <h3>Passed</h3>
                <div class="value passed">{summary.get('passed_tests', 0)}</div>
            </div>
            <div class="metric">
                <h3>Failed</h3>
                <div class="value failed">{summary.get('failed_tests', 0)}</div>
            </div>
            <div class="metric">
                <h3>Skipped</h3>
                <div class="value skipped">{summary.get('skipped_tests', 0)}</div>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value {'passed' if summary.get('success_rate', 0) >= 95 else 'failed'}">{summary.get('success_rate', 0):.1f}%</div>
            </div>
            <div class="metric">
                <h3>Execution Time</h3>
                <div class="value">{summary.get('test_execution', {}).get('execution_time_seconds', 0):.1f}s</div>
            </div>
        </div>
        
        <div class="test-results">
            <h2>📋 Test Results</h2>
    """
    
    # Add test results
    for result in summary.get('test_results', []):
        status_class = result['status']
        status_emoji = {'passed': '✅', 'failed': '❌', 'skipped': '⏭️'}.get(status_class, '❓')
        
        html_content += f"""
            <div class="test-item {status_class}">
                <div class="test-name">{status_emoji} {result['name']}</div>
                <div class="test-details">
                    Type: {result['type']} | Duration: {result['duration_ms']:.2f}ms | {result['message']}
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)


def print_test_summary(summary: dict, json_report: Path, html_report: Path):
    """Print test summary to console."""
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION TEST EXECUTION COMPLETE")
    print("=" * 60)
    
    execution_info = summary.get('test_execution', {})
    print(f"Environment: {execution_info.get('environment', 'Unknown')}")
    print(f"Region: {execution_info.get('region', 'Unknown')}")
    print(f"Execution Time: {execution_info.get('execution_time_seconds', 0):.1f} seconds")
    print(f"Overall Success: {'✅ YES' if execution_info.get('overall_success') else '❌ NO'}")
    print("")
    
    print("📊 Test Statistics:")
    print(f"  Total Tests: {summary.get('total_tests', 0)}")
    print(f"  ✅ Passed: {summary.get('passed_tests', 0)}")
    print(f"  ❌ Failed: {summary.get('failed_tests', 0)}")
    print(f"  ⏭️ Skipped: {summary.get('skipped_tests', 0)}")
    print(f"  📈 Success Rate: {summary.get('success_rate', 0):.1f}%")
    print("")
    
    print("📋 Test Suite Results:")
    for suite_name, passed in summary.get('suite_results', {}).items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {suite_name}: {status}")
    print("")
    
    print("📄 Reports Generated:")
    print(f"  JSON Report: {json_report}")
    print(f"  HTML Report: {html_report}")
    print("")
    
    if execution_info.get('overall_success'):
        print("🎉 ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("   Your AWS AI Concierge is ready for production use.")
    else:
        print("⚠️  SOME INTEGRATION TESTS FAILED")
        print("   Please review the detailed reports and fix any issues before deployment.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()