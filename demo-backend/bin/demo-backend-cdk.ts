#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DemoBackendStack } from '../cdk/demo-backend-stack';

const app = new cdk.App();
new DemoBackendStack(app, 'DemoBackend-dev', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});