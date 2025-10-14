// Type definitions for the Demo Interface

export interface User {
  username: string;
  email: string;
  name: string;
  sub: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
}

export interface ChatMessage {
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

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  sessionId: string;
  error: string | null;
}

export interface DemoSession {
  sessionId: string;
  userId: string;
  createdAt: string;
  lastActivity: string;
  messageCount: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    type: string;
  };
  metadata?: {
    requestId: string;
    timestamp: string;
    version: string;
  };
}

export interface BedrockResponse {
  success: boolean;
  operation: string;
  data: any;
  metadata: {
    requestId: string;
    timestamp: string;
    version: string;
  };
}

export interface QuerySuggestion {
  text: string;
  category: 'cost' | 'security' | 'resources' | 'general';
  description: string;
}