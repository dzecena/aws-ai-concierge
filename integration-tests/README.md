# AWS AI Concierge Integration Testing Suite

This directory contains comprehensive integration tests for the AWS AI Concierge system, designed to validate end-to-end functionality, performance requirements, and system reliability.

## 🎯 Testing Objectives

The integration testing suite validates:

1. **End-to-End Workflows**: Complete user journey from query to response
2. **Performance Requirements**: 5s for simple queries, 15s for complex queries
3. **Concurrent User Handling**: System scalability under load
4. **Audit Logging Compliance**: Complete audit trail for regulatory requirements
5. **Error Handling**: Graceful error management and user-friendly messages
6. **API Functionality**: All tool endpoints working correctly
7. **Bedrock Agent Integration**: AI assistant functionality and tool selection

## 📁 Test Suite Components

### Core Testing Framework
- **`test_framework.py`**: Main integration testing framework with comprehensive test orchestration
- **`test_scenarios.py`**: Specific test scenarios for different functionality areas
- **`performance_benchmark.py`**: Detailed performance testing and SLA validation
- **`simple_test_runner.py`**: Lightweight test runner with minimal dependencies

### Test Execution Scripts
- **`run_integration_tests.py`**: Comprehensive test runner with full reporting
- **`README.md`**: This documentation file

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate credentials
- Python 3.8+ with boto3 installed
- Deployed AWS AI Concierge infrastructure
- CDK stack outputs file (optional but recommended)

### Basic Test Execution

```bash
# Simple integration tests (minimal dependencies)
python simple_test_runner.py --environment dev --region us-east-1

# Comprehensive integration tests
python run_integration_tests.py --environment dev --region us-east-1

# Performance benchmarking
python performance_benchmark.py
```

### Advanced Test Execution

```bash
# Full test suite with custom parameters
python run_integration_tests.py \
    --environment prod \
    --region us-east-1 \
    --concurrent-users 20 \
    --requests-per-user 10 \
    --report-dir ./reports

# Skip specific test types
python run_integration_tests.py \
    --environment dev \
    --skip-bedrock \
    --skip-load

# Verbose output for debugging
python run_integration_tests.py --environment dev --verbose
```

## 📊 Test Categories

### 1. Core Integration Tests
- **Lambda Function Accessibility**: Verify function exists and is active
- **Direct Lambda Invocation**: Test function invocation and response
- **API Gateway Endpoints**: Validate all REST API endpoints
- **Response Structure Validation**: Ensure consistent response formats

### 2. Functional Test Scenarios
- **Cost Analysis Scenarios**: Various cost analysis configurations
- **Resource Discovery Scenarios**: Multi-service resource inventory
- **Security Assessment Scenarios**: Security checks and compliance
- **Error Handling Scenarios**: Invalid input and error recovery

### 3. Performance Testing
- **Simple Query Performance**: < 5 second response time validation
- **Complex Query Performance**: < 15 second response time validation
- **Concurrent User Load**: Multi-user scalability testing
- **Response Time Distribution**: P95, P99 performance metrics

### 4. End-to-End Testing
- **Bedrock Agent Integration**: AI assistant conversation flows
- **Tool Selection Validation**: Correct tool usage for queries
- **Multi-step Workflows**: Complex query processing
- **Natural Language Processing**: Query understanding and response

### 5. Compliance and Audit
- **Audit Log Verification**: Complete audit trail validation
- **Structured Logging**: JSON log format compliance
- **Performance Monitoring**: SLA compliance tracking
- **Error Tracking**: Error categorization and reporting

## 📈 Performance Requirements

### Response Time SLAs
- **Simple Queries**: ≤ 5 seconds (95th percentile)
  - Basic cost analysis
  - Resource counts
  - Simple security checks
  
- **Complex Queries**: ≤ 15 seconds (95th percentile)
  - Detailed cost breakdowns
  - Multi-region resource discovery
  - Comprehensive security assessments

### Scalability Requirements
- **Concurrent Users**: Support 10+ simultaneous users
- **Success Rate**: ≥ 95% success rate under normal load
- **Error Rate**: < 5% error rate during peak usage

## 🔍 Test Execution Examples

### Example 1: Development Environment Testing
```bash
# Quick validation of dev environment
python simple_test_runner.py --environment dev

# Expected output:
# ✅ PASS Lambda Function Accessibility: Function is active and accessible
# ✅ PASS Basic Lambda Invocation: Function invoked successfully
# ✅ PASS Cost Analysis Endpoint: Cost analysis completed successfully
# ✅ PASS Resource Inventory Endpoint: Found 5 resources
# ✅ PASS Security Assessment Endpoint: Assessment completed: 3 findings, risk score: 25
# ✅ PASS Performance - Simple Query: Meets 5s performance requirement (2.34s)
# ✅ PASS Error Handling: Error properly handled and formatted
```

