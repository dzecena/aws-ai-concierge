"""
Cost analysis tools for AWS AI Concierge
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
from botocore.exceptions import ClientError
from utils.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class CostAnalysisHandler:
    """Handles cost analysis and optimization recommendations."""
    
    @staticmethod
    def _normalize_time_period(time_period: str) -> str:
        """
        Normalize natural language time periods to expected format.
        
        Args:
            time_period: Natural language time period
            
        Returns:
            Normalized time period (DAILY, MONTHLY, YEARLY)
        """
        time_period_lower = time_period.lower().strip()
        
        # Daily patterns
        if any(word in time_period_lower for word in ['today', 'daily', 'day', 'yesterday']):
            return 'DAILY'
        
        # Monthly patterns  
        if any(word in time_period_lower for word in [
            'month', 'monthly', 'this month', 'current month', 
            'last month', 'past month', '30 days', 'last 30 days'
        ]):
            return 'MONTHLY'
        
        # Yearly patterns
        if any(word in time_period_lower for word in [
            'year', 'yearly', 'annual', 'this year', 'current year',
            'last year', 'past year', '12 months', 'last 12 months'
        ]):
            return 'YEARLY'
        
        # Default to original if no match (will be validated later)
        return time_period.upper()
    
    def __init__(self, aws_clients):
        self.aws_clients = aws_clients
        self.audit_logger = AuditLogger()
    
    def get_cost_analysis(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Analyze AWS costs and spending patterns with intelligent date parsing.
        
        Args:
            params: Parameters including time_period, granularity, group_by
            request_id: Request ID for tracking
            
        Returns:
            Cost analysis results
        """
        logger.info(f"[{request_id}] Starting cost analysis with params: {params}")
        
        try:
            # Extract and validate parameters
            time_period = params.get('time_period', 'MONTHLY')
            granularity = params.get('granularity', 'DAILY')
            group_by = params.get('group_by', 'SERVICE')
            
            # Check if this is a specific month/year query (e.g., "december_2024")
            parsed_dates = self._parse_specific_date(time_period, request_id)
            if parsed_dates:
                start_date, end_date = parsed_dates
                logger.info(f"[{request_id}] Using parsed dates: {start_date} to {end_date}")
                
                # Validate that the date range is not in the future
                current_date = datetime.utcnow().date()
                if start_date > current_date:
                    logger.warning(f"[{request_id}] Requested start date {start_date} is in the future")
                    return {
                        'total_cost': 0.0,
                        'currency': 'USD',
                        'time_period': f"{start_date} to {end_date}",
                        'group_by': group_by,
                        'breakdown': [],
                        'analysis_date': datetime.utcnow().isoformat(),
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'message': f'Cannot retrieve cost data for future dates. The requested period ({start_date.strftime("%B %Y")}) is in the future.',
                        'suggestion': 'Please specify a date range that is in the past or current month.',
                        'error_type': 'future_date'
                    }
            else:
                # Normalize natural language time periods
                time_period = self._normalize_time_period(time_period)
                
                # Calculate date range based on time period
                start_date, end_date = self._calculate_date_range(time_period)
            
            # Validate parameters
            valid_granularities = ['DAILY', 'MONTHLY']
            valid_group_by = ['SERVICE', 'REGION', 'USAGE_TYPE', 'INSTANCE_TYPE']
            
            # Validate parameters
            if granularity not in valid_granularities:
                raise ValueError(f"Invalid granularity '{granularity}'. Must be one of: {valid_granularities}")
            
            if group_by not in valid_group_by:
                raise ValueError(f"Invalid group_by '{group_by}'. Must be one of: {valid_group_by}")
            
            # Only validate time_period and calculate dates if we don't have parsed dates
            if not parsed_dates:
                valid_time_periods = ['DAILY', 'MONTHLY', 'YEARLY']
                
                if time_period not in valid_time_periods:
                    raise ValueError(f"Invalid time_period '{time_period}'. Must be one of: {valid_time_periods}")
                
                # Calculate date range based on time period
                end_date = datetime.now().date()
                if time_period == 'DAILY':
                    start_date = end_date - timedelta(days=1)
                    # For daily analysis, use DAILY granularity
                    granularity = 'DAILY'
                elif time_period == 'MONTHLY':
                    # Get current month data from 1st of month to today
                    start_date = end_date.replace(day=1)
                    # Cost Explorer requires end_date to be exclusive, so we use tomorrow
                    # But if we're on the 1st day of the month, we need at least 1 day of data
                    if start_date == end_date:
                        # If today is the 1st, we have no current month data yet
                        # Get previous month's complete data instead
                        if end_date.month == 1:
                            start_date = end_date.replace(year=end_date.year-1, month=12, day=1)
                            end_date = end_date.replace(year=end_date.year-1, month=12, day=31)
                        else:
                            start_date = end_date.replace(month=end_date.month-1, day=1)
                            # Get last day of previous month
                            import calendar
                            last_day = calendar.monthrange(end_date.year, end_date.month-1)[1]
                            end_date = end_date.replace(month=end_date.month-1, day=last_day)
                    else:
                        # Use current month data from 1st to today
                        # Note: Cost Explorer end date is exclusive, so we add 1 day
                        end_date = end_date + timedelta(days=1)
                elif time_period == 'YEARLY':
                    # Get current year data - but ensure start_date is before end_date
                    start_date = end_date.replace(month=1, day=1)
                    # If today is Jan 1st, get previous year's data instead
                    if start_date == end_date:
                        start_date = end_date.replace(year=end_date.year-1, month=1, day=1)
                        end_date = end_date.replace(year=end_date.year-1, month=12, day=31)
                    # For yearly analysis, use MONTHLY granularity for better performance
                    if granularity == 'DAILY':
                        granularity = 'MONTHLY'
            else:
                # For parsed dates, ensure end_date is exclusive for Cost Explorer
                end_date = end_date + timedelta(days=1)
            
            logger.info(f"[{request_id}] Analyzing costs from {start_date} to {end_date}")
            
            # Get Cost Explorer client
            ce_client = self.aws_clients.get_cost_explorer_client()
            
            # Build the Cost Explorer request
            cost_request = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': granularity,
                'Metrics': ['BlendedCost', 'UsageQuantity'],
                'GroupBy': [
                    {
                        'Type': 'DIMENSION',
                        'Key': group_by
                    }
                ]
            }
            
            # Execute the cost analysis with audit logging
            logger.info(f"[{request_id}] Executing Cost Explorer API call")
            response = self.aws_clients.make_api_call(
                client=ce_client,
                operation='get_cost_and_usage',
                request_id=request_id,
                **cost_request
            )
            
            # Process the response
            result = self._process_cost_response(response, time_period, group_by, start_date, end_date)
            
            # If Cost Explorer returns zero, try AWS Budgets API as fallback
            if result.get('total_cost', 0) == 0:
                logger.info(f"[{request_id}] Cost Explorer returned $0, trying AWS Budgets API fallback")
                budget_data = self._get_budget_costs(request_id)
                if budget_data and budget_data.get('total_cost', 0) > 0:
                    logger.info(f"[{request_id}] Using Budgets API data: ${budget_data.get('total_cost', 0):.2f}")
                    result = budget_data
                    result['data_source'] = 'AWS Budgets API (Cost Explorer data not yet available)'
                else:
                    result['message'] = 'Cost data is not yet available through Cost Explorer API. This is normal for recent charges which can take 8-24 hours to appear.'
                    result['suggestion'] = 'Try again in a few hours for more detailed cost breakdown.'
            
            # Log cost analysis activity
            self.audit_logger.log_cost_analysis(
                request_id=request_id,
                time_period=f"{start_date} to {end_date}",
                total_cost=result.get('total_cost', 0),
                currency='USD',
                optimization_opportunities=len(result.get('optimization_recommendations', []))
            )
            
            logger.info(f"[{request_id}] Cost analysis completed successfully - Total cost: ${result.get('total_cost', 0):.2f}")
            return result
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            logger.warning(f"[{request_id}] AWS Cost Explorer error: {error_code} - {error_message}")
            
            # Handle specific error cases with better messaging
            if 'end date past the beginning of next month' in error_message.lower():
                # Future date error
                return {
                    'total_cost': 0.0,
                    'currency': 'USD',
                    'time_period': time_period if not parsed_dates else f"{start_date} to {end_date}",
                    'group_by': group_by,
                    'breakdown': [],
                    'analysis_date': datetime.utcnow().isoformat(),
                    'start_date': start_date.isoformat() if 'start_date' in locals() else None,
                    'end_date': end_date.isoformat() if 'end_date' in locals() else None,
                    'message': f'Cannot retrieve cost data for future dates. The requested period appears to be in the future.',
                    'suggestion': 'Please specify a date range that is in the past or current month.',
                    'error_type': 'future_date'
                }
            elif error_code == 'DataUnavailableException':
                logger.warning(f"[{request_id}] Cost data unavailable for the specified period")
                # Try AWS Budgets API as fallback
                budget_data = self._get_budget_costs(request_id)
                if budget_data:
                    return budget_data
                
                # Return empty result with explanation
                return {
                    'total_cost': 0.0,
                    'currency': 'USD',
                    'time_period': time_period if not parsed_dates else f"{start_date} to {end_date}",
                    'group_by': group_by,
                    'breakdown': [],
                    'analysis_date': datetime.utcnow().isoformat(),
                    'start_date': start_date.isoformat() if 'start_date' in locals() else None,
                    'end_date': end_date.isoformat() if 'end_date' in locals() else None,
                    'message': 'Cost data is not available for the specified time period. Data may take up to 24 hours to appear.',
                    'suggestion': 'Try again in a few hours for more detailed cost breakdown.'
                }
            else:
                # Generic AWS error
                return {
                    'total_cost': 0.0,
                    'currency': 'USD',
                    'time_period': time_period if not parsed_dates else f"{start_date} to {end_date}",
                    'group_by': group_by,
                    'breakdown': [],
                    'analysis_date': datetime.utcnow().isoformat(),
                    'start_date': start_date.isoformat() if 'start_date' in locals() else None,
                    'end_date': end_date.isoformat() if 'end_date' in locals() else None,
                    'message': f'AWS Cost Explorer error: {error_message}',
                    'suggestion': 'Please try again or contact support if the issue persists.',
                    'error_type': 'aws_error'
                }
            logger.error(f"[{request_id}] AWS error in cost analysis: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error in cost analysis: {str(e)}")
            raise
    
    def get_idle_resources(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Identify idle or underutilized resources.
        
        Args:
            params: Parameters including region, cpu_threshold, days
            request_id: Request ID for tracking
            
        Returns:
            List of idle resources with potential savings
        """
        logger.info(f"[{request_id}] Starting idle resource analysis with params: {params}")
        
        try:
            region = params.get('region', 'us-east-1')
            cpu_threshold = float(params.get('cpu_threshold', 5.0))
            days = int(params.get('days', 7))
            
            # Validate parameters
            if cpu_threshold < 0 or cpu_threshold > 100:
                raise ValueError("CPU threshold must be between 0 and 100")
            
            if days < 1 or days > 30:
                raise ValueError("Analysis period must be between 1 and 30 days")
            
            logger.info(f"[{request_id}] Analyzing resources in {region} with CPU threshold {cpu_threshold}% over {days} days")
            
            # Get EC2 and CloudWatch clients
            ec2_client = self.aws_clients.get_ec2_client(region)
            cw_client = self.aws_clients.get_cloudwatch_client(region)
            
            # Get all running EC2 instances
            instances_response = ec2_client.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            idle_instances = []
            analyzed_instances = 0
            total_potential_savings = 0.0
            
            # Analyze each instance
            for reservation in instances_response['Reservations']:
                for instance in reservation['Instances']:
                    analyzed_instances += 1
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    launch_time = instance.get('LaunchTime')
                    
                    # Skip instances launched less than the analysis period
                    if launch_time:
                        instance_age = datetime.now(launch_time.tzinfo) - launch_time
                        if instance_age.days < days:
                            logger.debug(f"[{request_id}] Skipping {instance_id} - too new ({instance_age.days} days)")
                            continue
                    
                    # Get comprehensive metrics
                    metrics = self._get_instance_metrics(cw_client, instance_id, days, request_id)
                    
                    if metrics['avg_cpu'] is not None and metrics['avg_cpu'] < cpu_threshold:
                        # Estimate potential savings
                        estimated_monthly_cost = self._estimate_instance_cost(instance_type)
                        
                        # Determine optimization recommendation
                        recommendation = self._get_optimization_recommendation(
                            metrics, instance_type, estimated_monthly_cost
                        )
                        
                        idle_instance = {
                            'instance_id': instance_id,
                            'instance_type': instance_type,
                            'metrics': {
                                'average_cpu_utilization': round(metrics['avg_cpu'], 2),
                                'max_cpu_utilization': round(metrics['max_cpu'], 2) if metrics['max_cpu'] else None,
                                'average_network_in': round(metrics['avg_network_in'], 2) if metrics['avg_network_in'] else None,
                                'average_network_out': round(metrics['avg_network_out'], 2) if metrics['avg_network_out'] else None,
                                'data_points': metrics['data_points']
                            },
                            'launch_time': launch_time.isoformat() if launch_time else None,
                            'estimated_monthly_cost': estimated_monthly_cost,
                            'potential_monthly_savings': recommendation['potential_savings'],
                            'optimization_recommendation': recommendation['recommendation'],
                            'confidence_level': recommendation['confidence'],
                            'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                            'vpc_id': instance.get('VpcId'),
                            'subnet_id': instance.get('SubnetId'),
                            'availability_zone': instance.get('Placement', {}).get('AvailabilityZone')
                        }
                        
                        idle_instances.append(idle_instance)
                        total_potential_savings += recommendation['potential_savings']
            
            # Generate optimization insights
            optimization_insights = self._generate_idle_resource_insights(idle_instances, analyzed_instances)
            
            result = {
                'region': region,
                'analysis_period_days': days,
                'cpu_threshold_percent': cpu_threshold,
                'total_instances_analyzed': analyzed_instances,
                'idle_instances': idle_instances,
                'total_idle_instances': len(idle_instances),
                'potential_monthly_savings': round(total_potential_savings, 2),
                'optimization_insights': optimization_insights,
                'currency': 'USD',
                'analysis_date': datetime.utcnow().isoformat()
            }
            
            logger.info(f"[{request_id}] Found {len(idle_instances)} idle instances out of {analyzed_instances} analyzed")
            return result
            
        except ClientError as e:
            logger.error(f"[{request_id}] AWS error in idle resource analysis: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error in idle resource analysis: {str(e)}")
            raise
    
    def _process_cost_response(self, response: Dict[str, Any], time_period: str, group_by: str, start_date, end_date) -> Dict[str, Any]:
        """Process Cost Explorer response into structured format."""
        results_by_time = response.get('ResultsByTime', [])
        
        total_cost = 0.0
        breakdown = []
        daily_costs = []
        
        # Aggregate costs across time periods
        service_totals = {}
        
        for time_result in results_by_time:
            time_period_start = time_result.get('TimePeriod', {}).get('Start')
            time_period_end = time_result.get('TimePeriod', {}).get('End')
            
            # Track daily costs for trend analysis
            period_total = 0.0
            
            for group in time_result.get('Groups', []):
                service_name = group.get('Keys', ['Unknown'])[0]
                cost_amount = float(group.get('Metrics', {}).get('BlendedCost', {}).get('Amount', 0))
                usage_amount = float(group.get('Metrics', {}).get('UsageQuantity', {}).get('Amount', 0))
                
                if service_name not in service_totals:
                    service_totals[service_name] = {
                        'cost': 0.0,
                        'usage': 0.0,
                        'unit': group.get('Metrics', {}).get('UsageQuantity', {}).get('Unit', '')
                    }
                
                service_totals[service_name]['cost'] += cost_amount
                service_totals[service_name]['usage'] += usage_amount
                total_cost += cost_amount
                period_total += cost_amount
            
            # Add daily cost data
            if time_period_start and time_period_end:
                daily_costs.append({
                    'date': time_period_start,
                    'cost': round(period_total, 2)
                })
        
        # Create breakdown list
        for service_name, totals in service_totals.items():
            percentage = (totals['cost'] / total_cost * 100) if total_cost > 0 else 0
            breakdown.append({
                'service_name': service_name,
                'cost': round(totals['cost'], 2),
                'usage_quantity': round(totals['usage'], 2),
                'usage_unit': totals['unit'],
                'percentage': round(percentage, 2)
            })
        
        # Sort by cost descending
        breakdown.sort(key=lambda x: x['cost'], reverse=True)
        
        # Calculate cost trends
        cost_trend = self._calculate_cost_trend(daily_costs)
        
        # Generate cost optimization insights
        optimization_insights = self._generate_cost_insights(breakdown, total_cost)
        
        return {
            'total_cost': round(total_cost, 2),
            'currency': 'USD',
            'time_period': time_period,
            'group_by': group_by,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'breakdown': breakdown,
            'daily_costs': daily_costs,
            'cost_trend': cost_trend,
            'optimization_insights': optimization_insights,
            'analysis_date': datetime.utcnow().isoformat()
        }
    
    def _calculate_cost_trend(self, daily_costs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost trend from daily cost data."""
        if len(daily_costs) < 2:
            return {'trend': 'insufficient_data', 'change_percentage': 0}
        
        # Sort by date
        daily_costs.sort(key=lambda x: x['date'])
        
        first_cost = daily_costs[0]['cost']
        last_cost = daily_costs[-1]['cost']
        
        if first_cost == 0:
            return {'trend': 'no_baseline', 'change_percentage': 0}
        
        change_percentage = ((last_cost - first_cost) / first_cost) * 100
        
        if change_percentage > 10:
            trend = 'increasing'
        elif change_percentage < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_percentage': round(change_percentage, 2),
            'first_period_cost': first_cost,
            'last_period_cost': last_cost
        }
    
    def _generate_cost_insights(self, breakdown: List[Dict[str, Any]], total_cost: float) -> List[str]:
        """Generate cost optimization insights based on spending patterns."""
        insights = []
        
        if not breakdown or total_cost == 0:
            return ["No cost data available for analysis"]
        
        # Top service analysis
        top_service = breakdown[0]
        if top_service['percentage'] > 50:
            insights.append(f"{top_service['service_name']} accounts for {top_service['percentage']:.1f}% of your costs - consider optimization opportunities")
        
        # High-cost services
        high_cost_services = [s for s in breakdown if s['cost'] > 100]
        if len(high_cost_services) > 3:
            insights.append(f"You have {len(high_cost_services)} services with costs over $100 - review for optimization potential")
        
        # EC2 specific insights
        ec2_service = next((s for s in breakdown if 'EC2' in s['service_name']), None)
        if ec2_service and ec2_service['percentage'] > 30:
            insights.append("EC2 is a significant cost driver - consider Reserved Instances or Spot Instances for savings")
        
        # S3 specific insights
        s3_service = next((s for s in breakdown if 'S3' in s['service_name']), None)
        if s3_service and s3_service['cost'] > 50:
            insights.append("Review S3 storage classes and lifecycle policies to optimize storage costs")
        
        # Data transfer insights
        data_transfer = next((s for s in breakdown if 'Data Transfer' in s['service_name'] or 'CloudFront' in s['service_name']), None)
        if data_transfer and data_transfer['cost'] > 20:
            insights.append("Data transfer costs detected - consider CloudFront or optimize data transfer patterns")
        
        if not insights:
            insights.append("Your cost distribution looks reasonable - continue monitoring for optimization opportunities")
        
        return insights
    
    def _get_instance_metrics(self, cw_client, instance_id: str, days: int, request_id: str) -> Dict[str, Optional[float]]:
        """Get comprehensive metrics for an instance over specified days."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            metrics = {
                'avg_cpu': None,
                'max_cpu': None,
                'avg_network_in': None,
                'avg_network_out': None,
                'data_points': 0
            }
            
            # Get CPU utilization
            try:
                cpu_response = cw_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Average', 'Maximum']
                )
                
                cpu_datapoints = cpu_response.get('Datapoints', [])
                if cpu_datapoints:
                    metrics['avg_cpu'] = sum(dp['Average'] for dp in cpu_datapoints) / len(cpu_datapoints)
                    metrics['max_cpu'] = max(dp['Maximum'] for dp in cpu_datapoints)
                    metrics['data_points'] = len(cpu_datapoints)
                    
            except Exception as e:
                logger.warning(f"[{request_id}] Could not get CPU metrics for {instance_id}: {str(e)}")
            
            # Get network metrics
            try:
                network_in_response = cw_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkIn',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                network_in_datapoints = network_in_response.get('Datapoints', [])
                if network_in_datapoints:
                    metrics['avg_network_in'] = sum(dp['Average'] for dp in network_in_datapoints) / len(network_in_datapoints)
                    
            except Exception as e:
                logger.debug(f"[{request_id}] Could not get NetworkIn metrics for {instance_id}: {str(e)}")
            
            try:
                network_out_response = cw_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkOut',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                network_out_datapoints = network_out_response.get('Datapoints', [])
                if network_out_datapoints:
                    metrics['avg_network_out'] = sum(dp['Average'] for dp in network_out_datapoints) / len(network_out_datapoints)
                    
            except Exception as e:
                logger.debug(f"[{request_id}] Could not get NetworkOut metrics for {instance_id}: {str(e)}")
            
            return metrics
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not get metrics for {instance_id}: {str(e)}")
            return {
                'avg_cpu': None,
                'max_cpu': None,
                'avg_network_in': None,
                'avg_network_out': None,
                'data_points': 0
            }
    
    def _get_optimization_recommendation(self, metrics: Dict[str, Optional[float]], 
                                       instance_type: str, current_cost: float) -> Dict[str, Any]:
        """Generate optimization recommendation based on metrics."""
        avg_cpu = metrics.get('avg_cpu', 0) or 0
        max_cpu = metrics.get('max_cpu', 0) or 0
        data_points = metrics.get('data_points', 0)
        
        # Determine confidence level based on data availability
        if data_points < 24:  # Less than 1 day of hourly data
            confidence = 'low'
        elif data_points < 168:  # Less than 1 week of hourly data
            confidence = 'medium'
        else:
            confidence = 'high'
        
        # Generate recommendation based on utilization patterns
        if avg_cpu < 1 and max_cpu < 5:
            recommendation = 'terminate'
            potential_savings = current_cost
        elif avg_cpu < 2 and max_cpu < 10:
            recommendation = 'downsize_significantly'
            potential_savings = current_cost * 0.7  # Assume 70% savings
        elif avg_cpu < 5 and max_cpu < 20:
            recommendation = 'downsize'
            potential_savings = current_cost * 0.5  # Assume 50% savings
        elif avg_cpu < 10 and max_cpu < 30:
            recommendation = 'consider_burstable'
            potential_savings = current_cost * 0.3  # Assume 30% savings
        else:
            recommendation = 'monitor'
            potential_savings = 0
        
        return {
            'recommendation': recommendation,
            'potential_savings': round(potential_savings, 2),
            'confidence': confidence
        }
    
    def _generate_idle_resource_insights(self, idle_instances: List[Dict[str, Any]], 
                                       total_analyzed: int) -> List[str]:
        """Generate insights about idle resources."""
        insights = []
        
        if not idle_instances:
            insights.append(f"No idle instances found among {total_analyzed} analyzed instances")
            return insights
        
        idle_count = len(idle_instances)
        idle_percentage = (idle_count / total_analyzed * 100) if total_analyzed > 0 else 0
        
        insights.append(f"Found {idle_count} idle instances ({idle_percentage:.1f}% of analyzed instances)")
        
        # Analyze by recommendation type
        terminate_count = len([i for i in idle_instances if i['optimization_recommendation'] == 'terminate'])
        downsize_count = len([i for i in idle_instances if 'downsize' in i['optimization_recommendation']])
        
        if terminate_count > 0:
            insights.append(f"{terminate_count} instances can likely be terminated safely")
        
        if downsize_count > 0:
            insights.append(f"{downsize_count} instances could be downsized for cost savings")
        
        # Analyze by instance type
        instance_types = {}
        for instance in idle_instances:
            instance_type = instance['instance_type']
            if instance_type not in instance_types:
                instance_types[instance_type] = 0
            instance_types[instance_type] += 1
        
        if len(instance_types) > 1:
            most_common_type = max(instance_types.items(), key=lambda x: x[1])
            insights.append(f"Most idle instances are {most_common_type[0]} ({most_common_type[1]} instances)")
        
        # Total savings potential
        total_savings = sum(i['potential_monthly_savings'] for i in idle_instances)
        if total_savings > 100:
            insights.append(f"Potential monthly savings: ${total_savings:.2f}")
        
        return insights
    
    def _estimate_instance_cost(self, instance_type: str) -> float:
        """
        Estimate monthly cost for an instance type.
        This is a simplified estimation - in production, you'd use AWS Pricing API.
        """
        # Simplified cost estimates (USD per month for common instance types)
        cost_estimates = {
            't2.micro': 8.50,
            't2.small': 17.00,
            't2.medium': 34.00,
            't2.large': 68.00,
            't2.xlarge': 136.00,
            't3.micro': 7.60,
            't3.small': 15.20,
            't3.medium': 30.40,
            't3.large': 60.80,
            't3.xlarge': 121.60,
            't3.2xlarge': 243.20,
            'm5.large': 70.00,
            'm5.xlarge': 140.00,
            'm5.2xlarge': 280.00,
            'm5.4xlarge': 560.00,
            'c5.large': 62.00,
            'c5.xlarge': 124.00,
            'c5.2xlarge': 248.00,
            'c5.4xlarge': 496.00,
            'r5.large': 91.00,
            'r5.xlarge': 182.00,
            'r5.2xlarge': 364.00,
            'r5.4xlarge': 728.00,
        }
        
        return cost_estimates.get(instance_type, 50.0)  # Default estimate
    
    def get_cost_optimization_recommendations(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Get comprehensive cost optimization recommendations.
        
        Args:
            params: Parameters including region
            request_id: Request ID for tracking
            
        Returns:
            Cost optimization recommendations
        """
        logger.info(f"[{request_id}] Starting cost optimization recommendations with params: {params}")
        
        try:
            region = params.get('region', 'us-east-1')
            
            recommendations = []
            
            # Get cost analysis for context
            cost_params = {'time_period': 'MONTHLY', 'group_by': 'SERVICE'}
            cost_analysis = self.get_cost_analysis(cost_params, request_id)
            
            # Get idle resources
            idle_params = {'region': region, 'cpu_threshold': 5.0, 'days': 7}
            idle_analysis = self.get_idle_resources(idle_params, request_id)
            
            # Generate EC2 recommendations
            if idle_analysis['total_idle_instances'] > 0:
                recommendations.append({
                    'category': 'EC2 Optimization',
                    'priority': 'high',
                    'potential_savings': idle_analysis['potential_monthly_savings'],
                    'description': f"Found {idle_analysis['total_idle_instances']} idle EC2 instances",
                    'actions': [
                        'Review idle instances for termination or downsizing',
                        'Consider Reserved Instances for consistent workloads',
                        'Implement auto-scaling for variable workloads'
                    ]
                })
            
            # Generate service-specific recommendations based on cost analysis
            if cost_analysis.get('breakdown'):
                for service in cost_analysis['breakdown'][:5]:  # Top 5 services
                    service_name = service['service_name']
                    service_cost = service['cost']
                    
                    if 'S3' in service_name and service_cost > 50:
                        recommendations.append({
                            'category': 'S3 Storage Optimization',
                            'priority': 'medium',
                            'potential_savings': service_cost * 0.3,  # Estimate 30% savings
                            'description': f"S3 costs are ${service_cost:.2f}/month",
                            'actions': [
                                'Implement S3 Intelligent Tiering',
                                'Review and optimize lifecycle policies',
                                'Delete incomplete multipart uploads',
                                'Consider S3 Glacier for archival data'
                            ]
                        })
                    
                    elif 'RDS' in service_name and service_cost > 100:
                        recommendations.append({
                            'category': 'RDS Optimization',
                            'priority': 'medium',
                            'potential_savings': service_cost * 0.25,  # Estimate 25% savings
                            'description': f"RDS costs are ${service_cost:.2f}/month",
                            'actions': [
                                'Consider Reserved Instances for RDS',
                                'Right-size RDS instances based on utilization',
                                'Optimize backup retention periods',
                                'Consider Aurora Serverless for variable workloads'
                            ]
                        })
                    
                    elif 'Lambda' in service_name and service_cost > 20:
                        recommendations.append({
                            'category': 'Lambda Optimization',
                            'priority': 'low',
                            'potential_savings': service_cost * 0.2,  # Estimate 20% savings
                            'description': f"Lambda costs are ${service_cost:.2f}/month",
                            'actions': [
                                'Optimize Lambda memory allocation',
                                'Review function timeout settings',
                                'Consider Provisioned Concurrency usage',
                                'Optimize cold start performance'
                            ]
                        })
            
            # General recommendations
            total_cost = cost_analysis.get('total_cost', 0)
            if total_cost > 500:
                recommendations.append({
                    'category': 'General Cost Management',
                    'priority': 'medium',
                    'potential_savings': total_cost * 0.15,  # Estimate 15% savings
                    'description': f"Total monthly costs are ${total_cost:.2f}",
                    'actions': [
                        'Set up AWS Budgets and Cost Alerts',
                        'Enable AWS Cost Anomaly Detection',
                        'Review and optimize data transfer costs',
                        'Consider AWS Savings Plans for compute workloads',
                        'Implement resource tagging for cost allocation'
                    ]
                })
            
            # Sort recommendations by potential savings
            recommendations.sort(key=lambda x: x.get('potential_savings', 0), reverse=True)
            
            total_potential_savings = sum(r.get('potential_savings', 0) for r in recommendations)
            
            result = {
                'region': region,
                'total_monthly_cost': total_cost,
                'total_potential_savings': round(total_potential_savings, 2),
                'savings_percentage': round((total_potential_savings / total_cost * 100), 2) if total_cost > 0 else 0,
                'recommendations': recommendations,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
            logger.info(f"[{request_id}] Generated {len(recommendations)} cost optimization recommendations")
            return result
            
        except Exception as e:
            logger.error(f"[{request_id}] Error generating cost optimization recommendations: {str(e)}")
            raise
    
    def _get_budget_costs(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current costs from AWS Budgets API as fallback when Cost Explorer is delayed.
        
        Args:
            request_id: Request ID for tracking
            
        Returns:
            Budget cost data or None if unavailable
        """
        try:
            # Get Budgets client
            budgets_client = self.aws_clients.get_budgets_client()
            
            # Get account ID
            sts_client = self.aws_clients.get_sts_client()
            account_id = sts_client.get_caller_identity()['Account']
            
            # List budgets to find one with current spend data
            budgets_response = budgets_client.describe_budgets(AccountId=account_id)
            budgets = budgets_response.get('Budgets', [])
            
            logger.info(f"[{request_id}] Found {len(budgets)} budgets for fallback cost data")
            
            # Look for a budget with actual spend data
            for budget in budgets:
                calculated_spend = budget.get('CalculatedSpend', {})
                actual_spend = calculated_spend.get('ActualSpend', {})
                
                if actual_spend and actual_spend.get('Amount'):
                    cost_amount = float(actual_spend.get('Amount', 0))
                    currency = actual_spend.get('Unit', 'USD')
                    
                    if cost_amount > 0:
                        logger.info(f"[{request_id}] Found budget '{budget.get('BudgetName')}' with actual spend: ${cost_amount:.2f}")
                        
                        # Create a simplified cost response
                        return {
                            'total_cost': round(cost_amount, 2),
                            'currency': currency,
                            'time_period': 'CURRENT_MONTH',
                            'group_by': 'TOTAL',
                            'start_date': datetime.now().date().replace(day=1).isoformat(),
                            'end_date': datetime.now().date().isoformat(),
                            'breakdown': [{
                                'service_name': 'Total (from Budget)',
                                'cost': round(cost_amount, 2),
                                'percentage': 100.0,
                                'note': 'Aggregated cost from AWS Budgets - detailed breakdown not available'
                            }],
                            'daily_costs': [],
                            'cost_trend': {'trend': 'unknown', 'change_percentage': 0},
                            'optimization_insights': [
                                f"Current month spending: ${cost_amount:.2f}",
                                "Detailed cost breakdown will be available once Cost Explorer data updates (8-24 hours)",
                                "This data comes from AWS Budgets which updates more frequently than Cost Explorer"
                            ],
                            'analysis_date': datetime.utcnow().isoformat(),
                            'data_source': 'AWS Budgets API',
                            'note': 'Using AWS Budgets data due to Cost Explorer API delay'
                        }
            
            logger.info(f"[{request_id}] No budgets found with current spend data")
            return None
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not get budget costs: {str(e)}")
            return None 

    def _parse_specific_date(self, time_period: str, request_id: str) -> Optional[Tuple[date, date]]:
        """
        Parse specific month/year combinations like 'december_2024' or 'December 2024'.
        
        Returns:
            Tuple of (start_date, end_date) if parsed successfully, None otherwise
        """
        import re
        from calendar import monthrange
        
        time_period_lower = time_period.lower().replace('_', ' ')
        
        # Month name mapping
        months = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        # Look for month and year patterns
        found_month = None
        found_year = None
        
        for month_name, month_num in months.items():
            if month_name in time_period_lower:
                found_month = month_num
                logger.info(f"[{request_id}] Found month: {month_name} ({month_num})")
                break
        
        # Look for year (2024, 2025, etc.)
        year_match = re.search(r'\b(20\d{2})\b', time_period)
        if year_match:
            found_year = int(year_match.group(1))
            logger.info(f"[{request_id}] Found year: {found_year}")
        
        # If we found a specific month/year, calculate dates
        if found_month:
            if not found_year:
                # Default to current year if no year specified
                found_year = datetime.utcnow().year
                logger.info(f"[{request_id}] No year specified, defaulting to current year: {found_year}")
            
            try:
                # Calculate start and end dates for the specific month
                start_date = datetime(found_year, found_month, 1).date()
                _, last_day = monthrange(found_year, found_month)
                end_date = datetime(found_year, found_month, last_day).date()
                
                logger.info(f"[{request_id}] Parsed specific date range: {start_date} to {end_date}")
                return start_date, end_date
                
            except Exception as e:
                logger.error(f"[{request_id}] Error calculating specific dates: {str(e)}")
                return None
        
        return None

    def _calculate_date_range(self, time_period: str) -> Tuple[date, date]:
        """
        Calculate date range based on time period.
        
        Args:
            time_period: Time period string (DAILY, MONTHLY, YEARLY)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.utcnow().date()
        
        if time_period == 'DAILY':
            start_date = end_date - timedelta(days=1)
        elif time_period == 'MONTHLY':
            # Get current month data from 1st of month to today
            start_date = end_date.replace(day=1)
            # Cost Explorer requires end_date to be exclusive, so we use tomorrow
            # But if we're on the 1st day of the month, we need at least 1 day of data
            if start_date == end_date:
                # If today is the 1st, we have no current month data yet
                # Get previous month's complete data instead
                if end_date.month == 1:
                    start_date = end_date.replace(year=end_date.year-1, month=12, day=1)
                    end_date = end_date.replace(year=end_date.year-1, month=12, day=31)
                else:
                    start_date = end_date.replace(month=end_date.month-1, day=1)
                    # Get last day of previous month
                    import calendar
                    last_day = calendar.monthrange(end_date.year, end_date.month-1)[1]
                    end_date = end_date.replace(month=end_date.month-1, day=last_day)
        elif time_period == 'YEARLY':
            # Get current year data - but ensure start_date is before end_date
            start_date = end_date.replace(month=1, day=1)
            # If today is Jan 1st, get previous year's data instead
            if start_date == end_date:
                start_date = end_date.replace(year=end_date.year-1, month=1, day=1)
                end_date = end_date.replace(year=end_date.year-1, month=12, day=31)
        else:
            # Default to monthly
            start_date = end_date.replace(day=1)
        
        return start_date, end_date