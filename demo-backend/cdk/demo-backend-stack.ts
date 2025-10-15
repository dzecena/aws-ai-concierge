import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class DemoBackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB table for chat sessions
    const sessionsTable = new dynamodb.Table(this, 'ChatSessions', {
      tableName: 'demo-chat-sessions',
      partitionKey: { name: 'sessionId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // IAM role for Lambda
    const lambdaRole = new iam.Role(this, 'ChatLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      inlinePolicies: {
        BedrockAccess: new iam.PolicyDocument({
          statements: [
            // Bedrock Agent Runtime permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'bedrock-agent-runtime:InvokeAgent',
                'bedrock-runtime:InvokeModel',
                'bedrock:InvokeAgent',
                'bedrock:InvokeModel',
              ],
              resources: ['*'],
            }),
            // DynamoDB permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'dynamodb:PutItem',
                'dynamodb:GetItem',
                'dynamodb:Query',
              ],
              resources: [sessionsTable.tableArn],
            }),
            // Cost Explorer permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'ce:GetCostAndUsage',
                'ce:GetUsageReport',
                'ce:GetReservationCoverage',
                'ce:GetReservationPurchaseRecommendation',
                'ce:GetReservationUtilization',
                'ce:GetDimensionValues',
                'ce:GetRightsizingRecommendation',
                'ce:ListCostCategoryDefinitions',
              ],
              resources: ['*'],
            }),
            // EC2 permissions for resource discovery
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'ec2:DescribeInstances',
                'ec2:DescribeImages',
                'ec2:DescribeSnapshots',
                'ec2:DescribeVolumes',
                'ec2:DescribeSecurityGroups',
                'ec2:DescribeVpcs',
                'ec2:DescribeSubnets',
                'ec2:DescribeNetworkAcls',
                'ec2:DescribeRouteTables',
                'ec2:DescribeInternetGateways',
                'ec2:DescribeNatGateways',
                'ec2:DescribeLoadBalancers',
              ],
              resources: ['*'],
            }),
            // S3 permissions for resource discovery
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                's3:ListAllMyBuckets',
                's3:ListBucket',
                's3:GetBucketLocation',
                's3:GetBucketVersioning',
                's3:GetBucketEncryption',
                's3:GetBucketPublicAccessBlock',
              ],
              resources: ['*'],
            }),
            // RDS permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'rds:DescribeDBInstances',
                'rds:DescribeDBClusters',
                'rds:DescribeDBSnapshots',
                'rds:DescribeDBClusterSnapshots',
              ],
              resources: ['*'],
            }),
            // Lambda permissions for resource discovery
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'lambda:ListFunctions',
                'lambda:GetFunction',
              ],
              resources: ['*'],
            }),
            // CloudWatch permissions
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'cloudwatch:GetMetricStatistics',
                'cloudwatch:ListMetrics',
                'logs:DescribeLogGroups',
              ],
              resources: ['*'],
            }),
          ],
        }),
      },
    });

    // Lambda function for Bedrock Agent proxy
    const chatHandler = new lambda.Function(this, 'BedrockAgentProxy', {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'bedrock-agent-proxy.lambda_handler',
      code: lambda.Code.fromAsset('./lambda'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60),
      memorySize: 512,
      environment: {
        AGENT_ID: 'WWYOPOAATI',
        AGENT_ALIAS_ID: 'TSTALIASID',
      },
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'DemoBackendApi', {
      restApiName: 'AWS AI Concierge Demo Backend',
      description: 'Backend API for AWS AI Concierge demo integration',
      defaultCorsPreflightOptions: {
        allowOrigins: ['https://d3sfryrdjx8e9t.cloudfront.net', 'http://localhost:3000'],
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
    });

    // Chat endpoint
    const chatResource = api.root.addResource('chat');
    chatResource.addMethod('POST', new apigateway.LambdaIntegration(chatHandler));

    // Debug endpoint
    const debugResource = api.root.addResource('debug');
    debugResource.addMethod('POST', new apigateway.LambdaIntegration(chatHandler));

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'Demo Backend API URL',
    });

    new cdk.CfnOutput(this, 'ChatEndpoint', {
      value: `${api.url}chat`,
      description: 'Chat API Endpoint',
    });
  }
}