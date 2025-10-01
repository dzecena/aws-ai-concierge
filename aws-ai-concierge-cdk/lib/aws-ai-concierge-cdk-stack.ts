import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import { Construct } from 'constructs';

export class AwsAiConciergeCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Bucket for OpenAPI Specification
    const openApiBucket = new s3.Bucket(this, 'OpenApiBucket', {
      bucketName: `aws-ai-concierge-openapi-${this.account}-${this.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development - change to RETAIN for production
      autoDeleteObjects: true, // For development - remove for production
    });

    // CloudWatch Log Group for Lambda
    const lambdaLogGroup = new logs.LogGroup(this, 'LambdaLogGroup', {
      logGroupName: '/aws/lambda/aws-ai-concierge-tools',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // IAM Role for Lambda with read-only AWS permissions
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Execution role for AWS AI Concierge Lambda function',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
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

    // Grant Lambda role access to write to its log group
    lambdaLogGroup.grantWrite(lambdaRole);

    // Grant Lambda role access to read from OpenAPI bucket
    openApiBucket.grantRead(lambdaRole);

    // Lambda Function for AWS AI Concierge Tools
    const conciergeFunction = new lambda.Function(this, 'ConciergeFunction', {
      functionName: 'aws-ai-concierge-tools',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../lambda-src'),
      role: lambdaRole,
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        'OPENAPI_BUCKET': openApiBucket.bucketName,
        'LOG_LEVEL': 'INFO',
      },
      logGroup: lambdaLogGroup,
    });

    // API Gateway for Lambda integration
    const api = new apigateway.RestApi(this, 'ConciergeApi', {
      restApiName: 'AWS AI Concierge API',
      description: 'API Gateway for AWS AI Concierge Lambda function',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
      deployOptions: {
        stageName: 'prod',
        metricsEnabled: true,
      },
    });

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
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'IAM role for AWS AI Concierge Bedrock Agent',
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

    // Grant Lambda invoke permission to Bedrock Agent
    conciergeFunction.grantInvoke(bedrockAgentRole);

    // Bedrock Agent
    const bedrockAgent = new bedrock.CfnAgent(this, 'ConciergeAgent', {
      agentName: 'aws-ai-concierge',
      description: 'AWS AI Concierge - Intelligent assistant for AWS resource management and monitoring',
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
      agentAliasName: 'prod',
      description: 'Production alias for AWS AI Concierge Agent',
    });

    // Outputs for reference
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
