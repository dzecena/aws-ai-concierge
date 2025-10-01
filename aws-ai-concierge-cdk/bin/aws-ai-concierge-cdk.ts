#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AwsAiConciergeCdkStack } from '../lib/aws-ai-concierge-cdk-stack';

const app = new cdk.App();

// Get environment configuration from context or environment variables
const environment = app.node.tryGetContext('environment') || process.env.ENVIRONMENT || 'dev';
const account = app.node.tryGetContext('account') || process.env.CDK_DEFAULT_ACCOUNT;
const region = app.node.tryGetContext('region') || process.env.CDK_DEFAULT_REGION || 'us-east-1';

// Environment-specific stack naming
const stackName = `AwsAiConcierge-${environment}`;

// Deploy the stack with environment-specific configuration
new AwsAiConciergeCdkStack(app, stackName, {
  env: {
    account: account,
    region: region,
  },
  description: `AWS AI Concierge infrastructure for ${environment} environment`,
  tags: {
    Environment: environment,
    Project: 'AWS-AI-Concierge',
    ManagedBy: 'CDK',
    CostCenter: 'Engineering',
    Owner: 'DevOps-Team',
  },
  // Environment-specific configuration
  environmentConfig: {
    environment: environment,
    logRetentionDays: environment === 'prod' ? 90 : 30,
    lambdaMemorySize: environment === 'prod' ? 1024 : 512,
    lambdaTimeout: environment === 'prod' ? 300 : 180,
    enableDetailedMonitoring: environment === 'prod',
    enableXRayTracing: environment === 'prod',
    removalPolicy: environment === 'prod' ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
  },
});