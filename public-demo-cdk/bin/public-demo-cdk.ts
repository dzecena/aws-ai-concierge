#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { PublicDemoStack } from '../lib/public-demo-stack';

const app = new cdk.App();

// Get environment from context or default to 'dev'
const environment = app.node.tryGetContext('environment') || 'dev';

// Environment-specific configuration
const envConfig = {
  dev: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    logRetentionDays: 7,
    cognitoMfaRequired: false,
    enableDetailedMonitoring: false,
    removalPolicy: cdk.RemovalPolicy.DESTROY,
  },
  staging: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    logRetentionDays: 30,
    cognitoMfaRequired: true,
    enableDetailedMonitoring: true,
    removalPolicy: cdk.RemovalPolicy.RETAIN,
  },
  prod: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    logRetentionDays: 90,
    cognitoMfaRequired: true,
    enableDetailedMonitoring: true,
    removalPolicy: cdk.RemovalPolicy.RETAIN,
  }
};

const config = envConfig[environment as keyof typeof envConfig] || envConfig.dev;

new PublicDemoStack(app, `PublicDemo-${environment}`, {
  env: {
    account: config.account,
    region: config.region,
  },
  environment,
  config,
  tags: {
    Environment: environment,
    Project: 'AWS-AI-Concierge-Demo',
    ManagedBy: 'CDK',
    CostCenter: 'Demo',
    Owner: 'AI-Concierge-Team',
  },
});

app.synth();