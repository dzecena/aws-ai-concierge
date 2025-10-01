"""
AWS AI Concierge Performance Benchmarking
Detailed performance testing to validate response time requirements
"""

import time
import json
import statistics
import boto3
import asyncio
import concurrent.futures
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class BenchmarkResult:
    """Performance benchmark result."""
    test_name: str
    operation: str
    payload: Dict[str, Any]
    duration_ms: float
    success: bool
    error_message: str = ""
    response_size_bytes: int = 0


class PerformanceBenchmark:
    """Performance benchmarking for AWS AI Concierge."""
    
    def __init__(self, environment: str = "dev", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.function_name = f"aws-ai-concierge-tools-{environment}"
        
        # Performance thresholds
        self.simple_query_threshold_ms = 5000  # 5 seconds
        self.complex_query_threshold_ms = 15000  # 15 seconds
        
        self.results: List[BenchmarkResult] = []
    
    def benchmark_operation(self, test_name: str, operation: str, payload: Dict[str, Any], 
                          iterations: int = 10) -> List[BenchmarkResult]:
        """Benchmark a specific operation multiple times."""
        print(f"🔍 Benchmarking {test_name} ({iterations} iterations)...")
        
        iteration_results = []
        
        for i in range(iterations):
            start_time = time.time()
            success = False
            error_message = ""
            response_size = 0
            
            try:
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": operation,
                    "body": json.dumps(payload)
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.get('StatusCode') == 200:
                    response_data = json.loads(response['Payload'].read())
                    response_size = len(json.dumps(response_data))
                    success = True
                else:
                    error_message = f"Lambda returned status {response.get('StatusCode')}"
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_message = str(e)
            
            result = BenchmarkResult(
                test_name=f"{test_name} - Iteration {i+1}",
                operation=operation,
                payload=payload,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                response_size_bytes=response_size
            )
            
            iteration_results.append(result)
            self.results.append(result)
            
            # Brief pause between iterations
            time.sleep(0.1)
        
        return iteration_results
    
    def benchmark_simple_queries(self) -> Dict[str, Any]:
        """Benchmark simple queries (should complete in < 5s)."""
        simple_queries = [
            {
                "name": "Basic Cost Analysis",
                "operation": "/cost-analysis",
                "payload": {"time_period": "MONTHLY"}
            },
            {
                "name": "EC2 Instance Count",
                "operation": "/resource-inventory",
                "payload": {"resource_type": "ec2", "region": "us-east-1"}
            },
            {
                "name": "S3 Bucket List",
                "operation": "/resource-inventory",
                "payload": {"resource_type": "s3"}
            },
            {
                "name": "Basic Security Check",
                "operation": "/security-assessment",
                "payload": {"region": "us-east-1", "assessment_type": "security_groups"}
            }
        ]
        
        simple_results = {}
        
        for query in simple_queries:
            results = self.benchmark_operation(
                query["name"], 
                query["operation"], 
                query["payload"], 
                iterations=20
            )
            
            # Analyze results
            successful_results = [r for r in results if r.success]
            if successful_results:
                durations = [r.duration_ms for r in successful_results]
                
                analysis = {
                    "total_iterations": len(results),
                    "successful_iterations": len(successful_results),
                    "success_rate": len(successful_results) / len(results) * 100,
                    "min_time_ms": min(durations),
                    "max_time_ms": max(durations),
                    "avg_time_ms": statistics.mean(durations),
                    "median_time_ms": statistics.median(durations),
                    "p95_time_ms": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                    "p99_time_ms": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
                    "meets_sla": all(d <= self.simple_query_threshold_ms for d in durations),
                    "sla_violations": sum(1 for d in durations if d > self.simple_query_threshold_ms),
                    "threshold_ms": self.simple_query_threshold_ms
                }
                
                simple_results[query["name"]] = analysis
                
                # Print summary
                sla_status = "✅ PASS" if analysis["meets_sla"] else "❌ FAIL"
                print(f"  {query['name']}: {sla_status} (P95: {analysis['p95_time_ms']:.1f}ms, Avg: {analysis['avg_time_ms']:.1f}ms)")
            else:
                simple_results[query["name"]] = {"error": "All iterations failed"}
                print(f"  {query['name']}: ❌ ALL FAILED")
        
        return simple_results
    
    def benchmark_complex_queries(self) -> Dict[str, Any]:
        """Benchmark complex queries (should complete in < 15s)."""
        complex_queries = [
            {
                "name": "Detailed Cost Analysis",
                "operation": "/cost-analysis",
                "payload": {
                    "time_period": "MONTHLY",
                    "granularity": "DAILY",
                    "group_by": "SERVICE"
                }
            },
            {
                "name": "Multi-Region Resource Discovery",
                "operation": "/resource-inventory",
                "payload": {
                    "resource_type": "ec2",
                    "region": "all"
                }
            },
            {
                "name": "Comprehensive Security Assessment",
                "operation": "/security-assessment",
                "payload": {
                    "region": "us-east-1",
                    "assessment_type": "comprehensive"
                }
            },
            {
                "name": "Idle Resource Analysis",
                "operation": "/idle-resources",
                "payload": {
                    "region": "us-east-1",
                    "include_recommendations": True
                }
            }
        ]
        
        complex_results = {}
        
        for query in complex_queries:
            results = self.benchmark_operation(
                query["name"], 
                query["operation"], 
                query["payload"], 
                iterations=10
            )
            
            # Analyze results
            successful_results = [r for r in results if r.success]
            if successful_results:
                durations = [r.duration_ms for r in successful_results]
                
                analysis = {
                    "total_iterations": len(results),
                    "successful_iterations": len(successful_results),
                    "success_rate": len(successful_results) / len(results) * 100,
                    "min_time_ms": min(durations),
                    "max_time_ms": max(durations),
                    "avg_time_ms": statistics.mean(durations),
                    "median_time_ms": statistics.median(durations),
                    "p95_time_ms": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                    "p99_time_ms": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
                    "meets_sla": all(d <= self.complex_query_threshold_ms for d in durations),
                    "sla_violations": sum(1 for d in durations if d > self.complex_query_threshold_ms),
                    "threshold_ms": self.complex_query_threshold_ms
                }
                
                complex_results[query["name"]] = analysis
                
                # Print summary
                sla_status = "✅ PASS" if analysis["meets_sla"] else "❌ FAIL"
                print(f"  {query['name']}: {sla_status} (P95: {analysis['p95_time_ms']:.1f}ms, Avg: {analysis['avg_time_ms']:.1f}ms)")
            else:
                complex_results[query["name"]] = {"error": "All iterations failed"}
                print(f"  {query['name']}: ❌ ALL FAILED")
        
        return complex_results
    
    def benchmark_concurrent_load(self, concurrent_users: int = 20, requests_per_user: int = 5) -> Dict[str, Any]:
        """Benchmark concurrent load performance."""
        print(f"🔍 Benchmarking concurrent load ({concurrent_users} users, {requests_per_user} requests each)...")
        
        def make_concurrent_request(user_id: int, request_id: int) -> BenchmarkResult:
            """Make a single concurrent request."""
            start_time = time.time()
            
            try:
                payload = {
                    "time_period": "MONTHLY",
                    "user_id": f"load-test-user-{user_id}",
                    "request_id": f"req-{request_id}"
                }
                
                lambda_payload = {
                    "httpMethod": "POST",
                    "path": "/cost-analysis",
                    "body": json.dumps(payload)
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(lambda_payload)
                )
                
                duration_ms = (time.time() - start_time) * 1000
                success = response.get('StatusCode') == 200
                
                return BenchmarkResult(
                    test_name=f"Concurrent Load - User {user_id} Request {request_id}",
                    operation="/cost-analysis",
                    payload=payload,
                    duration_ms=duration_ms,
                    success=success,
                    error_message="" if success else f"Status: {response.get('StatusCode')}"
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                return BenchmarkResult(
                    test_name=f"Concurrent Load - User {user_id} Request {request_id}",
                    operation="/cost-analysis",
                    payload=payload,
                    duration_ms=duration_ms,
                    success=False,
                    error_message=str(e)
                )
        
        # Execute concurrent requests
        start_time = time.time()
        concurrent_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_concurrent_request, user_id, request_id)
                    futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                concurrent_results.append(result)
                self.results.append(result)
        
        total_duration = (time.time() - start_time) * 1000
        
        # Analyze concurrent results
        successful_results = [r for r in concurrent_results if r.success]
        durations = [r.duration_ms for r in successful_results]
        
        if durations:
            analysis = {
                "total_requests": len(concurrent_results),
                "successful_requests": len(successful_results),
                "failed_requests": len(concurrent_results) - len(successful_results),
                "success_rate": len(successful_results) / len(concurrent_results) * 100,
                "total_execution_time_ms": total_duration,
                "requests_per_second": len(concurrent_results) / (total_duration / 1000),
                "min_time_ms": min(durations),
                "max_time_ms": max(durations),
                "avg_time_ms": statistics.mean(durations),
                "median_time_ms": statistics.median(durations),
                "p95_time_ms": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                "p99_time_ms": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
                "concurrent_users": concurrent_users,
                "requests_per_user": requests_per_user
            }
            
            print(f"  Success Rate: {analysis['success_rate']:.1f}%")
            print(f"  Requests/Second: {analysis['requests_per_second']:.1f}")
            print(f"  P95 Response Time: {analysis['p95_time_ms']:.1f}ms")
            print(f"  Average Response Time: {analysis['avg_time_ms']:.1f}ms")
            
            return analysis
        else:
            return {"error": "All concurrent requests failed"}
    
    def generate_performance_report(self, output_file: str = None) -> str:
        """Generate comprehensive performance report."""
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"performance-benchmark-{self.environment}-{timestamp}.json"
        
        print("\n🚀 Running Performance Benchmark Suite")
        print("=" * 60)
        
        # Run benchmarks
        simple_results = self.benchmark_simple_queries()
        print()
        complex_results = self.benchmark_complex_queries()
        print()
        concurrent_results = self.benchmark_concurrent_load()
        
        # Generate summary
        report = {
            "benchmark_info": {
                "environment": self.environment,
                "region": self.region,
                "function_name": self.function_name,
                "timestamp": datetime.utcnow().isoformat(),
                "simple_query_threshold_ms": self.simple_query_threshold_ms,
                "complex_query_threshold_ms": self.complex_query_threshold_ms
            },
            "simple_queries": simple_results,
            "complex_queries": complex_results,
            "concurrent_load": concurrent_results,
            "raw_results": [
                {
                    "test_name": r.test_name,
                    "operation": r.operation,
                    "duration_ms": r.duration_ms,
                    "success": r.success,
                    "error_message": r.error_message,
                    "response_size_bytes": r.response_size_bytes
                } for r in self.results
            ]
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.print_performance_summary(report)
        
        return output_file
    
    def print_performance_summary(self, report: Dict[str, Any]):
        """Print performance benchmark summary."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        
        info = report["benchmark_info"]
        print(f"Environment: {info['environment']}")
        print(f"Function: {info['function_name']}")
        print(f"Simple Query SLA: {info['simple_query_threshold_ms']}ms")
        print(f"Complex Query SLA: {info['complex_query_threshold_ms']}ms")
        print()
        
        # Simple queries summary
        print("🔍 Simple Queries (< 5s SLA):")
        simple_passed = 0
        simple_total = 0
        for name, results in report["simple_queries"].items():
            if "error" not in results:
                simple_total += 1
                if results["meets_sla"]:
                    simple_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                print(f"  {name}: {status} (P95: {results['p95_time_ms']:.1f}ms)")
            else:
                print(f"  {name}: ❌ ERROR")
        
        # Complex queries summary
        print("\n🔍 Complex Queries (< 15s SLA):")
        complex_passed = 0
        complex_total = 0
        for name, results in report["complex_queries"].items():
            if "error" not in results:
                complex_total += 1
                if results["meets_sla"]:
                    complex_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                print(f"  {name}: {status} (P95: {results['p95_time_ms']:.1f}ms)")
            else:
                print(f"  {name}: ❌ ERROR")
        
        # Concurrent load summary
        print("\n🔍 Concurrent Load Test:")
        concurrent = report["concurrent_load"]
        if "error" not in concurrent:
            print(f"  Success Rate: {concurrent['success_rate']:.1f}%")
            print(f"  Requests/Second: {concurrent['requests_per_second']:.1f}")
            print(f"  P95 Response Time: {concurrent['p95_time_ms']:.1f}ms")
        else:
            print("  ❌ ERROR: Concurrent load test failed")
        
        # Overall assessment
        print("\n🎯 Overall Assessment:")
        simple_sla_rate = (simple_passed / simple_total * 100) if simple_total > 0 else 0
        complex_sla_rate = (complex_passed / complex_total * 100) if complex_total > 0 else 0
        
        print(f"  Simple Query SLA Compliance: {simple_sla_rate:.1f}% ({simple_passed}/{simple_total})")
        print(f"  Complex Query SLA Compliance: {complex_sla_rate:.1f}% ({complex_passed}/{complex_total})")
        
        overall_pass = simple_sla_rate >= 95 and complex_sla_rate >= 95
        if overall_pass:
            print("  🎉 PERFORMANCE REQUIREMENTS MET!")
        else:
            print("  ⚠️  PERFORMANCE REQUIREMENTS NOT MET")
        
        print("=" * 60)


if __name__ == "__main__":
    # Example usage
    benchmark = PerformanceBenchmark(environment="dev")
    report_file = benchmark.generate_performance_report()
    print(f"\n📄 Performance report saved to: {report_file}")