# Public Demo Interface - System Design Document

## 1. System Overview

The Public Demo Interface is a secure, serverless web application that provides judges with an intuitive chat interface to evaluate the AWS AI Concierge capabilities. Built on AWS with security-first principles, the system uses AWS Cognito for authentication, React.js for the frontend, and Lambda functions for backend processing.

### 1.1 Architecture Principles
- **Security-First**: AWS Cognito authentication with least privilege access
- **Serverless**: Pay-per-use model with automatic scaling
- **Real-time**: WebSocket streaming for responsive chat experience
- **Audit-Ready**: Comprehensive logging for compliance and analytics
- **Cost-Optimized**: Efficient resource utilization with budget controls

### 1.2 High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Judge Browser │    │   CloudFront     │    │   S3 Static     │
│   (React SPA)   │◄──►│   (CDN + WAF)    │◄──►│   Website       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  AWS Cognito    │    │  API Gateway     │    │  Lambda         │
│  (Auth)         │◄──►│  (REST+WebSocket)│◄──►│  Functions      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   DynamoDB       │    │  Existing       │
                       │   (Sessions)     │    │  Bedrock Agent  │
                       └──────────────────┘    └─────────────────┘
```

## 2. Component Architecture

### 2.1 Frontend Components

#### 2.1.1 React.js Single Page Application
- **Framework**: React 18 with TypeScript
- **State Management**: React Context API + useReducer
- **Styling**: Tailwind CSS for responsive design
- **Authentication**: AWS Amplify Auth library
- **Real-time**: WebSocket client for streaming responses

**Key Components**:
```typescript
// Main application structure
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── SessionManager.tsx
│   ├── chat/
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   └── StreamingResponse.tsx
│   ├── demo/
│   │   ├── WelcomePanel.tsx
│   │   ├── SuggestedQueries.tsx
│   │   └── HelpPanel.tsx
│   └── common/
│       ├── LoadingSpinner.tsx
│       ├── ErrorBoundary.tsx
│       └── DemoWatermark.tsx
├── contexts/
│   ├── AuthContext.tsx
│   ├── ChatContext.tsx
│   └── WebSocketContext.tsx
├── services/
│   ├── apiService.ts
│   ├── webSocketService.ts
│   └── authService.ts
└── utils/
    ├── constants.ts
    ├── validators.ts
    └── formatters.ts
```

#### 2.1.2 Authentication Flow
```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: CognitoUser | null;
  session: CognitoUserSession | null;
  loading: boolean;
  error: string | null;
}

// Authentication service integration
class AuthService {
  async signIn(username: string, password: string): Promise<AuthResult>
  async signOut(): Promise<void>
  async getCurrentSession(): Promise<CognitoUserSession>
  async refreshSession(): Promise<CognitoUserSession>
}
```

#### 2.1.3 Chat Interface Components
```typescript
interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  streaming?: boolean;
  metadata?: {
    queryType?: string;
    responseTime?: number;
    tokens?: number;
  };
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  sessionId: string;
  error: string | null;
}
```

### 2.2 Backend Components

#### 2.2.1 API Gateway Configuration
**REST API Endpoints**:
- `POST /auth/login` - Authentication (handled by Cognito)
- `GET /chat/history` - Retrieve conversation history
- `POST /chat/message` - Send message (fallback for non-WebSocket)
- `GET /demo/suggestions` - Get suggested queries
- `GET /health` - Health check endpoint

**WebSocket API**:
- `$connect` - Establish WebSocket connection
- `$disconnect` - Clean up WebSocket connection
- `sendMessage` - Send chat message
- `streamResponse` - Receive streaming response

#### 2.2.2 Lambda Functions

**Authentication Handler** (`auth-handler.py`):
```python
def lambda_handler(event, context):
    """Handle authentication and session management"""
    # Validate Cognito JWT tokens
    # Create/update session in DynamoDB
    # Return user profile and permissions
```

**Chat Handler** (`chat-handler.py`):
```python
def lambda_handler(event, context):
    """Handle chat messages and Bedrock integration"""
    # Validate user session
    # Process and sanitize user input
    # Invoke existing Bedrock Agent
    # Stream response back via WebSocket
    # Log interaction for analytics
```

**WebSocket Manager** (`websocket-handler.py`):
```python
def lambda_handler(event, context):
    """Manage WebSocket connections"""
    # Handle connect/disconnect events
    # Route messages to appropriate handlers
    # Manage connection state in DynamoDB
    # Handle streaming response delivery
```

**Analytics Handler** (`analytics-handler.py`):
```python
def lambda_handler(event, context):
    """Process usage analytics and reporting"""
    # Classify query types using keywords
    # Aggregate usage statistics
    # Generate usage reports
    # Update CloudWatch metrics
