// AWS Configuration for the Demo Interface
export const awsConfig = {
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_cDWMB4e5E',
    userPoolWebClientId: '39c4ta19sbbgpuvkcksq20hvue',
    mandatorySignIn: true,
    authenticationFlowType: 'USER_SRP_AUTH'
  },
  API: {
    endpoints: [
      {
        name: 'DemoAPI',
        endpoint: 'https://api.demo.aws-ai-concierge.com', // Will be updated with actual API Gateway URL
        region: 'us-east-1'
      }
    ]
  }
};

export const demoConfig = {
  environment: 'dev',
  cloudFrontUrl: 'https://d3sfryrdjx8e9t.cloudfront.net',
  maxMessageLength: 1000,
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
  suggestedQueries: [
    "What are my AWS costs this month?",
    "Show me my EC2 instances",
    "Are there any security issues I should know about?",
    "Which resources are costing me the most?",
    "Find idle or underutilized resources"
  ]
};