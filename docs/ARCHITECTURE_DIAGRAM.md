# AWS AI Concierge - Architecture Diagrams

## Production Architecture Overview

### Mermaid Diagram Code

```mermaid
graph TB
    User[👤 User] --> Bedrock[🤖 Amazon Bedrock Agent<br/>aws-ai-concierge-dev<br/>Claude 3 Haiku]
    
    Bedrock --> Lambda[⚡ AWS Lambda<br/>aws-ai-concierge-tools-dev<br/>512MB, Python 3.11]
    
    Lambda --> CE[💰 Cost Explorer<br/>Cost Analysis]
    Lambda --> EC2[🖥️ EC2<br/>Resource Discovery]
    Lambda --> S3[🪣 S3<br/>Security Assessment]
    Lambda --> RDS[🗄️ RDS<br/>Resource Monitoring]
    Lambda --> CW[📊 CloudWatch<br/>Metrics & Health]
    
    Lambda --> CWLogs[📝 CloudWatch Logs<br/>Audit Trail]
    
    IAM[🔐 IAM Roles<br/>Read-only Permissions] --> Lambda
    IAM --> Bedrock
    
    S3Bucket[🪣 S3 Bucket<br/>OpenAPI Specs] -.-> Bedrock
    
    style User fill:#e1f5fe
    style Bedrock fill:#fff3e0
    style Lambda fill:#fff3e0
    style CE fill:#e8f5e8
    style EC2 fill:#fff3e0
    style S3 fill:#e8f5e8
    style RDS fill:#e3f2fd
    style CW fill:#f3e5f5
    style CWLogs fill:#f3e5f5
    style IAM fill:#ffebee
    style S3Bucket fill:#e8f5e8
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