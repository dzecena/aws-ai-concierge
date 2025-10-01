"""
AWS AI Concierge Integration Test Scenarios
Specific test cases for different functionality areas
"""

import json
import time
import boto3
import requests
from typing import Dict, List, Any, Tuple
from test_framework import IntegrationTestFramework, TestType, TestStatus


class SpecificTestScenarios:
    """Specific test scenarios for AWS AI Concierge functionality."""
    
    def __init__(self, framework: IntegrationTestFramework):
        self.framework = framework
        self.lambda_client = framework.lambda_client
        self.function_name = framework.lambda_function_name
    
    def test_cost_analysis_scenarios(self) -> bool:
        """Test various cost analysis scenarios."""
        scenarios = [
            {
                "name": "Monthly Cost Analysis",
                "payload": {"time_period": "MONTHLY", "granularity": "DAILY"},
                "expected_fields": ["total_cost", "cost_breakdown", "time_period"]
            },
            {
                "name": "Service-based Cost Breakdown",
                "payload": {"time_period": "MONTHLY", "group_by": "SERVICE"},
                "expected_fields": ["total_cost", "cost_breakdown", "services"]
            },
            {
                "name": "Regional Cost Analysis",
                "payload": {"time_period": "MONTHLY", "group_by": "REGION"},
                "expected_fields": ["total_cost", "cost_breakdown", "regions"]
            },
            {
                "name": "Daily Granularity Analysis",
                "payload": {"time_period": "DAILY", "granularity": "DAILY"},
                "expected_fields": ["total_cost", "daily_breakdown"]
            }
        ]
        
        all_passed = True
        
        for scenario in scenarios:
            test_name = f"Cost Analysis - {scenario['name']}"
            start_time = time.time()
            
            try:
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": "/cost-analysis",
                    "body": json.dumps(scenario["payload"])
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                response_data = json.loads(response['Payload'].read())
                
                # Validate response structure
                if response.get('StatusCode') == 200:
                    if 'body' in response_data:
                        body = json.loads(response_data['body'])
                        if body.get('success') and 'data' in body:
                            data = body['data']
                            missing_fields = [field for field in scenario['expected_fields'] 
                                            if field not in data]
                            
                            if not missing_fields:
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.PASSED,
                                    duration_ms, "Cost analysis completed successfully",
                                    {"scenario": scenario['name'], "data_keys": list(data.keys())}
                                )
                            else:
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                    duration_ms, f"Missing expected fields: {missing_fields}",
                                    {"missing_fields": missing_fields, "actual_keys": list(data.keys())}
                                )
                                all_passed = False
                        else:
                            self.framework.add_result(
                                test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                duration_ms, "Response indicates failure or missing data",
                                {"response": body}
                            )
                            all_passed = False
                    else:
                        self.framework.add_result(
                            test_name, TestType.INTEGRATION, TestStatus.FAILED,
                            duration_ms, "Response missing body",
                            {"response": response_data}
                        )
                        all_passed = False
                else:
                    self.framework.add_result(
                        test_name, TestType.INTEGRATION, TestStatus.FAILED,
                        duration_ms, f"Lambda returned status {response.get('StatusCode')}",
                        {"response": response_data}
                    )
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.framework.add_result(
                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                    duration_ms, f"Test failed with exception: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_resource_discovery_scenarios(self) -> bool:
        """Test resource discovery scenarios."""
        scenarios = [
            {
                "name": "EC2 Instance Discovery",
                "payload": {"resource_type": "ec2", "region": "us-east-1"},
                "expected_fields": ["resources", "total_count", "resource_type"]
            },
            {
                "name": "S3 Bucket Discovery",
                "payload": {"resource_type": "s3"},
                "expected_fields": ["resources", "total_count", "resource_type"]
            },
            {
                "name": "RDS Instance Discovery",
                "payload": {"resource_type": "rds", "region": "us-east-1"},
                "expected_fields": ["resources", "total_count", "resource_type"]
            },
            {
                "name": "Lambda Function Discovery",
                "payload": {"resource_type": "lambda", "region": "us-east-1"},
                "expected_fields": ["resources", "total_count", "resource_type"]
            }
        ]
        
        all_passed = True
        
        for scenario in scenarios:
            test_name = f"Resource Discovery - {scenario['name']}"
            start_time = time.time()
            
            try:
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": "/resource-inventory",
                    "body": json.dumps(scenario["payload"])
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                response_data = json.loads(response['Payload'].read())
                
                if response.get('StatusCode') == 200:
                    if 'body' in response_data:
                        body = json.loads(response_data['body'])
                        if body.get('success') and 'data' in body:
                            data = body['data']
                            missing_fields = [field for field in scenario['expected_fields'] 
                                            if field not in data]
                            
                            if not missing_fields:
                                resource_count = data.get('total_count', 0)
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.PASSED,
                                    duration_ms, f"Found {resource_count} resources",
                                    {"resource_count": resource_count, "resource_type": data.get('resource_type')}
                                )
                            else:
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                    duration_ms, f"Missing expected fields: {missing_fields}",
                                    {"missing_fields": missing_fields}
                                )
                                all_passed = False
                        else:
                            self.framework.add_result(
                                test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                duration_ms, "Response indicates failure or missing data",
                                {"response": body}
                            )
                            all_passed = False
                    else:
                        self.framework.add_result(
                            test_name, TestType.INTEGRATION, TestStatus.FAILED,
                            duration_ms, "Response missing body"
                        )
                        all_passed = False
                else:
                    self.framework.add_result(
                        test_name, TestType.INTEGRATION, TestStatus.FAILED,
                        duration_ms, f"Lambda returned status {response.get('StatusCode')}"
                    )
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.framework.add_result(
                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                    duration_ms, f"Test failed with exception: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_security_assessment_scenarios(self) -> bool:
        """Test security assessment scenarios."""
        scenarios = [
            {
                "name": "Security Groups Assessment",
                "payload": {"region": "us-east-1", "assessment_type": "security_groups"},
                "expected_fields": ["findings", "risk_score", "assessment_type"]
            },
            {
                "name": "S3 Public Access Check",
                "payload": {"assessment_type": "s3_public_access"},
                "expected_fields": ["findings", "risk_score", "buckets_checked"]
            },
            {
                "name": "Encryption Status Check",
                "payload": {"region": "us-east-1", "resource_type": "s3"},
                "endpoint": "/encryption-status",
                "expected_fields": ["encryption_status", "resources_checked"]
            }
        ]
        
        all_passed = True
        
        for scenario in scenarios:
            test_name = f"Security Assessment - {scenario['name']}"
            start_time = time.time()
            
            try:
                endpoint = scenario.get('endpoint', '/security-assessment')
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": endpoint,
                    "body": json.dumps(scenario["payload"])
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                response_data = json.loads(response['Payload'].read())
                
                if response.get('StatusCode') == 200:
                    if 'body' in response_data:
                        body = json.loads(response_data['body'])
                        if body.get('success') and 'data' in body:
                            data = body['data']
                            missing_fields = [field for field in scenario['expected_fields'] 
                                            if field not in data]
                            
                            if not missing_fields:
                                findings_count = len(data.get('findings', []))
                                risk_score = data.get('risk_score', 0)
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.PASSED,
                                    duration_ms, f"Assessment completed: {findings_count} findings, risk score: {risk_score}",
                                    {"findings_count": findings_count, "risk_score": risk_score}
                                )
                            else:
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                    duration_ms, f"Missing expected fields: {missing_fields}",
                                    {"missing_fields": missing_fields}
                                )
                                all_passed = False
                        else:
                            self.framework.add_result(
                                test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                duration_ms, "Response indicates failure or missing data",
                                {"response": body}
                            )
                            all_passed = False
                    else:
                        self.framework.add_result(
                            test_name, TestType.INTEGRATION, TestStatus.FAILED,
                            duration_ms, "Response missing body"
                        )
                        all_passed = False
                else:
                    self.framework.add_result(
                        test_name, TestType.INTEGRATION, TestStatus.FAILED,
                        duration_ms, f"Lambda returned status {response.get('StatusCode')}"
                    )
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.framework.add_result(
                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                    duration_ms, f"Test failed with exception: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_error_handling_scenarios(self) -> bool:
        """Test error handling scenarios."""
        error_scenarios = [
            {
                "name": "Invalid Time Period",
                "payload": {"time_period": "INVALID_PERIOD"},
                "endpoint": "/cost-analysis",
                "expected_error": "ValueError"
            },
            {
                "name": "Invalid Resource Type",
                "payload": {"resource_type": "invalid_type", "region": "us-east-1"},
                "endpoint": "/resource-inventory",
                "expected_error": "ValueError"
            },
            {
                "name": "Invalid Region",
                "payload": {"region": "invalid-region", "assessment_type": "security_groups"},
                "endpoint": "/security-assessment",
                "expected_error": "ValueError"
            },
            {
                "name": "Missing Required Parameters",
                "payload": {},
                "endpoint": "/cost-analysis",
                "expected_error": "KeyError"
            }
        ]
        
        all_passed = True
        
        for scenario in error_scenarios:
            test_name = f"Error Handling - {scenario['name']}"
            start_time = time.time()
            
            try:
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": scenario["endpoint"],
                    "body": json.dumps(scenario["payload"])
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                response_data = json.loads(response['Payload'].read())
                
                # For error scenarios, we expect either a 500 status or an error response
                if response.get('StatusCode') == 200:
                    if 'body' in response_data:
                        body = json.loads(response_data['body'])
                        if not body.get('success') and 'error' in body:
                            # This is a properly handled error
                            error_info = body['error']
                            if scenario['expected_error'] in error_info.get('error_type', ''):
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.PASSED,
                                    duration_ms, f"Error properly handled: {error_info.get('user_message', '')}",
                                    {"error_type": error_info.get('error_type'), "user_message": error_info.get('user_message')}
                                )
                            else:
                                self.framework.add_result(
                                    test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                    duration_ms, f"Unexpected error type: {error_info.get('error_type')}",
                                    {"expected": scenario['expected_error'], "actual": error_info.get('error_type')}
                                )
                                all_passed = False
                        else:
                            # Request succeeded when it should have failed
                            self.framework.add_result(
                                test_name, TestType.INTEGRATION, TestStatus.FAILED,
                                duration_ms, "Request succeeded when error was expected",
                                {"response": body}
                            )
                            all_passed = False
                    else:
                        self.framework.add_result(
                            test_name, TestType.INTEGRATION, TestStatus.FAILED,
                            duration_ms, "Response missing body"
                        )
                        all_passed = False
                else:
                    # Lambda returned error status - this might be expected
                    self.framework.add_result(
                        test_name, TestType.INTEGRATION, TestStatus.PASSED,
                        duration_ms, f"Lambda returned error status as expected: {response.get('StatusCode')}",
                        {"status_code": response.get('StatusCode')}
                    )
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                # For error scenarios, exceptions might be expected
                if scenario['expected_error'] in str(type(e).__name__):
                    self.framework.add_result(
                        test_name, TestType.INTEGRATION, TestStatus.PASSED,
                        duration_ms, f"Expected exception occurred: {str(e)}"
                    )
                else:
                    self.framework.add_result(
                        test_name, TestType.INTEGRATION, TestStatus.FAILED,
                        duration_ms, f"Unexpected exception: {str(e)}"
                    )
                    all_passed = False
        
        return all_passed
    
    def test_bedrock_agent_scenarios(self) -> bool:
        """Test specific Bedrock Agent conversation scenarios."""
        if not self.framework.bedrock_agent_id:
            self.framework.add_result(
                "Bedrock Agent Scenarios", TestType.END_TO_END, TestStatus.SKIPPED,
                0, "Bedrock Agent not available"
            )
            return False
        
        conversation_scenarios = [
            {
                "name": "Cost Optimization Query",
                "query": "What are my highest AWS costs this month and how can I optimize them?",
                "expected_tools": ["getCostAnalysis", "getIdleResources"],
                "min_response_length": 100
            },
            {
                "name": "Security Assessment Query",
                "query": "Check my AWS account for security vulnerabilities and compliance issues",
                "expected_tools": ["getSecurityAssessment", "checkEncryptionStatus"],
                "min_response_length": 100
            },
            {
                "name": "Resource Inventory Query",
                "query": "Show me all my EC2 instances and their current status across all regions",
                "expected_tools": ["getResourceInventory", "getResourceHealth"],
                "min_response_length": 50
            },
            {
                "name": "Multi-step Analysis",
                "query": "Give me a comprehensive overview of my AWS environment including costs, resources, and security",
                "expected_tools": ["getCostAnalysis", "getResourceInventory", "getSecurityAssessment"],
                "min_response_length": 200
            }
        ]
        
        all_passed = True
        
        for scenario in conversation_scenarios:
            test_name = f"Bedrock Conversation - {scenario['name']}"
            start_time = time.time()
            
            try:
                session_id = f"test-session-{int(time.time())}"
                
                response = self.framework.bedrock_agent_client.invoke_agent(
                    agentId=self.framework.bedrock_agent_id,
                    agentAliasId=self.framework.bedrock_agent_alias_id,
                    sessionId=session_id,
                    inputText=scenario['query']
                )
                
                # Process streaming response
                response_text = ""
                tool_calls = []
                
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            response_text += chunk['bytes'].decode('utf-8')
                    elif 'trace' in event:
                        # Extract tool usage information from trace
                        trace = event['trace']
                        if 'orchestrationTrace' in trace:
                            orch_trace = trace['orchestrationTrace']
                            if 'invocationInput' in orch_trace:
                                tool_calls.append(orch_trace['invocationInput'])
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Validate response
                response_valid = len(response_text) >= scenario['min_response_length']
                
                if response_valid:
                    self.framework.add_result(
                        test_name, TestType.END_TO_END, TestStatus.PASSED,
                        duration_ms, f"Conversation completed successfully ({len(response_text)} chars)",
                        {
                            "query": scenario['query'],
                            "response_length": len(response_text),
                            "tool_calls": len(tool_calls),
                            "session_id": session_id
                        }
                    )
                else:
                    self.framework.add_result(
                        test_name, TestType.END_TO_END, TestStatus.FAILED,
                        duration_ms, f"Response too short: {len(response_text)} chars (min: {scenario['min_response_length']})",
                        {"response_length": len(response_text), "min_required": scenario['min_response_length']}
                    )
                    all_passed = False
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.framework.add_result(
                    test_name, TestType.END_TO_END, TestStatus.FAILED,
                    duration_ms, f"Bedrock Agent conversation failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def run_all_scenarios(self) -> bool:
        """Run all specific test scenarios."""
        scenario_suites = [
            ("Cost Analysis Scenarios", self.test_cost_analysis_scenarios),
            ("Resource Discovery Scenarios", self.test_resource_discovery_scenarios),
            ("Security Assessment Scenarios", self.test_security_assessment_scenarios),
            ("Error Handling Scenarios", self.test_error_handling_scenarios),
            ("Bedrock Agent Scenarios", self.test_bedrock_agent_scenarios),
        ]
        
        all_passed = True
        
        for suite_name, test_function in scenario_suites:
            print(f"\n🔍 Running {suite_name}...")
            try:
                suite_passed = test_function()
                if not suite_passed:
                    all_passed = False
            except Exception as e:
                print(f"❌ {suite_name} failed with exception: {e}")
                all_passed = False
        
        return all_passed


if __name__ == "__main__":
    # Example usage
    framework = IntegrationTestFramework(environment="dev")
    framework.load_stack_outputs()
    
    scenarios = SpecificTestScenarios(framework)
    scenarios.run_all_scenarios()
    
    summary = framework.run_all_tests()
    framework.generate_report(summary)