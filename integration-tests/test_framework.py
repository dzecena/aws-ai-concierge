"""
AWS AI Concierge Integration Testing Framework
"""

import asyncio
import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
import requests
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of integration tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    LOAD = "load"
    END_TO_END = "end_to_end"


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    test_type: TestType
    status: TestStatus
    duration_ms: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics for test results."""
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    p95_time: float
    p99_time: float
    success_rate: float
    total_requests: int
    failed_requests: int


class IntegrationTestFramework:
    """Comprehensive integration testing framework for AWS AI Concierge."""
    
    def __init__(self, environment: str = "dev", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.results: List[TestResult] = []
        
        # Initialize AWS clients
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
        # Configuration
        self.lambda_function_name = f"aws-ai-concierge-tools-{environment}"
        self.api_gateway_url = None  # Will be set from stack outputs
        self.bedrock_agent_id = None  # Will be set from stack outputs
        self.bedrock_agent_alias_id = None  # Will be set from stack outputs
        
        # Performance thresholds
        self.simple_query_threshold_ms = 5000  # 5 seconds
        self.complex_query_threshold_ms = 15000  # 15 seconds
        
    def load_stack_outputs(self, outputs_file: str = None):
        """Load CDK stack outputs to get resource identifiers."""
        if not outputs_file:
            outputs_file = f"aws-ai-concierge-cdk/cdk-outputs-{self.environment}.json"
        
        try:
            with open(outputs_file, 'r') as f:
                outputs = json.load(f)
                
            stack_name = f"AwsAiConcierge-{self.environment}"
            if stack_name in outputs:
                stack_outputs = outputs[stack_name]
                self.api_gateway_url = stack_outputs.get('ApiGatewayUrl')
                self.bedrock_agent_id = stack_outputs.get('BedrockAgentId')
                self.bedrock_agent_alias_id = stack_outputs.get('BedrockAgentAliasId')
                
                logger.info(f"Loaded stack outputs for {stack_name}")
                logger.info(f"API Gateway URL: {self.api_gateway_url}")
                logger.info(f"Bedrock Agent ID: {self.bedrock_agent_id}")
                
        except FileNotFoundError:
            logger.warning(f"Stack outputs file not found: {outputs_file}")
        except Exception as e:
            logger.error(f"Error loading stack outputs: {e}")
    
    def add_result(self, test_name: str, test_type: TestType, status: TestStatus, 
                   duration_ms: float, message: str, details: Dict[str, Any] = None):
        """Add a test result to the results list."""
        result = TestResult(
            test_name=test_name,
            test_type=test_type,
            status=status,
            duration_ms=duration_ms,
            message=message,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        self.results.append(result)
        
        # Log the result
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.RUNNING: "🔄"
        }
        
        logger.info(f"{status_emoji.get(status, '❓')} {test_name}: {message} ({duration_ms:.2f}ms)")
    
    def test_lambda_direct_invocation(self) -> bool:
        """Test direct Lambda function invocation."""
        test_name = "Lambda Direct Invocation"
        start_time = time.time()
        
        try:
            # Test payload for cost analysis
            payload = {
                "httpMethod": "POST",
                "path": "/cost-analysis",
                "body": json.dumps({
                    "time_period": "MONTHLY",
                    "granularity": "DAILY"
                })
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.lambda_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response.get('StatusCode') == 200:
                self.add_result(test_name, TestType.INTEGRATION, TestStatus.PASSED, 
                              duration_ms, "Lambda function invoked successfully",
                              {"response": response_payload})
                return True
            else:
                self.add_result(test_name, TestType.INTEGRATION, TestStatus.FAILED,
                              duration_ms, f"Lambda returned status {response.get('StatusCode')}",
                              {"response": response_payload})
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.add_result(test_name, TestType.INTEGRATION, TestStatus.FAILED,
                          duration_ms, f"Lambda invocation failed: {str(e)}")
            return False
    
    def test_api_gateway_endpoints(self) -> bool:
        """Test API Gateway endpoints."""
        if not self.api_gateway_url:
            self.add_result("API Gateway Test", TestType.INTEGRATION, TestStatus.SKIPPED,
                          0, "API Gateway URL not available")
            return False
        
        endpoints = [
            ("cost-analysis", {"time_period": "MONTHLY"}),
            ("idle-resources", {"region": "us-east-1"}),
            ("resource-inventory", {"resource_type": "ec2", "region": "us-east-1"}),
            ("security-assessment", {"region": "us-east-1", "assessment_type": "security_groups"})
        ]
        
        all_passed = True
        
        for endpoint, payload in endpoints:
            test_name = f"API Gateway - {endpoint}"
            start_time = time.time()
            
            try:
                url = f"{self.api_gateway_url.rstrip('/')}/{endpoint}"
                response = requests.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.add_result(test_name, TestType.INTEGRATION, TestStatus.PASSED,
                                  duration_ms, f"API endpoint responded successfully",
                                  {"status_code": response.status_code, "response": response_data})
                else:
                    self.add_result(test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                  duration_ms, f"API returned status {response.status_code}",
                                  {"status_code": response.status_code, "response": response.text})
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.add_result(test_name, TestType.INTEGRATION, TestStatus.FAILED,
                              duration_ms, f"API request failed: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_bedrock_agent_integration(self) -> bool:
        """Test Bedrock Agent integration."""
        if not self.bedrock_agent_id or not self.bedrock_agent_alias_id:
            self.add_result("Bedrock Agent Test", TestType.END_TO_END, TestStatus.SKIPPED,
                          0, "Bedrock Agent IDs not available")
            return False
        
        test_queries = [
            "What are my AWS costs for this month?",
            "Show me my EC2 instances in us-east-1",
            "Check for security issues in my AWS account",
            "Find idle resources that I can optimize"
        ]
        
        all_passed = True
        
        for query in test_queries:
            test_name = f"Bedrock Agent - {query[:30]}..."
            start_time = time.time()
            
            try:
                response = self.bedrock_agent_client.invoke_agent(
                    agentId=self.bedrock_agent_id,
                    agentAliasId=self.bedrock_agent_alias_id,
                    sessionId=f"test-session-{int(time.time())}",
                    inputText=query
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Process streaming response
                response_text = ""
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            response_text += chunk['bytes'].decode('utf-8')
                
                if response_text:
                    self.add_result(test_name, TestType.END_TO_END, TestStatus.PASSED,
                                  duration_ms, "Bedrock Agent responded successfully",
                                  {"query": query, "response_length": len(response_text)})
                else:
                    self.add_result(test_name, TestType.END_TO_END, TestStatus.FAILED,
                                  duration_ms, "Bedrock Agent returned empty response",
                                  {"query": query})
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.add_result(test_name, TestType.END_TO_END, TestStatus.FAILED,
                              duration_ms, f"Bedrock Agent invocation failed: {str(e)}",
                              {"query": query})
                all_passed = False
        
        return all_passed
    
    def test_performance_requirements(self) -> bool:
        """Test performance requirements for simple and complex queries."""
        test_cases = [
            # Simple queries (should complete in < 5s)
            ("Simple - Cost Analysis", "/cost-analysis", {"time_period": "MONTHLY"}, self.simple_query_threshold_ms),
            ("Simple - Resource Count", "/resource-inventory", {"resource_type": "ec2", "region": "us-east-1"}, self.simple_query_threshold_ms),
            
            # Complex queries (should complete in < 15s)
            ("Complex - Multi-region Security", "/security-assessment", {"region": "us-east-1", "assessment_type": "comprehensive"}, self.complex_query_threshold_ms),
            ("Complex - Cost Analysis with Details", "/cost-analysis", {"time_period": "MONTHLY", "granularity": "DAILY", "group_by": "SERVICE"}, self.complex_query_threshold_ms),
        ]
        
        all_passed = True
        
        for test_name, endpoint, payload, threshold_ms in test_cases:
            start_time = time.time()
            
            try:
                # Test via Lambda direct invocation for consistent timing
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": endpoint,
                    "body": json.dumps(payload)
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.lambda_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms <= threshold_ms:
                    self.add_result(f"Performance - {test_name}", TestType.PERFORMANCE, TestStatus.PASSED,
                                  duration_ms, f"Completed within {threshold_ms}ms threshold",
                                  {"threshold_ms": threshold_ms, "actual_ms": duration_ms})
                else:
                    self.add_result(f"Performance - {test_name}", TestType.PERFORMANCE, TestStatus.FAILED,
                                  duration_ms, f"Exceeded {threshold_ms}ms threshold",
                                  {"threshold_ms": threshold_ms, "actual_ms": duration_ms})
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.add_result(f"Performance - {test_name}", TestType.PERFORMANCE, TestStatus.FAILED,
                              duration_ms, f"Performance test failed: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_concurrent_users(self, num_users: int = 10, requests_per_user: int = 5) -> bool:
        """Test concurrent user scenarios."""
        test_name = f"Concurrent Users ({num_users} users, {requests_per_user} requests each)"
        
        def make_request(user_id: int, request_id: int) -> Tuple[bool, float, str]:
            """Make a single request and return success, duration, and message."""
            start_time = time.time()
            try:
                payload = {
                    "httpMethod": "POST",
                    "path": "/cost-analysis",
                    "body": json.dumps({
                        "time_period": "MONTHLY",
                        "user_id": f"test-user-{user_id}",
                        "request_id": f"req-{request_id}"
                    })
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.lambda_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                duration = (time.time() - start_time) * 1000
                success = response.get('StatusCode') == 200
                message = "Success" if success else f"Status: {response.get('StatusCode')}"
                
                return success, duration, message
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                return False, duration, str(e)
        
        # Execute concurrent requests
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            
            for user_id in range(num_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)
            
            for future in as_completed(futures):
                success, duration, message = future.result()
                results.append((success, duration, message))
        
        total_duration_ms = (time.time() - start_time) * 1000
        
        # Analyze results
        successful_requests = sum(1 for success, _, _ in results if success)
        failed_requests = len(results) - successful_requests
        success_rate = (successful_requests / len(results)) * 100
        
        durations = [duration for _, duration, _ in results]
        metrics = PerformanceMetrics(
            min_time=min(durations),
            max_time=max(durations),
            avg_time=statistics.mean(durations),
            median_time=statistics.median(durations),
            p95_time=statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
            p99_time=statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
            success_rate=success_rate,
            total_requests=len(results),
            failed_requests=failed_requests
        )
        
        # Determine if test passed
        passed = success_rate >= 95.0 and metrics.p95_time <= self.simple_query_threshold_ms
        status = TestStatus.PASSED if passed else TestStatus.FAILED
        
        message = f"Success rate: {success_rate:.1f}%, P95: {metrics.p95_time:.1f}ms"
        
        self.add_result(test_name, TestType.LOAD, status, total_duration_ms, message,
                       {"metrics": metrics.__dict__, "individual_results": results[:10]})  # Limit details
        
        return passed
    
    def test_audit_logging(self) -> bool:
        """Test audit logging functionality."""
        test_name = "Audit Logging Verification"
        start_time = time.time()
        
        try:
            # Make a test request to generate logs
            test_payload = {
                "httpMethod": "POST",
                "path": "/cost-analysis",
                "body": json.dumps({
                    "time_period": "MONTHLY",
                    "test_audit": True
                })
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.lambda_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            # Wait a moment for logs to be written
            time.sleep(2)
            
            # Check CloudWatch logs for audit entries
            log_group_name = f"/aws/lambda/{self.lambda_function_name}"
            
            # Get recent log events
            end_time = int(time.time() * 1000)
            start_time_logs = end_time - (5 * 60 * 1000)  # Last 5 minutes
            
            log_response = self.logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time_logs,
                endTime=end_time,
                filterPattern="AUDIT_"
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Analyze log events
            audit_events = log_response.get('events', [])
            audit_types = set()
            
            for event in audit_events:
                message = event.get('message', '')
                if 'AUDIT_REQUEST:' in message:
                    audit_types.add('REQUEST_RECEIVED')
                elif 'AUDIT_TOOL:' in message:
                    audit_types.add('TOOL_INVOCATION')
                elif 'AUDIT_RESPONSE:' in message:
                    audit_types.add('RESPONSE_SENT')
                elif 'AUDIT_ERROR:' in message:
                    audit_types.add('ERROR_OCCURRED')
            
            expected_audit_types = {'REQUEST_RECEIVED', 'TOOL_INVOCATION', 'RESPONSE_SENT'}
            missing_types = expected_audit_types - audit_types
            
            if not missing_types:
                self.add_result(test_name, TestType.INTEGRATION, TestStatus.PASSED,
                              duration_ms, f"All required audit events found ({len(audit_events)} events)",
                              {"audit_types": list(audit_types), "event_count": len(audit_events)})
                return True
            else:
                self.add_result(test_name, TestType.INTEGRATION, TestStatus.FAILED,
                              duration_ms, f"Missing audit event types: {missing_types}",
                              {"found_types": list(audit_types), "missing_types": list(missing_types)})
                return False
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.add_result(test_name, TestType.INTEGRATION, TestStatus.FAILED,
                          duration_ms, f"Audit logging test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests and return summary."""
        logger.info("🚀 Starting AWS AI Concierge Integration Tests")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Region: {self.region}")
        logger.info("=" * 60)
        
        # Load stack outputs
        self.load_stack_outputs()
        
        # Run all test suites
        test_suites = [
            ("Lambda Direct Invocation", self.test_lambda_direct_invocation),
            ("API Gateway Endpoints", self.test_api_gateway_endpoints),
            ("Bedrock Agent Integration", self.test_bedrock_agent_integration),
            ("Performance Requirements", self.test_performance_requirements),
            ("Concurrent Users", lambda: self.test_concurrent_users(10, 3)),
            ("Audit Logging", self.test_audit_logging),
        ]
        
        suite_results = {}
        
        for suite_name, test_function in test_suites:
            logger.info(f"\n🔍 Running {suite_name} tests...")
            try:
                suite_results[suite_name] = test_function()
            except Exception as e:
                logger.error(f"Test suite {suite_name} failed with exception: {e}")
                suite_results[suite_name] = False
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        skipped_tests = len([r for r in self.results if r.status == TestStatus.SKIPPED])
        
        summary = {
            "environment": self.environment,
            "region": self.region,
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "suite_results": suite_results,
            "test_results": [
                {
                    "name": r.test_name,
                    "type": r.test_type.value,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message
                } for r in self.results
            ]
        }
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any], output_file: str = None):
        """Generate a comprehensive test report."""
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"integration-test-report-{self.environment}-{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n📊 Integration Test Report saved to: {output_file}")
        
        # Print summary to console
        logger.info("\n" + "=" * 60)
        logger.info("🎯 INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Environment: {summary['environment']}")
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Passed: {summary['passed_tests']}")
        logger.info(f"❌ Failed: {summary['failed_tests']}")
        logger.info(f"⏭️ Skipped: {summary['skipped_tests']}")
        logger.info(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        logger.info("")
        
        # Suite results
        logger.info("📋 Test Suite Results:")
        for suite_name, passed in summary['suite_results'].items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"  {suite_name}: {status}")
        
        overall_success = summary['failed_tests'] == 0
        logger.info("")
        if overall_success:
            logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            logger.info("⚠️  SOME INTEGRATION TESTS FAILED - Review the report for details")
        
        return output_file


if __name__ == "__main__":
    # Example usage
    framework = IntegrationTestFramework(environment="dev")
    summary = framework.run_all_tests()
    framework.generate_report(summary)