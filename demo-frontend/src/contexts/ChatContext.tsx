import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { ChatState, ChatMessage } from '../types';
import { v4 as uuidv4 } from 'uuid';

interface ChatContextType extends ChatState {
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; content: string; streaming?: boolean } }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_STREAMING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_SESSION_ID'; payload: string };

const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, content: action.payload.content, streaming: action.payload.streaming }
            : msg
        ),
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_STREAMING':
      return { ...state, isStreaming: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] };
    case 'SET_SESSION_ID':
      return { ...state, sessionId: action.payload };
    default:
      return state;
  }
};

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  isStreaming: false,
  sessionId: uuidv4(),
  error: null,
};

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const sendMessage = useCallback(async (content: string) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      // Add user message
      const userMessage: ChatMessage = {
        id: uuidv4(),
        type: 'user',
        content,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

      // Set loading state
      dispatch({ type: 'SET_LOADING', payload: true });

      // Create assistant message placeholder
      const assistantMessageId = uuidv4();
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: '',
        timestamp: new Date(),
        streaming: true,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

      // Simulate streaming response for now
      // TODO: Replace with actual API call to backend
      await simulateStreamingResponse(assistantMessageId, content, dispatch);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
      dispatch({ type: 'SET_STREAMING', payload: false });
    }
  }, []);

  const clearMessages = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' });
    dispatch({ type: 'SET_SESSION_ID', payload: uuidv4() });
  }, []);

  const setStreaming = useCallback((streaming: boolean) => {
    dispatch({ type: 'SET_STREAMING', payload: streaming });
  }, []);

  const value: ChatContextType = {
    ...state,
    sendMessage,
    clearMessages,
    setStreaming,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

// Simulate streaming response - will be replaced with real API
const simulateStreamingResponse = async (
  messageId: string,
  userQuery: string,
  dispatch: React.Dispatch<ChatAction>
) => {
  dispatch({ type: 'SET_STREAMING', payload: true });

  // Simulate different responses based on query content
  let response = '';
  if (userQuery.toLowerCase().includes('cost')) {
    response = `**DEMO DATA** - AWS Cost Analysis

Based on your AWS account analysis:

**Total Monthly Cost:** $245.67 USD

**Service Breakdown:**
• Amazon EC2: $123.45 (50.2%)
• Amazon RDS: $67.89 (27.6%)
• Amazon S3: $31.23 (12.7%)
• Other Services: $23.10 (9.4%)

**Cost Optimization Recommendations:**
1. **Idle EC2 Instances:** Found 3 instances with <5% CPU utilization
   - Potential savings: $45.67/month
2. **RDS Right-sizing:** Database instances appear oversized
   - Potential savings: $23.45/month
3. **S3 Storage Classes:** Consider moving old data to IA or Glacier
   - Potential savings: $12.34/month

**Total Potential Savings:** $81.46/month (33.2%)

*This is demo data for evaluation purposes only.*`;
  } else if (userQuery.toLowerCase().includes('security')) {
    response = `**DEMO DATA** - Security Assessment

Security analysis of your AWS environment:

**Overall Security Score:** 7.2/10 (Good)

**Security Findings:**
🔴 **High Priority (2 issues)**
• Security Group allows SSH (port 22) from 0.0.0.0/0
• S3 bucket 'demo-bucket-public' has public read access

🟡 **Medium Priority (3 issues)**
• EBS volumes not encrypted in us-west-2
• CloudTrail logging not enabled in all regions
• IAM users with console access but no MFA

🟢 **Low Priority (1 issue)**
• Some resources missing cost allocation tags

**Recommendations:**
1. Restrict SSH access to specific IP ranges
2. Enable S3 bucket public access blocking
3. Enable EBS encryption by default
4. Configure multi-region CloudTrail
5. Enforce MFA for all IAM users

*This is demo data for evaluation purposes only.*`;
  } else if (userQuery.toLowerCase().includes('resource') || userQuery.toLowerCase().includes('instance')) {
    response = `**DEMO DATA** - Resource Inventory

AWS Resources in your account:

**EC2 Instances (12 total)**
• Running: 8 instances
• Stopped: 4 instances
• Instance Types: t3.medium (6), m5.large (4), c5.xlarge (2)

**RDS Databases (3 total)**
• Production MySQL: db.r5.large (Multi-AZ)
• Staging PostgreSQL: db.t3.medium
• Development MySQL: db.t3.micro

**S3 Buckets (15 total)**
• Total Storage: 2.3 TB
• Largest Bucket: production-data-backup (1.8 TB)
• Public Buckets: 1 (requires attention)

**Lambda Functions (23 total)**
• Active Functions: 18
• Total Invocations (30 days): 1.2M
• Average Duration: 245ms

**Load Balancers (2 total)**
• Application Load Balancer: prod-alb
• Network Load Balancer: api-nlb

*This is demo data for evaluation purposes only.*`;
  } else {
    response = `**DEMO DATA** - AWS AI Concierge Response

I'm here to help you manage and optimize your AWS infrastructure! I can assist with:

**💰 Cost Analysis**
• "What are my AWS costs this month?"
• "Show me cost breakdown by service"
• "Find opportunities to save money"

**🔍 Resource Discovery**
• "List all my EC2 instances"
• "What S3 buckets do I have?"
• "Show me my Lambda functions"

**🛡️ Security Assessment**
• "Are there any security issues?"
• "Check my security group configurations"
• "What resources are publicly accessible?"

**🔧 Optimization**
• "Find idle or underutilized resources"
• "Recommend cost optimizations"
• "Check for best practice violations"

Try asking me about your AWS costs, security, or resources!

*This is demo data for evaluation purposes only.*`;
  }

  // Simulate streaming by adding text gradually
  const words = response.split(' ');
  let currentText = '';

  for (let i = 0; i < words.length; i++) {
    currentText += (i > 0 ? ' ' : '') + words[i];
    
    dispatch({
      type: 'UPDATE_MESSAGE',
      payload: {
        id: messageId,
        content: currentText,
        streaming: true,
      },
    });

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  // Mark streaming as complete
  dispatch({
    type: 'UPDATE_MESSAGE',
    payload: {
      id: messageId,
      content: currentText,
      streaming: false,
    },
  });
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};