### Example 2: Production Environment Validation
```bash
# Comprehensive production testing
python run_integration_tests.py \
    --environment prod \
    --concurrent-users 50 \
    --requests-per-user 10

# Expected output includes:
# 🔍 Phase 1: Core Integration Tests
# 🔍 Phase 2: Functional Test Scenarios  
# 🔍 Phase 3: Performance Testing
# 🔍 Phase 4: End-to-End Testing
# 🔍 Phase 5: Compliance and Audit
# 🎉 ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!
```

### Example 3: Performance Benchmarking
```bash
# Detailed performance analysis
python performance_benchmark.py

# Expected output:
# 🔍 Benchmarking Basic Cost Analysis (20 iterations)...
# 🔍 Benchmarking EC2 Instance Count (20 iterations)...
# 📊 PERFORMANCE BENCHMARK SUMMARY
# Simple Query SLA Compliance: 100.0% (4/4)
# Complex Query SLA Compliance: 100.0% (4/4)
# 🎉 PERFORMANCE REQUIREMENTS MET!
```

## 📄 Test Reports

### Report Types Generated
1. **JSON Reports**: Machine-readable test results with detailed metrics
2. **HTML Reports**: Human-readable visual reports with charts and summaries
3. **Performance Reports**: Detailed performance analysis with SLA compliance
4. **Console Output**: Real-time test execution feedback

### Report Locations
- **Default Directory**: `./reports/`
- **Naming Convention**: `integration-test-report-{environment}-{timestamp}.{format}`
- **Performance Reports**: `performance-benchmark-{environment}-{timestamp}.json`

### Sample Report Structure
```json
{
  "environment": "dev",
  "region": "us-east-1",
  "total_tests": 25,
  "passed_tests": 24,
  "failed_tests": 1,
  "success_rate": 96.0,
  "test_execution": {
    "start_time": "2025-10-01T22:30:00.000Z",
    "end_time": "2025-10-01T22:35:30.000Z",
    "execution_time_seconds": 330.5
  },
  "suite_results": {
    "Lambda Direct Invocation": true,
    "API Gateway Endpoints": true,
    "Performance Requirements": true,
    "Concurrent Users": true,
    "Audit Logging": true
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Lambda Function Not Found
```
❌ Lambda Function Accessibility: Error: Function not found
```
**Solution**: Verify the function name and ensure CDK deployment completed successfully.

#### 2. Permission Denied
```
❌ Basic Lambda Invocation: Error: AccessDenied
```
**Solution**: Check AWS credentials and IAM permissions for Lambda invocation.

#### 3. Performance Test Failures
```
❌ Performance - Simple Query: Exceeds 5s performance requirement (7.23s)
```
**Solution**: Check Lambda memory allocation, cold start issues, or AWS service latency.

#### 4. Bedrock Agent Not Available
```
⏭️ Bedrock Agent Test: SKIPPED - Bedrock Agent IDs not available
```
**Solution**: Ensure Bedrock Agent is deployed and CDK outputs are loaded correctly.

### Debug Commands

```bash
# Check Lambda function status
aws lambda get-function --function-name aws-ai-concierge-tools-dev

# View recent Lambda logs
aws logs tail /aws/lambda/aws-ai-concierge-tools-dev --follow

# Test Lambda function directly
aws lambda invoke --function-name aws-ai-concierge-tools-dev \
    --payload '{"httpMethod":"POST","path":"/cost-analysis","body":"{\"time_period\":\"MONTHLY\"}"}' \
    response.json
```

## 🔧 Customization

### Adding New Test Scenarios
1. Create new test methods in `test_scenarios.py`
2. Add test cases to the appropriate test suite
3. Update the test runner to include new scenarios
4. Document expected behavior and validation criteria

### Modifying Performance Thresholds
```python
# In test_framework.py
self.simple_query_threshold_ms = 3000  # 3 seconds instead of 5
self.complex_query_threshold_ms = 10000  # 10 seconds instead of 15
```

### Custom Test Environments
```python
# Create environment-specific test configurations
test_configs = {
    "dev": {"concurrent_users": 5, "iterations": 10},
    "staging": {"concurrent_users": 20, "iterations": 20},
    "prod": {"concurrent_users": 50, "iterations": 50}
}
```

## 📋 Test Checklist

Before considering integration testing complete, ensure:

- [ ] All core Lambda endpoints respond correctly
- [ ] Performance requirements are met (5s/15s SLAs)
- [ ] Concurrent user scenarios pass with >95% success rate
- [ ] Error handling provides user-friendly messages
- [ ] Audit logging captures all required events
- [ ] Bedrock Agent integration works end-to-end
- [ ] All test reports are generated successfully
- [ ] No critical security vulnerabilities detected

## 🎯 Success Criteria

Integration testing is considered successful when:

1. **Functional Tests**: 100% pass rate for core functionality
2. **Performance Tests**: 95%+ queries meet SLA requirements
3. **Load Tests**: 95%+ success rate under concurrent load
4. **End-to-End Tests**: Complete workflows function correctly
5. **Compliance Tests**: All audit requirements are met

## 📞 Support

For integration testing issues:
1. Check the troubleshooting section above
2. Review CloudWatch logs for detailed error information
3. Validate AWS permissions and resource availability
4. Ensure all prerequisites are met
5. Run tests with `--verbose` flag for detailed output