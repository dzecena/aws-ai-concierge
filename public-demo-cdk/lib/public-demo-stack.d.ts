import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
export interface PublicDemoStackProps extends cdk.StackProps {
    environment: string;
    config: {
        account?: string;
        region: string;
        logRetentionDays: number;
        cognitoMfaRequired: boolean;
        enableDetailedMonitoring: boolean;
        removalPolicy: cdk.RemovalPolicy;
    };
}
export declare class PublicDemoStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: PublicDemoStackProps);
}
