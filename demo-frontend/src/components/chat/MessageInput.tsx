import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { demoConfig } from '../../config/aws-config';

interface MessageInputProps {
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ disabled = false }) => {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const { sendMessage, isLoading } = useChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || disabled || isLoading) {
      return;
    }

    const messageToSend = message.trim();
    setMessage('');
    
    try {
      await sendMessage(messageToSend);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    
    if (value.length <= demoConfig.maxMessageLength) {
      setMessage(value);
      setIsTyping(value.length > 0);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const isDisabled = disabled || isLoading;
  const characterCount = message.length;
  const isNearLimit = characterCount > demoConfig.maxMessageLength * 0.8;

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={isDisabled ? "AI is responding..." : "Ask me about your AWS infrastructure..."}
          disabled={isDisabled}
          rows={1}
          className={`w-full px-4 py-3 pr-12 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-aws-orange focus:border-transparent transition-colors ${
            isDisabled 
              ? 'bg-gray-50 border-gray-200 text-gray-500 cursor-not-allowed' 
              : 'bg-white border-gray-300 text-gray-900'
          }`}
          style={{ minHeight: '48px', maxHeight: '120px' }}
        />
        
        {/* Send Button */}
        <button
          type="submit"
          disabled={isDisabled || !message.trim()}
          className={`absolute right-2 bottom-2 p-2 rounded-md transition-colors ${
            isDisabled || !message.trim()
              ? 'text-gray-400 cursor-not-allowed'
              : 'text-aws-orange hover:bg-orange-50'
          }`}
        >
          {isLoading ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </div>

      {/* Character Count and Tips */}
      <div className="flex justify-between items-center text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span>Press Enter to send, Shift+Enter for new line</span>
          {isTyping && (
            <span className="flex items-center">
              <div className="w-1 h-1 bg-green-500 rounded-full mr-1"></div>
              Typing...
            </span>
          )}
        </div>
        <span className={isNearLimit ? 'text-orange-600 font-medium' : ''}>
          {characterCount}/{demoConfig.maxMessageLength}
        </span>
      </div>
    </form>
  );
};