"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PublicDemoStack = void 0;
const cdk = require("aws-cdk-lib");
const cognito = require("aws-cdk-lib/aws-cognito");
const s3 = require("aws-cdk-lib/aws-s3");
const cloudfront = require("aws-cdk-lib/aws-cloudfront");
const origins = require("aws-cdk-lib/aws-cloudfront-origins");
const iam = require("aws-cdk-lib/aws-iam");
const dynamodb = require("aws-cdk-lib/aws-dynamodb");
const wafv2 = require("aws-cdk-lib/aws-wafv2");
class PublicDemoStack extends cdk.Stack {
    constructor(scope, id, props) {
        super(scope, id, props);
        const { environment, config } = props;
        // 1. AWS Cognito User Pool for Judge Authentication
        const userPool = new cognito.UserPool(this, 'JudgesUserPool', {
            userPoolName: `demo-judges-pool-${environment}`,
            selfSignUpEnabled: false,
            signInAliases: {
                email: true,
                username: false,
            },
            passwordPolicy: {
                minLength: 12,
                requireLowercase: true,
                requireUppercase: true,
                requireDigits: true,
                requireSymbols: true,
                tempPasswordValidity: cdk.Duration.days(7),
            },
            mfa: config.cognitoMfaRequired ? cognito.Mfa.REQUIRED : cognito.Mfa.OPTIONAL,
            removalPolicy: config.removalPolicy,
        });
        // User Pool Client for the React app
        const userPoolClient = new cognito.UserPoolClient(this, 'JudgesUserPoolClient', {
            userPool,
            userPoolClientName: `demo-judges-client-${environment}`,
            generateSecret: false,
            authFlows: {
                userSrp: true,
                userPassword: false,
                adminUserPassword: true, // For admin account creation
            },
            oAuth: {
                flows: {
                    authorizationCodeGrant: true,
                },
                scopes: [cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
            },
            refreshTokenValidity: cdk.Duration.hours(2),
            accessTokenValidity: cdk.Duration.hours(1),
            idTokenValidity: cdk.Duration.hours(1),
        });
        // 2. S3 Bucket for Static Website Hosting
        const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
            bucketName: `demo-interface-${environment}-${this.account}-${this.region}`,
            websiteIndexDocument: 'index.html',
            websiteErrorDocument: 'error.html',
            publicReadAccess: true,
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
            removalPolicy: config.removalPolicy,
            autoDeleteObjects: config.removalPolicy === cdk.RemovalPolicy.DESTROY,
        });
        // 3. WAF Web ACL for Security
        const webAcl = new wafv2.CfnWebACL(this, 'WebACL', {
            scope: 'CLOUDFRONT',
            defaultAction: { allow: {} },
            rules: [
                {
                    name: 'RateLimitRule',
                    priority: 1,
                    statement: {
                        rateBasedStatement: {
                            limit: 2000,
                            aggregateKeyType: 'IP',
                        },
                    },
                    action: { block: {} },
                    visibilityConfig: {
                        sampledRequestsEnabled: true,
                        cloudWatchMetricsEnabled: true,
                        metricName: 'RateLimitRule',
                    },
                },
                {
                    name: 'AWSManagedRulesCommonRuleSet',
                    priority: 2,
                    overrideAction: { none: {} },
                    statement: {
                        managedRuleGroupStatement: {
                            vendorName: 'AWS',
                            name: 'AWSManagedRulesCommonRuleSet',
                        },
                    },
                    visibilityConfig: {
                        sampledRequestsEnabled: true,
                        cloudWatchMetricsEnabled: true,
                        metricName: 'CommonRuleSetMetric',
                    },
                },
            ],
            visibilityConfig: {
                sampledRequestsEnabled: true,
                cloudWatchMetricsEnabled: true,
                metricName: 'webACL',
            },
        });
        // 4. CloudFront Distribution
        const distribution = new cloudfront.Distribution(this, 'Distribution', {
            defaultBehavior: {
                origin: new origins.S3Origin(websiteBucket),
                viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress: true,
            },
            defaultRootObject: 'index.html',
            errorResponses: [
                {
                    httpStatus: 404,
                    responseHttpStatus: 200,
                    responsePagePath: '/index.html', // SPA routing
                },
            ],
            webAclId: webAcl.attrArn,
        });
        // 5. DynamoDB Tables
        const sessionsTable = new dynamodb.Table(this, 'SessionsTable', {
            tableName: `demo-sessions-${environment}`,
            partitionKey: { name: 'sessionId', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: config.removalPolicy,
            pointInTimeRecovery: environment === 'prod',
        });
        sessionsTable.addGlobalSecondaryIndex({
            indexName: 'userId-createdAt-index',
            partitionKey: { name: 'userId', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'createdAt', type: dynamodb.AttributeType.STRING },
        });
        const conversationsTable = new dynamodb.Table(this, 'ConversationsTable', {
            tableName: `demo-conversations-${environment}`,
            partitionKey: { name: 'sessionId', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'messageId', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: config.removalPolicy,
            pointInTimeRecovery: environment === 'prod',
        });
        // 6. Lambda Execution Role
        const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
            roleName: `demo-lambda-role-${environment}`,
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
            ],
            inlinePolicies: {
                DemoPolicy: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'dynamodb:GetItem',
                                'dynamodb:PutItem',
                                'dynamodb:UpdateItem',
                                'dynamodb:DeleteItem',
                                'dynamodb:Query',
                                'dynamodb:Scan',
                            ],
                            resources: [
                                sessionsTable.tableArn,
                                conversationsTable.tableArn,
                                `${sessionsTable.tableArn}/index/*`,
                                `${conversationsTable.tableArn}/index/*`,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'bedrock:InvokeAgent',
                                'bedrock:InvokeModel',
                            ],
                            resources: ['*'], // Will be restricted to specific agent
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'execute-api:ManageConnections',
                            ],
                            resources: ['*'], // WebSocket API connections
                        }),
                    ],
                }),
            },
        });
        // 7. Outputs for other stacks/applications
        new cdk.CfnOutput(this, 'UserPoolId', {
            value: userPool.userPoolId,
            description: 'Cognito User Pool ID',
            exportName: `${id}-UserPoolId`,
        });
        new cdk.CfnOutput(this, 'UserPoolClientId', {
            value: userPoolClient.userPoolClientId,
            description: 'Cognito User Pool Client ID',
            exportName: `${id}-UserPoolClientId`,
        });
        new cdk.CfnOutput(this, 'WebsiteBucketName', {
            value: websiteBucket.bucketName,
            description: 'S3 Website Bucket Name',
            exportName: `${id}-WebsiteBucketName`,
        });
        new cdk.CfnOutput(this, 'CloudFrontDistributionId', {
            value: distribution.distributionId,
            description: 'CloudFront Distribution ID',
            exportName: `${id}-CloudFrontDistributionId`,
        });
        new cdk.CfnOutput(this, 'CloudFrontDomainName', {
            value: distribution.distributionDomainName,
            description: 'CloudFront Distribution Domain Name',
            exportName: `${id}-CloudFrontDomainName`,
        });
        new cdk.CfnOutput(this, 'SessionsTableName', {
            value: sessionsTable.tableName,
            description: 'DynamoDB Sessions Table Name',
            exportName: `${id}-SessionsTableName`,
        });
        new cdk.CfnOutput(this, 'ConversationsTableName', {
            value: conversationsTable.tableName,
            description: 'DynamoDB Conversations Table Name',
            exportName: `${id}-ConversationsTableName`,
        });
    }
}
exports.PublicDemoStack = PublicDemoStack;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicHVibGljLWRlbW8tc3RhY2suanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyJwdWJsaWMtZGVtby1zdGFjay50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFBQSxtQ0FBbUM7QUFDbkMsbURBQW1EO0FBQ25ELHlDQUF5QztBQUN6Qyx5REFBeUQ7QUFDekQsOERBQThEO0FBQzlELDJDQUEyQztBQUczQyxxREFBcUQ7QUFFckQsK0NBQStDO0FBZS9DLE1BQWEsZUFBZ0IsU0FBUSxHQUFHLENBQUMsS0FBSztJQUM1QyxZQUFZLEtBQWdCLEVBQUUsRUFBVSxFQUFFLEtBQTJCO1FBQ25FLEtBQUssQ0FBQyxLQUFLLEVBQUUsRUFBRSxFQUFFLEtBQUssQ0FBQyxDQUFDO1FBRXhCLE1BQU0sRUFBRSxXQUFXLEVBQUUsTUFBTSxFQUFFLEdBQUcsS0FBSyxDQUFDO1FBRXRDLG9EQUFvRDtRQUNwRCxNQUFNLFFBQVEsR0FBRyxJQUFJLE9BQU8sQ0FBQyxRQUFRLENBQUMsSUFBSSxFQUFFLGdCQUFnQixFQUFFO1lBQzVELFlBQVksRUFBRSxvQkFBb0IsV0FBVyxFQUFFO1lBQy9DLGlCQUFpQixFQUFFLEtBQUs7WUFDeEIsYUFBYSxFQUFFO2dCQUNiLEtBQUssRUFBRSxJQUFJO2dCQUNYLFFBQVEsRUFBRSxLQUFLO2FBQ2hCO1lBQ0QsY0FBYyxFQUFFO2dCQUNkLFNBQVMsRUFBRSxFQUFFO2dCQUNiLGdCQUFnQixFQUFFLElBQUk7Z0JBQ3RCLGdCQUFnQixFQUFFLElBQUk7Z0JBQ3RCLGFBQWEsRUFBRSxJQUFJO2dCQUNuQixjQUFjLEVBQUUsSUFBSTtnQkFDcEIsb0JBQW9CLEVBQUUsR0FBRyxDQUFDLFFBQVEsQ0FBQyxJQUFJLENBQUMsQ0FBQyxDQUFDO2FBQzNDO1lBQ0QsR0FBRyxFQUFFLE1BQU0sQ0FBQyxrQkFBa0IsQ0FBQyxDQUFDLENBQUMsT0FBTyxDQUFDLEdBQUcsQ0FBQyxRQUFRLENBQUMsQ0FBQyxDQUFDLE9BQU8sQ0FBQyxHQUFHLENBQUMs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LENBQUMsQ0FBQztJQUNMLENBQUM7Q0FDRjtBQTdPRCwwQ0E2T0MiLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgKiBhcyBjZGsgZnJvbSAnYXdzLWNkay1saWInO1xyXG5pbXBvcnQgKiBhcyBjb2duaXRvIGZyb20gJ2F3cy1jZGstbGliL2F3cy1jb2duaXRvJztcclxuaW1wb3J0ICogYXMgczMgZnJvbSAnYXdzLWNkay1saWIvYXdzLXMzJztcclxuaW1wb3J0ICogYXMgY2xvdWRmcm9udCBmcm9tICdhd3MtY2RrLWxpYi9hd3MtY2xvdWRmcm9udCc7XHJcbmltcG9ydCAqIGFzIG9yaWdpbnMgZnJvbSAnYXdzLWNkay1saWIvYXdzLWNsb3VkZnJvbnQtb3JpZ2lucyc7XHJcbmltcG9ydCAqIGFzIGlhbSBmcm9tICdhd3MtY2RrLWxpYi9hd3MtaWFtJztcclxuaW1wb3J0ICogYXMgbGFtYmRhIGZyb20gJ2F3cy1jZGstbGliL2F3cy1sYW1iZGEnO1xyXG5pbXBvcnQgKiBhcyBhcGlnYXRld2F5IGZyb20gJ2F3cy1jZGstbGliL2F3cy1hcGlnYXRld2F5JztcclxuaW1wb3J0ICogYXMgZHluYW1vZGIgZnJvbSAnYXdzLWNkay1saWIvYXdzLWR5bmFtb2RiJztcclxuaW1wb3J0ICogYXMgbG9ncyBmcm9tICdhd3MtY2RrLWxpYi9hd3MtbG9ncyc7XHJcbmltcG9ydCAqIGFzIHdhZnYyIGZyb20gJ2F3cy1jZGstbGliL2F3cy13YWZ2Mic7XHJcbmltcG9ydCB7IENvbnN0cnVjdCB9IGZyb20gJ2NvbnN0cnVjdHMnO1xyXG5cclxuZXhwb3J0IGludGVyZmFjZSBQdWJsaWNEZW1vU3RhY2tQcm9wcyBleHRlbmRzIGNkay5TdGFja1Byb3BzIHtcclxuICBlbnZpcm9ubWVudDogc3RyaW5nO1xyXG4gIGNvbmZpZzoge1xyXG4gICAgYWNjb3VudD86IHN0cmluZztcclxuICAgIHJlZ2lvbjogc3RyaW5nO1xyXG4gICAgbG9nUmV0ZW50aW9uRGF5czogbnVtYmVyO1xyXG4gICAgY29nbml0b01mYVJlcXVpcmVkOiBib29sZWFuO1xyXG4gICAgZW5hYmxlRGV0YWlsZWRNb25pdG9yaW5nOiBib29sZWFuO1xyXG4gICAgcmVtb3ZhbFBvbGljeTogY2RrLlJlbW92YWxQb2xpY3k7XHJcbiAgfTtcclxufVxyXG5cclxuZXhwb3J0IGNsYXNzIFB1YmxpY0RlbW9TdGFjayBleHRlbmRzIGNkay5TdGFjayB7XHJcbiAgY29uc3RydWN0b3Ioc2NvcGU6IENvbnN0cnVjdCwgaWQ6IHN0cmluZywgcHJvcHM6IFB1YmxpY0RlbW9TdGFja1Byb3BzKSB7XHJcbiAgICBzdXBlcihzY29wZSwgaWQsIHByb3BzKTtcclxuXHJcbiAgICBjb25zdCB7IGVudmlyb25tZW50LCBjb25maWcgfSA9IHByb3BzO1xyXG5cclxuICAgIC8vIDEuIEFXUyBDb2duaXRvIFVzZXIgUG9vbCBmb3IgSnVkZ2UgQXV0aGVudGljYXRpb25cclxuICAgIGNvbnN0IHVzZXJQb29sID0gbmV3IGNvZ25pdG8uVXNlclBvb2wodGhpcywgJ0p1ZGdlc1VzZXJQb29sJywge1xyXG4gICAgICB1c2VyUG9vbE5hbWU6IGBkZW1vLWp1ZGdlcy1wb29sLSR7ZW52aXJvbm1lbnR9YCxcclxuICAgICAgc2VsZlNpZ25VcEVuYWJsZWQ6IGZhbHNlLCAvLyBPbmx5IGFkbWluIGNhbiBjcmVhdGUgYWNjb3VudHNcclxuICAgICAgc2lnbkluQWxpYXNlczoge1xyXG4gICAgICAgIGVtYWlsOiB0cnVlLFxyXG4gICAgICAgIHVzZXJuYW1lOiBmYWxzZSxcclxuICAgICAgfSxcclxuICAgICAgcGFzc3dvcmRQb2xpY3k6IHtcclxuICAgICAgICBtaW5MZW5ndGg6IDEyLFxyXG4gICAgICAgIHJlcXVpcmVMb3dlcmNhc2U6IHRydWUsXHJcbiAgICAgICAgcmVxdWlyZVVwcGVyY2FzZTogdHJ1ZSxcclxuICAgICAgICByZXF1aXJlRGlnaXRzOiB0cnVlLFxyXG4gICAgICAgIHJlcXVpcmVTeW1ib2xzOiB0cnVlLFxyXG4gICAgICAgIHRlbXBQYXNzd29yZFZhbGlkaXR5OiBjZGsuRHVyYXRpb24uZGF5cyg3KSxcclxuICAgICAgfSxcclxuICAgICAgbWZhOiBjb25maWcuY29nbml0b01mYVJlcXVpcmVkID8gY29nbml0by5NZmEuUkVRVUlSRUQgOiBjb2duaXRvLk1mYS5PUFRJT05BTCxcclxuICAgICAgcmVtb3ZhbFBvbGljeTogY29uZmlnLnJlbW92YWxQb2xpY3ksXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyBVc2VyIFBvb2wgQ2xpZW50IGZvciB0aGUgUmVhY3QgYXBwXHJcbiAgICBjb25zdCB1c2VyUG9vbENsaWVudCA9IG5ldyBjb2duaXRvLlVzZXJQb29sQ2xpZW50KHRoaXMsICdKdWRnZXNVc2VyUG9vbENsaWVudCcsIHtcclxuICAgICAgdXNlclBvb2wsXHJcbiAgICAgIHVzZXJQb29sQ2xpZW50TmFtZTogYGRlbW8tanVkZ2VzLWNsaWVudC0ke2Vudmlyb25tZW50fWAsXHJcbiAgICAgIGdlbmVyYXRlU2VjcmV0OiBmYWxzZSwgLy8gRm9yIFNQQSBhcHBsaWNhdGlvbnNcclxuICAgICAgYXV0aEZsb3dzOiB7XHJcbiAgICAgICAgdXNlclNycDogdHJ1ZSxcclxuICAgICAgICB1c2VyUGFzc3dvcmQ6IGZhbHNlLCAvLyBEaXNhYmxlIGxlc3Mgc2VjdXJlIGZsb3dzXHJcbiAgICAgICAgYWRtaW5Vc2VyUGFzc3dvcmQ6IHRydWUsIC8vIEZvciBhZG1pbiBhY2NvdW50IGNyZWF0aW9uXHJcbiAgICAgIH0sXHJcbiAgICAgIG9BdXRoOiB7XHJcbiAgICAgICAgZmxvd3M6IHtcclxuICAgICAgICAgIGF1dGhvcml6YXRpb25Db2RlR3JhbnQ6IHRydWUsXHJcbiAgICAgICAgfSxcclxuICAgICAgICBzY29wZXM6IFtjb2duaXRvLk9BdXRoU2NvcGUuT1BFTklELCBjb2duaXRvLk9BdXRoU2NvcGUuRU1BSUwsIGNvZ25pdG8uT0F1dGhTY29wZS5QUk9GSUxFXSxcclxuICAgICAgfSxcclxuICAgICAgcmVmcmVzaFRva2VuVmFsaWRpdHk6IGNkay5EdXJhdGlvbi5ob3VycygyKSxcclxuICAgICAgYWNjZXNzVG9rZW5WYWxpZGl0eTogY2RrLkR1cmF0aW9uLmhvdXJzKDEpLFxyXG4gICAgICBpZFRva2VuVmFsaWRpdHk6IGNkay5EdXJhdGlvbi5ob3VycygxKSxcclxuICAgIH0pO1xyXG5cclxuICAgIC8vIDIuIFMzIEJ1Y2tldCBmb3IgU3RhdGljIFdlYnNpdGUgSG9zdGluZ1xyXG4gICAgY29uc3Qgd2Vic2l0ZUJ1Y2tldCA9IG5ldyBzMy5CdWNrZXQodGhpcywgJ1dlYnNpdGVCdWNrZXQnLCB7XHJcbiAgICAgIGJ1Y2tldE5hbWU6IGBkZW1vLWludGVyZmFjZS0ke2Vudmlyb25tZW50fS0ke3RoaXMuYWNjb3VudH0tJHt0aGlzLnJlZ2lvbn1gLFxyXG4gICAgICB3ZWJzaXRlSW5kZXhEb2N1bWVudDogJ2luZGV4Lmh0bWwnLFxyXG4gICAgICB3ZWJzaXRlRXJyb3JEb2N1bWVudDogJ2Vycm9yLmh0bWwnLFxyXG4gICAgICBwdWJsaWNSZWFkQWNjZXNzOiB0cnVlLFxyXG4gICAgICBibG9ja1B1YmxpY0FjY2VzczogczMuQmxvY2tQdWJsaWNBY2Nlc3MuQkxPQ0tfQUNMUyxcclxuICAgICAgcmVtb3ZhbFBvbGljeTogY29uZmlnLnJlbW92YWxQb2xpY3ksXHJcbiAgICAgIGF1dG9EZWxldGVPYmplY3RzOiBjb25maWcucmVtb3ZhbFBvbGljeSA9PT0gY2RrLlJlbW92YWxQb2xpY3kuREVTVFJPWSxcclxuICAgIH0pO1xyXG5cclxuICAgIC8vIDMuIFdBRiBXZWIgQUNMIGZvciBTZWN1cml0eVxyXG4gICAgY29uc3Qgd2ViQWNsID0gbmV3IHdhZnYyLkNmbldlYkFDTCh0aGlzLCAnV2ViQUNMJywge1xyXG4gICAgICBzY29wZTogJ0NMT1VERlJPTlQnLFxyXG4gICAgICBkZWZhdWx0QWN0aW9uOiB7IGFsbG93OiB7fSB9LFxyXG4gICAgICBydWxlczogW1xyXG4gICAgICAgIHtcclxuICAgICAgICAgIG5hbWU6ICdSYXRlTGltaXRSdWxlJyxcclxuICAgICAgICAgIHByaW9yaXR5OiAxLFxyXG4gICAgICAgICAgc3RhdGVtZW50OiB7XHJcbiAgICAgICAgICAgIHJhdGVCYXNlZFN0YXRlbWVudDoge1xyXG4gICAgICAgICAgICAgIGxpbWl0OiAyMDAwLFxyXG4gICAgICAgICAgICAgIGFnZ3JlZ2F0ZUtleVR5cGU6ICdJUCcsXHJcbiAgICAgICAgICAgIH0sXHJcbiAgICAgICAgICB9LFxyXG4gICAgICAgICAgYWN0aW9uOiB7IGJsb2NrOiB7fSB9LFxyXG4gICAgICAgICAgdmlzaWJpbGl0eUNvbmZpZzoge1xyXG4gICAgICAgICAgICBzYW1wbGVkUmVxdWVzdHNFbmFibGVkOiB0cnVlLFxyXG4gICAgICAgICAgICBjbG91ZFdhdGNoTWV0cmljc0VuYWJsZWQ6IHRydWUsXHJcbiAgICAgICAgICAgIG1ldHJpY05hbWU6ICdSYXRlTGltaXRSdWxlJyxcclxuICAgICAgICAgIH0sXHJcbiAgICAgICAgfSxcclxuICAgICAgICB7XHJcbiAgICAgICAgICBuYW1lOiAnQVdTTWFuYWdlZFJ1bGVzQ29tbW9uUnVsZVNldCcsXHJcbiAgICAgICAgICBwcmlvcml0eTogMixcclxuICAgICAgICAgIG92ZXJyaWRlQWN0aW9uOiB7IG5vbmU6IHt9IH0sXHJcbiAgICAgICAgICBzdGF0ZW1lbnQ6IHtcclxuICAgICAgICAgICAgbWFuYWdlZFJ1bGVHcm91cFN0YXRlbWVudDoge1xyXG4gICAgICAgICAgICAgIHZlbmRvck5hbWU6ICdBV1MnLFxyXG4gICAgICAgICAgICAgIG5hbWU6ICdBV1NNYW5hZ2VkUnVsZXNDb21tb25SdWxlU2V0JyxcclxuICAgICAgICAgICAgfSxcclxuICAgICAgICAgIH0sXHJcbiAgICAgICAgICB2aXNpYmlsaXR5Q29uZmlnOiB7XHJcbiAgICAgICAgICAgIHNhbXBsZWRSZXF1ZXN0c0VuYWJsZWQ6IHRydWUsXHJcbiAgICAgICAgICAgIGNsb3VkV2F0Y2hNZXRyaWNzRW5hYmxlZDogdHJ1ZSxcclxuICAgICAgICAgICAgbWV0cmljTmFtZTogJ0NvbW1vblJ1bGVTZXRNZXRyaWMnLFxyXG4gICAgICAgICAgfSxcclxuICAgICAgICB9LFxyXG4gICAgICBdLFxyXG4gICAgICB2aXNpYmlsaXR5Q29uZmlnOiB7XHJcbiAgICAgICAgc2FtcGxlZFJlcXVlc3RzRW5hYmxlZDogdHJ1ZSxcclxuICAgICAgICBjbG91ZFdhdGNoTWV0cmljc0VuYWJsZWQ6IHRydWUsXHJcbiAgICAgICAgbWV0cmljTmFtZTogJ3dlYkFDTCcsXHJcbiAgICAgIH0sXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyA0LiBDbG91ZEZyb250IERpc3RyaWJ1dGlvblxyXG4gICAgY29uc3QgZGlzdHJpYnV0aW9uID0gbmV3IGNsb3VkZnJvbnQuRGlzdHJpYnV0aW9uKHRoaXMsICdEaXN0cmlidXRpb24nLCB7XHJcbiAgICAgIGRlZmF1bHRCZWhhdmlvcjoge1xyXG4gICAgICAgIG9yaWdpbjogbmV3IG9yaWdpbnMuUzNPcmlnaW4od2Vic2l0ZUJ1Y2tldCksXHJcbiAgICAgICAgdmlld2VyUHJvdG9jb2xQb2xpY3k6IGNsb3VkZnJvbnQuVmlld2VyUHJvdG9jb2xQb2xpY3kuUkVESVJFQ1RfVE9fSFRUUFMsXHJcbiAgICAgICAgYWxsb3dlZE1ldGhvZHM6IGNsb3VkZnJvbnQuQWxsb3dlZE1ldGhvZHMuQUxMT1dfR0VUX0hFQURfT1BUSU9OUyxcclxuICAgICAgICBjYWNoZWRNZXRob2RzOiBjbG91ZGZyb250LkNhY2hlZE1ldGhvZHMuQ0FDSEVfR0VUX0hFQURfT1BUSU9OUyxcclxuICAgICAgICBjb21wcmVzczogdHJ1ZSxcclxuICAgICAgfSxcclxuICAgICAgZGVmYXVsdFJvb3RPYmplY3Q6ICdpbmRleC5odG1sJyxcclxuICAgICAgZXJyb3JSZXNwb25zZXM6IFtcclxuICAgICAgICB7XHJcbiAgICAgICAgICBodHRwU3RhdHVzOiA0MDQsXHJcbiAgICAgICAgICByZXNwb25zZUh0dHBTdGF0dXM6IDIwMCxcclxuICAgICAgICAgIHJlc3BvbnNlUGFnZVBhdGg6ICcvaW5kZXguaHRtbCcsIC8vIFNQQSByb3V0aW5nXHJcbiAgICAgICAgfSxcclxuICAgICAgXSxcclxuICAgICAgd2ViQWNsSWQ6IHdlYkFjbC5hdHRyQXJuLFxyXG4gICAgfSk7XHJcblxyXG4gICAgLy8gNS4gRHluYW1vREIgVGFibGVzXHJcbiAgICBjb25zdCBzZXNzaW9uc1RhYmxlID0gbmV3IGR5bmFtb2RiLlRhYmxlKHRoaXMsICdTZXNzaW9uc1RhYmxlJywge1xyXG4gICAgICB0YWJsZU5hbWU6IGBkZW1vLXNlc3Npb25zLSR7ZW52aXJvbm1lbnR9YCxcclxuICAgICAgcGFydGl0aW9uS2V5OiB7IG5hbWU6ICdzZXNzaW9uSWQnLCB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyB9LFxyXG4gICAgICBiaWxsaW5nTW9kZTogZHluYW1vZGIuQmlsbGluZ01vZGUuUEFZX1BFUl9SRVFVRVNULFxyXG4gICAgICByZW1vdmFsUG9saWN5OiBjb25maWcucmVtb3ZhbFBvbGljeSxcclxuICAgICAgcG9pbnRJblRpbWVSZWNvdmVyeTogZW52aXJvbm1lbnQgPT09ICdwcm9kJyxcclxuICAgIH0pO1xyXG5cclxuICAgIHNlc3Npb25zVGFibGUuYWRkR2xvYmFsU2Vjb25kYXJ5SW5kZXgoe1xyXG4gICAgICBpbmRleE5hbWU6ICd1c2VySWQtY3JlYXRlZEF0LWluZGV4JyxcclxuICAgICAgcGFydGl0aW9uS2V5OiB7IG5hbWU6ICd1c2VySWQnLCB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyB9LFxyXG4gICAgICBzb3J0S2V5OiB7IG5hbWU6ICdjcmVhdGVkQXQnLCB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyB9LFxyXG4gICAgfSk7XHJcblxyXG4gICAgY29uc3QgY29udmVyc2F0aW9uc1RhYmxlID0gbmV3IGR5bmFtb2RiLlRhYmxlKHRoaXMsICdDb252ZXJzYXRpb25zVGFibGUnLCB7XHJcbiAgICAgIHRhYmxlTmFtZTogYGRlbW8tY29udmVyc2F0aW9ucy0ke2Vudmlyb25tZW50fWAsXHJcbiAgICAgIHBhcnRpdGlvbktleTogeyBuYW1lOiAnc2Vzc2lvbklkJywgdHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcgfSxcclxuICAgICAgc29ydEtleTogeyBuYW1lOiAnbWVzc2FnZUlkJywgdHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcgfSxcclxuICAgICAgYmlsbGluZ01vZGU6IGR5bmFtb2RiLkJpbGxpbmdNb2RlLlBBWV9QRVJfUkVRVUVTVCxcclxuICAgICAgcmVtb3ZhbFBvbGljeTogY29uZmlnLnJlbW92YWxQb2xpY3ksXHJcbiAgICAgIHBvaW50SW5UaW1lUmVjb3Zlcnk6IGVudmlyb25tZW50ID09PSAncHJvZCcsXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyA2LiBMYW1iZGEgRXhlY3V0aW9uIFJvbGVcclxuICAgIGNvbnN0IGxhbWJkYVJvbGUgPSBuZXcgaWFtLlJvbGUodGhpcywgJ0xhbWJkYUV4ZWN1dGlvblJvbGUnLCB7XHJcbiAgICAgIHJvbGVOYW1lOiBgZGVtby1sYW1iZGEtcm9sZS0ke2Vudmlyb25tZW50fWAsXHJcbiAgICAgIGFzc3VtZWRCeTogbmV3IGlhbS5TZXJ2aWNlUHJpbmNpcGFsKCdsYW1iZGEuYW1hem9uYXdzLmNvbScpLFxyXG4gICAgICBtYW5hZ2VkUG9saWNpZXM6IFtcclxuICAgICAgICBpYW0uTWFuYWdlZFBvbGljeS5mcm9tQXdzTWFuYWdlZFBvbGljeU5hbWUoJ3NlcnZpY2Utcm9sZS9BV1NMYW1iZGFCYXNpY0V4ZWN1dGlvblJvbGUnKSxcclxuICAgICAgXSxcclxuICAgICAgaW5saW5lUG9saWNpZXM6IHtcclxuICAgICAgICBEZW1vUG9saWN5OiBuZXcgaWFtLlBvbGljeURvY3VtZW50KHtcclxuICAgICAgICAgIHN0YXRlbWVudHM6IFtcclxuICAgICAgICAgICAgbmV3IGlhbS5Qb2xpY3lTdGF0ZW1lbnQoe1xyXG4gICAgICAgICAgICAgIGVmZmVjdDogaWFtLkVmZmVjdC5BTExPVyxcclxuICAgICAgICAgICAgICBhY3Rpb25zOiBbXHJcbiAgICAgICAgICAgICAgICAnZHluYW1vZGI6R2V0SXRlbScsXHJcbiAgICAgICAgICAgICAgICAnZHluYW1vZGI6UHV0SXRlbScsXHJcbiAgICAgICAgICAgICAgICAnZHluYW1vZGI6VXBkYXRlSXRlbScsXHJcbiAgICAgICAgICAgICAgICAnZHluYW1vZGI6RGVsZXRlSXRlbScsXHJcbiAgICAgICAgICAgICAgICAnZHluYW1vZGI6UXVlcnknLFxyXG4gICAgICAgICAgICAgICAgJ2R5bmFtb2RiOlNjYW4nLFxyXG4gICAgICAgICAgICAgIF0sXHJcbiAgICAgICAgICAgICAgcmVzb3VyY2VzOiBbXHJcbiAgICAgICAgICAgICAgICBzZXNzaW9uc1RhYmxlLnRhYmxlQXJuLFxyXG4gICAgICAgICAgICAgICAgY29udmVyc2F0aW9uc1RhYmxlLnRhYmxlQXJuLFxyXG4gICAgICAgICAgICAgICAgYCR7c2Vzc2lvbnNUYWJsZS50YWJsZUFybn0vaW5kZXgvKmAsXHJcbiAgICAgICAgICAgICAgICBgJHtjb252ZXJzYXRpb25zVGFibGUudGFibGVBcm59L2luZGV4LypgLFxyXG4gICAgICAgICAgICAgIF0sXHJcbiAgICAgICAgICAgIH0pLFxyXG4gICAgICAgICAgICBuZXcgaWFtLlBvbGljeVN0YXRlbWVudCh7XHJcbiAgICAgICAgICAgICAgZWZmZWN0OiBpYW0uRWZmZWN0LkFMTE9XLFxyXG4gICAgICAgICAgICAgIGFjdGlvbnM6IFtcclxuICAgICAgICAgICAgICAgICdiZWRyb2NrOkludm9rZUFnZW50JyxcclxuICAgICAgICAgICAgICAgICdiZWRyb2NrOkludm9rZU1vZGVsJyxcclxuICAgICAgICAgICAgICBdLFxyXG4gICAgICAgICAgICAgIHJlc291cmNlczogWycqJ10sIC8vIFdpbGwgYmUgcmVzdHJpY3RlZCB0byBzcGVjaWZpYyBhZ2VudFxyXG4gICAgICAgICAgICB9KSxcclxuICAgICAgICAgICAgbmV3IGlhbS5Qb2xpY3lTdGF0ZW1lbnQoe1xyXG4gICAgICAgICAgICAgIGVmZmVjdDogaWFtLkVmZmVjdC5BTExPVyxcclxuICAgICAgICAgICAgICBhY3Rpb25zOiBbXHJcbiAgICAgICAgICAgICAgICAnZXhlY3V0ZS1hcGk6TWFuYWdlQ29ubmVjdGlvbnMnLFxyXG4gICAgICAgICAgICAgIF0sXHJcbiAgICAgICAgICAgICAgcmVzb3VyY2VzOiBbJyonXSwgLy8gV2ViU29ja2V0IEFQSSBjb25uZWN0aW9uc1xyXG4gICAgICAgICAgICB9KSxcclxuICAgICAgICAgIF0sXHJcbiAgICAgICAgfSksXHJcbiAgICAgIH0sXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyA3LiBPdXRwdXRzIGZvciBvdGhlciBzdGFja3MvYXBwbGljYXRpb25zXHJcbiAgICBuZXcgY2RrLkNmbk91dHB1dCh0aGlzLCAnVXNlclBvb2xJZCcsIHtcclxuICAgICAgdmFsdWU6IHVzZXJQb29sLnVzZXJQb29sSWQsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnQ29nbml0byBVc2VyIFBvb2wgSUQnLFxyXG4gICAgICBleHBvcnROYW1lOiBgJHtpZH0tVXNlclBvb2xJZGAsXHJcbiAgICB9KTtcclxuXHJcbiAgICBuZXcgY2RrLkNmbk91dHB1dCh0aGlzLCAnVXNlclBvb2xDbGllbnRJZCcsIHtcclxuICAgICAgdmFsdWU6IHVzZXJQb29sQ2xpZW50LnVzZXJQb29sQ2xpZW50SWQsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnQ29nbml0byBVc2VyIFBvb2wgQ2xpZW50IElEJyxcclxuICAgICAgZXhwb3J0TmFtZTogYCR7aWR9LVVzZXJQb29sQ2xpZW50SWRgLFxyXG4gICAgfSk7XHJcblxyXG4gICAgbmV3IGNkay5DZm5PdXRwdXQodGhpcywgJ1dlYnNpdGVCdWNrZXROYW1lJywge1xyXG4gICAgICB2YWx1ZTogd2Vic2l0ZUJ1Y2tldC5idWNrZXROYW1lLFxyXG4gICAgICBkZXNjcmlwdGlvbjogJ1MzIFdlYnNpdGUgQnVja2V0IE5hbWUnLFxyXG4gICAgICBleHBvcnROYW1lOiBgJHtpZH0tV2Vic2l0ZUJ1Y2tldE5hbWVgLFxyXG4gICAgfSk7XHJcblxyXG4gICAgbmV3IGNkay5DZm5PdXRwdXQodGhpcywgJ0Nsb3VkRnJvbnREaXN0cmlidXRpb25JZCcsIHtcclxuICAgICAgdmFsdWU6IGRpc3RyaWJ1dGlvbi5kaXN0cmlidXRpb25JZCxcclxuICAgICAgZGVzY3JpcHRpb246ICdDbG91ZEZyb250IERpc3RyaWJ1dGlvbiBJRCcsXHJcbiAgICAgIGV4cG9ydE5hbWU6IGAke2lkfS1DbG91ZEZyb250RGlzdHJpYnV0aW9uSWRgLFxyXG4gICAgfSk7XHJcblxyXG4gICAgbmV3IGNkay5DZm5PdXRwdXQodGhpcywgJ0Nsb3VkRnJvbnREb21haW5OYW1lJywge1xyXG4gICAgICB2YWx1ZTogZGlzdHJpYnV0aW9uLmRpc3RyaWJ1dGlvbkRvbWFpbk5hbWUsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnQ2xvdWRGcm9udCBEaXN0cmlidXRpb24gRG9tYWluIE5hbWUnLFxyXG4gICAgICBleHBvcnROYW1lOiBgJHtpZH0tQ2xvdWRGcm9udERvbWFpbk5hbWVgLFxyXG4gICAgfSk7XHJcblxyXG4gICAgbmV3IGNkay5DZm5PdXRwdXQodGhpcywgJ1Nlc3Npb25zVGFibGVOYW1lJywge1xyXG4gICAgICB2YWx1ZTogc2Vzc2lvbnNUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnRHluYW1vREIgU2Vzc2lvbnMgVGFibGUgTmFtZScsXHJcbiAgICAgIGV4cG9ydE5hbWU6IGAke2lkfS1TZXNzaW9uc1RhYmxlTmFtZWAsXHJcbiAgICB9KTtcclxuXHJcbiAgICBuZXcgY2RrLkNmbk91dHB1dCh0aGlzLCAnQ29udmVyc2F0aW9uc1RhYmxlTmFtZScsIHtcclxuICAgICAgdmFsdWU6IGNvbnZlcnNhdGlvbnNUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnRHluYW1vREIgQ29udmVyc2F0aW9ucyBUYWJsZSBOYW1lJyxcclxuICAgICAgZXhwb3J0TmFtZTogYCR7aWR9LUNvbnZlcnNhdGlvbnNUYWJsZU5hbWVgLFxyXG4gICAgfSk7XHJcbiAgfVxyXG59Il19