```

#### 2.2.3 DynamoDB Schema

**Sessions Table**:
```json
{
  "TableName": "demo-sessions",
  "KeySchema": [
    {"AttributeName": "sessionId", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "sessionId", "AttributeType": "S"},
    {"AttributeName": "userId", "AttributeType": "S"},
    {"AttributeName": "createdAt", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "userId-createdAt-index",
      "KeySchema": [
        {"AttributeName": "userId", "KeyType": "HASH"},
        {"AttributeName": "createdAt", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

**Conversations Table**:
```json
{
  "TableName": "demo-conversations",
  "KeySchema": [
    {"AttributeName": "sessionId", "KeyType": "HASH"},
    {"AttributeName": "messageId", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "sessionId", "AttributeType": "S"},
    {"AttributeName": "messageId", "AttributeType": "S"},
    {"AttributeName": "timestamp", "AttributeType": "S"}
  ]
}
```

**Analytics Table**:
```json
{
  "TableName": "demo-analytics",
  "KeySchema": [
    {"AttributeName": "date", "KeyType": "HASH"},
    {"AttributeName": "metric", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "date", "AttributeType": "S"},
    {"AttributeName": "metric", "AttributeType": "S"}
  ]
}
```

### 2.3 Integration Components

#### 2.3.1 Bedrock Agent Integration
```python
class BedrockIntegration:
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-agent-runtime')
        self.agent_id = os.environ['BEDROCK_AGENT_ID']
        self.agent_alias_id = os.environ['BEDROCK_AGENT_ALIAS_ID']
    
    async def invoke_agent(self, query: str, session_id: str) -> AsyncIterator[str]:
        """Invoke Bedrock Agent and stream response"""
        try:
            response = self.bedrock_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=query
            )
            
            # Stream response chunks
            for chunk in response['completion']:
                if 'chunk' in chunk:
                    yield chunk['chunk']['bytes'].decode('utf-8')
                    
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {str(e)}")
            yield f"I apologize, but I'm experiencing technical difficulties. Please try again."
```

#### 2.3.2 Demo Data Service
```python
class DemoDataService:
    def __init__(self):
        self.demo_data = self._load_demo_data()
    
    def _load_demo_data(self) -> Dict[str, Any]:
        """Load pre-generated demo data from S3 or local files"""
        return {
            'cost_data': self._load_cost_samples(),
            'resource_data': self._load_resource_samples(),
            'security_data': self._load_security_samples()
        }
    
    def get_demo_response(self, query_type: str, parameters: Dict) -> Dict[str, Any]:
        """Return appropriate demo data based on query type"""
        # Return realistic but anonymized sample data
        # Ensure all data is clearly marked as demo
```

## 3. Security Architecture

### 3.1 Authentication and Authorization

#### 3.1.1 AWS Cognito Configuration
```json
{
  "UserPool": {
    "PoolName": "demo-judges-pool",
    "Policies": {
      "PasswordPolicy": {
        "MinimumLength": 12,
        "RequireUppercase": true,
        "RequireLowercase": true,
        "RequireNumbers": true,
        "RequireSymbols": true
      }
    },
    "MfaConfiguration": "OPTIONAL",
    "AccountRecoverySetting": {
      "RecoveryMechanisms": [
        {"Name": "admin_only", "Priority": 1}
      ]
    },
    "UserPoolTags": {
      "Environment": "demo",
      "Purpose": "judge-evaluation"
    }
  }
}
```

#### 3.1.2 IAM Roles and Policies
```json
{
  "JudgeRole": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "execute-api:Invoke"
        ],
        "Resource": "arn:aws:execute-api:*:*:*/demo/*"
      }
    ]
  },
  "LambdaExecutionRole": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "bedrock:InvokeAgent",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "*"
      }
    ]
  }
}
```

### 3.2 Input Validation and Sanitization
```python
class InputValidator:
    def __init__(self):
        self.max_query_length = 1000
        self.rate_limit = 100  # queries per 10 minutes
        
    def validate_query(self, query: str, user_id: str) -> ValidationResult:
        """Validate and sanitize user input"""
        # Check query length
        if len(query) > self.max_query_length:
            raise ValidationError("Query too long")
        
        # Check for XSS attempts
        if self._contains_xss(query):
            raise SecurityError("Potential XSS detected")
        
        # Check rate limiting
        if self._check_rate_limit(user_id):
            raise RateLimitError("Too many requests")
        
        # Sanitize input
        return ValidationResult(
            sanitized_query=self._sanitize(query),
            is_valid=True
        )
```

### 3.3 Network Security
- **CloudFront**: CDN with AWS WAF for DDoS protection
- **API Gateway**: Throttling and request validation
- **VPC Endpoints**: Private communication between services
- **Security Groups**: Restrictive inbound/outbound rules

## 4. Data Flow Architecture

### 4.1 Authentication Flow
```
1. Judge visits demo URL
2. CloudFront serves React SPA from S3
3. React app redirects to Cognito login
4. Judge enters credentials
5. Cognito validates and returns JWT tokens
6. React app stores tokens and establishes WebSocket
7. Backend validates JWT on each request
```

### 4.2 Chat Message Flow
```
1. Judge types message in React interface
2. Frontend validates input and shows loading state
3. Message sent via WebSocket to API Gateway
4. Lambda function validates session and input
5. Lambda invokes existing Bedrock Agent
6. Bedrock Agent processes query and returns response
7. Lambda streams response back via WebSocket
8. React interface displays streaming response
9. Conversation saved to DynamoDB
10. Analytics updated in background
```

### 4.3 Demo Data Flow
```
1. Bedrock Agent receives query
2. Agent determines if real or demo data needed
3. For demo: Lambda returns pre-generated sample data
4. For real: Agent calls actual AWS APIs (existing functionality)
5. Response formatted with demo watermarks
6. Streamed back to judge interface
```

## 5. Performance Architecture

### 5.1 Frontend Optimization
- **Code Splitting**: Lazy loading of components
- **Caching**: Service worker for offline capability
- **Compression**: Gzip/Brotli compression via CloudFront
- **CDN**: Global edge locations for low latency

### 5.2 Backend Optimization
- **Lambda Provisioned Concurrency**: Eliminate cold starts
- **DynamoDB On-Demand**: Auto-scaling based on traffic
- **Connection Pooling**: Reuse database connections
- **Caching**: ElastiCache for frequently accessed data

### 5.3 Real-time Performance
```python
class StreamingManager:
    def __init__(self):
        self.websocket_client = boto3.client('apigatewaymanagementapi')
    
    async def stream_response(self, connection_id: str, response_iterator):
        """Stream response chunks to WebSocket client"""
        try:
            async for chunk in response_iterator:
                await self._send_chunk(connection_id, chunk)
                await asyncio.sleep(0.1)  # Prevent overwhelming client
        except Exception as e:
            await self._send_error(connection_id, str(e))
```

## 6. Monitoring and Analytics

### 6.1 CloudWatch Metrics
```python
CUSTOM_METRICS = {
    'JudgeLogins': 'Count of judge login attempts',
    'QueryTypes': 'Distribution of query categories',
    'ResponseTimes': 'Average response time by query type',
    'ErrorRates': 'Error rate by component',
    'ConcurrentSessions': 'Number of active judge sessions'
}

class MetricsCollector:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def record_query(self, query_type: str, response_time: float):
        """Record query metrics"""
        self.cloudwatch.put_metric_data(
            Namespace='DemoInterface',
            MetricData=[
                {
                    'MetricName': 'QueryCount',
                    'Dimensions': [{'Name': 'QueryType', 'Value': query_type}],
                    'Value': 1,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'ResponseTime',
                    'Dimensions': [{'Name': 'QueryType', 'Value': query_type}],
                    'Value': response_time,
                    'Unit': 'Seconds'
                }
            ]
        )
```

### 6.2 Usage Analytics Dashboard
```python
class AnalyticsDashboard:
    def generate_usage_report(self, start_date: str, end_date: str) -> Dict:
        """Generate comprehensive usage report"""
        return {
            'total_sessions': self._count_sessions(start_date, end_date),
            'total_queries': self._count_queries(start_date, end_date),
            'query_distribution': self._analyze_query_types(start_date, end_date),
            'average_session_duration': self._calculate_avg_duration(start_date, end_date),
            'peak_usage_times': self._identify_peak_times(start_date, end_date),
            'error_analysis': self._analyze_errors(start_date, end_date)
        }
```

## 7. Cost Architecture

### 7.1 Cost Optimization Strategies
```python
# Estimated monthly costs for 50 concurrent judges over 2 weeks
COST_ESTIMATES = {
    'CloudFront': '$10-20',      # CDN and data transfer
    'S3': '$5',                  # Static website hosting
    'API Gateway': '$50-100',    # REST + WebSocket requests
    'Lambda': '$100-200',        # Function executions
    'DynamoDB': '$20-50',        # On-demand pricing
    'Cognito': '$25-50',         # User authentication
    'CloudWatch': '$20-40',      # Logs and metrics
    'Total': '$230-465/month'    # Well under $500/day budget
}
```

### 7.2 Cost Controls
```python
class CostController:
    def __init__(self):
        self.daily_budget = 500  # $500/day limit
        self.cloudwatch = boto3.client('cloudwatch')
        
    def check_daily_costs(self):
        """Monitor daily costs and alert if approaching limits"""
        current_costs = self._get_current_costs()
        if current_costs > self.daily_budget * 0.8:
            self._send_cost_alert(current_costs)
        
    def _send_cost_alert(self, current_costs: float):
        """Send cost alert to administrators"""
        # Send SNS notification
        # Update CloudWatch alarm
        # Optionally throttle requests
```

## 8. Deployment Architecture

### 8.1 Infrastructure as Code (CDK)
```typescript
export class DemoInterfaceStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // Cognito User Pool
    const userPool = new UserPool(this, 'JudgesUserPool', {
      userPoolName: 'demo-judges-pool',
      passwordPolicy: {
        minLength: 12,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      mfa: Mfa.OPTIONAL,
    });

    // S3 + CloudFront for frontend
    const websiteBucket = new Bucket(this, 'WebsiteBucket', {
      websiteIndexDocument: 'index.html',
      publicReadAccess: true,
    });

    const distribution = new CloudFrontWebDistribution(this, 'Distribution', {
      originConfigs: [{
        s3OriginSource: { s3BucketSource: websiteBucket },
        behaviors: [{ isDefaultBehavior: true }],
      }],
      webACLId: this.createWAF(),
    });

    // API Gateway + Lambda
    const api = new RestApi(this, 'DemoApi');
    const chatHandler = new Function(this, 'ChatHandler', {
      runtime: Runtime.PYTHON_3_11,
      handler: 'chat_handler.lambda_handler',
      code: Code.fromAsset('lambda'),
      environment: {
        BEDROCK_AGENT_ID: props.bedrockAgentId,
        BEDROCK_AGENT_ALIAS_ID: props.bedrockAgentAliasId,
      },
    });

    // DynamoDB tables
    const sessionsTable = new Table(this, 'SessionsTable', {
      partitionKey: { name: 'sessionId', type: AttributeType.STRING },
      billingMode: BillingMode.ON_DEMAND,
    });

    // WebSocket API
    const webSocketApi = new WebSocketApi(this, 'WebSocketApi', {
      connectRouteOptions: { integration: new WebSocketLambdaIntegration('ConnectIntegration', connectHandler) },
      disconnectRouteOptions: { integration: new WebSocketLambdaIntegration('DisconnectIntegration', disconnectHandler) },
    });
  }
}
```

### 8.2 CI/CD Pipeline
```yaml
# buildspec.yml
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - npm install
      - npm run test
  build:
    commands:
      - echo Build started on `date`
      - npm run build
      - cdk synth
  post_build:
    commands:
      - echo Build completed on `date`
      - cdk deploy --require-approval never
artifacts:
  files:
    - '**/*'
  base-directory: 'build'
```

## 9. Security Testing and Validation

### 9.1 Security Test Plan
```python
class SecurityTestSuite:
    def test_authentication(self):
        """Test authentication bypass attempts"""
        # Test invalid JWT tokens
        # Test expired sessions
        # Test privilege escalation
        
    def test_input_validation(self):
        """Test input sanitization"""
        # Test XSS payloads
        # Test SQL injection attempts
        # Test command injection
        
    def test_rate_limiting(self):
        """Test rate limiting effectiveness"""
        # Test burst requests
        # Test sustained high volume
        # Test distributed attacks
```

### 9.2 Penetration Testing Checklist
- [ ] Authentication bypass testing
- [ ] Session management testing
- [ ] Input validation testing
- [ ] Authorization testing
- [ ] Rate limiting testing
- [ ] WebSocket security testing
- [ ] Infrastructure security testing

## 10. Operational Procedures

### 10.1 Judge Account Management
```python
class JudgeAccountManager:
    def create_judge_account(self, email: str, name: str) -> str:
        """Create new judge account with temporary password"""
        temp_password = self._generate_temp_password()
        
        user = self.cognito.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name},
                {'Name': 'custom:role', 'Value': 'judge'}
            ],
            TemporaryPassword=temp_password,
            MessageAction='SUPPRESS'  # Don't send AWS email
        )
        
        # Send custom welcome email with instructions
        self._send_welcome_email(email, temp_password)
        return user['User']['Username']
```

### 10.2 Demo Data Management
```python
class DemoDataManager:
    def update_demo_data(self, data_type: str, new_data: Dict):
        """Update demo data with version control"""
        # Validate new data contains no PII
        self._validate_no_pii(new_data)
        
        # Version the data
        version = self._create_version()
        
        # Store in S3 with versioning
        self.s3.put_object(
            Bucket=self.demo_data_bucket,
            Key=f'{data_type}/{version}/data.json',
            Body=json.dumps(new_data),
            ServerSideEncryption='AES256'
        )
        
        # Update current pointer
        self._update_current_version(data_type, version)
```

This design document provides a comprehensive blueprint for implementing the secure, scalable public demo interface that showcases the AWS AI Concierge capabilities while maintaining enterprise-grade security and operational excellence.