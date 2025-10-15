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
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'bedrock-agent-runtime:InvokeAgent',
              ],
              resources: ['*'],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'dynamodb:PutItem',
                'dynamodb:GetItem',
                'dynamodb:Query',
              ],
              resources: [sessionsTable.tableArn],
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