import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import { Construct } from 'constructs';

export interface EnvironmentConfig {
  environment: string;
  logRetentionDays: number;
  lambdaMemorySize: number;
  lambdaTimeout: number;
  enableDetailedMonitoring: boolean;
  enableXRayTracing: boolean;
  removalPolicy: cdk.RemovalPolicy;
}

export interface AwsAiConciergeCdkStackProps extends cdk.StackProps {
  environmentConfig?: EnvironmentConfig;
}

export class AwsAiConciergeCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: AwsAiConciergeCdkStackProps) {
    super(scope, id, props);

    // Get environment configuration with defaults
    const envConfig: EnvironmentConfig = props?.environmentConfig || {
      environment: 'dev',
      logRetentionDays: 30,
      lambdaMemorySize: 512,
      lambdaTimeout: 180,
      enableDetailedMonitoring: false,
      enableXRayTracing: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    };

    // Common resource tags
    const commonTags = {
      Environment: envConfig.environment,
      Project: 'AWS-AI-Concierge',
      ManagedBy: 'CDK',
      CostCenter: 'Engineering',
      Owner: 'DevOps-Team',
      DeployedAt: new Date().toISOString(),
    };

    // S3 Bucket for OpenAPI Specification
    const openApiBucket = new s3.Bucket(this, 'OpenApiBucket', {
      bucketName: `aws-ai-concierge-openapi-${envConfig.environment}-${this.account}-${this.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: envConfig.removalPolicy,
      autoDeleteObjects: envConfig.removalPolicy === cdk.RemovalPolicy.DESTROY,
      lifecycleRules: [
        {
          id: 'DeleteOldVersions',
          enabled: true,
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
      ],
    });

    // Apply tags to S3 bucket
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(openApiBucket).add(key, value);
    });
    cdk.Tags.of(openApiBucket).add('ResourceType', 'S3Bucket');
    cdk.Tags.of(openApiBucket).add('Purpose', 'OpenAPI-Specification-Storage');

    // CloudWatch Log Group for Lambda
    const lambdaLogGroup = new logs.LogGroup(this, 'LambdaLogGroup', {
      logGroupName: `/aws/lambda/aws-ai-concierge-tools-${envConfig.environment}`,
      retention: envConfig.logRetentionDays as logs.RetentionDays,
      removalPolicy: envConfig.removalPolicy,
    });

    // Apply tags to log group
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(lambdaLogGroup).add(key, value);
    });
    cdk.Tags.of(lambdaLogGroup).add('ResourceType', 'CloudWatchLogGroup');
    cdk.Tags.of(lambdaLogGroup).add('Purpose', 'Lambda-Function-Logs');

    // IAM Role for Lambda with read-only AWS permissions
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: `aws-ai-concierge-lambda-role-${envConfig.environment}`,
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: `Execution role for AWS AI Concierge Lambda function (${envConfig.environment})`,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        ...(envConfig.enableXRayTracing ? [iam.ManagedPolicy.fromAwsManagedPolicyName('AWSXRayDaemonWriteAccess')] : []),
      ],
      inlinePolicies: {
        AWSReadOnlyAccess: new iam.PolicyDocument({
          statements: [
            // Cost Explorer permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'ce:GetCostAndUsage',
                'ce:GetDimensionValues',
                'ce:GetReservationCoverage',
                'ce:GetReservationPurchaseRecommendation',
                'ce:GetReservationUtilization',
                'ce:GetUsageReport',
                'ce:ListCostCategoryDefinitions',
                'ce:GetRightsizingRecommendation',
              ],
              resources: ['*'],
            }),
            // EC2 read-only permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'ec2:Describe*',
                'ec2:Get*',
                'ec2:List*',
              ],
              resources: ['*'],
            }),
            // S3 read-only permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                's3:GetObject',
                's3:GetObjectVersion',
                's3:ListBucket',
                's3:ListAllMyBuckets',
                's3:GetBucketLocation',
                's3:GetBucketVersioning',
                's3:GetEncryptionConfiguration',
              ],
              resources: ['*'],
            }),
            // CloudWatch permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'cloudwatch:GetMetricStatistics',
                'cloudwatch:GetMetricData',
                'cloudwatch:ListMetrics',
                'cloudwatch:DescribeAlarms',
                'cloudwatch:DescribeAlarmsForMetric',
              ],
              resources: ['*'],
            }),
            // IAM read-only permissions for security analysis
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'iam:Get*',
                'iam:List*',
                'iam:GenerateCredentialReport',
                'iam:GenerateServiceLastAccessedDetails',
              ],
              resources: ['*'],
            }),
            // RDS read-only permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'rds:Describe*',
                'rds:ListTagsForResource',
              ],
              resources: ['*'],
            }),
            // Lambda read-only permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'lambda:Get*',
                'lambda:List*',
              ],
              resources: ['*'],
            }),
            // Support API permissions for recommendations
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'support:DescribeTrustedAdvisorChecks',
                'support:DescribeTrustedAdvisorCheckResult',
              ],
              resources: ['*'],
            }),
            // Organizations permissions for account info
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'organizations:DescribeAccount',
                'organizations:DescribeOrganization',
                'organizations:ListAccounts',
              ],
              resources: ['*'],
            }),
          ],
        }),
      },
    });

    // Apply tags to Lambda role
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(lambdaRole).add(key, value);
    });
    cdk.Tags.of(lambdaRole).add('ResourceType', 'IAMRole');
    cdk.Tags.of(lambdaRole).add('Purpose', 'Lambda-Execution-Role');

    // Grant Lambda role access to write to its log group
    lambdaLogGroup.grantWrite(lambdaRole);

    // Grant Lambda role access to read from OpenAPI bucket
    openApiBucket.grantRead(lambdaRole);

    // Lambda Function for AWS AI Concierge Tools
    const conciergeFunction = new lambda.Function(this, 'ConciergeFunction', {
      functionName: `aws-ai-concierge-tools-${envConfig.environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../lambda-src'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(envConfig.lambdaTimeout),
      memorySize: envConfig.lambdaMemorySize,
      environment: {
        'OPENAPI_BUCKET': openApiBucket.bucketName,
        'LOG_LEVEL': envConfig.environment === 'prod' ? 'INFO' : 'DEBUG',
        'ENVIRONMENT': envConfig.environment,
      },
      logGroup: lambdaLogGroup,
      tracing: envConfig.enableXRayTracing ? lambda.Tracing.ACTIVE : lambda.Tracing.DISABLED,
      reservedConcurrentExecutions: envConfig.environment === 'prod' ? 100 : 10,
      deadLetterQueueEnabled: envConfig.environment === 'prod',
    });

    // Apply tags to Lambda function
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(conciergeFunction).add(key, value);
    });
    cdk.Tags.of(conciergeFunction).add('ResourceType', 'LambdaFunction');
    cdk.Tags.of(conciergeFunction).add('Purpose', 'AWS-AI-Concierge-Tools');

    // API Gateway for Lambda integration
    const api = new apigateway.RestApi(this, 'ConciergeApi', {
      restApiName: `AWS AI Concierge API (${envConfig.environment})`,
      description: `API Gateway for AWS AI Concierge Lambda function - ${envConfig.environment} environment`,
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
      deployOptions: {
        stageName: envConfig.environment,
        metricsEnabled: envConfig.enableDetailedMonitoring,
        loggingLevel: envConfig.environment === 'prod' ? apigateway.MethodLoggingLevel.ERROR : apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: envConfig.environment !== 'prod',
        tracingEnabled: envConfig.enableXRayTracing,
        throttlingRateLimit: envConfig.environment === 'prod' ? 1000 : 100,
        throttlingBurstLimit: envConfig.environment === 'prod' ? 2000 : 200,
      },
      policy: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            principals: [new iam.AnyPrincipal()],
            actions: ['execute-api:Invoke'],
            resources: ['*'],
          }),
        ],
      }),
    });

    // Apply tags to API Gateway
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(api).add(key, value);
    });
    cdk.Tags.of(api).add('ResourceType', 'APIGateway');
    cdk.Tags.of(api).add('Purpose', 'Lambda-Integration-API');

    // Lambda integration
    const lambdaIntegration = new apigateway.LambdaIntegration(conciergeFunction, {
      requestTemplates: { 'application/json': '{ "statusCode": "200" }' },
      proxy: true,
    });

    // Add API Gateway endpoints for each tool
    const endpoints = [
      'cost-analysis',
      'idle-resources', 
      'resource-inventory',
      'resource-details',
      'resource-health',
      'security-assessment',
      'encryption-status'
    ];

    endpoints.forEach(endpoint => {
      const resource = api.root.addResource(endpoint);
      resource.addMethod('POST', lambdaIntegration, {
        apiKeyRequired: false,
        authorizationType: apigateway.AuthorizationType.NONE,
      });
    });

    // IAM Role for Bedrock Agent
    const bedrockAgentRole = new iam.Role(this, 'BedrockAgentRole', {
      roleName: `aws-ai-concierge-bedrock-role-${envConfig.environment}`,
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: `IAM role for AWS AI Concierge Bedrock Agent (${envConfig.environment})`,
      inlinePolicies: {
        BedrockAgentPolicy: new iam.PolicyDocument({
          statements: [
            // Allow Bedrock Agent to invoke Lambda function
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['lambda:InvokeFunction'],
              resources: [conciergeFunction.functionArn],
            }),
            // Allow Bedrock Agent to access S3 bucket for OpenAPI spec
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['s3:GetObject'],
              resources: [`${openApiBucket.bucketArn}/*`],
            }),
            // Allow Bedrock Agent to use foundation models
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
              ],
              resources: [
                `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0`,
                `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0`,
              ],
            }),
          ],
        }),
      },
    });

    // Apply tags to Bedrock Agent role
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(bedrockAgentRole).add(key, value);
    });
    cdk.Tags.of(bedrockAgentRole).add('ResourceType', 'IAMRole');
    cdk.Tags.of(bedrockAgentRole).add('Purpose', 'Bedrock-Agent-Execution-Role');

    // Grant Lambda invoke permission to Bedrock Agent
    conciergeFunction.grantInvoke(bedrockAgentRole);

    // Bedrock Agent
    const bedrockAgent = new bedrock.CfnAgent(this, 'ConciergeAgent', {
      agentName: `aws-ai-concierge-${envConfig.environment}`,
      description: `AWS AI Concierge - Intelligent assistant for AWS resource management and monitoring (${envConfig.environment})`,
      agentResourceRoleArn: bedrockAgentRole.roleArn,
      foundationModel: 'anthropic.claude-3-haiku-20240307-v1:0',
      instruction: `You are an AWS Cloud Concierge, an expert assistant for Amazon Web Services management and monitoring. Your primary goal is to help users understand, monitor, and optimize their AWS infrastructure through natural language interactions.

CORE CAPABILITIES:
- Analyze AWS costs and identify optimization opportunities
- Monitor and discover AWS resources across regions
- Provide security and compliance insights
- Translate technical AWS concepts into business-friendly language

TOOL USAGE GUIDELINES:
- Always use the most specific tool available for the user's request
- When multiple regions are involved, clearly specify which regions you're analyzing
- For cost queries, always include the time period and currency in your response
- When security issues are found, prioritize them by risk level
- If a tool returns no results, clearly state this and suggest alternative approaches

RESPONSE FORMAT:
- Use clear, business-friendly language while maintaining technical accuracy
- Always cite the specific AWS region(s) in your responses
- Provide actionable recommendations when possible
- Include relevant timestamps and metadata for context
- Format large datasets in tables or bullet points for readability

ERROR HANDLING:
- If AWS API calls fail, explain the issue in user-friendly terms
- When permissions are insufficient, specify what permissions are needed
- If services are unavailable, provide status information and alternatives
- For ambiguous requests, ask clarifying questions before proceeding

SECURITY PRINCIPLES:
- Never perform write operations without explicit user confirmation
- Always operate with read-only permissions by default
- Respect regional compliance and data residency requirements
- Log all operations for audit purposes

Remember to be helpful, accurate, and always prioritize the user's AWS environment security and cost optimization.`,
      idleSessionTtlInSeconds: 1800, // 30 minutes
      actionGroups: [
        {
          actionGroupName: 'aws-ai-concierge-tools',
          description: 'Tools for AWS cost analysis, resource discovery, and security assessment',
          actionGroupExecutor: {
            lambda: conciergeFunction.functionArn,
          },
          apiSchema: {
            s3: {
              s3BucketName: openApiBucket.bucketName,
              s3ObjectKey: 'aws-ai-concierge-tools.yaml',
            },
          },
          actionGroupState: 'ENABLED',
        },
      ],
    });

    // Bedrock Agent Alias
    const bedrockAgentAlias = new bedrock.CfnAgentAlias(this, 'ConciergeAgentAlias', {
      agentId: bedrockAgent.attrAgentId,
      agentAliasName: envConfig.environment,
      description: `${envConfig.environment.charAt(0).toUpperCase() + envConfig.environment.slice(1)} alias for AWS AI Concierge Agent`,
    });

    // Apply tags to Bedrock Agent (via CloudFormation tags)
    cdk.Tags.of(bedrockAgent).add('Environment', envConfig.environment);
    cdk.Tags.of(bedrockAgent).add('Project', 'AWS-AI-Concierge');
    cdk.Tags.of(bedrockAgent).add('ManagedBy', 'CDK');
    cdk.Tags.of(bedrockAgent).add('ResourceType', 'BedrockAgent');
    cdk.Tags.of(bedrockAgent).add('Purpose', 'AI-Assistant');

    cdk.Tags.of(bedrockAgentAlias).add('Environment', envConfig.environment);
    cdk.Tags.of(bedrockAgentAlias).add('Project', 'AWS-AI-Concierge');
    cdk.Tags.of(bedrockAgentAlias).add('ManagedBy', 'CDK');
    cdk.Tags.of(bedrockAgentAlias).add('ResourceType', 'BedrockAgentAlias');
    cdk.Tags.of(bedrockAgentAlias).add('Purpose', 'AI-Assistant-Alias');

    // CloudWatch Monitoring and Alerting (for production)
    if (envConfig.enableDetailedMonitoring) {
      // Lambda Error Rate Alarm
      const lambdaErrorAlarm = new cloudwatch.Alarm(this, 'LambdaErrorAlarm', {
        alarmName: `aws-ai-concierge-lambda-errors-${envConfig.environment}`,
        alarmDescription: 'Lambda function error rate is too high',
        metric: conciergeFunction.metricErrors({
          period: cdk.Duration.minutes(5),
          statistic: 'Sum',
        }),
        threshold: 10,
        evaluationPeriods: 2,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });

      // Lambda Duration Alarm
      const lambdaDurationAlarm = new cloudwatch.Alarm(this, 'LambdaDurationAlarm', {
        alarmName: `aws-ai-concierge-lambda-duration-${envConfig.environment}`,
        alarmDescription: 'Lambda function duration is too high',
        metric: conciergeFunction.metricDuration({
          period: cdk.Duration.minutes(5),
          statistic: 'Average',
        }),
        threshold: 30000, // 30 seconds
        evaluationPeriods: 3,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });

      // API Gateway 4XX Error Rate Alarm
      const api4xxAlarm = new cloudwatch.Alarm(this, 'Api4xxAlarm', {
        alarmName: `aws-ai-concierge-api-4xx-${envConfig.environment}`,
        alarmDescription: 'API Gateway 4XX error rate is too high',
        metric: new cloudwatch.Metric({
          namespace: 'AWS/ApiGateway',
          metricName: '4XXError',
          dimensionsMap: {
            ApiName: api.restApiName,
            Stage: envConfig.environment,
          },
          period: cdk.Duration.minutes(5),
          statistic: 'Sum',
        }),
        threshold: 50,
        evaluationPeriods: 2,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });

      // API Gateway 5XX Error Rate Alarm
      const api5xxAlarm = new cloudwatch.Alarm(this, 'Api5xxAlarm', {
        alarmName: `aws-ai-concierge-api-5xx-${envConfig.environment}`,
        alarmDescription: 'API Gateway 5XX error rate is too high',
        metric: new cloudwatch.Metric({
          namespace: 'AWS/ApiGateway',
          metricName: '5XXError',
          dimensionsMap: {
            ApiName: api.restApiName,
            Stage: envConfig.environment,
          },
          period: cdk.Duration.minutes(5),
          statistic: 'Sum',
        }),
        threshold: 10,
        evaluationPeriods: 2,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });

      // Apply tags to alarms
      [lambdaErrorAlarm, lambdaDurationAlarm, api4xxAlarm, api5xxAlarm].forEach(alarm => {
        Object.entries(commonTags).forEach(([key, value]) => {
          cdk.Tags.of(alarm).add(key, value);
        });
        cdk.Tags.of(alarm).add('ResourceType', 'CloudWatchAlarm');
        cdk.Tags.of(alarm).add('Purpose', 'Monitoring-Alerting');
      });
    }

    // Outputs for reference
    new cdk.CfnOutput(this, 'Environment', {
      value: envConfig.environment,
      description: 'Deployment environment',
    });

    new cdk.CfnOutput(this, 'OpenApiBucketName', {
      value: openApiBucket.bucketName,
      description: 'S3 bucket name for OpenAPI specification',
    });

    new cdk.CfnOutput(this, 'OpenApiSpecUrl', {
      value: `https://${openApiBucket.bucketName}.s3.amazonaws.com/aws-ai-concierge-tools.yaml`,
      description: 'URL to OpenAPI specification in S3',
    });

    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      value: api.url,
      description: 'API Gateway URL for tool invocation',
    });

    new cdk.CfnOutput(this, 'BedrockAgentId', {
      value: bedrockAgent.attrAgentId,
      description: 'Bedrock Agent ID for AWS AI Concierge',
    });

    new cdk.CfnOutput(this, 'BedrockAgentAliasId', {
      value: bedrockAgentAlias.attrAgentAliasId,
      description: 'Bedrock Agent Alias ID for production',
    });

    new cdk.CfnOutput(this, 'BedrockAgentArn', {
      value: bedrockAgent.attrAgentArn,
      description: 'Bedrock Agent ARN for AWS AI Concierge',
    });

    new cdk.CfnOutput(this, 'LambdaFunctionName', {
      value: conciergeFunction.functionName,
      description: 'Lambda function name for AWS AI Concierge tools',
    });

    new cdk.CfnOutput(this, 'LambdaFunctionArn', {
      value: conciergeFunction.functionArn,
      description: 'Lambda function ARN for Bedrock Agent integration',
    });

    new cdk.CfnOutput(this, 'LambdaRoleArn', {
      value: lambdaRole.roleArn,
      description: 'IAM role ARN for Lambda execution',
    });

    new cdk.CfnOutput(this, 'BedrockAgentRoleArn', {
      value: bedrockAgentRole.roleArn,
      description: 'IAM role ARN for Bedrock Agent',
    });

    new cdk.CfnOutput(this, 'LogGroupName', {
      value: lambdaLogGroup.logGroupName,
      description: 'CloudWatch log group for Lambda function',
    });
  }
}
