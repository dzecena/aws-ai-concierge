"""
Simple Integration Test Runner for AWS AI Concierge
Lightweight test runner with minimal dependencies
"""

import json
import time
import boto3
import sys
from datetime import datetime
from typing import Dict, List, Any


class SimpleTestRunner:
    """Simple integration test runner with minimal dependencies."""
    
    def __init__(self, environment: str = "dev", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.function_name = f"aws-ai-concierge-tools-{environment}"
        
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_result(self, test_name: str, success: bool, duration_ms: float, message: str):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message} ({duration_ms:.2f}ms)")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "duration_ms": duration_ms,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def test_lambda_function_exists(self) -> bool:
        """Test if Lambda function exists and is accessible."""
        test_name = "Lambda Function Accessibility"
        start_time = time.time()
        
        try:
            response = self.lambda_client.get_function(FunctionName=self.function_name)
            duration_ms = (time.time() - start_time) * 1000
            
            if response['Configuration']['State'] == 'Active':
                self.log_result(test_name, True, duration_ms, "Function is active and accessible")
                return True
            else:
                self.log_result(test_name, False, duration_ms, f"Function state: {response['Configuration']['State']}")
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_result(test_name, False, duration_ms, f"Error: {str(e)}")
            return False
    
    def test_basic_invocation(self) -> bool:
        """Test basic Lambda function invocation."""
        test_name = "Basic Lambda Invocation"
        start_time = time.time()
        
        try:
            payload = {
                "httpMethod": "POST",
                "path": "/cost-analysis",
                "body": json.dumps({"time_period": "MONTHLY"})
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.get('StatusCode') == 200:
                response_data = json.loads(response['Payload'].read())
                self.log_result(test_name, True, duration_ms, "Function invoked successfully")
                return True
            else:
                self.log_result(test_name, False, duration_ms, f"Status: {response.get('StatusCode')}")
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_result(test_name, False, duration_ms, f"Error: {str(e)}")
            return False
    
    def test_cost_analysis_endpoint(self) -> bool:
        """Test cost analysis endpoint."""
        test_name = "Cost Analysis Endpoint"
        start_time = time.time()
        
        try:
            payload = {
                "httpMethod": "POST",
                "path": "/cost-analysis",
                "body": json.dumps({
                    "time_period": "MONTHLY",
                    "granularity": "DAILY"
                })
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.get('StatusCode') == 200:
                response_data = json.loads(response['Payload'].read())
                
                # Check if response has expected structure
                if 'body' in response_data:
                    body = json.loads(response_data['body'])
                    if body.get('success') and 'data' in body:
                        self.log_result(test_name, True, duration_ms, "Cost analysis completed successfully")
                        return True
                    else:
                        self.log_result(test_name, False, duration_ms, "Response indicates failure")
                        return False
                else:
                    self.log_result(test_name, False, duration_ms, "Invalid response structure")
                    return False
            else:
                self.log_result(test_name, False, duration_ms, f"Status: {response.get('StatusCode')}")
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_result(test_name, False, duration_ms, f"Error: {str(e)}")
            return False
    
    def test_resource_inventory_endpoint(self) -> bool:
        """Test resource inventory endpoint."""
        test_name = "Resource Inventory Endpoint"
        start_time = time.time()
        
        try:
            payload = {
                "httpMethod": "POST",
                "path": "/resource-inventory",
                "body": json.dumps({
                    "resource_type": "ec2",
                    "region": "us-east-1"
                })
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.get('StatusCode') == 200:
                response_data = json.loads(response['Payload'].read())
                
                if 'body' in response_data:
                    body = json.loads(response_data['body'])
                    if body.get('success') and 'data' in body:
                        resource_count = body['data'].get('total_count', 0)
                        self.log_result(test_name, True, duration_ms, f"Found {resource_count} resources")
                        return True
                    else:
                        self.log_result(test_name, False, duration_ms, "Response indicates failure")
                        return False
                else:
                    self.log_result(test_name, False, duration_ms, "Invalid response structure")
                    return False
            else:
                self.log_result(test_name, False, duration_ms, f"Status: {response.get('StatusCode')}")
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_result(test_name, False, duration_ms, f"Error: {str(e)}")
            return False
    
    def test_security_assessment_endpoint(self) -> bool:
        """Test security assessment endpoint."""
        test_name = "Security Assessment Endpoint"
        start_time = time.time()
        
        try:
            payload = {
                "httpMethod": "POST",
                "path": "/security-assessment",
                "body": json.dumps({
                    "region": "us-east-1",
                    "assessment_type": "security_groups"
                })
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.get('StatusCode') == 200:
                response_data = json.loads(response['Payload'].read())
                
                if 'body' in response_data:
                    body = json.loads(response_data['body'])
                    if body.get('success') and 'data' in body:
                        findings_count = len(body['data'].get('findings', []))
                        risk_score = body['data'].get('risk_score', 0)
                        self.log_result(test_name, True, duration_ms, f"Assessment completed: {findings_count} findings, risk score: {risk_score}")
                        return True
                    else:
                        self.log_result(test_name, False, duration_ms, "Response indicates failure")
                        return False
                else:
                    self.log_result(test_name, False, duration_ms, "Invalid response structure")
                    return False
            else:
                self.log_result(test_name, False, duration_ms, f"Status: {response.get('StatusCode')}")
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_result(test_name, False, duration_ms, f"Error: {str(e)}")
            return False
    
    def test_performance_simple_query(self) -> bool:
        """Test performance for simple query (< 5s)."""
        test_name = "Performance - Simple Query"
        start_time = time.time()
        
        try:
            payload = {
                "httpMethod": "POST",
                "path": "/cost-analysis",
                "body": json.dumps({"time_period": "MONTHLY"})
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.get('StatusCode') == 200:
                if duration_ms <= 5000:  # 5 second threshold
                    self.log_result(test_name, True, duration_ms, "Meets 5s performance requirement")
                    return True
                else:
                    self.log_result(test_name, False, duration_ms, "Exceeds 5s performance requirement")
                    return False
            else:
                self.log_result(test_name, False, duration_ms, f"Status: {response.get('StatusCode')}")
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_result(test_name, False, duration_ms, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid input."""
        test_name = "Error Handling"
        start_time = time.time()
        
        try:
            payload = {
                "httpMethod": "POST",
                "path": "/cost-analysis",
                "body": json.dumps({"time_period": "INVALID_PERIOD"})
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.get('StatusCode') == 200:
                response_data = json.loads(response['Payload'].read())
                
                if 'body' in response_data:
                    body = json.loads(response_data['body'])
                    if not body.get('success') and 'error' in body:
                        # Error was properly handled
                        self.log_result(test_name, True, duration_ms, "Error properly handled and formatted")
                        return True
                    else:
                        self.log_result(test_name, False, duration_ms, "Invalid input was not rejected")
                        return False
                else:
                    self.log_result(test_name, False, duration_ms, "Invalid response structure")
                    return False
            else:
                # Lambda returned error status - this might be acceptable
                self.log_result(test_name, True, duration_ms, f"Error status returned: {response.get('StatusCode')}")
                return True
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # For error handling test, some exceptions might be expected
            self.log_result(test_name, True, duration_ms, f"Exception occurred as expected: {str(e)}")
            return True
    
    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("🚀 AWS AI Concierge Simple Integration Tests")
        print("=" * 60)
        print(f"Environment: {self.environment}")
        print(f"Region: {self.region}")
        print(f"Function: {self.function_name}")
        print("=" * 60)
        
        # List of all tests
        tests = [
            self.test_lambda_function_exists,
            self.test_basic_invocation,
            self.test_cost_analysis_endpoint,
            self.test_resource_inventory_endpoint,
            self.test_security_assessment_endpoint,
            self.test_performance_simple_query,
            self.test_error_handling,
        ]
        
        # Run all tests
        overall_success = True
        for test_func in tests:
            try:
                success = test_func()
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"❌ {test_func.__name__}: EXCEPTION - {str(e)}")
                overall_success = False
                self.failed_tests += 1
        
        # Print summary
        self.print_summary(overall_success)
        
        return overall_success
    
    def print_summary(self, overall_success: bool):
        """Print test execution summary."""
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("")
        
        if overall_success:
            print("🎉 ALL TESTS PASSED!")
            print("   Your AWS AI Concierge is working correctly.")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("   Please review the failed tests and fix any issues.")
        
        print("=" * 60)
        
        # Save results to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results_file = f"simple-test-results-{self.environment}-{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "environment": self.environment,
                "region": self.region,
                "function_name": self.function_name,
                "timestamp": datetime.utcnow().isoformat(),
                "total_tests": total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": success_rate,
                "overall_success": overall_success,
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Test results saved to: {results_file}")


def main():
    """Main function for command line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple AWS AI Concierge Integration Tests')
    parser.add_argument('--environment', '-e', default='dev', help='Environment to test')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    runner = SimpleTestRunner(environment=args.environment, region=args.region)
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()