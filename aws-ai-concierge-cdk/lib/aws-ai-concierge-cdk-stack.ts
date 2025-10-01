import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
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

    new cdk.CfnOutput(this, 'LogGroupName', {
      value: lambdaLogGroup.logGroupName,
      description: 'CloudWatch log group for Lambda function',
    });
  }
}
