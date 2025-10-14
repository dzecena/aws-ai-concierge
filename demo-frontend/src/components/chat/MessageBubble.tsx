import React from 'react';
import { ChatMessage } from '../../types';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.type === 'user';
  const isStreaming = message.streaming;

  const formatContent = (content: string) => {
    // Simple markdown-like formatting for demo
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/•/g, '•')
      .split('\n')
      .map((line, index) => (
        <div key={index} className={index > 0 ? 'mt-1' : ''}>
          <span dangerouslySetInnerHTML={{ __html: line }} />
        </div>
      ));
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-4xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        {/* Avatar and Name */}
        <div className={`flex items-center mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <div className={`flex items-center ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              isUser ? 'bg-aws-blue ml-2' : 'bg-aws-orange mr-2'
            }`}>
              {isUser ? (
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              )}
            </div>
            <span className="text-sm font-medium text-gray-600">
              {isUser ? 'You' : 'AI Concierge'}
            </span>
          </div>
        </div>

        {/* Message Content */}
        <div className={`chat-message ${isUser ? 'user' : 'assistant'} ${
          isStreaming ? 'border-l-4 border-aws-orange' : ''
        }`}>
          {!isUser && message.content.includes('**DEMO DATA**') && (
            <div className="demo-watermark mb-3">
              🧪 DEMO DATA - For evaluation purposes only
            </div>
          )}
          
          <div className="text-sm leading-relaxed">
            {formatContent(message.content)}
          </div>

          {isStreaming && (
            <div className="flex items-center mt-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-aws-orange rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-aws-orange rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-aws-orange rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="ml-2 text-xs text-gray-500">AI is responding...</span>
            </div>
          )}

          {/* Timestamp */}
          <div className={`text-xs text-gray-400 mt-2 ${isUser ? 'text-right' : 'text-left'}`}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
};