#!/bin/bash

# AWS AI Concierge CDK Deployment Script
# Usage: ./scripts/deploy.sh [environment] [region] [account]

set -e

# Default values
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
ACCOUNT=${3:-}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AWS AI Concierge CDK Deployment${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
if [ -n "$ACCOUNT" ]; then
    echo -e "${BLUE}Account: ${ACCOUNT}${NC}"
fi
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo -e "${YELLOW}Valid environments: dev, staging, prod${NC}"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured or no valid credentials${NC}"
    echo -e "${YELLOW}Please run 'aws configure' or set up your AWS credentials${NC}"
    exit 1
fi

# Get current AWS account and region
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
CURRENT_REGION=$(aws configure get region || echo "us-east-1")

echo -e "${GREEN}✅ AWS CLI configured${NC}"
echo -e "${BLUE}Current Account: ${CURRENT_ACCOUNT}${NC}"
echo -e "${BLUE}Current Region: ${CURRENT_REGION}${NC}"
echo ""

# Validate account if provided
if [ -n "$ACCOUNT" ] && [ "$ACCOUNT" != "$CURRENT_ACCOUNT" ]; then
    echo -e "${RED}❌ Account mismatch: specified $ACCOUNT but current account is $CURRENT_ACCOUNT${NC}"
    exit 1
fi

# Use current account if not specified
if [ -z "$ACCOUNT" ]; then
    ACCOUNT=$CURRENT_ACCOUNT
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ AWS CDK not found${NC}"
    echo -e "${YELLOW}Please install CDK: npm install -g aws-cdk${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CDK found${NC}"

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
npm install

# Build the project
echo -e "${YELLOW}🔨 Building project...${NC}"
npm run build

# Bootstrap CDK if needed (only for first deployment in account/region)
echo -e "${YELLOW}🏗️  Checking CDK bootstrap status...${NC}"
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $REGION > /dev/null 2>&1; then
    echo -e "${YELLOW}🏗️  Bootstrapping CDK for account $ACCOUNT in region $REGION...${NC}"
    cdk bootstrap aws://$ACCOUNT/$REGION
else
    echo -e "${GREEN}✅ CDK already bootstrapped${NC}"
fi

# Synthesize the stack
echo -e "${YELLOW}🔍 Synthesizing CDK stack...${NC}"
cdk synth \
    --context environment=$ENVIRONMENT \
    --context region=$REGION \
    --context account=$ACCOUNT

# Deploy the stack
echo -e "${YELLOW}🚀 Deploying CDK stack...${NC}"
cdk deploy \
    --context environment=$ENVIRONMENT \
    --context region=$REGION \
    --context account=$ACCOUNT \
    --require-approval never \
    --outputs-file cdk-outputs-$ENVIRONMENT.json

# Check deployment status
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Deployment Summary:${NC}"
    echo -e "${BLUE}  Environment: ${ENVIRONMENT}${NC}"
    echo -e "${BLUE}  Region: ${REGION}${NC}"
    echo -e "${BLUE}  Account: ${ACCOUNT}${NC}"
    echo -e "${BLUE}  Stack Name: AwsAiConcierge-${ENVIRONMENT}${NC}"
    echo ""
    
    # Display outputs if file exists
    if [ -f "cdk-outputs-$ENVIRONMENT.json" ]; then
        echo -e "${BLUE}📊 Stack Outputs:${NC}"
        cat cdk-outputs-$ENVIRONMENT.json | jq -r 'to_entries[] | .value | to_entries[] | "  \(.key): \(.value)"'
        echo ""
    fi
    
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo -e "${YELLOW}  1. Upload OpenAPI specification to S3 bucket${NC}"
    echo -e "${YELLOW}  2. Test Lambda function endpoints${NC}"
    echo -e "${YELLOW}  3. Test Bedrock Agent integration${NC}"
    echo -e "${YELLOW}  4. Set up monitoring and alerting${NC}"
    
else
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo -e "${YELLOW}Check the error messages above for details${NC}"
    exit 1
fi