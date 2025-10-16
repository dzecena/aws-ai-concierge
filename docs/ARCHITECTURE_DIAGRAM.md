# AWS AI Concierge - Final Production Architecture

## 🏗️ **Hybrid Multi-Model Architecture Overview**

The AWS AI Concierge implements a groundbreaking **hybrid architecture** that combines Amazon Nova Lite's advanced reasoning with Bedrock Agent Core's reliability, delivering real-time AWS insights with zero hallucination.

### **Hybrid Multi-Model Architecture**

```mermaid
graph TB
    User[👤 User<br/>Natural Language Query] --> API[🌐 API Gateway<br/>CORS Enabled]
    
    API --> Lambda[⚡ AWS Lambda<br/>Hybrid AI Engine<br/>512MB, Python 3.11]
    
    Lambda --> NovaLite[🚀 Amazon Nova Lite<br/>Direct Integration<br/>2.7s avg response]
    Lambda --> BedrockAgent[🤖 Bedrock Agent Core<br/>Claude 3 Haiku Fallback<br/>7s avg response]
    
    Lambda --> DateParser[📅 Intelligent Date Parser<br/>Any Month/Year Support]
    
    DateParser --> CE[💰 Cost Explorer API<br/>Real Historical Data]
    Lambda --> EC2[🖥️ EC2 API<br/>Live Resource Discovery]
    Lambda --> S3[🪣 S3 API<br/>Storage Analysis]
    Lambda --> RDS[🗄️ RDS API<br/>Database Inventory]
    Lambda --> SG[🛡️ Security Groups<br/>Security Assessment]
    
    Lambda --> DDB[📊 DynamoDB<br/>Session Storage]
    Lambda --> CWLogs[📝 CloudWatch Logs<br/>Debug & Audit]
    
    IAMLambda[🔐 Lambda Role<br/>AWS Service Access] --> Lambda
    IAMBedrock[🔐 Bedrock Role<br/>Model Permissions] --> BedrockAgent
    
    Frontend[🌐 React Frontend<br/>CloudFront + S3] --> API
    
    style User fill:#e1f5fe
    style NovaLite fill:#4caf50
    style BedrockAgent fill:#ff9800
    style Lambda fill:#2196f3
    style DateParser fill:#9c27b0
    style CE fill:#e8f5e8
    style Frontend fill:#00bcd4
```

### Detailed Component Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bedrock Agent
    participant L as Lambda Function
    participant AWS as AWS Services
    participant CW as CloudWatch
    
    U->>B: "What are my AWS costs?"
    B->>B: Parse natural language
    B->>L: getCostAnalysis(time_period="monthly")
    L->>AWS: Cost Explorer API calls
    AWS-->>L: Cost data response
    L->>CW: Log audit trail
    L-->>B: Formatted JSON response
    B->>B: Generate natural language
    B-->>U: "Your AWS costs this month are $245.67..."
    
    Note over U,CW: Response time: 8-12 seconds
    Note over L,AWS: Read-only permissions
```

### Infrastructure Components

```mermaid
graph LR
    subgraph "Production Environment (us-east-1)"
        subgraph "Compute"
            Lambda[AWS Lambda<br/>aws-ai-concierge-tools-dev]
        end
        
        subgraph "AI/ML"
            Bedrock[Amazon Bedrock<br/>Claude 3 Haiku<br/>Agent ID: WWYOPOAATI]
        end
        
        subgraph "Storage"
            S3[S3 Bucket<br/>OpenAPI Specs]
        end
        
        subgraph "Monitoring"
            CWLogs[CloudWatch Logs]
            CWMetrics[CloudWatch Metrics]
            CWAlarms[CloudWatch Alarms]
        end
        
        subgraph "Security"
            IAMLambda[Lambda Execution Role]
            IAMBedrock[Bedrock Agent Role]
        end
        
        subgraph "Target Services"
            CE[Cost Explorer]
            EC2[EC2 Service]
            S3Service[S3 Service]
            RDS[RDS Service]
        end
    end
    
    Bedrock --> Lambda
    Lambda --> CE
    Lambda --> EC2
    Lambda --> S3Service
    Lambda --> RDS
    Lambda --> CWLogs
    IAMLambda --> Lambda
    IAMBedrock --> Bedrock
```

## Cost Breakdown Visualization

```mermaid
pie title Monthly Operating Costs ($55-105)
    "Bedrock (Claude 3 Haiku)" : 50
    "Lambda Execution" : 30
    "CloudWatch" : 15
    "S3 Storage" : 5
```

## Performance Metrics

```mermaid
gantt
    title Response Time Performance (Production Validated)
    dateFormat X
    axisFormat %s
    
    section Simple Queries
    Cost Analysis (Basic)    :0, 5
    EC2 Instance Count      :0, 3
    S3 Bucket List         :0, 2
    
    section Complex Queries
    Detailed Cost Analysis  :0, 12
    Multi-Region Discovery  :0, 15
    Security Assessment     :0, 10
    Idle Resource Analysis  :0, 8
```